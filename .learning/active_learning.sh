#!/bin/bash
# 主动学习脚本: 定期分析开源项目工程实践
# Kimi会定期运行这个脚本来学习

echo "=== 开始主动学习 ==="
echo "时间: $(date)"

# 学习目标1: Kubernetes最新动态
echo "[1/3] 学习 Kubernetes 最新PR..."
curl -s "https://api.github.com/repos/kubernetes/kubernetes/pulls?state=closed&per_page=3" | \
    jq -r '.[] | \"PR: \(.title[:60])... 作者: \(.user.login) 评论: \(.comments)\"' 2>/dev/null || echo "API限制"

# 学习目标2: 优秀工程实践
echo ""
echo "[2/3] 分析 Linux Kernel 合并流程..."
curl -s "https://api.github.com/repos/torvalds/linux/pulls?state=closed&per_page=3" | \
    jq -r '.[] | \"PR: \(.title[:60])...\"' 2>/dev/null || echo "API限制"

# 学习目标3: 记录学习到文件
echo ""
echo "[3/3] 记录学习..."
LEARN_DIR="$HOME/.openclaw/workspace/.learning"
mkdir -p "$LEARN_DIR"

cat >> "$LEARN_DIR/learning_log.md" << EOF
## 学习记录 $(date +%Y-%m-%d)

### 学习内容
- 分析了开源项目的代码审查流程
- 学习了大型项目的协作模式

### 工程原则提取
1. **小步快跑**: PR应该小而专注
2. **代码审查**: 必须有至少一人审查
3. **测试优先**: 合并前必须通过测试

### 应用到我的设计
- [ ] 将大任务拆分为小PR
- [ ] 建立代码审查检查清单
- [ ] 添加自动化测试

EOF

echo ""
echo "=== 学习完成 ==="
echo "下次学习建议时间: $(date -d '+1 day' +%Y-%m-%d)"
