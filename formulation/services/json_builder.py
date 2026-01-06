# formulation/services/json_builder.py
from pathlib import Path
import json
from ingredients.models import Ingredient
from animal_requirements.models import AnimalRequirement

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "GA_feed_sheep" / "configs"
OUTPUT_DIR = BASE_DIR / "GA_feed_sheep" / "results"

CONFIG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def get_json_paths(requirement_id):
    """
    ✅ 根据动物类型 + 体重 + 日增重 动态生成 JSON 路径
    """
    try:
        req = AnimalRequirement.objects.get(id=requirement_id)
    except AnimalRequirement.DoesNotExist:
        raise ValueError(f"动物营养需求记录(ID: {requirement_id})不存在，请先创建相应的记录。")

    filename = f"{req.animal_type}_{req.body_weight}kg_{req.daily_gain}g.json"
    base, ext = filename.rsplit('.', 1)
    base = base.replace('.', '_')
    filename = f"{base}.{ext}"
    input_path = CONFIG_DIR / filename
    output_path = OUTPUT_DIR / filename.replace(".json", "_result.json")

    return input_path, output_path


def build_feed_json(requirement_id, selected_ingredient_ids=None):
    """
    ✅ 构建饲料配方JSON配置文件，动态读取字段并确保兼容性
    """
    try:
        req = AnimalRequirement.objects.get(id=requirement_id)
    except AnimalRequirement.DoesNotExist:
        raise ValueError(f"动物营养需求记录(ID: {requirement_id})不存在，请先创建相应的记录。")

    # 1. 动态获取所有字段（从AnimalRequirement模型）
    all_fields = [field.name for field in AnimalRequirement._meta.get_fields()]

    # 2. 过滤掉非营养字段
    non_nutrient_fields = ['id', 'animal_type', 'body_weight', 'daily_gain', 'status',
                           'created_by', 'approved_by', 'approved_at', 'created_at', 'custom_nutrients']
    filtered_fields = [field for field in all_fields if field not in non_nutrient_fields]

    # 3. 提取营养字段名称（去除_lower和_upper后缀）
    nutrient_fields = []
    new_filtered_fields = []
    for field in filtered_fields:
        if field.endswith('_lower') or field.endswith('_upper'):
            nutrient_name = field[:-6]  # 移除"_lower"或"_upper"
            new_filtered_fields.append(nutrient_name)
            if nutrient_name not in nutrient_fields:
                nutrient_fields.append(nutrient_name)

    # 4. 添加自定义营养元素
    custom_nutrients = req.custom_nutrients.all()
    for custom_nutrient in custom_nutrients:
        if custom_nutrient.nutrient_name not in nutrient_fields:
            nutrient_fields.append(custom_nutrient.nutrient_name)

    # 5. 按字母顺序排序营养字段
    nutrient_fields.sort()

    # 6. 建立AnimalRequirement到IngredientNutrient的字段映射
    field_mapping = {
        'dm': 'dm',
        'calcium': 'calcium',
        'protein': 'protein',
        'phosphorus': 'phosphorus',
        'ndf': 'ndf',
        'energy': 'metabolizable_energy',  # 注意这里的映射
        'mp': 'mp'
    }

    # 7. 获取选中的原料
    if selected_ingredient_ids:
        ingredients = Ingredient.objects.filter(id__in=selected_ingredient_ids).order_by("id")
    else:
        ingredients = Ingredient.objects.all().order_by("id")

    # 确保有原料
    if not ingredients.exists():
        raise ValueError("没有可用的饲料原料，请先添加原料。")

    # 8. 构建营养需求下界和上界（按排序后的顺序）
    nutrient_lower = []
    nutrient_upper = []
    nutrient_names = []  # 用于存储营养名称，保持顺序

    # 创建自定义营养元素的字典，便于查找
    custom_nutrient_dict = {cn.nutrient_name: cn for cn in custom_nutrients}

    for nutrient in nutrient_fields:
        if nutrient in custom_nutrient_dict:
            # 处理自定义营养元素
            custom_nutrient = custom_nutrient_dict[nutrient]
            lower_value = float(custom_nutrient.nutrient_lower)
            upper_value = float(custom_nutrient.nutrient_upper)
        else:
            # 处理固定营养元素
            lower_value = getattr(req, f"{nutrient}_lower", 0)
            upper_value = getattr(req, f"{nutrient}_upper", float('inf'))  # 默认上界为无穷大

        nutrient_lower.append(float(lower_value))
        nutrient_upper.append(float(upper_value))
        nutrient_names.append(nutrient)

    # 9. 构建原料成本和营养矩阵
    costs = []
    nutrition = []
    ingredient_names = []

    for ingredient in ingredients:
        # 获取原料成本
        costs.append(float(ingredient.cost))
        ingredient_names.append(ingredient.name)

        # 获取原料营养数据
        try:
            # 收集原料的所有营养元素（包括固定和自定义）
            ingredient_all_nutrients = {}

            # 添加固定营养元素
            ingredient_nutrient = ingredient.nutrients.first()
            if ingredient_nutrient:
                for nutrient in nutrient_fields:
                    # 获取对应的原料营养字段名
                    ingredient_field = field_mapping.get(nutrient, nutrient)
                    # 获取营养值，缺失时用0填充
                    nutrient_value = getattr(ingredient_nutrient, ingredient_field, 0)
                    ingredient_all_nutrients[nutrient] = float(nutrient_value)

            # 添加自定义营养元素
            custom_nutrients = ingredient.custom_nutrients.all()
            for custom_nutrient in custom_nutrients:
                ingredient_all_nutrients[custom_nutrient.nutrient_name] = float(custom_nutrient.value)

            # 按排序后的营养需求顺序构建营养数据（缺失的营养元素用0填充）
            nutrient_data = []
            for nutrient in nutrient_fields:
                nutrient_value = ingredient_all_nutrients.get(nutrient, 0)
                nutrient_data.append(float(nutrient_value))

            nutrition.append(nutrient_data)
        except Exception as e:
            raise ValueError(f"处理原料 {ingredient.name} 的营养数据时出错: {str(e)}")

    # 10. 设置原料使用范围（默认0-100%）
    ingredient_bounds = [[0, 100] for _ in range(len(ingredients))]

    # 11. 构建最终的配置数据（JSON格式）
    feed_config = {
        "metadata": {
            "animal_type": req.animal_type,
            "body_weight": float(req.body_weight),
            "daily_gain": float(req.daily_gain),
            "nutrient_names": nutrient_names,
            "ingredient_names": ingredient_names,
            "field_mapping": field_mapping
        },
        "costs": costs,
        "nutrition": nutrition,
        "nutrient_bounds": {
            "lower": nutrient_lower,
            "upper": nutrient_upper
        },
        "ingredient_bounds": ingredient_bounds,
        "settings": {
            "device": "cuda",
            "tol": 0.05
        }
    }

    # 12. 保存JSON格式的配置文件
    json_filename = f"{req.animal_type}_{req.body_weight}kg_{req.daily_gain}g.json"
    base, ext = json_filename.rsplit('.', 1)
    base = base.replace('.', '_')
    json_filename = f"{base}.{ext}"
    json_path = CONFIG_DIR / json_filename

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(feed_config, f, ensure_ascii=False, indent=2)

    return feed_config