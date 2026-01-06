from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import Ingredient, IngredientNutrient, CustomIngredientNutrient, IngredientPendingChange
from .forms import IngredientForm, IngredientNutrientForm, CustomIngredientNutrientFormSet


@login_required
def ingredient_detail(request, ingredient_id):
    """
    显示饲料原料详情
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    nutrients = IngredientNutrient.objects.filter(ingredient=ingredient).first()
    custom_nutrients = CustomIngredientNutrient.objects.filter(ingredient=ingredient)

    # 如果有待审核的变更，并且状态是待审核，则显示待审核的变更
    if ingredient.status == Ingredient.PENDING and hasattr(ingredient, 'pending_change'):
        # 使用临时数据覆盖原数据
        pending_data = ingredient.pending_change

        # 创建一个新的对象来存储合并后的数据
        class MergedIngredient:
            def __init__(self, original, pending):
                # 复制原对象的所有属性
                for field in original._meta.fields:
                    setattr(self, field.name, getattr(original, field.name))

                # 使用临时数据覆盖需要修改的字段
                for field in ['name', 'description', 'cost']:
                    setattr(self, field, getattr(pending, field))

        class MergedNutrient:
            def __init__(self, pending):
                # 使用临时数据设置营养成分字段
                for field in ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp']:
                    setattr(self, field, getattr(pending, field))

        ingredient = MergedIngredient(ingredient, pending_data)
        nutrients = MergedNutrient(pending_data)

        # 处理自定义营养成分
        custom_nutrients = []
        if pending_data.custom_nutrients:
            for custom in pending_data.custom_nutrients:
                custom_nutrients.append(type('obj', (object,), {
                    'nutrient_name': custom['nutrient_name'],
                    'value': custom['value'],
                    'unit': custom['unit']
                })())

    return render(request, 'ingredients/detail.html', {
        'ingredient': ingredient,
        'nutrients': nutrients,
        'custom_nutrients': custom_nutrients
    })


@login_required
def add_ingredient(request):
    """
    添加饲料原料
    """
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        nutrient_form = IngredientNutrientForm(request.POST)
        custom_nutrient_formset = CustomIngredientNutrientFormSet(request.POST)
        submit_type = request.POST.get('submit_type', 'draft')  # 获取提交类型

        if form.is_valid() and nutrient_form.is_valid() and custom_nutrient_formset.is_valid():
            # 处理自定义营养成分数据
            custom_nutrients_data = []
            for custom_form in custom_nutrient_formset:
                if custom_form.cleaned_data and not custom_form.cleaned_data.get('DELETE', False):
                    custom_nutrients_data.append({
                        'nutrient_name': custom_form.cleaned_data['nutrient_name'],
                        'value': float(custom_form.cleaned_data['value']),
                        'unit': custom_form.cleaned_data['unit']
                    })

            if submit_type == 'draft':
                # 保存为草稿：直接保存到主表
                ingredient = form.save(commit=False)
                ingredient.created_by = request.user
                ingredient.status = Ingredient.DRAFT
                ingredient.save()

                # 保存营养成分信息
                nutrient = nutrient_form.save(commit=False)
                nutrient.ingredient = ingredient
                nutrient.save()

                # 保存自定义营养成分信息
                custom_nutrients = custom_nutrient_formset.save(commit=False)
                for custom_nutrient in custom_nutrients:
                    custom_nutrient.ingredient = ingredient
                    custom_nutrient.save()

                # 处理删除的自定义营养成分
                for obj in custom_nutrient_formset.deleted_objects:
                    obj.delete()
            else:
                # 提交审核：保存到主表并创建待审核变更记录
                # 创建基本的原料记录，详细信息将保存到临时表
                ingredient = Ingredient(
                    created_by=request.user,
                    status=Ingredient.PENDING,  # 设置为待审核状态
                    # 基本信息字段
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description'],
                    cost=form.cleaned_data['cost'],
                )
                ingredient.save()

                # 创建待审核变更记录，将所有营养指标数据放入临时表
                pending_change = IngredientPendingChange(
                    ingredient=ingredient,
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description'],
                    cost=form.cleaned_data['cost'],
                    # 营养成分字段初始化为0，根据复选框状态更新
                    dm=0,
                    calcium=0,
                    protein=0,
                    phosphorus=0,
                    ndf=0,
                    metabolizable_energy=0,
                    mp=0,
                    # 自定义营养成分
                    custom_nutrients=custom_nutrients_data,
                    created_by=request.user
                )

                # 只有当用户勾选了复选框时，才更新待审核变更中的营养指标字段
                nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp']
                for nutrient in nutrient_fields:
                    include_field_name = f"include_{nutrient}"
                    if include_field_name in request.POST:
                        # 如果勾选了复选框，使用表单数据更新对应字段
                        setattr(pending_change, nutrient, nutrient_form.cleaned_data[nutrient])

                # 保存待审核变更
                pending_change.save()

            # 重定向到详情页面
            return redirect('ingredient_detail', ingredient_id=ingredient.id)
    else:
        form = IngredientForm()
        nutrient_form = IngredientNutrientForm()
        custom_nutrient_formset = CustomIngredientNutrientFormSet()

    return render(request, 'ingredients/add.html', {
        'form': form,
        'nutrient_form': nutrient_form,
        'custom_nutrient_formset': custom_nutrient_formset
    })


@login_required
def edit_ingredient(request, ingredient_id):
    """
    编辑饲料原料
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    nutrient = IngredientNutrient.objects.filter(ingredient=ingredient).first()

    # 检查是否已经是待审核状态
    if ingredient.status == Ingredient.PENDING:
        return render(request, 'ingredients/edit.html', {
            'ingredient': ingredient,
            'error': '该记录已提交审核，无法编辑'
        })

    if request.method == 'POST':
        # 添加instance参数，这样clean_name方法就能识别是编辑操作
        form = IngredientForm(request.POST, instance=ingredient)
        nutrient_form = IngredientNutrientForm(request.POST)
        custom_nutrient_formset = CustomIngredientNutrientFormSet(request.POST)

        if form.is_valid() and nutrient_form.is_valid() and custom_nutrient_formset.is_valid():
            # 获取自定义营养成分数据
            custom_nutrients_data = []
            nutrient_count = int(request.POST.get('custom_nutrients-TOTAL_FORMS', 0))
            for i in range(nutrient_count):
                prefix = f'custom_nutrients-{i}-'
                delete = request.POST.get(prefix + 'DELETE')
                if not delete:
                    nutrient_name = request.POST.get(prefix + 'nutrient_name')
                    value = request.POST.get(prefix + 'value')
                    unit = request.POST.get(prefix + 'unit')

                    if nutrient_name and value and unit:
                        custom_data = {
                            'nutrient_name': nutrient_name,
                            'value': float(value),
                            'unit': unit
                        }
                        custom_nutrients_data.append(custom_data)

            # 检查是否有实际修改
            has_changes = False

            # 1. 检查基本信息字段是否有变化
            if (form.cleaned_data['name'] != ingredient.name or
                    form.cleaned_data['description'] != ingredient.description or
                    form.cleaned_data['cost'] != ingredient.cost):
                has_changes = True

            # 2. 检查营养指标字段是否有变化
            nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp']
            for nutrient_field in nutrient_fields:
                include_field_name = f"include_{nutrient_field}"
                if include_field_name in request.POST:
                    # 如果勾选了复选框，比较表单值和原始值
                    form_value = form.cleaned_data[nutrient_field] if nutrient_field in form.cleaned_data else 0
                    original_value = getattr(nutrient, nutrient_field) if nutrient else 0
                    if form_value != original_value:
                        has_changes = True
                        break

            # 3. 检查自定义营养需求数据是否有变化
            # 获取原始自定义营养需求数据
            original_custom_nutrients = list(
                ingredient.custom_nutrients.values('nutrient_name', 'value', 'unit'))

            # 转换为与表单数据相同的格式
            original_custom_data = []
            for item in original_custom_nutrients:
                original_custom_data.append({
                    'nutrient_name': item['nutrient_name'],
                    'value': float(item['value']),
                    'unit': item['unit']
                })

            # 比较自定义营养需求数据
            if sorted(custom_nutrients_data, key=lambda x: x['nutrient_name']) != sorted(original_custom_data,
                                                                                         key=lambda x: x[
                                                                                             'nutrient_name']):
                has_changes = True

            # 如果没有任何变化，直接重定向到详情页面
            if not has_changes:
                return redirect('ingredient_detail', ingredient_id=ingredient.id)

            # 如果有变化，保存到临时变更表
            # 先删除已有的待审核变更（如果有）
            IngredientPendingChange.objects.filter(ingredient=ingredient).delete()

            # 创建新的待审核变更记录
            pending_change = IngredientPendingChange(
                ingredient=ingredient,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                cost=form.cleaned_data['cost'],
                # 营养成分字段：如果勾选了复选框则使用表单值，否则使用原始值
                dm=nutrient_form.cleaned_data['dm'] if 'include_dm' in request.POST and nutrient_form.cleaned_data[
                    'dm'] is not None else getattr(nutrient, 'dm', 0),
                calcium=nutrient_form.cleaned_data['calcium'] if 'include_calcium' in request.POST and
                                                                 nutrient_form.cleaned_data[
                                                                     'calcium'] is not None else getattr(nutrient,
                                                                                                         'calcium', 0),
                protein=nutrient_form.cleaned_data['protein'] if 'include_protein' in request.POST and
                                                                 nutrient_form.cleaned_data[
                                                                     'protein'] is not None else getattr(nutrient,
                                                                                                         'protein', 0),
                phosphorus=nutrient_form.cleaned_data['phosphorus'] if 'include_phosphorus' in request.POST and
                                                                       nutrient_form.cleaned_data[
                                                                           'phosphorus'] is not None else getattr(
                    nutrient, 'phosphorus', 0),
                ndf=nutrient_form.cleaned_data['ndf'] if 'include_ndf' in request.POST and nutrient_form.cleaned_data[
                    'ndf'] is not None else getattr(nutrient, 'ndf', 0),
                metabolizable_energy=nutrient_form.cleaned_data[
                    'metabolizable_energy'] if 'include_me' in request.POST and nutrient_form.cleaned_data[
                    'metabolizable_energy'] is not None else getattr(nutrient, 'metabolizable_energy', 0),
                mp=nutrient_form.cleaned_data['mp'] if 'include_mp' in request.POST and nutrient_form.cleaned_data[
                    'mp'] is not None else getattr(nutrient, 'mp', 0),
                # 自定义营养成分
                custom_nutrients=custom_nutrients_data,
                created_by=request.user
            )
            pending_change.save()

            # 更新原记录状态为待审核
            ingredient.status = Ingredient.PENDING
            ingredient.approved_by = None
            ingredient.approved_at = None
            ingredient.save(update_fields=['status', 'approved_by', 'approved_at'])

            # 重定向到详情页面
            return redirect('ingredient_detail', ingredient_id=ingredient.id)
    else:
        # 使用instance参数替代initial参数，这样clean_name方法就能识别是编辑操作
        form = IngredientForm(instance=ingredient)

        # 设置营养成分表单的初始值，处理nutrient为None的情况
        nutrient_initial = {
            'dm': nutrient.dm if nutrient else 0,
            'calcium': nutrient.calcium if nutrient else 0,
            'protein': nutrient.protein if nutrient else 0,
            'phosphorus': nutrient.phosphorus if nutrient else 0,
            'ndf': nutrient.ndf if nutrient else 0,
            'metabolizable_energy': nutrient.metabolizable_energy if nutrient else 0,
            'mp': nutrient.mp if nutrient else 0,
        }

        nutrient_form = IngredientNutrientForm(initial=nutrient_initial)

        # 处理自定义营养成分表单集
        custom_nutrient_formset = CustomIngredientNutrientFormSet(instance=ingredient)

    return render(request, 'ingredients/edit.html', {
        'form': form,
        'nutrient_form': nutrient_form,
        'custom_nutrient_formset': custom_nutrient_formset,
        'ingredient': ingredient
    })


@user_passes_test(lambda u: u.is_superuser)
def review_ingredient(request, ingredient_id):
    """
    审核饲料原料
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    # 获取待审核的变更
    pending_change = IngredientPendingChange.objects.filter(ingredient=ingredient).first()

    if not pending_change:
        return redirect('ingredient_detail', ingredient_id=ingredient.id)

    # 初始化changed_fields字典
    changed_fields = {}

    # 获取营养成分对象
    original_nutrient = ingredient.nutrients.first() if ingredient.nutrients.exists() else None

    # 比较基本信息字段
    basic_fields = ['name', 'cost']  # 移除'description'字段，只在下面单独处理
    for field in basic_fields:
        original_value = getattr(ingredient, field)
        new_value = getattr(pending_change, field)
        if original_value != new_value:
            changed_fields[field] = (original_value, new_value)

    # 单独处理description字段，避免None和空字符串的问题
    original_desc = getattr(ingredient, 'description') or ''
    new_desc = getattr(pending_change, 'description') or ''
    if original_desc != new_desc:
        changed_fields['description'] = (original_desc, new_desc)

    # 比较营养成分字段
    nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp']
    for field in nutrient_fields:
        original_value = getattr(original_nutrient, field) if original_nutrient else 0
        new_value = getattr(pending_change, field)
        if original_value != new_value:
            changed_fields[field] = (original_value, new_value)

    # 比较自定义营养成分
    # 获取原始自定义营养成分数据
    original_custom_nutrients = list(
        ingredient.custom_nutrients.values('nutrient_name', 'value', 'unit'))

    # 转换为与pending_change数据相同的格式
    original_custom_data = []
    for item in original_custom_nutrients:
        original_custom_data.append({
            'nutrient_name': item['nutrient_name'],
            'value': float(item['value']),
            'unit': item['unit']
        })

    # 获取待审核的自定义营养成分数据
    pending_custom_data = pending_change.custom_nutrients or []

    # 比较自定义营养成分数据
    if sorted(original_custom_data, key=lambda x: x['nutrient_name']) != sorted(pending_custom_data,
                                                                                key=lambda x: x['nutrient_name']):
        # 如果有变化，将变化的营养成分添加到changed_fields
        # 为了展示方便，我们将所有原始和新的自定义营养成分都显示出来
        changed_fields['custom_nutrients'] = (original_custom_data, pending_custom_data)

    if request.method == 'POST':
        # 保持原有POST处理逻辑不变
        action = request.POST.get('action')
        comments = request.POST.get('comments')

        from django.utils import timezone

        if action == 'approve':
            # 审核通过，应用变更
            ingredient.name = pending_change.name
            ingredient.description = pending_change.description
            ingredient.cost = pending_change.cost
            ingredient.status = Ingredient.APPROVED
            ingredient.approved_by = request.user
            ingredient.approved_at = timezone.now()
            ingredient.comments = comments
            ingredient.save()

            # 更新营养成分
            nutrient, created = IngredientNutrient.objects.get_or_create(ingredient=ingredient)
            nutrient.dm = pending_change.dm
            nutrient.calcium = pending_change.calcium
            nutrient.protein = pending_change.protein
            nutrient.phosphorus = pending_change.phosphorus
            nutrient.ndf = pending_change.ndf
            nutrient.metabolizable_energy = pending_change.metabolizable_energy
            nutrient.mp = pending_change.mp
            nutrient.save()

            # 更新自定义营养成分
            if pending_change.custom_nutrients:
                # 删除现有自定义营养成分
                CustomIngredientNutrient.objects.filter(ingredient=ingredient).delete()
                # 创建新的自定义营养成分
                for custom in pending_change.custom_nutrients:
                    CustomIngredientNutrient.objects.create(
                        ingredient=ingredient,
                        nutrient_name=custom['nutrient_name'],
                        value=custom['value'],
                        unit=custom['unit']
                    )
            else:
                # 如果没有自定义营养成分，删除所有现有自定义营养成分
                CustomIngredientNutrient.objects.filter(ingredient=ingredient).delete()

            # 删除待审核变更
            pending_change.delete()

        elif action == 'reject':
            # 审核拒绝
            ingredient.status = Ingredient.REJECTED
            ingredient.approved_by = request.user
            ingredient.approved_at = timezone.now()
            ingredient.comments = comments
            ingredient.save()

            # 删除待审核变更
            pending_change.delete()

        return redirect('ingredient_detail', ingredient_id=ingredient.id)

    # 渲染审核页面，传递ingredient和pending_change数据
    return render(request, 'ingredients/review.html', {
        'ingredient': ingredient,
        'pending_change': pending_change,
        'changed_fields': changed_fields
    })


@login_required
def api_ingredients_list(request):
    """
    API端点：获取饲料原料列表（仅返回已审核通过的原料）
    """
    try:
        # 只返回已审核通过的原料
        ingredients = Ingredient.objects.filter(status=Ingredient.APPROVED)
        result = []

        for ingredient in ingredients:
            nutrient = IngredientNutrient.objects.filter(ingredient=ingredient).first()
            custom_nutrients = CustomIngredientNutrient.objects.filter(ingredient=ingredient)

            if nutrient:
                ingredient_data = {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'cost': float(ingredient.cost),  # 转换为元/吨
                    'dm': float(nutrient.dm),
                    'ndf': float(nutrient.ndf),
                    'mp': float(nutrient.mp),
                    'cp': float(nutrient.protein),
                    'ca': float(nutrient.calcium),
                    'p': float(nutrient.phosphorus),
                    'me': float(nutrient.metabolizable_energy),  # 代谢能
                    'custom_nutrients': [{
                        'name': cn.nutrient_name,
                        'value': float(cn.value),
                        'unit': cn.unit
                    } for cn in custom_nutrients]
                }
            else:
                ingredient_data = {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'cost': float(ingredient.cost),  # 转换为元/吨
                    'dm': 0,
                    'ndf': 0,
                    'mp': 0,
                    'cp': 0,
                    'ca': 0,
                    'p': 0,
                    'me': 0,
                    'custom_nutrients': []
                }

            result.append(ingredient_data)

        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# 饲料原料列表视图
@login_required
def ingredients_list(request):
    """
    显示饲料原料列表
    """
    # 所有登录用户都可以看到所有原料
    ingredients = Ingredient.objects.all().order_by('name')
    return render(request, 'ingredients/list.html', {'ingredients': ingredients})
