from django import forms
from .models import AnimalRequirement, CustomNutrientRequirement
from django.utils.translation import gettext_lazy as _


class AnimalRequirementForm(forms.ModelForm):
    """
    动物营养需求表单，处理基本信息和固定营养需求
    """
    # 添加复选框字段
    include_dm = forms.BooleanField(required=False, label=_('干物质(%)'))
    include_calcium = forms.BooleanField(required=False, label=_('钙(%)'))
    include_protein = forms.BooleanField(required=False, label=_('蛋白(%)'))
    include_phosphorus = forms.BooleanField(required=False, label=_('磷(%)'))
    include_ndf = forms.BooleanField(required=False, label=_('中性洗涤纤维(%)'))
    include_energy = forms.BooleanField(required=False, label=_('代谢能(kcal/kg)'))
    include_mp = forms.BooleanField(required=False, label=_('代谢蛋白(%)'))

    # 将所有上下界字段设置为非必填
    dm_lower = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('下界'))
    dm_upper = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('上界'))
    calcium_lower = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('下界'))
    calcium_upper = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('上界'))
    protein_lower = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('下界'))
    protein_upper = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('上界'))
    phosphorus_lower = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('下界'))
    phosphorus_upper = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('上界'))
    ndf_lower = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('下界'))
    ndf_upper = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label=_('上界'))
    energy_lower = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('下界'))
    energy_upper = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('上界'))
    mp_lower = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('下界'))
    mp_upper = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('上界'))

    def __init__(self, *args, **kwargs):
        """
        初始化表单，根据现有记录的上下界值设置复选框状态
        """
        super().__init__(*args, **kwargs)

        # 如果是编辑表单（有instance），根据上下界值设置复选框状态
        if self.instance and self.instance.pk:
            nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']

            for nutrient in nutrient_fields:
                lower_field_name = f"{nutrient}_lower"
                upper_field_name = f"{nutrient}_upper"

                # 不再自动勾选复选框，默认全部不选中
                # if getattr(self.instance, lower_field_name) != 0 or getattr(self.instance, upper_field_name) != 0:
                #     self.initial[include_field_name] = True

                # 将现有值填充到表单字段中
                self.initial[lower_field_name] = getattr(self.instance, lower_field_name)
                self.initial[upper_field_name] = getattr(self.instance, upper_field_name)

    class Meta:
        model = AnimalRequirement
        fields = [
            'animal_type', 'body_weight', 'daily_gain',
            'include_dm', 'dm_lower', 'dm_upper',
            'include_calcium', 'calcium_lower', 'calcium_upper',
            'include_protein', 'protein_lower', 'protein_upper',
            'include_phosphorus', 'phosphorus_lower', 'phosphorus_upper',
            'include_ndf', 'ndf_lower', 'ndf_upper',
            'include_energy', 'energy_lower', 'energy_upper',
            'include_mp', 'mp_lower', 'mp_upper'
        ]
        labels = {
            'animal_type': _('动物类型'),
            'body_weight': _('体重(kg)'),
            'daily_gain': _('日增重(g)'),
            'dm_lower': _('下界'),
            'dm_upper': _('上界'),
            'calcium_lower': _('下界'),
            'calcium_upper': _('上界'),
            'protein_lower': _('下界'),
            'protein_upper': _('上界'),
            'phosphorus_lower': _('下界'),
            'phosphorus_upper': _('上界'),
            'ndf_lower': _('下界'),
            'ndf_upper': _('上界'),
            'energy_lower': _('下界'),
            'energy_upper': _('上界'),
            'mp_lower': _('下界'),
            'mp_upper': _('上界')
        }
        widgets = {
            'animal_type': forms.TextInput(attrs={'class': 'form-control'}),
            'body_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'daily_gain': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 干物质
            'dm_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'dm_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 钙
            'calcium_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'calcium_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 蛋白
            'protein_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'protein_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 磷
            'phosphorus_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'phosphorus_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 中性洗涤纤维
            'ndf_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'ndf_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 代谢能
            'energy_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'energy_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # 代谢蛋白
            'mp_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'mp_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
        }

    def clean(self):
        cleaned_data = super().clean()

        # 根据复选框状态验证上下界字段
        nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']

        for nutrient in nutrient_fields:
            include_field_name = f"include_{nutrient}"
            lower_field_name = f"{nutrient}_lower"
            upper_field_name = f"{nutrient}_upper"

            # 获取表单提交的值 - 直接从POST数据中检查复选框状态
            include_value = include_field_name in self.data
            lower_value = cleaned_data.get(lower_field_name)
            upper_value = cleaned_data.get(upper_field_name)

            # 如果勾选了复选框，必须填写上下界
            if include_value:
                if lower_value is None:
                    self.add_error(lower_field_name, f'{self.fields[include_field_name].label}{_("下界不能为空")}')
                if upper_value is None:
                    self.add_error(upper_field_name, f'{self.fields[include_field_name].label}{_("上界不能为空")}')

                # 确保上界大于等于下界
                if lower_value is not None and upper_value is not None and upper_value < lower_value:
                    self.add_error(upper_field_name, f'{self.fields[include_field_name].label}{_("上界不能小于下界")}')

                # 确保所有数值字段不为负数
                if lower_value is not None and lower_value < 0:
                    self.add_error(lower_field_name, f'{self.fields[include_field_name].label}{_("下界不能为负数")}')
                if upper_value is not None and upper_value < 0:
                    self.add_error(upper_field_name, f'{self.fields[include_field_name].label}{_("上界不能为负数")}')
            # 未勾选的保持原有值不变，不再设置为0

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # 处理营养指标字段
        nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'energy', 'mp']

        for nutrient in nutrient_fields:
            include_field_name = f"include_{nutrient}"
            lower_field_name = f"{nutrient}_lower"
            upper_field_name = f"{nutrient}_upper"

            # 获取表单提交的值 - 直接从POST数据中检查复选框状态
            include_value = include_field_name in self.data
            lower_value = self.cleaned_data.get(lower_field_name)
            upper_value = self.cleaned_data.get(upper_field_name)

            # 只有勾选了复选框，才更新上下界值
            if include_value:
                setattr(instance, lower_field_name, lower_value)
                setattr(instance, upper_field_name, upper_value)
            # 未勾选的保持原有值不变，不再设置为0

        if commit:
            instance.save()

        return instance


class CustomNutrientRequirementForm(forms.ModelForm):
    """
    自定义营养需求表单，处理用户自定义的营养需求字段
    """

    # 将数值字段设置为可以为空，这样在用户没有输入时，它们会被设置为None
    nutrient_lower = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('下界'))
    nutrient_upper = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label=_('上界'))

    class Meta:
        model = CustomNutrientRequirement
        fields = ['nutrient_name', 'nutrient_lower', 'nutrient_upper', 'unit']
        labels = {
            'nutrient_name': _('营养元素名称'),
            'nutrient_lower': _('下界'),
            'nutrient_upper': _('上界'),
            'unit': _('单位')
        }
        widgets = {
            'nutrient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nutrient_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'nutrient_upper': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：%、kcal/kg、g/kg等'})
        }

    def clean(self):
        cleaned_data = super().clean()
        nutrient_name = cleaned_data.get('nutrient_name')
        nutrient_lower = cleaned_data.get('nutrient_lower')
        nutrient_upper = cleaned_data.get('nutrient_upper')
        unit = cleaned_data.get('unit')

        # 检查是否是空表单（营养名称和单位为空，数值字段也为空）
        if not nutrient_name and not unit and nutrient_lower is None and nutrient_upper is None:
            # 对于空表单，清除所有错误并返回空数据
            self._errors.clear()
            return {}

        # 如果不是空表单，确保所有必填字段都已填写
        if not nutrient_name:
            self.add_error('nutrient_name', _('营养元素名称不能为空'))
        if not unit:
            self.add_error('unit', _('单位不能为空'))

        # 确保上界大于等于下界
        if nutrient_lower is not None and nutrient_upper is not None and nutrient_upper < nutrient_lower:
            self.add_error('nutrient_upper', _('上界不能小于下界'))

        # 确保所有数值字段不为负数
        if nutrient_lower is not None and nutrient_lower < 0:
            self.add_error('nutrient_lower', _('下界不能为负数'))
        if nutrient_upper is not None and nutrient_upper < 0:
            self.add_error('nutrient_upper', _('上界不能为负数'))

        # 如果数值字段为空，设置为0
        if nutrient_lower is None:
            cleaned_data['nutrient_lower'] = 0
        if nutrient_upper is None:
            cleaned_data['nutrient_upper'] = 0

        return cleaned_data


# 创建表单集，用于处理多个自定义营养需求
CustomNutrientRequirementFormSet = forms.inlineformset_factory(
    AnimalRequirement,
    CustomNutrientRequirement,
    form=CustomNutrientRequirementForm,
    extra=1,  # 默认显示1个空表单
    can_delete=True,  # 允许删除表单
    min_num=0,  # 最少0个
    validate_min=False  # 不验证最少数量，避免空表单集报错
)