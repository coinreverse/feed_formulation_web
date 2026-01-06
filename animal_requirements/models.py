from django.db import models
from users.models import CustomUser
import json


class AnimalRequirement(models.Model):
    """
    动物营养需求表（例如：40kg 日增重100g）
    """
    # 审核状态枚举
    DRAFT = 'draft'  # 草稿状态
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (DRAFT, '草稿'),
        (PENDING, '待审核'),
        (APPROVED, '已通过'),
        (REJECTED, '已拒绝'),
    ]

    # 其他字段保持不变
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, verbose_name="审核状态")

    animal_type = models.CharField(max_length=50, verbose_name="动物类型")
    body_weight = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="体重(kg)")
    daily_gain = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="日增重(g)")

    dm_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质下界(%))")
    dm_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质上界(%))")
    # 钙
    calcium_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙下界(%))")
    calcium_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙上界(%))")
    # 蛋白
    protein_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="蛋白下界(%))")
    protein_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="蛋白上界(%))")
    # 磷
    phosphorus_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷下界(%))")
    phosphorus_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷上界(%))")
    # 中性洗涤纤维
    ndf_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维下界(%))")
    ndf_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维上界(%))")
    # 代谢能
    energy_lower = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢能下界(kcal/kg))")
    energy_upper = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢能上界(kcal/kg))")
    # 代谢蛋白
    mp_lower = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢蛋白下界(%))")
    mp_upper = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢蛋白上界(%))")

    # 添加审核相关字段
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_requirements',
                                   verbose_name="提交用户", null=True, blank=True)
    approved_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='approved_requirements', verbose_name="审核用户")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "动物营养需求"
        verbose_name_plural = "动物营养需求"

    def __str__(self):
        return f"{self.animal_type} {self.body_weight}kg 日增重{self.daily_gain}g"


class CustomNutrientRequirement(models.Model):
    """
    自定义营养需求表，用于存储用户自定义的营养需求字段
    """
    requirement = models.ForeignKey(AnimalRequirement, on_delete=models.CASCADE, related_name='custom_nutrients',
                                    verbose_name="关联的动物营养需求")
    nutrient_name = models.CharField(max_length=50, verbose_name="营养元素名称")
    nutrient_lower = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="营养元素下界")
    nutrient_upper = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="营养元素上界")
    unit = models.CharField(max_length=20, verbose_name="单位")  # 例如：%、kcal/kg、g/kg等

    class Meta:
        verbose_name = "自定义营养需求"
        verbose_name_plural = "自定义营养需求"

    def __str__(self):
        return f"{self.nutrient_name}: {self.nutrient_lower}-{self.nutrient_upper}{self.unit}"


class AnimalRequirementHistory(models.Model):
    """
    动物营养需求历史版本表，用于保存审核前的数据
    """
    requirement = models.ForeignKey(AnimalRequirement, on_delete=models.CASCADE, related_name='history')
    data = models.JSONField()  # 保存完整的需求数据
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "动物营养需求历史版本"
        verbose_name_plural = "动物营养需求历史版本"


class AnimalRequirementPendingChange(models.Model):
    """
    动物营养需求待审核变更表，用于存储待审核的修改
    """
    requirement = models.OneToOneField(AnimalRequirement, on_delete=models.CASCADE, related_name='pending_change')
    # 基本字段变更
    animal_type = models.CharField(max_length=50, verbose_name="动物类型")
    body_weight = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="体重(kg)")
    daily_gain = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="日增重(g)")

    # 营养指标变更
    dm_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质下界(%))")
    dm_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质上界(%))")
    calcium_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙下界(%))")
    calcium_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙上界(%))")
    protein_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="蛋白下界(%))")
    protein_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="蛋白上界(%))")
    phosphorus_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷下界(%))")
    phosphorus_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷上界(%))")
    ndf_lower = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维下界(%))")
    ndf_upper = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维上界(%))")
    energy_lower = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢能下界(kcal/kg))")
    energy_upper = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢能上界(kcal/kg))")
    mp_lower = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢蛋白下界(%))")
    mp_upper = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="代谢蛋白上界(%))")

    # 自定义营养需求变更（JSON格式存储）
    custom_nutrients = models.JSONField(blank=True, null=True)

    # 审核相关字段
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "动物营养需求待审核变更"
        verbose_name_plural = "动物营养需求待审核变更"
