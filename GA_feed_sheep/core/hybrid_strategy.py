import torch
import numpy as np
from botorch.utils.multi_objective import pareto
from typing import Tuple, List
from botorch.utils.multi_objective.hypervolume import Hypervolume


class HybridStrategy:
    def __init__(self, ref_point: torch.Tensor):
        """
        初始化混合策略

        Args:
            ref_point: 用于计算超体积的参考点
        """
        self.ref_point = ref_point.float()
        self.hv_calculator = Hypervolume(ref_point=ref_point)


    def elite_selection(
            self,
            X: torch.Tensor,
            Y: torch.Tensor,
            n_elites: int = 10,
            diversity_weight: float = 0
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        动态精英选择策略（自动平衡目标值和多样性）

        Args:
            X: 候选解集 (n_samples, n_var)
            Y: 目标值集 (n_samples, n_obj)
            n_elites: 选择的精英数量
            diversity_weight: 基础多样性权重 (0-1)

        Returns:
            elite_X: 精英解集
            elite_Y: 精英目标值
        """
        device = X.device
        Y = Y.to(device)

        # 获取帕累托前沿
        pareto_mask = pareto.is_non_dominated(Y)
        pareto_X, pareto_Y = X[pareto_mask], Y[pareto_mask]

        # 如果解不足直接返回
        if len(pareto_X) <= n_elites:
            return pareto_X, pareto_Y

        # 计算成本排名（成本越低，rank越高）
        cost_rank = torch.argsort(torch.argsort(pareto_Y[:, 0]))  # 双重argsort得到排名
        cost_rank = 1.0 - (cost_rank.float() / (len(cost_rank) - 1))  # 归一化到[0,1]

        # 计算多样性（目标空间拥挤距离）
        dist_matrix = torch.cdist(pareto_Y, pareto_Y, p=2)
        diversity_score = dist_matrix.sort(dim=1).values[:, 1]  # 第二近邻距离
        diversity_rank = (diversity_score - diversity_score.min()) / (
                diversity_score.max() - diversity_score.min() + 1e-6)

        if diversity_weight == 0:
            # 纯成本优化：选择成本最低的n_elites个解
            elite_indices = torch.argsort(pareto_Y[:, 0])[:n_elites]
        else:
            # 综合排名：加权成本和多样性
            combined_rank = (1 - diversity_weight) * cost_rank + diversity_weight * diversity_rank
            elite_indices = torch.argsort(combined_rank, descending=True)[:n_elites]

        return pareto_X[elite_indices], pareto_Y[elite_indices]

