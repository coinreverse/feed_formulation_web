# 修改 formulation/services/result_parser.py 文件

import json  # 替换 yaml 为 json
from ingredients.models import Ingredient
from formulation.models import (
    FeedFormulaResult,
    FeedFormulaIngredient
)
from animal_requirements.models import AnimalRequirement


def import_ga_result_to_db(json_path, requirement_id, selected_ingredient_ids=None):  # 替换 yaml_path 为 json_path
    """
    将 GA 的 result.json 正确导入数据库
    """
    with open(json_path, "r", encoding="utf-8") as f:  # 替换 yaml_path 为 json_path
        data = json.load(f)  # 替换 yaml.safe_load 为 json.load

    solutions = data["solutions"]  # 每种原料的比例
    objectives = data["objectives"]  # 成本 + 多个营养值
    nutrient_names = data.get("nutrient_names", [])  # 获取营养素名称列表

    # 获取动物需求对象
    requirement = AnimalRequirement.objects.get(id=requirement_id)

    # 🚨 覆盖旧数据（防止重复）
    FeedFormulaResult.objects.filter(requirement=requirement).delete()

    # 获取选中的原料（顺序与 GA 输入一致）
    if selected_ingredient_ids:
        ingredients = list(Ingredient.objects.filter(id__in=selected_ingredient_ids).order_by("id"))
    else:
        ingredients = list(Ingredient.objects.order_by("id"))

    if len(ingredients) != len(solutions[0]):
        raise ValueError(
            f"⚠ 原料数量({len(ingredients)}) 与 GA 输出({len(solutions[0])}) 不一致！"
        )

    # 营养素名称映射字典：GA结果中的名称 -> 数据库字段名
    nutrient_mapping = {
        "calcium": "ca",
        "energy": "me",
        "phosphorus": "p",
        "protein": "cp"
    }

    # 遍历每个解
    for idx, (sol, obj) in enumerate(zip(solutions, objectives)):

        # ---- 保存 FeedFormulaResult ----
        # 创建基本结果对象
        result_data = {
            'requirement_id': requirement_id,
            'solution_index': idx,
            'total_cost': obj[0],
        }

        # 根据营养素名称动态添加营养值
        for i, nutrient_name in enumerate(nutrient_names):
            if i + 1 < len(obj):  # 确保不越界
                # 将营养素名称转换为小写
                nutrient_name_lower = nutrient_name.lower()
                # 使用映射字典转换字段名，如果没有映射则使用原始名称
                field_name = nutrient_mapping.get(nutrient_name_lower, nutrient_name_lower)
                # 确保字段名在模型中存在
                if hasattr(FeedFormulaResult, field_name):
                    result_data[field_name] = obj[i + 1]

        # 创建结果记录
        result = FeedFormulaResult.objects.create(**result_data)

        # ---- 保存配方中每种原料比例 ----
        for ingr, ratio in zip(ingredients, sol):
            FeedFormulaIngredient.objects.create(
                formula=result,
                ingredient=ingr,
                ratio=float(ratio)
            )

    return True