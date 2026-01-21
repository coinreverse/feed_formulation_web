import os
import random
import sys
import json
from pathlib import Path
import numpy as np
import torch
import time
from typing import Dict, Any
import yaml
from core.genetic_algorithm import run_ga
from core.evaluator import FeedEvaluator
from core.hybrid_strategy import HybridStrategy
from utils.plot_ga_convergence import plot_convergence
from utils.plot_sampling_comparison import plot_convergence_speed, plot_decision_space


# torch.set_default_tensor_type(torch.cuda.DoubleTensor)  # 全局默认 CUDA


def load_configs(config_path: str = None) -> Dict[str, Any]:
    """加载所有配置文件"""
    # 加载GA配置和混合策略配置（仍然使用YAML）
    with open("configs/ga_config.yaml", encoding='utf-8') as f:
        ga_config = yaml.safe_load(f)
    with open("configs/hybrid_config.yaml", encoding='utf-8') as f:
        hybrid_config = yaml.safe_load(f)

    # 加载饲料配置（使用JSON）
    if config_path and os.path.exists(config_path):
        # 如果提供了特定的配置文件路径，则使用该文件
        with open(config_path, encoding='utf-8') as f:
            feed_config = json.load(f)
    else:
        # 默认行为：查找configs目录下的JSON文件
        config_dir = Path("configs")
        json_files = list(config_dir.glob("*.json"))
        if json_files:
            # 使用找到的第一个JSON文件
            with open(json_files[0], encoding='utf-8') as f:
                feed_config = json.load(f)
        else:
            raise FileNotFoundError("No JSON configuration file found in configs directory")

    return ga_config, hybrid_config, feed_config


def save_results(X: torch.Tensor, Y: torch.Tensor, filename: str = "results/pareto_front.pt"):
    """保存优化结果"""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    X_top5 = X[:5] if len(X) >= 5 else X
    Y_top5 = Y[:5] if len(Y) >= 5 else Y
    torch.save({
        'solutions': X_top5,
        'objectives': Y_top5
    }, filename)
    print(f"Results saved to {filename}")


def save_results_json(X: torch.Tensor, Y: torch.Tensor, filename: str = "results/pareto_front.json", nutrient_names: list = None):
    """保存优化结果为JSON格式"""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    X_top5 = X[:5] if len(X) >= 5 else X
    Y_top5 = Y[:5] if len(Y) >= 5 else Y

    # 将PyTorch张量转换为Python列表以便JSON保存
    results = {
        'solutions': X_top5.cpu().numpy().tolist(),
        'objectives': Y_top5.cpu().numpy().tolist(),
        'nutrient_names': nutrient_names if nutrient_names else []
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved to {filename}")


def main(config_path: str = None, output_path: str = "results/ga_pareto_front.json"):
    # 设置随机种子
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    np.random.seed(42)
    random.seed(42)
    # 记录总开始时间
    # start_time = time.time()

    # 加载配置
    ga_config, hybrid_config, feed_config = load_configs(config_path)

    # 初始化组件 - 使用动态配置文件路径
    evaluator = FeedEvaluator(config_path=config_path,
                              device='cuda' if torch.cuda.is_available() else 'cpu', precision='float32')
    ref_point = torch.tensor(hybrid_config['ref_point'])
    strategy = HybridStrategy(ref_point)

    # 阶段1: GA全局探索
    print("\n=== Phase 1: Genetic Algorithm Exploration ===")

    X_ga, Y_ga, ga_population, ga_metadata = run_ga(
        evaluator=evaluator,
        ref_point=ref_point,
    )

    # ga_time = time.time() - start_time  # 计算GA耗时
    # print(f"GA阶段耗时: {ga_time:.2f}秒")

    # 4. 绘制收敛曲线
    output_dir = Path(output_path).parent
    # plot_convergence(
    #     hv_history=ga_metadata["hv_history"],
    #     best_solutions=ga_metadata["best_solutions"],
    #     save_path="results/ga_convergence.png",  # 可选保存路径
    #     show_plot=False  # 不显示图形
    # )

    # 最终结果处理
    elite_ga_X, elite_ga_Y = strategy.elite_selection(
        X_ga, Y_ga,
        n_elites=hybrid_config['n_elites'],
        diversity_weight=hybrid_config['diversity_weight']
    )

    # 保存结果 - 使用JSON格式
    save_results(elite_ga_X, elite_ga_Y, filename=str(Path(output_path).with_suffix('.pt')))
    # 获取营养素名称并传入save_results_json函数
    save_results_json(elite_ga_X, elite_ga_Y, filename=output_path, nutrient_names=evaluator.get_nutrient_names())

    # 5. 绘制不同方式采样收敛与最终散点
    # plot_convergence_speed(
    #     hv_history=ga_metadata["hv_history"],
    #     best_solutions=ga_metadata["best_solutions"],
    #     save_path="results/convergence_mixed_paper.png",
    #     start_gen=20,
    #     method_name="random",
    #     show_plot=False  # 不显示图形
    # )
    # 绘制决策空间分布
    # plot_decision_space(
    #     population=ga_population,
    #     population_F=ga_metadata["population_F"],
    #     save_path="results/decision_mixed_paper.png",
    #     method_name="random",
    #     show_plot=False  # 不显示图形
    # )

    # 输出最佳解
    nutrient_names = evaluator.get_nutrient_names()

    # 动态选择要显示的营养素，不再硬编码
    try:
        # 尝试找到蛋白质和能量相关的营养素
        protein_candidates = [name for name in nutrient_names if 'protein' in name.lower() or 'cp' in name.lower()]
        energy_candidates = [name for name in nutrient_names if
                             'energy' in name.lower() or 'me' in name.lower() or 'digestible_energy' in name.lower()]

        if protein_candidates and energy_candidates:
            # 如果都找到了，使用这些
            crude_protein = nutrient_names.index(protein_candidates[0])
            metabolic_energy = nutrient_names.index(energy_candidates[0])
            protein_display_name = protein_candidates[0].upper()
            energy_display_name = energy_candidates[0].upper()
        else:
            # 否则根据顺序选择前两个营养素
            crude_protein = 0  # 第一个营养素
            metabolic_energy = 1  # 第二个营养素
            # 使用实际的营养素名称作为显示名称
            protein_display_name = nutrient_names[0].upper() if len(nutrient_names) > 0 else "PROTEIN"
            energy_display_name = nutrient_names[1].upper() if len(nutrient_names) > 1 else "ENERGY"
    except (ValueError, IndexError):
        # 如果出现任何错误，回退到根据顺序选择
        crude_protein = 0
        metabolic_energy = 1
        # 使用实际的营养素名称作为显示名称
        protein_display_name = nutrient_names[0].upper() if len(nutrient_names) > 0 else "PROTEIN"
        energy_display_name = nutrient_names[1].upper() if len(nutrient_names) > 1 else "ENERGY"

    min_cost_idx = torch.argmin(elite_ga_Y[:, 0])
    # print("\nBest Solution Summary:")
    # print(f"- Cost: {elite_ga_Y[min_cost_idx, 0]:.2f} 元/T")
    # print(f"- {protein_display_name}: {elite_ga_Y[min_cost_idx, 1 + crude_protein]:.3f}%")
    # print(f"- {energy_display_name}: {elite_ga_Y[min_cost_idx, 1 + metabolic_energy]:.2f} MJ/kg")
    # print("\nOptimization completed!")

    # total_time = time.time() - start_time
    # print("\n=== 性能统计 ===")
    # print(f"总运行时间: {total_time:.2f}秒")
    # print(f"- GA阶段: {ga_time:.2f}秒 ({ga_time / total_time * 100:.1f}%)")


if __name__ == "__main__":
    config_path = None
    output_path = "results/ga_pareto_front.json"

    if len(sys.argv) > 1:
        # 第一个参数是配置文件路径
        config_path = sys.argv[1]
        # 推断结果文件路径
        if config_path and os.path.exists(config_path):
            config_file_name = Path(config_path).stem
            output_path = f"results/{config_file_name}_result.json"

    if len(sys.argv) > 2:
        # 第二个参数是指定的结果文件路径
        output_path = sys.argv[2]

    main(config_path, output_path)