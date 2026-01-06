import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端


def plot_convergence(hv_history, best_solutions, save_path=None, show_plot=False):
    """
    绘制GA收敛曲线（超体积和成本）

    Args:
        hv_history: 超体积历史（列表）
        best_solutions: 每代最优解的目标值（列表，形状为n_gen x n_objectives）
        save_path: 图片保存路径（可选）
        show_plot: 是否显示图形（默认False）
    """
    plt.figure(figsize=(7, 3), dpi=600)

    # 1. 绘制超体积曲线
    plt.subplot(1, 2, 1)
    plt.plot(hv_history, 'b-', linewidth=1, label="Hypervolume")
    plt.xlabel("Generation")
    plt.ylabel("Hypervolume (HV)")
    plt.title("Hypervolume Convergence")
    plt.grid(True)
    plt.legend()

    # 2. 绘制成本曲线（过滤>1000的值）
    best_costs = [sol[0] for sol in best_solutions if sol[0] <= 10000]  # 过滤条件

    # 生成对应的x轴索引（可能比原始数据短）
    valid_generations = [i for i, sol in enumerate(best_solutions) if sol[0] <= 10000]

    plt.subplot(1, 2, 2)
    plt.plot(valid_generations, best_costs, 'r-', linewidth=1, label="Best Cost")

    plt.xlabel("Generation")
    plt.ylabel("Cost (yuan/T)")
    plt.title("Best Cost Convergence (Filtered)")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=900)
    if show_plot:
        plt.show()
    plt.close()  # 关闭图形以释放内存
