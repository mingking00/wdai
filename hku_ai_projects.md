# HKU AI/机器学习项目完整报告

生成时间: 2026-03-16
来源: GitHub arclab-hku 组织分析

---

## 执行摘要

HKU（香港大学）在 GitHub 上的 AI 项目主要集中在 **机器人学习 (Robot Learning)** 方向，而非传统纯软件 AI（如 NLP、推荐系统）。核心实验室为 **ARC Lab** (`arclab-hku`)，研究方向涵盖深度学习、强化学习、模仿学习在机器人感知与导航中的应用。

---

## 一、深度学习 + 机器人（核心方向）

### 1. DEIO (Deep Event-Inertial Odometry)
- **链接**: https://github.com/arclab-hku/DEIO
- **Stars**: 100 ⭐
- **发表**: ICCV 2025 (Oral)
- **核心创新**: 用深度神经网络替代传统手工设计的特征提取，实现事件相机与 IMU 的端到端融合
- **技术栈**: PyTorch, 事件相机数据处理, 惯性测量单元融合
- **应用场景**: 高速运动场景下的视觉-惯性里程计（无人机、自动驾驶）

### 2. P2M (Planning to Move)
- **链接**: https://github.com/arclab-hku/P2M
- **Stars**: 75 ⭐
- **发表**: RA-L 2025
- **核心创新**: 纯 LiDAR 的端到端导航框架，使用强化学习（PPO/SAC）实现动态环境下的实时避障
- **技术栈**: ROS, PyTorch, PPO, SAC, LiDAR 点云处理
- **应用场景**: 室内/室外机器人自主导航

### 3. Imitation_from_video
- **链接**: https://github.com/arclab-hku/Imitation_from_video
- **Stars**: 57 ⭐
- **核心创新**: 从人类/专家操作视频中提取动作策略，迁移到四足机器人控制
- **技术栈**: 模仿学习 (Behavioral Cloning), 计算机视觉, 动作重定向
- **应用场景**: 机器人技能快速迁移，降低编程成本

### 4. MGDP (Multi-modal Generalized Depth Perception)
- **链接**: https://github.com/arclab-hku/MGDP
- **Stars**: 4 ⭐
- **核心创新**: 四足机器人的通用深度感知模型学习，适应多种地形
- **技术栈**: 多模态融合, 深度估计, 域随机化
- **应用场景**: 复杂地形（草地、砂石、楼梯）下的深度感知

---

## 二、强化学习 (Reinforcement Learning)

### 5. Risky_gym
- **链接**: https://github.com/arclab-hku/Risky_gym
- **Stars**: 27 ⭐
- **核心创新**: 风险感知的机器人训练环境，评估策略在危险场景下的表现
- **技术栈**: OpenAI Gym, PyTorch, 风险度量 (CVaR)
- **应用场景**: 安全关键型机器人任务训练

### 6. reinforcement_learning
- **链接**: https://github.com/arclab-hku/reinforcement_learning
- **Stars**: 8 ⭐
- **核心创新**: 实验室内部 RL 算法基础代码库，包含 PPO、SAC、TD3 等实现
- **技术栈**: PyTorch, RL Baselines
- **应用场景**: 快速原型开发，算法对比实验

### 7. DRL_Agile_Gap_Traversal
- **链接**: https://github.com/arclab-hku/DRL_Agile_Gap_Traversal
- **Stars**: 2 ⭐
- **核心创新**: 深度强化学习实现无人机高速穿越狭窄缝隙（敏捷飞行）
- **技术栈**: DRL, 轨迹优化, 四旋翼动力学建模
- **应用场景**: 无人机竞技飞行、搜索救援狭窄空间探索

---

## 三、自监督学习 / 元学习

### 8. SuperEIO
- **链接**: https://github.com/arclab-hku/SuperEIO
- **Stars**: 16 ⭐
- **发表**: TIE 2026
- **核心创新**: 自监督事件特征学习，无需标注数据即可训练事件相机特征提取器
- **技术栈**: 自监督学习, 对比学习, 事件表示学习
- **应用场景**: 降低事件相机数据标注成本，提升泛化能力

### 9. MorAL_Quadruped_Robots
- **链接**: https://github.com/arclab-hku/MorAL_Quadruped_Robots
- **Stars**: 20 ⭐
- **核心创新**: 形态自适应运动控制器的元学习（MAML 变体）
- **技术栈**: 元学习 (Meta-Learning), MAML, 四足机器人控制
- **应用场景**: 机器人损伤自适应（腿受伤后自动调整步态）

---

## 四、神经渲染 + 3D 视觉

### 10. comment_3DGS
- **链接**: https://github.com/arclab-hku/comment_3DGS
- **Stars**: 169 ⭐
- **核心创新**: 3D Gaussian Splatting 详细中文注释版本，便于学习神经渲染
- **技术栈**: 3D Gaussian Splatting, CUDA, PyTorch
- **应用场景**: 实时神经渲染、场景重建

### 11. comment_SplaTAM
- **链接**: https://github.com/arclab-hku/comment_SplaTAM
- **Stars**: 22 ⭐
- **核心创新**: SplaTAM (SLAM + 3DGS) 代码解析与注释
- **技术栈**: SLAM, 3D Gaussian Splatting, 相机位姿估计
- **应用场景**: 实时 SLAM 与高质量场景重建结合

---

## 研究方向分布

```
机器人学习 (RL + 模仿学习)     ████████████████████  40%
视觉-惯性融合 (深度学习)        ██████████████        30%
端到端导航/避障                ████████              18%
自监督/元学习                  ████                  12%
```

---

## 关键结论

1. **AI + 机器人硬件结合**: HKU 的 AI 项目并非纯软件，而是聚焦 AI 算法在机器人感知、决策、控制中的应用

2. **事件相机是特色**: 多个项目涉及事件相机（Event Camera），这是 HKU ARC Lab 的核心研究方向

3. **顶会背书**: DEIO (ICCV 2025 Oral)、P2M (RA-L 2025)、SuperEIO (TIE 2026) 均有顶会发表

4. **开源活跃**: comment_3DGS (169⭐) 是最受欢迎的仓库，显示社区对详细代码注释的需求

---

## 相关资源

- **ARC Lab 官网**: https://arclab.hku.hk/
- **arclab-hku GitHub**: https://github.com/arclab-hku
- **MaRS Lab GitHub**: https://github.com/hku-mars (SLAM/LiDAR 传统强项)

---

*报告生成: wdai | 数据来源: GitHub API*
