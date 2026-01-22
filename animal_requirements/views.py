from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from .models import AnimalRequirement, AnimalRequirementPendingChange, CustomNutrientRequirement
from .forms import AnimalRequirementForm, CustomNutrientRequirementFormSet


@login_required
def animal_requirements_list(request):
    """
    显示动物营养需求列表
    """
    requirements = AnimalRequirement.objects.all().order_by('animal_type', 'body_weight')
    return render(request, 'animal_requirements/list.html', {'requirements': requirements})


@login_required
def animal_requirement_detail(request, requirement_id):
    """
    显示动物营养需求详情，根据状态决定显示原数据还是临时数据
    """
    requirement = get_object_or_404(AnimalRequirement, id=requirement_id)

    # 如果有待审核的变更，并且状态是待审核，则显示待审核的变更
    if requirement.status == AnimalRequirement.PENDING and hasattr(requirement, 'pending_change'):
        # 使用临时数据覆盖原数据
        pending_data = requirement.pending_change

        # 创建一个新的对象来存储合并后的数据
        class MergedRequirement:
            def __init__(self, original, pending):
                # 复制原对象的所有属性
                for field in original._meta.fields:
                    setattr(self, field.name, getattr(original, field.name))

                # 使用临时数据覆盖需要修改的字段
                for field in ['animal_type', 'body_weight', 'daily_gain',
                              'dm_lower', 'dm_upper', 'calcium_lower', 'calcium_upper',
                              'protein_lower', 'protein_upper', 'phosphorus_lower', 'phosphorus_upper',
                              'ndf_lower', 'ndf_upper', 'energy_lower', 'energy_upper',
                              'mp_lower', 'mp_upper']:
                    setattr(self, field, getattr(pending, field))

                # 处理自定义营养需求
                self.custom_nutrients = []
                if pending.custom_nutrients:
                    for custom in pending.custom_nutrients:
                        self.custom_nutrients.append(type('obj', (object,), custom)())

        requirement = MergedRequirement(requirement, pending_data)

    return render(request, 'animal_requirements/detail.html', {'requirement': requirement})


@login_required
def add_animal_requirement(request):
    """
    添加动物营养需求
    """
    if request.method == 'POST':
        form = AnimalRequirementForm(request.POST)
        formset = CustomNutrientRequirementFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 只创建基本的动物营养需求记录，不保存详细的营养指标
            animal_requirement = AnimalRequirement(
                created_by=request.user,
                status=AnimalRequirement.PENDING,  # 直接设置为待审核状态
                # 基本信息字段
                animal_type=form.cleaned_data['animal_type'],
                body_weight=form.cleaned_data['body_weight'],
                daily_gain=form.cleaned_data['daily_gain'],
                # 固定营养需求字段初始化为0，审核通过后才更新
                dm_lower=0,
                dm_upper=0,
                calcium_lower=0,
                calcium_upper=0,
                protein_lower=0,
                protein_upper=0,
                phosphorus_lower=0,
                phosphorus_upper=0,
                ndf_lower=0,
                ndf_upper=0,
                energy_lower=0,
                energy_upper=0,
                mp_lower=0,
                mp_upper=0,
            )
            animal_requirement.save()

            # 处理自定义营养需求数据
            custom_nutrients_data = []
            for custom_form in formset:
                if custom_form.cleaned_data and not custom_form.cleaned_data.get('DELETE', False):
                    custom_nutrients_data.append({
                        'nutrient_name': custom_form.cleaned_data['nutrient_name'],
                        'nutrient_lower': float(custom_form.cleaned_data['nutrient_lower']),
                        'nutrient_upper': float(custom_form.cleaned_data['nutrient_upper']),
                        'unit': custom_form.cleaned_data['unit']
                    })

            # 创建待审核变更记录，将所有营养指标数据放入临时表
            pending_change = AnimalRequirementPendingChange(
                requirement=animal_requirement,
                animal_type=form.cleaned_data['animal_type'],
                body_weight=form.cleaned_data['body_weight'],
                daily_gain=form.cleaned_data['daily_gain'],
                # 初始值从表单获取，默认0
                dm_lower=0,
                dm_upper=0,
                calcium_lower=0,
                calcium_upper=0,
                protein_lower=0,
                protein_upper=0,
                phosphorus_lower=0,
                phosphorus_upper=0,
                ndf_lower=0,
                ndf_upper=0,
                energy_lower=0,
                energy_upper=0,
                mp_lower=0,
                mp_upper=0,
                custom_nutrients=custom_nutrients_data,
                created_by=request.user
            )

            # 只有当用户勾选了复选框时，才更新待审核变更中的营养指标字段
            nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']
            for nutrient in nutrient_fields:
                include_field_name = f"include_{nutrient}"
                lower_field_name = f"{nutrient}_lower"
                upper_field_name = f"{nutrient}_upper"

                if include_field_name in request.POST:
                    # 如果勾选了复选框，使用表单数据更新对应字段
                    setattr(pending_change, lower_field_name, form.cleaned_data[lower_field_name])
                    setattr(pending_change, upper_field_name, form.cleaned_data[upper_field_name])

            # 保存待审核变更
            pending_change.save()

            # 重定向到详情页面
            return redirect('animal_requirement_detail', requirement_id=animal_requirement.id)
    else:
        form = AnimalRequirementForm()
        formset = CustomNutrientRequirementFormSet()

    return render(request, 'animal_requirements/add.html', {
        'form': form,
        'formset': formset
    })


@login_required
def edit_animal_requirement(request, requirement_id):
    """
    编辑动物营养需求
    """
    requirement = get_object_or_404(AnimalRequirement, id=requirement_id)

    # 检查是否已经是待审核状态
    if requirement.status == AnimalRequirement.PENDING:
        return render(request, 'animal_requirements/edit.html', {
            'requirement': requirement,
            'error': '该记录已提交审核，无法编辑'
        })

    if request.method == 'POST':
        # 不使用instance参数，避免直接修改原始对象
        form = AnimalRequirementForm(request.POST, initial={
            'animal_type': requirement.animal_type,
            'body_weight': requirement.body_weight,
            'daily_gain': requirement.daily_gain,
            'dm_lower': requirement.dm_lower,
            'dm_upper': requirement.dm_upper,
            'calcium_lower': requirement.calcium_lower,
            'calcium_upper': requirement.calcium_upper,
            'protein_lower': requirement.protein_lower,
            'protein_upper': requirement.protein_upper,
            'phosphorus_lower': requirement.phosphorus_lower,
            'phosphorus_upper': requirement.phosphorus_upper,
            'ndf_lower': requirement.ndf_lower,
            'ndf_upper': requirement.ndf_upper,
            'energy_lower': requirement.energy_lower,
            'energy_upper': requirement.energy_upper,
            'mp_lower': requirement.mp_lower,
            'mp_upper': requirement.mp_upper,
        })
        # 创建表单集对象处理自定义营养需求数据
        formset = CustomNutrientRequirementFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 获取自定义营养需求数据
            custom_nutrients_data = []
            for custom_form in formset:
                if custom_form.cleaned_data and not custom_form.cleaned_data.get('DELETE', False):
                    custom_data = {
                        'nutrient_name': custom_form.cleaned_data['nutrient_name'],
                        'nutrient_lower': float(custom_form.cleaned_data['nutrient_lower']),
                        'nutrient_upper': float(custom_form.cleaned_data['nutrient_upper']),
                        'unit': custom_form.cleaned_data['unit']
                    }
                    custom_nutrients_data.append(custom_data)

            # 检查是否有实际修改
            has_changes = False

            # 1. 检查基本信息字段是否有变化
            if (form.cleaned_data['animal_type'] != requirement.animal_type or
                    form.cleaned_data['body_weight'] != requirement.body_weight or
                    form.cleaned_data['daily_gain'] != requirement.daily_gain):
                has_changes = True

            # 2. 检查营养指标字段是否有变化（当用户勾选了相应的复选框时）
            nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']
            for nutrient in nutrient_fields:
                include_field_name = f"include_{nutrient}"
                lower_field_name = f"{nutrient}_lower"
                upper_field_name = f"{nutrient}_upper"

                if include_field_name in request.POST:
                    # 如果勾选了复选框，从表单数据中获取值
                    form_lower = form.cleaned_data[lower_field_name]
                    form_upper = form.cleaned_data[upper_field_name]
                    original_lower = getattr(requirement, lower_field_name)
                    original_upper = getattr(requirement, upper_field_name)

                    if form_lower != original_lower or form_upper != original_upper:
                        has_changes = True
                        break

            # 3. 检查自定义营养需求数据是否有变化
            # 获取原始自定义营养需求数据
            original_custom_nutrients = list(
                requirement.custom_nutrients.values('nutrient_name', 'nutrient_lower', 'nutrient_upper', 'unit'))

            # 转换为与表单数据相同的格式
            original_custom_data = []
            for item in original_custom_nutrients:
                original_custom_data.append({
                    'nutrient_name': item['nutrient_name'],
                    'nutrient_lower': float(item['nutrient_lower']),
                    'nutrient_upper': float(item['nutrient_upper']),
                    'unit': item['unit']
                })

            # 比较自定义营养需求数据
            if sorted(custom_nutrients_data, key=lambda x: x['nutrient_name']) != sorted(original_custom_data,
                                                                                         key=lambda x: x[
                                                                                             'nutrient_name']):
                has_changes = True

            # 如果没有任何变化，直接重定向到详情页面
            if not has_changes:
                return redirect('animal_requirement_detail', requirement_id=requirement.id)

            # 如果有变化，保存到临时变更表
            # 先删除已有的待审核变更（如果有）
            AnimalRequirementPendingChange.objects.filter(requirement=requirement).delete()

            # 创建待审核变更对象
            pending_change = AnimalRequirementPendingChange(
                requirement=requirement,
                animal_type=form.cleaned_data['animal_type'],
                body_weight=form.cleaned_data['body_weight'],
                daily_gain=form.cleaned_data['daily_gain'],
                # 营养指标字段初始值从原始对象获取
                dm_lower=requirement.dm_lower,
                dm_upper=requirement.dm_upper,
                calcium_lower=requirement.calcium_lower,
                calcium_upper=requirement.calcium_upper,
                protein_lower=requirement.protein_lower,
                protein_upper=requirement.protein_upper,
                phosphorus_lower=requirement.phosphorus_lower,
                phosphorus_upper=requirement.phosphorus_upper,
                ndf_lower=requirement.ndf_lower,
                ndf_upper=requirement.ndf_upper,
                energy_lower=requirement.energy_lower,
                energy_upper=requirement.energy_upper,
                mp_lower=requirement.mp_lower,
                mp_upper=requirement.mp_upper,
                custom_nutrients=custom_nutrients_data,
                created_by=request.user
            )

            # 只有当用户勾选了复选框时，才更新营养指标字段
            for nutrient in nutrient_fields:
                include_field_name = f"include_{nutrient}"
                lower_field_name = f"{nutrient}_lower"
                upper_field_name = f"{nutrient}_upper"

                if include_field_name in request.POST:
                    # 如果勾选了复选框，使用表单数据更新对应字段
                    setattr(pending_change, lower_field_name, form.cleaned_data[lower_field_name])
                    setattr(pending_change, upper_field_name, form.cleaned_data[upper_field_name])

            # 保存待审核变更
            pending_change.save()

            # 更新原记录状态为待审核
            requirement.status = AnimalRequirement.PENDING
            requirement.approved_by = None
            requirement.approved_at = None
            requirement.save(update_fields=['status', 'approved_by', 'approved_at'])

            # 重定向到详情页面
            return redirect('animal_requirement_detail', requirement_id=requirement.id)
    else:
        # 不使用instance参数，而是手动设置初始值
        initial_data = {
            'animal_type': requirement.animal_type,
            'body_weight': requirement.body_weight,
            'daily_gain': requirement.daily_gain,
            # 设置所有营养指标的初始值
            'dm_lower': requirement.dm_lower,
            'dm_upper': requirement.dm_upper,
            'calcium_lower': requirement.calcium_lower,
            'calcium_upper': requirement.calcium_upper,
            'protein_lower': requirement.protein_lower,
            'protein_upper': requirement.protein_upper,
            'phosphorus_lower': requirement.phosphorus_lower,
            'phosphorus_upper': requirement.phosphorus_upper,
            'ndf_lower': requirement.ndf_lower,
            'ndf_upper': requirement.ndf_upper,
            'energy_lower': requirement.energy_lower,
            'energy_upper': requirement.energy_upper,
            'mp_lower': requirement.mp_lower,
            'mp_upper': requirement.mp_upper,
        }
        form = AnimalRequirementForm(initial=initial_data)
        formset = CustomNutrientRequirementFormSet(instance=requirement)

    return render(request, 'animal_requirements/edit.html', {
        'form': form,
        'formset': formset,
        'requirement': requirement
    })


@user_passes_test(lambda u: u.is_superuser)
def review_animal_requirement(request, requirement_id):
    """
    审核动物营养需求（仅管理员可访问）
    """
    requirement = get_object_or_404(AnimalRequirement, id=requirement_id)

    # 检查是否有待审核的变更
    if not hasattr(requirement, 'pending_change'):
        return render(request, 'animal_requirements/detail.html', {
            'requirement': requirement,
            'error': '没有待审核的变更'
        })

    pending_change = requirement.pending_change

    # 添加比较逻辑，确定哪些字段发生了变化
    changed_fields = {}

    # 比较基本信息字段
    basic_fields = ['animal_type', 'body_weight', 'daily_gain']
    for field in basic_fields:
        original_value = getattr(requirement, field)
        new_value = getattr(pending_change, field)
        if original_value != new_value:
            changed_fields[field] = {'original': original_value, 'new': new_value}

    # 比较营养指标字段
    nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']
    for nutrient in nutrient_fields:
        lower_field = f"{nutrient}_lower"
        upper_field = f"{nutrient}_upper"

        original_lower = getattr(requirement, lower_field)
        original_upper = getattr(requirement, upper_field)
        new_lower = getattr(pending_change, lower_field)
        new_upper = getattr(pending_change, upper_field)

        if original_lower != new_lower or original_upper != new_upper:
            changed_fields[nutrient] = {
                'lower': {'original': original_lower, 'new': new_lower},
                'upper': {'original': original_upper, 'new': new_upper}
            }

    # 比较自定义营养需求
    original_custom_nutrients = list(
        requirement.custom_nutrients.values('nutrient_name', 'nutrient_lower', 'nutrient_upper', 'unit'))
    original_custom_data = []
    for item in original_custom_nutrients:
        original_custom_data.append({
            'nutrient_name': item['nutrient_name'],
            'nutrient_lower': float(item['nutrient_lower']),
            'nutrient_upper': float(item['nutrient_upper']),
            'unit': item['unit']
        })

    new_custom_data = pending_change.custom_nutrients or []

    # 识别被删除的自定义营养需求
    original_names = {item['nutrient_name'] for item in original_custom_data}
    new_names = {item['nutrient_name'] for item in new_custom_data}
    deleted_custom_nutrients = [item for item in original_custom_data if item['nutrient_name'] not in new_names]

    # 比较自定义营养需求数据
    if sorted(original_custom_data, key=lambda x: x['nutrient_name']) != sorted(new_custom_data,
                                                                                key=lambda x: x['nutrient_name']):
        changed_fields['custom_nutrients'] = {
            'original': sorted(original_custom_data, key=lambda x: x['nutrient_name']),
            'new': sorted(new_custom_data, key=lambda x: x['nutrient_name']),
            'deleted': sorted(deleted_custom_nutrients, key=lambda x: x['nutrient_name'])
        }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # 审核通过，将临时数据合并到原表
            # 更新基本字段
            for field in ['animal_type', 'body_weight', 'daily_gain',
                          'dm_lower', 'dm_upper', 'calcium_lower', 'calcium_upper',
                          'protein_lower', 'protein_upper', 'phosphorus_lower', 'phosphorus_upper',
                          'ndf_lower', 'ndf_upper', 'energy_lower', 'energy_upper',
                          'mp_lower', 'mp_upper']:
                setattr(requirement, field, getattr(pending_change, field))

            # 更新自定义营养需求
            requirement.custom_nutrients.all().delete()
            if pending_change.custom_nutrients:
                for custom_data in pending_change.custom_nutrients:
                    CustomNutrientRequirement.objects.create(
                        requirement=requirement,
                        nutrient_name=custom_data['nutrient_name'],
                        nutrient_lower=custom_data['nutrient_lower'],
                        nutrient_upper=custom_data['nutrient_upper'],
                        unit=custom_data['unit']
                    )

            # 更新状态
            requirement.status = AnimalRequirement.APPROVED
            requirement.approved_by = request.user
            from django.utils import timezone
            requirement.approved_at = timezone.now()
            requirement.save()

            # 删除临时变更
            pending_change.delete()

        elif action == 'reject':
            # 审核拒绝，删除临时变更
            pending_change.delete()

            # 更新状态为拒绝
            requirement.status = AnimalRequirement.REJECTED
            requirement.approved_by = request.user
            from django.utils import timezone
            requirement.approved_at = timezone.now()
            requirement.save()

        return redirect('animal_requirement_detail', requirement_id=requirement_id)

    return render(request, 'animal_requirements/review.html', {
        'requirement': requirement,
        'pending_change': pending_change,
        'changed_fields': changed_fields
    })


def api_animal_requirement(request, requirement_id):
    try:
        requirement = get_object_or_404(AnimalRequirement, id=requirement_id)

        # 获取当前语言
        from django.utils.translation import get_language
        current_lang = get_language()

        # 根据当前语言获取翻译后的动物类型
        if current_lang == 'en':
            animal_type_translated = getattr(requirement, 'animal_type_en', requirement.animal_type)
        else:
            animal_type_translated = getattr(requirement, 'animal_type_zh_hans', requirement.animal_type)

        # 如果有待审核的变更，并且状态是待审核，则使用待审核的数据
        if requirement.status == AnimalRequirement.PENDING and hasattr(requirement, 'pending_change'):
            pending = requirement.pending_change
            data = {
                'id': requirement.id,
                'animal_type': animal_type_translated,
                'body_weight': float(pending.body_weight),
                'daily_gain': float(pending.daily_gain),
                'dm_lower': float(pending.dm_lower),
                'dm_upper': float(pending.dm_upper),
                'ndf_lower': float(pending.ndf_lower),
                'ndf_upper': float(pending.ndf_upper),
                'mp_lower': float(pending.mp_lower),
                'mp_upper': float(pending.mp_upper),
                'cp_lower': float(pending.protein_lower),
                'cp_upper': float(pending.protein_upper),
                'ca_lower': float(pending.calcium_lower),
                'ca_upper': float(pending.calcium_upper),
                'p_lower': float(pending.phosphorus_lower),
                'p_upper': float(pending.phosphorus_upper),
                'energy_lower': float(pending.energy_lower),
                'energy_upper': float(pending.energy_upper),
                'custom_nutrients': pending.custom_nutrients or []
            }
        else:
            # 获取自定义营养需求
            # 从数据库获取最新的自定义营养需求
            custom_nutrients = []
            for custom in requirement.custom_nutrients.all():
                # 根据当前语言获取翻译后的字段
                if current_lang == 'en':
                    nutrient_name = getattr(custom, 'nutrient_name_en', custom.nutrient_name)
                    unit = getattr(custom, 'unit_en', custom.unit)
                else:
                    nutrient_name = getattr(custom, 'nutrient_name_zh_hans', custom.nutrient_name)
                    unit = getattr(custom, 'unit_zh_hans', custom.unit)

                custom_nutrients.append({
                    'name': nutrient_name,
                    'lower': float(custom.nutrient_lower),
                    'upper': float(custom.nutrient_upper),
                    'unit': unit
                })

            data = {
                'id': requirement.id,
                'animal_type': animal_type_translated,
                'body_weight': float(requirement.body_weight),
                'daily_gain': float(requirement.daily_gain),
                'dm_lower': float(requirement.dm_lower),
                'dm_upper': float(requirement.dm_upper),
                'ndf_lower': float(requirement.ndf_lower),
                'ndf_upper': float(requirement.ndf_upper),
                'mp_lower': float(requirement.mp_lower),
                'mp_upper': float(requirement.mp_upper),
                'cp_lower': float(requirement.protein_lower),
                'cp_upper': float(requirement.protein_upper),
                'ca_lower': float(requirement.calcium_lower),
                'ca_upper': float(requirement.calcium_upper),
                'p_lower': float(requirement.phosphorus_lower),
                'p_upper': float(requirement.phosphorus_upper),
                'energy_lower': float(requirement.energy_lower),
                'energy_upper': float(requirement.energy_upper),
                'custom_nutrients': custom_nutrients
            }

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
