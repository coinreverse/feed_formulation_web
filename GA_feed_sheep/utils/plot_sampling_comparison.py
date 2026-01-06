import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端



def plot_convergence_speed(hv_history, best_solutions=None, save_path=None, start_gen=20, method_name="random", show_plot=False):
    """
    绘制遗传算法收敛曲线（HV随代数变化）——风格与另一绘图函数保持一致
    """
    generations = np.arange(start_gen, start_gen + len(hv_history))

    plt.figure(figsize=(7, 3), dpi=600)
    plt.plot(generations, hv_history, 'b-', linewidth=1, label='HV Evolution')
    plt.fill_between(generations, hv_history, color='b', alpha=0.15)

    plt.title(f'Convergence Speed ({method_name})')
    plt.xlabel('Generation')
    plt.ylabel('Hypervolume')
    plt.grid(True, linestyle='--', linewidth=0.8, alpha=0.7, color='gray')
    plt.legend(loc='upper left', frameon=False)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=900)
    if show_plot:
        plt.show()
    plt.close()  # 关闭图形以释放内存


def plot_decision_space(population, population_F, save_path=None, method_name="random", show_plot=False):
    """
    绘制决策空间散点图（与另一绘图函数风格统一）
    """
    X = population.detach().cpu().numpy()
    F = population_F.detach().cpu().numpy()
    objective_sum = np.sum(F, axis=1)

    plt.figure(figsize=(7, 3), dpi=600)
    sc = plt.scatter(X[:, 0], X[:, 1], c=objective_sum, cmap='viridis',
                     s=30, edgecolor='k', linewidth=0.4)
    cbar = plt.colorbar(sc)
    cbar.set_label('Objective Sum', fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    plt.title(f'Decision Space ({method_name})')
    plt.xlabel('Decision Variable 1')
    plt.ylabel('Decision Variable 2')
    plt.grid(True, linestyle='--', linewidth=0.8, alpha=0.7, color='gray')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=900)
    if show_plot:
        plt.show()
    plt.close()  # 关闭图形以释放内存
