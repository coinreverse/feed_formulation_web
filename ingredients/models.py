from django.db import models
from users.models import CustomUser


class Ingredient(models.Model):
    """
    原料表
    """
    # 审核状态枚举
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (DRAFT, '草稿'),
        (PENDING, '待审核'),
        (APPROVED, '已通过'),
        (REJECTED, '已拒绝'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name="原料名称")
    description = models.TextField(blank=True, null=True, verbose_name="原料说明")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="单价(元/kg)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    # 审核相关字段
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, verbose_name="审核状态")
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_ingredients',
                                   verbose_name="提交用户", null=True, blank=True)
    approved_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='approved_ingredients', verbose_name="审核用户")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    comments = models.TextField(blank=True, null=True, verbose_name="审核意见")

    class Meta:
        verbose_name = "原料"
        verbose_name_plural = "原料"

    def __str__(self):
        return self.name


class IngredientNutrient(models.Model):
    """
    原料营养含量表（关联原料）
    """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="nutrients",
        verbose_name="所属原料"
    )

    # 营养成分字段
    dm = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质(DM)")
    calcium = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙(Ca)")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="粗蛋白(CP)")
    phosphorus = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷(P)")
    ndf = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维(NDF)")
    metabolizable_energy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="代谢能(ME)"
    )
    mp = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="代谢蛋白(MP)")

    class Meta:
        verbose_name = "原料营养含量"
        verbose_name_plural = "原料营养含量"

    def __str__(self):
        return f"{self.ingredient.name} 的营养含量"


class CustomIngredientNutrient(models.Model):
    """
    自定义原料营养成分表
    """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="custom_nutrients",
        verbose_name="所属原料"
    )
    nutrient_name = models.CharField(max_length=50, verbose_name="营养元素名称")
    value = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="营养元素值")
    unit = models.CharField(max_length=20, default="%", verbose_name="单位")

    class Meta:
        verbose_name = "自定义原料营养成分"
        verbose_name_plural = "自定义原料营养成分"

    def __str__(self):
        return f"{self.ingredient.name} - {self.nutrient_name}"


class IngredientPendingChange(models.Model):
    """
    原料待审核变更表，用于存储待审核的原料修改
    """
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE, related_name='pending_change')

    # 基本字段变更
    name = models.CharField(max_length=100, verbose_name="原料名称")
    description = models.TextField(blank=True, null=True, verbose_name="原料说明")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="单价(元/kg)")

    # 营养成分变更
    dm = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="干物质(DM)")
    calcium = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="钙(Ca)")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="粗蛋白(CP)")
    phosphorus = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="磷(P)")
    ndf = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="中性洗涤纤维(NDF)")
    metabolizable_energy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="代谢能(ME)"
    )
    mp = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="代谢蛋白(MP)")

    # 自定义营养成分变更（JSON格式存储）
    custom_nutrients = models.JSONField(blank=True, null=True)

    # 审核相关字段
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "原料待审核变更"
        verbose_name_plural = "原料待审核变更"