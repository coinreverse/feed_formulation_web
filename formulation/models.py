from django.db import models
from django.utils.translation import gettext_lazy as _


class FeedFormulaResult(models.Model):
    requirement = models.ForeignKey(
        'animal_requirements.AnimalRequirement',
        on_delete=models.CASCADE,
        verbose_name=_("动物需求方案")
    )

    solution_index = models.IntegerField(verbose_name=_("帕累托序号"))

    # ---- GA 的 8 个目标 ----
    total_cost = models.FloatField(default=0, verbose_name=_("成本"))

    dm = models.FloatField(default=0, verbose_name=_("干物质(DM)"))
    ca = models.FloatField(default=0, verbose_name=_("钙(Ca)"))
    cp = models.FloatField(default=0, verbose_name=_("粗蛋白(CP)"))
    p = models.FloatField(default=0, verbose_name=_("磷(P)"))
    ndf = models.FloatField(default=0, verbose_name=_("中性洗涤纤维(NDF)"))
    me = models.FloatField(default=0, verbose_name=_("代谢能(ME)"))
    mp = models.FloatField(default=0, verbose_name=_("代谢蛋白(MP)"))
    # 新增：存储自定义营养元素的JSON字段
    custom_nutrients = models.JSONField(default=dict, verbose_name=_("自定义营养元素"))

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requirement} - 解 {self.solution_index}"


class FeedFormulaIngredient(models.Model):
    formula = models.ForeignKey(
        FeedFormulaResult,
        on_delete=models.CASCADE,
        related_name="ingredients"
    )

    ingredient = models.ForeignKey(
        'ingredients.Ingredient',
        on_delete=models.CASCADE
    )

    ratio = models.FloatField(verbose_name=_("比例"))

    json_feed_formula = models.TextField(
        default="",
        verbose_name=_("创造yaml文件所需的json数据")
    )

    def __str__(self):
        return f"{self.ingredient.name}: {self.ratio:.4f}"