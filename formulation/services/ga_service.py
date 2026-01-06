import subprocess
from pathlib import Path

from formulation.services.json_builder import (
    build_feed_json,
    get_json_paths
)
from formulation.services.result_parser import import_ga_result_to_db
from animal_requirements.models import AnimalRequirement
from formulation.models import FeedFormulaResult

# ✅ Django 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ✅ 你的 GA-feed-sheep 项目根目录（关键变量）
GA_DIR = BASE_DIR / "GA_feed_sheep"


def sync_data_automatically(requirement_id):
    """
    ✅ 自动同步数据：
    1. 如果JSON配置文件存在但数据库中没有对应数据，则从JSON导入到数据库
    2. 如果数据库中有数据但JSON配置文件不存在，则从数据库生成JSON文件
    """
    # 检查数据库中是否已经有对应的动物需求数据
    try:
        requirement = AnimalRequirement.objects.get(id=requirement_id)
    except AnimalRequirement.DoesNotExist:
        raise ValueError(f"动物营养需求记录(ID: {requirement_id})不存在，请先创建相应的记录。")

    input_path, output_path = get_json_paths(requirement_id)  # 替换 get_yaml_paths 为 get_json_paths

    # 检查JSON配置文件是否存在
    if input_path.exists():
        # 检查数据库中是否已经有对应的动物需求数据
        try:
            requirement = AnimalRequirement.objects.get(id=requirement_id)
            # 如果数据库中没有配方结果，则尝试从JSON导入
            if not FeedFormulaResult.objects.filter(requirement=requirement).exists():
                # 这里我们可以考虑从JSON导入数据到数据库
                # 但考虑到JSON主要用于GA算法输入，而不是结果，所以此场景可能不适用
                pass
        except AnimalRequirement.DoesNotExist:
            # 如果数据库中没有动物需求数据，则从JSON导入
            # 注意：这需要JSON文件有完整的动物需求数据
            pass

    # 如果JSON配置文件不存在但数据库中有数据，则生成JSON文件
    if not input_path.exists():
        try:
            AnimalRequirement.objects.get(id=requirement_id)
            # 生成JSON配置文件
            build_feed_json(requirement_id)  # 替换 build_feed_yaml 为 build_feed_json
            # build_feed_json 函数已经包含了保存文件的逻辑，所以不需要额外写入

        except AnimalRequirement.DoesNotExist:
            # 数据库中也没有数据，无法生成JSON
            pass


def generate_and_write_feed_json(requirement_id, selected_ingredient_ids=None):
    """
    ✅ 生成 feed_config.json（不覆盖旧文件，按动物参数命名）
    """
    # build_feed_json 函数已经包含了保存文件的逻辑，所以只需要调用它
    build_feed_json(requirement_id, selected_ingredient_ids)  # 替换 build_feed_yaml 为 build_feed_json

    input_path, output_path = get_json_paths(requirement_id)  # 替换 get_yaml_paths 为 get_json_paths

    return input_path, output_path


def run_ga_and_import(requirement_id, selected_ingredient_ids=None):
    """
    ✅ 终极函数：
    1️⃣ 生成 JSON
    2️⃣ 运行 GA
    3️⃣ 解析 result.json
    4️⃣ 自动入库
    """

    # 先进行数据同步检查
    sync_data_automatically(requirement_id)

    # 将selected_ingredient_ids传递给generate_and_write_feed_json函数
    output_json_path = run_ga_algorithm(requirement_id,
                                        selected_ingredient_ids)  # 替换 output_yaml_path 为 output_json_path

    import_ga_result_to_db(
        json_path=output_json_path,
        requirement_id=requirement_id,
        selected_ingredient_ids=selected_ingredient_ids  # 添加这个参数
    )

    return True


def run_ga_algorithm(requirement_id, selected_ingredient_ids=None):
    """
    ✅ 调用 GA-feed-sheep 算法主程序
    """
    # 将selected_ingredient_ids传递给generate_and_write_feed_json函数
    input_path, output_path = generate_and_write_feed_json(requirement_id, selected_ingredient_ids)  # 替换 generate_and_write_feed_yaml 为 generate_and_write_feed_json

    # ✅ 通过命令行参数将 JSON 配置文件传给算法
    result = subprocess.run(
        ["python", "main.py", str(input_path), str(output_path)],
        cwd=GA_DIR,  # ✅ 确保在 ga_engine 目录下执行
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"GA 算法运行失败:\n{result.stderr}"
        )

    return output_path