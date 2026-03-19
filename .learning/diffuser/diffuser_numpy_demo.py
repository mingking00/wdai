#!/usr/bin/env python3
"""
Diffuser Concept Demo - 扩散模型规划器概念演示
使用NumPy实现核心算法，无需PyTorch

学习目标: 理解"扩散模型如何生成轨迹"
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 无GUI模式
import matplotlib.pyplot as plt
from pathlib import Path

class SimpleDiffuser:
    """
    简化版Diffuser
    
    核心思想:
    1. 学习从噪声中恢复轨迹
    2. 通过去噪过程生成新的合理轨迹
    """
    
    def __init__(self, horizon: int = 50, dim: int = 2, n_steps: int = 20):
        self.horizon = horizon  # 轨迹长度
        self.dim = dim          # 维度 (x, y)
        self.n_steps = n_steps  # 扩散步数
        
        # 简化的噪声预测器 (线性模型)
        self.weights = None
        self.bias = None
        
        # 扩散参数
        self.betas = np.linspace(1e-4, 0.02, n_steps)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas)
    
    def add_noise(self, x0: np.ndarray, t: int) -> np.ndarray:
        """向轨迹添加噪声"""
        noise = np.random.randn(*x0.shape)
        sqrt_alpha = np.sqrt(self.alphas_cumprod[t])
        sqrt_one_minus_alpha = np.sqrt(1 - self.alphas_cumprod[t])
        return sqrt_alpha * x0 + sqrt_one_minus_alpha * noise
    
    def train(self, trajectories: np.ndarray, epochs: int = 100):
        """
        训练噪声预测器
        
        简化版: 使用线性回归预测噪声
        """
        print(f"训练扩散模型...")
        print(f"数据形状: {trajectories.shape}")
        print(f"训练轮数: {epochs}")
        
        n_samples = len(trajectories)
        
        # 准备训练数据
        X_train = []
        y_train = []
        
        for _ in range(epochs * n_samples):
            # 随机选择轨迹
            idx = np.random.randint(n_samples)
            x0 = trajectories[idx]
            
            # 随机时间步
            t = np.random.randint(self.n_steps)
            
            # 添加噪声
            noise = np.random.randn(*x0.shape)
            x_t = self.add_noise(x0, t)
            
            # 展平
            X_train.append(np.concatenate([[t / self.n_steps], x_t.flatten()]))
            y_train.append(noise.flatten())
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        # 线性回归 (简化)
        self.weights = np.linalg.lstsq(X_train, y_train, rcond=None)[0]
        
        print(f"训练完成! 权重形状: {self.weights.shape}")
    
    def predict_noise(self, x_t: np.ndarray, t: int) -> np.ndarray:
        """预测噪声"""
        features = np.concatenate([[t / self.n_steps], x_t.flatten()])
        noise_pred = features @ self.weights
        return noise_pred.reshape(x_t.shape)
    
    def sample(self) -> np.ndarray:
        """
        采样轨迹: 从纯噪声逐步去噪
        
        这是Diffuser的核心!
        """
        # 从纯噪声开始
        x = np.random.randn(self.horizon, self.dim)
        
        # 逐步去噪
        for t in reversed(range(self.n_steps)):
            # 预测噪声
            predicted_noise = self.predict_noise(x, t)
            
            # 去噪 (简化的DDPM公式)
            alpha_t = self.alphas[t]
            alpha_cumprod_t = self.alphas_cumprod[t]
            beta_t = self.betas[t]
            
            # 计算均值
            mean = (x - beta_t / np.sqrt(1 - alpha_cumprod_t) * predicted_noise) / np.sqrt(alpha_t)
            
            if t > 0:
                # 添加随机性
                noise = np.random.randn(*x.shape) * 0.1
                x = mean + noise
            else:
                x = mean
        
        return x


def generate_navigation_data(n_trajectories: int = 100) -> np.ndarray:
    """
    生成导航任务数据
    
    任务: 从(0,0)移动到(10,10)
    """
    trajectories = []
    
    for _ in range(n_trajectories):
        # 起点
        start = np.array([0.0, 0.0])
        
        # 终点
        end = np.array([10.0, 10.0])
        
        # 直线插值 + 随机噪声
        t = np.linspace(0, 1, 50)
        trajectory = (1 - t)[:, None] * start + t[:, None] * end
        trajectory += np.random.randn(50, 2) * 0.3  # 添加噪声
        
        trajectories.append(trajectory)
    
    return np.array(trajectories)


def visualize(trajectories: np.ndarray, generated: np.ndarray, output_path: str):
    """可视化结果"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 专家轨迹
    ax = axes[0]
    for traj in trajectories[:10]:  # 只画10条
        ax.plot(traj[:, 0], traj[:, 1], alpha=0.5, color='blue')
    ax.scatter([0], [0], color='green', s=100, label='Start')
    ax.scatter([10], [10], color='red', s=100, label='Goal')
    ax.set_xlim(-2, 12)
    ax.set_ylim(-2, 12)
    ax.set_title('Expert Trajectories (训练数据)')
    ax.legend()
    ax.grid(True)
    
    # 生成轨迹
    ax = axes[1]
    for i in range(5):  # 生成5条
        gen = generated[i]
        ax.plot(gen[:, 0], gen[:, 1], alpha=0.7, label=f'Generated {i+1}')
    ax.scatter([0], [0], color='green', s=100, label='Start')
    ax.scatter([10], [10], color='red', s=100, label='Goal')
    ax.set_xlim(-2, 12)
    ax.set_ylim(-2, 12)
    ax.set_title('Generated Trajectories (扩散模型生成)')
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n可视化结果已保存: {output_path}")


def demo():
    """演示Diffuser核心概念"""
    print("=" * 60)
    print("🧠 Diffuser Concept Demo - 扩散模型规划器")
    print("=" * 60)
    
    # 1. 生成训练数据
    print("\n[1] 生成专家轨迹...")
    expert_data = generate_navigation_data(n_trajectories=100)
    print(f"   生成 {len(expert_data)} 条轨迹")
    print(f"   每条轨迹形状: {expert_data[0].shape}")
    
    # 2. 创建并训练Diffuser
    print("\n[2] 创建Diffuser...")
    diffuser = SimpleDiffuser(horizon=50, dim=2, n_steps=20)
    
    print("\n[3] 训练模型...")
    diffuser.train(expert_data, epochs=50)
    
    # 3. 生成新轨迹
    print("\n[4] 生成新轨迹 (从噪声中采样)...")
    generated_trajs = []
    for i in range(5):
        traj = diffuser.sample()
        generated_trajs.append(traj)
        print(f"   轨迹 {i+1}: 起点({traj[0,0]:.2f}, {traj[0,1]:.2f}) -> 终点({traj[-1,0]:.2f}, {traj[-1,1]:.2f})")
    
    generated_trajs = np.array(generated_trajs)
    
    # 4. 可视化
    print("\n[5] 可视化结果...")
    output_dir = Path(".learning/diffuser")
    output_dir.mkdir(parents=True, exist_ok=True)
    visualize(expert_data, generated_trajs, str(output_dir / "diffuser_demo.png"))
    
    # 5. 总结
    print("\n" + "=" * 60)
    print("📊 总结")
    print("=" * 60)
    print("\n✅ 成功实现了Diffuser的核心概念:")
    print("   1. 前向扩散: 向专家轨迹添加噪声")
    print("   2. 训练: 学习预测噪声")
    print("   3. 反向去噪: 从纯噪声生成合理轨迹")
    print("\n🎯 关键技术洞察:")
    print("   - 扩散模型通过学习'去噪'来理解轨迹分布")
    print("   - 采样时从噪声开始，逐步去噪生成新轨迹")
    print("   - 这实现了'全局规划'而非'逐步决策'")
    print("\n🔬 应用到RL:")
    print("   - 状态-动作序列 = 轨迹")
    print("   - 训练数据 = 专家演示")
    print("   - 生成 = 规划")
    print("=" * 60)


if __name__ == "__main__":
    demo()
