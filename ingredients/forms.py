from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .models import Ingredient, IngredientNutrient, CustomIngredientNutrient


class IngredientForm(forms.ModelForm):
    """
    饲料原料基本信息表单
    """

    class Meta:
        model = Ingredient
        fields = ['name', 'description', 'cost']
        labels = {
            'name': _('原料名称'),
            'description': _('原料说明'),
            'cost': _('单价(元/kg)')
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
        }

    def clean_name(self):
        """
        验证原料名称唯一性
        """
        name = self.cleaned_data.get('name')

        # 如果表单绑定到实例（self.instance.pk存在），则排除当前记录
        if self.instance.pk:
            if Ingredient.objects.exclude(pk=self.instance.pk).filter(name=name).exists():
                raise forms.ValidationError(_('具有该名称的原料已存在'))
        else:
            # 如果表单没有绑定到实例（新建或编辑模式），检查是否有其他记录使用该名称
            if Ingredient.objects.filter(name=name).exists():
                raise forms.ValidationError(_('具有该名称的原料已存在'))
        return name


class IngredientNutrientForm(forms.ModelForm):
    """
    原料营养成分表单
    """
    # 添加复选框字段
    include_dm = forms.BooleanField(required=False, label=_('干物质(DM)(%)'))
    include_calcium = forms.BooleanField(required=False, label=_('钙(Ca)(%)'))
    include_protein = forms.BooleanField(required=False, label=_('粗蛋白(CP)(%)'))
    include_phosphorus = forms.BooleanField(required=False, label=_('磷(P)(%)'))
    include_ndf = forms.BooleanField(required=False, label=_('中性洗涤纤维(NDF)(%)'))
    include_me = forms.BooleanField(required=False, label=_('代谢能(ME)(%)'))
    include_mp = forms.BooleanField(required=False, label=_('代谢蛋白(MP)(%)'))

    # 将所有营养成分字段设置为非必填
    dm = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')
    calcium = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')
    protein = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')
    phosphorus = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')
    ndf = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')
    metabolizable_energy = forms.DecimalField(required=False, max_digits=8, decimal_places=2, label='')
    mp = forms.DecimalField(required=False, max_digits=6, decimal_places=2, label='')

    def __init__(self, *args, **kwargs):
        """
        初始化表单，默认不选择任何复选框
        """
        super().__init__(*args, **kwargs)

        # 将现有值填充到表单字段中，但不自动勾选复选框
        if self.instance and self.instance.pk:
            nutrient_fields_map = {
                'dm': 'include_dm',
                'calcium': 'include_calcium',
                'protein': 'include_protein',
                'phosphorus': 'include_phosphorus',
                'ndf': 'include_ndf',
                'metabolizable_energy': 'include_me',
                'mp': 'include_mp'
            }

            for field_name, include_field_name in nutrient_fields_map.items():
                field_value = getattr(self.instance, field_name)
                # 将现有值填充到表单中，但不自动勾选复选框
                self.initial[field_name] = field_value

    class Meta:
        model = IngredientNutrient
        fields = [
            'dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp'
        ]
        labels = {
            'dm': '',
            'calcium': '',
            'protein': '',
            'phosphorus': '',
            'ndf': '',
            'metabolizable_energy': '',
            'mp': ''
        }
        widgets = {
            'dm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'calcium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'phosphorus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'ndf': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'metabolizable_energy': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'mp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
        }

    def clean(self):
        cleaned_data = super().clean()

        # 根据复选框状态设置字段的必填性
        nutrient_fields_map = {
            'dm': 'include_dm',
            'calcium': 'include_calcium',
            'protein': 'include_protein',
            'phosphorus': 'include_phosphorus',
            'ndf': 'include_ndf',
            'metabolizable_energy': 'include_me',
            'mp': 'include_mp'
        }

        for field_name, include_field_name in nutrient_fields_map.items():
            include_value = cleaned_data.get(include_field_name)
            field_value = cleaned_data.get(field_name)

            # 如果勾选了复选框，必须填写对应的值
            if include_value and field_value is None:
                # 获取include字段的标签
                include_label = self.fields[include_field_name].label
                self.add_error(field_name, f'{include_label}值不能为空')

        # 确保所有数值字段不为负数
        nutrient_fields = ['dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp']

        for field in nutrient_fields:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                # 获取对应的include字段名称
                if field == 'metabolizable_energy':
                    include_field_name = 'include_me'
                else:
                    include_field_name = f"include_{field}"
                # 获取include字段的标签
                include_label = self.fields[include_field_name].label
                # 添加错误信息
                self.add_error(field, f'{include_label}{_("不能为负数")}')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # 只有勾选了复选框的字段才更新值，未勾选的保持原有值
        nutrient_fields_map = {
            'dm': 'include_dm',
            'calcium': 'include_calcium',
            'protein': 'include_protein',
            'phosphorus': 'include_phosphorus',
            'ndf': 'include_ndf',
            'metabolizable_energy': 'include_me',
            'mp': 'include_mp'
        }

        for field_name, include_field_name in nutrient_fields_map.items():
            include_value = self.cleaned_data.get(include_field_name)

            # 如果勾选了复选框，更新字段值
            if include_value:
                field_value = self.cleaned_data.get(field_name)
                setattr(instance, field_name, field_value)
            # 如果未勾选，保持原有值不变

        if commit:
            instance.save()

        return instance


class CustomIngredientNutrientForm(forms.ModelForm):
    """
    自定义原料营养成分表单
    """

    class Meta:
        model = CustomIngredientNutrient
        fields = ['nutrient_name', 'value', 'unit']
        labels = {
            'nutrient_name': _('营养元素名称'),
            'value': _('含量'),
            'unit': _('单位')
        }
        widgets = {
            'nutrient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '%'})
        }

    def clean_value(self):
        """
        确保自定义营养成分值不为负数
        """
        value = self.cleaned_data.get('value')
        if value is not None and value < 0:
            raise forms.ValidationError(_("营养成分值不能为负数"))
        return value


# 创建内联表单集
CustomIngredientNutrientFormSet = inlineformset_factory(
    Ingredient,
    CustomIngredientNutrient,
    form=CustomIngredientNutrientForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)