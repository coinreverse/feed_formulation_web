from django.core.management.base import BaseCommand
import yaml
from ingredients.models import Ingredient, IngredientNutrient
from animal_requirements.models import AnimalRequirement


class Command(BaseCommand):
    help = "从 YAML 文件导入原料和营养数据"

    def add_arguments(self, parser):
        parser.add_argument('yaml_file', type=str, help="YAML 文件路径")

    def handle(self, *args, **kwargs):
        yaml_file = kwargs['yaml_file']

        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # ===== 导入原料和价格 =====
        ingredient_names = [
            "大麦皮", "小麦麸", "玉米", "高粱", "大豆粕", "棉籽粕", "花生仁粕",
            "羊草", "苜蓿青贮", "玉米秸秆", "大豆秸秆", "玉米秸秆青贮", "磷酸氢钙"
        ]
        costs = data.get("costs", [])

        for i, name in enumerate(ingredient_names):
            cost = costs[i] if i < len(costs) else 0
            ingredient, created = Ingredient.objects.get_or_create(
                name=name,
                defaults={"cost": cost}
            )
            if not created:
                ingredient.cost = cost
                ingredient.save()

        # ===== 导入原料营养含量 =====
        nutrition_matrix = data.get("nutrition", [])
        for i, nutrient_values in enumerate(nutrition_matrix):
            ingredient_name = ingredient_names[i]
            ingredient = Ingredient.objects.get(name=ingredient_name)

            dm, ca, cp, p, ndf, me, mp = nutrient_values

            IngredientNutrient.objects.update_or_create(
                ingredient=ingredient,
                defaults={
                    "dm": dm,
                    "calcium": ca,
                    "protein": cp,
                    "phosphorus": p,
                    "ndf": ndf,
                    "metabolizable_energy": me,
                    "mp": mp
                }
            )

        # ===== 导入动物营养需求 =====
        nutrient_bounds = data.get("nutrient_bounds", {})
        lower = nutrient_bounds.get("lower", [0] * 7)

        animal_req, created = AnimalRequirement.objects.get_or_create(
            animal_type="未填",
            body_weight=0,
            daily_gain=0,
            defaults={
                "required_dm": lower[0],
                "required_calcium": lower[1],
                "required_protein": lower[2],
                "required_phosphorus": lower[3],
                "required_ndf": lower[4],
                "required_energy": lower[5],
                "required_mp": lower[6],
            }
        )

        self.stdout.write(self.style.SUCCESS("导入完成！"))
