#!/usr/bin/env python3
"""
Diffuser Core Implementation - 扩散模型规划器核心实现
基于论文: Planning with Diffusion for Flexible Behavior Synthesis (Janner et al., 2022)

学习目标:
1. 理解扩散模型在轨迹规划中的应用
2. 实现核心的去噪扩散过程
3. 应用到实际的决策场景
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Tuple, Optional, List
from dataclasses import dataclass

@dataclass
class DiffuserConfig:
    """Diffuser配置"""
    horizon: int = 100          # 规划时间步长
    transition_dim: int = 4     # 状态+动作维度 (e.g., x, y, vx, vy)
    n_diffusion_steps: int = 20 # 扩散步数
    n_train_steps: int = 10000  # 训练步数
    batch_size: int = 32
    learning_rate: float = 2e-4
    device: str = "cpu"

class TemporalUNet(nn.Module):
    """
    时间U-Net架构
    输入: 噪声轨迹 [batch, horizon, transition_dim]
    输出: 预测的噪声 [batch, horizon, transition_dim]
    """
    
    def __init__(self, transition_dim: int, horizon: int, time_embed_dim: int = 64):
        super().__init__()
        self.transition_dim = transition_dim
        self.horizon = horizon
        
        # 时间步嵌入
        self.time_embed = nn.Sequential(
            nn.Linear(1, time_embed_dim),
            nn.SiLU(),
            nn.Linear(time_embed_dim, time_embed_dim),
        )
        
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(transition_dim + time_embed_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
        )
        
        # 中间层 (保持序列长度)
        self.middle = nn.Sequential(
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
        )
        
        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, transition_dim),
        )
    
    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 噪声轨迹 [batch, horizon, transition_dim]
            t: 时间步 [batch]
        
        Returns:
            预测的噪声 [batch, horizon, transition_dim]
        """
        batch_size, horizon, trans_dim = x.shape
        
        # 时间嵌入 [batch, time_embed_dim]
        t_embed = self.time_embed(t.float().unsqueeze(-1) / 20.0)
        
        # 扩展时间嵌入到每个时间步 [batch, horizon, time_embed_dim]
        t_embed = t_embed.unsqueeze(1).expand(-1, horizon, -1)
        
        # 拼接轨迹和时间嵌入
        x_t = torch.cat([x, t_embed], dim=-1)  # [batch, horizon, trans_dim + time_embed]
        
        # 编码 [batch, horizon, 256]
        h = self.encoder(x_t)
        
        # 中间处理
        h = self.middle(h)
        
        # 解码 [batch, horizon, trans_dim]
        out = self.decoder(h)
        
        return out

class Diffuser:
    """
    Diffuser: 基于扩散模型的轨迹规划器
    """
    
    def __init__(self, config: DiffuserConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # 模型
        self.model = TemporalUNet(
            config.transition_dim, 
            config.horizon
        ).to(self.device)
        
        # 优化器
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), 
            lr=config.learning_rate
        )
        
        # 扩散参数
        self.betas = torch.linspace(1e-4, 0.02, config.n_diffusion_steps).to(self.device)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)
    
    def add_noise(self, x0: torch.Tensor, t: torch.Tensor, noise: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向扩散: 向干净轨迹添加噪声
        
        q(x_t | x_0) = N(x_t; sqrt(alpha_t) * x_0, (1-alpha_t) * I)
        """
        if noise is None:
            noise = torch.randn_like(x0)
        
        sqrt_alpha_t = self.sqrt_alphas_cumprod[t].view(-1, 1, 1)
        sqrt_one_minus_alpha_t = self.sqrt_one_minus_alphas_cumprod[t].view(-1, 1, 1)
        
        return sqrt_alpha_t * x0 + sqrt_one_minus_alpha_t * noise
    
    def train_step(self, batch: torch.Tensor) -> float:
        """
        训练一步
        
        目标: 预测添加的噪声
        Loss = E[|| noise - model(x_t, t) ||^2]
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        batch = batch.to(self.device)
        batch_size = batch.shape[0]
        
        # 随机采样时间步
        t = torch.randint(0, self.config.n_diffusion_steps, (batch_size,), device=self.device)
        
        # 添加噪声
        noise = torch.randn_like(batch)
        x_t = self.add_noise(batch, t, noise)
        
        # 预测噪声
        predicted_noise = self.model(x_t, t)
        
        # 计算损失
        loss = torch.nn.functional.mse_loss(predicted_noise, noise)
        
        # 反向传播
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def sample(self, batch_size: int = 1) -> torch.Tensor:
        """
        采样轨迹: 从噪声逐步去噪生成完整轨迹
        """
        self.model.eval()
        
        # 从纯噪声开始
        x = torch.randn(batch_size, self.config.horizon, self.config.transition_dim, device=self.device)
        
        # 逐步去噪
        with torch.no_grad():
            for t in reversed(range(self.config.n_diffusion_steps)):
                t_batch = torch.full((batch_size,), t, device=self.device, dtype=torch.long)
                
                # 预测噪声
                predicted_noise = self.model(x, t_batch)
                
                # 计算去噪后的x
                alpha_t = self.alphas[t]
                alpha_cumprod_t = self.alphas_cumprod[t]
                beta_t = self.betas[t]
                
                # 均值
                mean = (x - beta_t / torch.sqrt(1 - alpha_cumprod_t) * predicted_noise) / torch.sqrt(alpha_t)
                
                if t > 0:
                    # 添加随机噪声 (除了最后一步)
                    noise = torch.randn_like(x)
                    variance = beta_t
                    x = mean + torch.sqrt(variance) * noise
                else:
                    x = mean
        
        return x
    
    def train(self, dataset: torch.Tensor):
        """
        训练模型
        
        Args:
            dataset: 专家轨迹数据集 [N, horizon, transition_dim]
        """
        print(f"开始训练 Diffuser...")
        print(f"数据集大小: {dataset.shape}")
        print(f"训练步数: {self.config.n_train_steps}")
        
        for step in range(self.config.n_train_steps):
            # 随机采样批次
            indices = torch.randint(0, len(dataset), (self.config.batch_size,))
            batch = dataset[indices]
            
            loss = self.train_step(batch)
            
            if step % 1000 == 0:
                print(f"Step {step}/{self.config.n_train_steps}, Loss: {loss:.4f}")
        
        print("训练完成!")


# ==================== 演示: 简单导航任务 ====================

def generate_expert_data(n_trajectories: int = 1000, horizon: int = 100) -> torch.Tensor:
    """
    生成专家演示数据
    
    任务: 从(0,0)导航到(10,10)
    状态: [x, y, vx, vy]
    """
    trajectories = []
    
    for _ in range(n_trajectories):
        trajectory = []
        
        # 起始点
        x, y = 0.0, 0.0
        
        # 目标点
        target_x, target_y = 10.0, 10.0
        
        for t in range(horizon):
            # 简单的专家策略: 朝向目标移动
            dx = target_x - x
            dy = target_y - y
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                vx = dx / horizon * 2 + np.random.randn() * 0.1
                vy = dy / horizon * 2 + np.random.randn() * 0.1
            else:
                vx, vy = 0, 0
            
            trajectory.append([x, y, vx, vy])
            
            # 更新位置
            x += vx * 0.1
            y += vy * 0.1
        
        trajectories.append(trajectory)
    
    return torch.tensor(trajectories, dtype=torch.float32)


def demo():
    """演示Diffuser在导航任务中的应用"""
    print("=" * 60)
    print("Diffuser Demo: 简单导航任务")
    print("=" * 60)
    
    # 配置
    config = DiffuserConfig(
        horizon=100,
        transition_dim=4,  # [x, y, vx, vy]
        n_diffusion_steps=20,
        n_train_steps=5000,
        batch_size=64,
    )
    
    # 生成专家数据
    print("\n[1] 生成专家轨迹数据...")
    expert_data = generate_expert_data(n_trajectories=1000, horizon=config.horizon)
    
    # 归一化
    mean = expert_data.mean(dim=(0, 1))
    std = expert_data.std(dim=(0, 1))
    expert_data = (expert_data - mean) / (std + 1e-8)
    
    # 创建Diffuser
    print("\n[2] 初始化Diffuser...")
    diffuser = Diffuser(config)
    
    # 训练
    print("\n[3] 训练模型...")
    diffuser.train(expert_data)
    
    # 生成新轨迹
    print("\n[4] 生成新轨迹...")
    generated_traj = diffuser.sample(batch_size=1)[0]  # [horizon, 4]
    
    # 反归一化
    generated_traj = generated_traj * std + mean
    
    print("\n生成的轨迹 (前5步):")
    for i in range(5):
        x, y, vx, vy = generated_traj[i].numpy()
        print(f"  Step {i}: pos=({x:.2f}, {y:.2f}), vel=({vx:.2f}, {vy:.2f})")
    
    print(f"\n起点: ({generated_traj[0, 0]:.2f}, {generated_traj[0, 1]:.2f})")
    print(f"终点: ({generated_traj[-1, 0]:.2f}, {generated_traj[-1, 1]:.2f})")
    print(f"目标: (10.00, 10.00)")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
