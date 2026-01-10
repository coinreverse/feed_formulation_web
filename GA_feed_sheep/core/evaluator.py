import torch
import json
from typing import Optional


class FeedEvaluator:
    def __init__(self, config_path: str = None, device: Optional[str] = None,
                 precision: str = 'float32'):
        """
        从 JSON 文件加载所有配置的饲料配方评估器

        Args:
            config_path: JSON 配置文件路径
            device: 可选，覆盖配置文件中的设备设置
        """
        # 如果没有提供配置路径，查找默认的JSON文件
        if config_path is None:
            import os
            from pathlib import Path
            config_dir = Path("configs")
            json_files = list(config_dir.glob("*.json"))
            if json_files:
                config_path = str(json_files[0])
            else:
                raise FileNotFoundError("No JSON configuration file found in configs directory")

        with open(config_path, encoding='utf-8') as f:
            feed_config = json.load(f)

        # 设置计算设备（优先使用传入的device参数）
        if device is not None:
            self.device = torch.device(device)
        else:
            self.device = torch.device(feed_config.get("settings", {}).get("device", "cpu"))

        # 加载数据并转换为张量
        self.precision = torch.float32 if precision == 'float32' else torch.float64
        self.costs = torch.tensor(feed_config["costs"], device=self.device, dtype=self.precision)
        self.nutrition = torch.tensor(feed_config["nutrition"], device=self.device, dtype=self.precision)
        self.lower_bounds = torch.tensor(feed_config["nutrient_bounds"]["lower"], device=self.device,
                                         dtype=self.precision)
        self.upper_bounds = torch.tensor(feed_config["nutrient_bounds"]["upper"], device=self.device,
                                         dtype=self.precision)

        # 处理原料上下限
        ingredient_bounds = torch.tensor(feed_config["ingredient_bounds"], device=self.device, dtype=self.precision)
        self.ingredient_lower_bounds = ingredient_bounds[:, 0] / 100.0
        self.ingredient_upper_bounds = ingredient_bounds[:, 1] / 100.0

        # 加载其他配置
        self.tol = feed_config["settings"]["tol"]
        self.penalty_value = 1e6

        # 加载元数据
        self.metadata = feed_config.get("metadata", {})
        self.nutrient_names = self.metadata.get("nutrient_names", [])
        self.ingredient_names = self.metadata.get("ingredient_names", [])

        # 输入验证 - 动态检查维度
        assert len(self.costs) == len(self.ingredient_lower_bounds), _("成本向量与原料数量不匹配")
        assert self.nutrition.shape[0] == len(self.ingredient_lower_bounds), _("营养矩阵行与原料数量不匹配")
        assert self.nutrition.shape[1] == len(self.lower_bounds), _("营养矩阵列与营养素数量不匹配")

    def __call__(self, X: torch.Tensor, tol: float = 0.05) -> torch.Tensor:
        """
        评估饲料配方 (兼容NumPy和PyTorch输入)
        Args:
            X: (n_samples, n_ingredients) 原料配比矩阵 (NumPy数组或PyTorch张量)
            tol: 配比总和的容差阈值
        """
        # 如果需要，将输入转换为pytorch张量
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X, dtype=self.precision, device=self.device)
        else:
            X = X.to(device=self.device, dtype=self.precision)

        with torch.no_grad():
            cost = X @ self.costs
            # 计算所有营养素（包括DM）
            nutrients = X @ self.nutrition
            # 实际应为：各原料干物质含量×原料比例
            dm_calculated = nutrients[:, 0]  # 第0列应为干物质

            # 验证干物质计算逻辑
            if torch.any(dm_calculated < 0) or torch.any(dm_calculated > 100):
                raise ValueError(f"无效干物质值: min={dm_calculated.min()}, max={dm_calculated.max()}")

            nutrients = torch.where(
                torch.isfinite(nutrients),
                nutrients,
                torch.tensor(1e4, device=self.device)
            )

            valid = self._check_constraints(X, nutrients, tol)

            # 动态确定输出维度
            output_dim = 1 + len(self.lower_bounds)  # [成本, 所有营养素]
            output = torch.full(
                (X.shape[0], output_dim),  # [成本, n种营养素]
                self.penalty_value,
                device=self.device,
                dtype=self.precision
            )

            if valid.any():
                output[valid] = torch.cat([
                    cost[valid].unsqueeze(1),
                    nutrients[valid]
                ], dim=1)

            return output

    def _check_constraints(self, X: torch.Tensor, nutrients: torch.Tensor, tol: float) -> torch.Tensor:
        """
        检查给定配方的所有约束
        Args:
            X: 成分比例 (n_samples, n_ingredients)
            nutrients: 计算的营养素 (n_samples, n_nutrients)
            tol: 比率总和的容差
        """
        # 检查成分总和是否为1
        sum_check = torch.abs(torch.sum(X, dim=1) - 1.0) <= tol

        # 检查原料上下限
        ingredient_lower_check = torch.all(X >= self.ingredient_lower_bounds, dim=1)
        ingredient_upper_check = torch.all(X <= self.ingredient_upper_bounds, dim=1)

        # 检查营养素约束
        nutrient_lower_check = torch.all(nutrients >= self.lower_bounds, dim=1)
        nutrient_upper_check = torch.all(nutrients <= self.upper_bounds, dim=1)

        return (sum_check &
                ingredient_lower_check &
                ingredient_upper_check &
                nutrient_lower_check &
                nutrient_upper_check)

    def get_nutrient_names(self) -> list:
        """获取营养素名称"""
        if self.nutrient_names:
            return self.nutrient_names
        # 默认返回常见营养素名称
        return ['DM', 'CP', 'ME', 'MP', 'NDF', 'Ca', 'P']

    def get_ingredient_names(self) -> list:
        """获取原料名称"""
        return self.ingredient_names