#!/bin/bash
# CodeDev Agent 管理脚本

CODEDEV_DIR="/root/.openclaw/workspace/skills/code-dev-agent"
PID_FILE="$CODEDEV_DIR/codedev.pid"
LOG_FILE="$CODEDEV_DIR/logs/service.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查是否运行
is_running() {
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 启动服务
start() {
    if is_running; then
        echo -e "${YELLOW}CodeDev Agent 已在运行 (PID: $(get_pid))${NC}"
        return 0
    fi
    
    echo -e "${BLUE}启动 CodeDev Agent...${NC}"
    
    # 确保目录存在
    mkdir -p "$CODEDEV_DIR/requests"
    mkdir -p "$CODEDEV_DIR/results"
    mkdir -p "$CODEDEV_DIR/logs"
    
    # 启动服务
    nohup python3 "$CODEDEV_DIR/codedev_service.py" > "$LOG_FILE" 2>&1 &
    pid=$!
    
    # 保存PID
    echo $pid > "$PID_FILE"
    
    # 等待启动
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✓ CodeDev Agent 已启动 (PID: $pid)${NC}"
        echo -e "${BLUE}  请求目录: $CODEDEV_DIR/requests${NC}"
        echo -e "${BLUE}  结果目录: $CODEDEV_DIR/results${NC}"
        echo -e "${BLUE}  日志文件: $LOG_FILE${NC}"
    else
        echo -e "${RED}✗ 启动失败${NC}"
        return 1
    fi
}

# 停止服务
stop() {
    if ! is_running; then
        echo -e "${YELLOW}CodeDev Agent 未在运行${NC}"
        return 0
    fi
    
    pid=$(get_pid)
    echo -e "${BLUE}停止 CodeDev Agent (PID: $pid)...${NC}"
    
    kill "$pid" 2>/dev/null
    
    # 等待停止
    for i in {1..10}; do
        if ! is_running; then
            break
        fi
        sleep 1
    done
    
    if ! is_running; then
        echo -e "${GREEN}✓ CodeDev Agent 已停止${NC}"
        rm -f "$PID_FILE"
    else
        echo -e "${RED}✗ 停止失败，强制终止...${NC}"
        kill -9 "$pid" 2>/dev/null
        rm -f "$PID_FILE"
    fi
}

# 查看状态
status() {
    if is_running; then
        pid=$(get_pid)
        echo -e "${GREEN}CodeDev Agent 运行中 (PID: $pid)${NC}"
        
        # 统计请求
        req_count=$(ls -1 "$CODEDEV_DIR/requests"/req_*.json 2>/dev/null | wc -l)
        result_count=$(ls -1 "$CODEDEV_DIR/results"/result_*.json 2>/dev/null | wc -l)
        
        echo -e "${BLUE}  待处理请求: $req_count${NC}"
        echo -e "${BLUE}  已完成结果: $result_count${NC}"
    else
        echo -e "${YELLOW}CodeDev Agent 未运行${NC}"
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# 提交开发请求
dev() {
    description="$1"
    language="${2:-python}"
    
    if [ -z "$description" ]; then
        echo -e "${RED}错误: 请提供开发需求描述${NC}"
        echo "用法: ./codedev.sh dev '需求描述' [语言]"
        return 1
    fi
    
    if ! is_running; then
        echo -e "${YELLOW}CodeDev Agent 未运行，正在启动...${NC}"
        start
        sleep 2
    fi
    
    # 生成请求ID
    request_id="CODEDEV_$(date +%Y%m%d_%H%M%S)"
    
    # 创建请求文件
    cat > "$CODEDEV_DIR/requests/req_$request_id.json" << EOF
{
  "request_id": "$request_id",
  "description": "$description",
  "language": "$language",
  "requirements": [],
  "constraints": [],
  "priority": 5,
  "created_at": "$(date -Iseconds)"
}
EOF
    
    echo -e "${GREEN}✓ 已提交开发请求${NC}"
    echo -e "${BLUE}  请求ID: $request_id${NC}"
    echo -e "${BLUE}  语言: $language${NC}"
    echo ""
    echo -e "${YELLOW}正在处理中，请稍候...${NC}"
    
    # 等待处理完成
    for i in {1..60}; do
        if [ -f "$CODEDEV_DIR/results/result_$request_id.json" ]; then
            echo -e "${GREEN}✓ 处理完成!${NC}"
            echo ""
            
            # 显示结果摘要
            if command -v jq >/dev/null 2>&1; then
                echo -e "${BLUE}执行流程:${NC}"
                jq -r '.results[] | "  \(.role): \(.status)"' "$CODEDEV_DIR/results/result_$request_id.json"
                echo ""
                echo -e "${BLUE}最终输出预览:${NC}"
                jq -r '.final_output' "$CODEDEV_DIR/results/result_$request_id.json" | head -20
            else
                cat "$CODEDEV_DIR/results/result_$request_id.json"
            fi
            
            return 0
        fi
        sleep 1
    done
    
    echo -e "${YELLOW}处理超时，请稍后查看结果${NC}"
    echo -e "${BLUE}结果文件: $CODEDEV_DIR/results/result_$request_id.json${NC}"
}

# 查看结果
result() {
    request_id="$1"
    
    if [ -z "$request_id" ]; then
        # 列出所有结果
        echo -e "${BLUE}可用结果:${NC}"
        for f in "$CODEDEV_DIR/results"/result_*.json; do
            if [ -f "$f" ]; then
                basename "$f" .json | sed 's/result_//'
            fi
        done
        return 0
    fi
    
    result_file="$CODEDEV_DIR/results/result_$request_id.json"
    
    if [ -f "$result_file" ]; then
        if command -v jq >/dev/null 2>&1; then
            cat "$result_file" | jq .
        else
            cat "$result_file"
        fi
    else
        echo -e "${RED}结果不存在: $request_id${NC}"
    fi
}

# 查看IER经验统计
ier_stats() {
    echo -e "${BLUE}IER迭代经验精炼系统统计${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_system import get_experience_manager
    manager = get_experience_manager()
    stats = manager.get_statistics()
    
    print(f"总经验数: {stats['total_experiences']}")
    print(f"活跃经验: {stats['active_experiences']}")
    print(f"可靠经验: {stats['reliable_experiences']}")
    print(f"历史任务: {stats['total_tasks']}")
    print("")
    print("按类型分布:")
    for exp_type, count in stats['by_type'].items():
        print(f"  {exp_type}: {count}")
except Exception as e:
    print(f"获取统计失败: {e}")
EOF
}

# 列出经验
ier_list() {
    exp_type="$1"
    
    echo -e "${BLUE}IER经验列表${NC}"
    if [ -n "$exp_type" ]; then
        echo -e "${BLUE}过滤类型: $exp_type${NC}"
    fi
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_system import get_experience_manager
    manager = get_experience_manager()
    
    filter_type = "$exp_type"
    count = 0
    
    for exp_id, exp in manager.experiences.items():
        if filter_type and exp.exp_type.value != filter_type:
            continue
        count += 1
        print(f"ID: {exp.id}")
        print(f"名称: {exp.name}")
        print(f"类型: {exp.exp_type.value}")
        print(f"成功率: {exp.success_rate():.1%} ({exp.success_count}/{exp.usage_count})")
        print(f"状态: {exp.status.value}")
        print(f"场景: {exp.context[:80]}...")
        print("-" * 50)
    
    if count == 0:
        print("没有找到经验")
    else:
        print(f"\n共 {count} 条经验")
except Exception as e:
    print(f"列出经验失败: {e}")
EOF
}

# 运行经验维护
ier_maintain() {
    echo -e "${BLUE}运行IER经验维护...${NC}"
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_system import get_experience_manager
    manager = get_experience_manager()
    
    eliminated = manager.evaluate_and_eliminate()
    stats = manager.get_statistics()
    
    print(f"淘汰经验数: {len(eliminated)}")
    if eliminated:
        print("被淘汰的经验:")
        for exp_id in eliminated:
            print(f"  - {exp_id}")
    print("")
    print(f"当前状态: {stats['active_experiences']}/{stats['total_experiences']} 活跃经验")
except Exception as e:
    print(f"维护失败: {e}")
EOF
}

# IER-KG知识图谱统计
ier_kg_stats() {
    echo -e "${BLUE}IER-KG 知识图谱系统统计${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    stats = adapter.get_statistics()
    
    print("=" * 50)
    print("IER基础统计:")
    print(f"  总经验数: {stats['ier']['total_experiences']}")
    print(f"  活跃经验: {stats['ier']['active_experiences']}")
    print(f"  可靠经验: {stats['ier']['reliable_experiences']}")
    print(f"  历史任务: {stats['ier']['total_tasks']}")
    
    if stats['kg_enabled'] and 'kg' in stats:
        print("")
        print("=" * 50)
        print("KG知识图谱统计:")
        kg = stats['kg']
        print(f"  代码实体: {kg.get('code_entities', 0)}")
        print(f"  代码关系: {kg.get('code_relations', 0)}")
        print(f"  图谱经验: {kg.get('experiences', 0)}")
        print(f"  经验关系: {kg.get('experience_edges', 0)}")
        print(f"  溯源链: {kg.get('provenance_chains', 0)}")
        
        if 'enhancement' in stats:
            print("")
            print("=" * 50)
            print("KG增强指标:")
            enh = stats['enhancement']
            print(f"  ✓ 代码实体索引: {enh['code_entities_indexed']}")
            print(f"  ✓ 带溯源经验: {enh['experiences_with_provenance']}")
            print(f"  ✓ 溯源链数: {enh['provenance_chains']}")
            print(f"  ✓ 多跳检索就绪: {enh['multihop_retrieval_ready']}")
    else:
        print("\n⚠ 知识图谱系统未启用")
    
    adapter.close()
except Exception as e:
    print(f"获取统计失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG检索测试
ier_kg_search() {
    query="$1"
    
    if [ -z "$query" ]; then
        echo -e "${RED}错误: 请提供查询内容${NC}"
        echo "用法: ./codedev.sh ier-kg-search '查询内容'"
        return 1
    fi
    
    echo -e "${BLUE}IER-KG多跳检索: $query${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    results = adapter.retrieve_for_task(
        task_description="$query",
        max_hops=2
    )
    
    print(f"检索结果: {len(results['experiences'])} 条")
    print(f"  来源IER: {results['ier_count']}")
    print(f"  来源KG: {results['kg_count']}")
    print(f"  多跳发现: {results['multihop_count']}")
    print("")
    print("=" * 60)
    
    for i, item in enumerate(results['experiences'][:5], 1):
        exp = item['experience']
        source_icon = "🎯" if item['source'] == 'ier' else "🔗"
        hop_info = f"[{item.get('hop', 0)}跳]" if item.get('hop', 0) > 0 else ""
        
        print(f"{source_icon} #{i} {exp.name} {hop_info}")
        print(f"   相关度: {item['score']:.2f}")
        print(f"   描述: {exp.description[:60]}...")
        if 'path' in item:
            path_str = " → ".join(str(p) for p in item['path'])
            print(f"   路径: {path_str}")
        print("")
    
    adapter.close()
except Exception as e:
    print(f"检索失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG添加经验关系
ier_kg_link() {
    source="$1"
    target="$2"
    relation="$3"
    
    if [ -z "$source" ] || [ -z "$target" ] || [ -z "$relation" ]; then
        echo -e "${RED}错误: 参数不完整${NC}"
        echo "用法: ./codedev.sh ier-kg-link '源经验' '目标经验' '关系类型'"
        echo ""
        echo "关系类型: solves/causes/requires/complements/replaces/prevents"
        return 1
    fi
    
    echo -e "${BLUE}添加经验关系: $source --$relation--> $target${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    success = adapter.add_experience_relation(
        source_exp_name="$source",
        target_exp_name="$target",
        relation_type="$relation",
        strength=1.0
    )
    
    if success:
        print("✓ 关系添加成功")
    else:
        print("✗ 关系添加失败")
    
    adapter.close()
except Exception as e:
    print(f"添加关系失败: {e}")
EOF
}

# IER-KG溯源查询
ier_kg_trace() {
    exp_name="$1"
    
    if [ -z "$exp_name" ]; then
        echo -e "${RED}错误: 请提供经验名称${NC}"
        echo "用法: ./codedev.sh ier-kg-trace '经验名称'"
        return 1
    fi
    
    echo -e "${BLUE}查询经验溯源: $exp_name${NC}"
    echo ""
    
    python3 << EOF
import sys
import json
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    trace = adapter.trace_experience_provenance("$exp_name")
    
    if 'error' in trace:
        print(f"错误: {trace['error']}")
    else:
        print("=" * 60)
        print("经验信息:")
        exp = trace['experience']
        print(f"  ID: {exp['id']}")
        print(f"  名称: {exp['name']}")
        print(f"  类型: {exp['exp_type']}")
        print(f"  可靠度: {exp['reliability_score']:.2f}")
        print(f"  使用次数: {exp['usage_count']}")
        print("")
        
        if trace.get('related_experiences'):
            print("=" * 60)
            print(f"相关经验: {len(trace['related_experiences'])} 条")
            for rel in trace['related_experiences']:
                print(f"  - {rel['experience']['name']} ({rel['relation']['relation_type']})")
            print("")
        
        if trace.get('provenance'):
            prov = trace['provenance']
            print("=" * 60)
            print(f"溯源链: {prov['provenance_count']} 条")
            for chain in prov['chains'][:3]:  # 显示前3条
                print(f"  任务: {chain['task_id']}")
                print(f"  文件: {chain['file_path']}")
                print(f"  实体: {len(chain['code_entities'])} 个")
                print(f"  置信度: {chain['confidence']:.2f}")
                print(f"  时间: {chain['created_at']}")
                print("  ---")
    
    adapter.close()
except Exception as e:
    print(f"溯源查询失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG导出可视化数据
ier_kg_export() {
    output_file="${1:-ier_kg_graph.json}"
    
    echo -e "${BLUE}导出IER-KG图谱数据${NC}"
    echo "输出文件: $output_file"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    output = adapter.export_graph_for_visualization("$output_file")
    
    if output.startswith('{'):
        print(f"✓ 数据已导出到: $output_file")
        print("")
        print("可以使用以下工具可视化:")
        print("  - D3.js: 力导向图")
        print("  - Cytoscape: 网络分析")
        print("  - Neo4j Browser: 原生图谱浏览")
    else:
        print(output)
    
    adapter.close()
except Exception as e:
    print(f"导出失败: {e}")
EOF
}

# IER-KG去重检查
ier_kg_dedup() {
    echo -e "${BLUE}运行IER-KG经验去重检查${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    result = adapter.run_deduplication_check()
    
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print("=" * 60)
        print("去重检查完成!")
        print(f"  - 检查的经验对: {result['checked']}")
        print(f"  - 发现的重复: {result['duplicates_found']}")
        
        if result['similar_pairs']:
            print("\n相似度最高的经验对:")
            for pair in sorted(result['similar_pairs'], 
                             key=lambda x: x['similarity'], reverse=True)[:5]:
                print(f"  • {pair['exp1']}")
                print(f"    ~ {pair['exp2']}: {pair['similarity']:.2f}")
    
    adapter.close()
except Exception as e:
    print(f"去重检查失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG使用统计
ier_kg_usage() {
    echo -e "${BLUE}IER-KG使用频率统计${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    import json
    adapter = create_ier_kg_adapter(use_kg=True)
    
    report = adapter.get_usage_statistics()
    
    if "error" in report:
        print(f"错误: {report['error']}")
    else:
        print("=" * 60)
        print("📊 使用频率统计报告")
        print("=" * 60)
        print(f"\n总经验数: {report['total_experiences']}")
        print(f"总访问次数: {report['total_accesses']}")
        print(f"平均活跃度: {report['avg_activity_score']:.2f}")
        print(f"过期经验数: {report['expired_count']}")
        
        print("\n频率分布:")
        for cls, count in report['frequency_distribution'].items():
            bar = '█' * count
            print(f"  {cls:10s}: {count:3d} {bar}")
        
        if report['top_experiences']:
            print("\n🔥 Top 5 活跃经验:")
            for i, exp in enumerate(report['top_experiences'], 1):
                print(f"  {i}. {exp['name'][:30]:30s} "
                      f"(访问{exp['accesses']:2d}次, 评分{exp['score']:.1f})")
    
    adapter.close()
except Exception as e:
    print(f"统计失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG标记低频经验
ier_kg_mark_low() {
    echo -e "${BLUE}标记低频经验${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("正在标记低频经验...")
    result = adapter.mark_low_frequency_experiences()
    
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print("=" * 60)
        print("✅ 标记完成!")
        print(f"  - 标记为低频/归档: {result['marked_count']} 条经验")
        print("\n频率分布:")
        for cls, count in result['frequency_distribution'].items():
            print(f"  {cls:10s}: {count:3d}")
    
    adapter.close()
except Exception as e:
    print(f"标记失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG代码实体重要性评分
ier_kg_entity_score() {
    echo -e "${BLUE}IER-KG代码实体重要性评分${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("正在分析代码实体重要性...")
    report = adapter.analyze_code_entity_importance()
    
    if "error" in report:
        print(f"错误: {report['error']}")
    else:
        print("=" * 60)
        print("📊 代码实体重要性分析报告")
        print("=" * 60)
        print(f"\n总实体数: {report['total_entities']}")
        
        print("\n重要性分布:")
        for level, count in report.get('importance_distribution', {}).items():
            bar = '█' * count
            emoji = "🔴" if level == "critical" else "🟠" if level == "high" else "🟡" if level == "medium" else "⚪"
            print(f"  {emoji} {level:10s}: {count:4d} {bar}")
        
        if report.get('top_entities'):
            print("\n🏆 Top 10 关键实体:")
            for i, entity in enumerate(report['top_entities'], 1):
                emoji = "🔴" if entity['level'] == "critical" else "🟠" if entity['level'] == "high" else "🟡"
                print(f"  {i:2d}. {emoji} {entity['name'][:25]:25s} "
                      f"[{entity['type']:8s}] "
                      f"评分:{entity['score']:5.1f} "
                      f"被引用:{entity['refs']:3d}")
    
    adapter.close()
except Exception as e:
    print(f"分析失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG构建向量索引
ier_kg_build_index() {
    echo -e "${BLUE}构建经验向量索引${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("正在构建向量索引...")
    result = adapter.build_vector_index()
    
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print("=" * 60)
        print("✅ 向量索引构建完成!")
        print(f"  - 索引经验数: {result['indexed_count']}")
        print(f"  - 向量维度: {result['vector_dim']}")
        print("\n现在可以使用向量检索了!")
    
    adapter.close()
except Exception as e:
    print(f"构建失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG向量检索
ier_kg_vector_search() {
    local query="${1:-装饰器}"
    echo -e "${BLUE}向量语义检索: '${query}'${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    results = adapter.search_with_vector("$query", top_k=5)
    
    print("=" * 60)
    print(f"🔍 向量检索结果: '${query}'")
    print("=" * 60)
    
    if not results:
        print("\n暂无结果。请先运行: ./codedev.sh ier-kg-build-index")
    else:
        print()
        for i, r in enumerate(results, 1):
            bar = '█' * int(r['similarity'] * 20)
            print(f"{i}. {r['exp_id'][:30]:30s} "
                  f"相似度: {r['similarity']:.3f} {bar}")
    
    adapter.close()
except Exception as e:
    print(f"检索失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG混合检索
ier_kg_hybrid() {
    local query="${1:-装饰器缓存}"
    echo -e "${BLUE}混合检索 (图谱+向量): '${query}'${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("正在执行混合检索...")
    results = adapter.hybrid_retrieve("$query", top_k=5)
    
    print("=" * 60)
    print(f"🔍 混合检索结果: '${query}'")
    print("=" * 60)
    print(f"图谱结果: {results['graph_count']} | "
          f"向量结果: {results['vector_count']} | "
          f"融合后: {results['merged_count']}")
    print()
    
    for i, r in enumerate(results['results'], 1):
        emoji = "🟢" if r['level'] == 'high' else "🟡" if r['level'] == 'medium' else "⚪"
        hop_info = f"[{r['hop']}跳]" if r['hop'] > 0 else "[直接]"
        print(f"{i}. {emoji} {r['exp_name'][:25]:25s} "
              f"置信度:{r['confidence']:.3f} {hop_info}")
    
    adapter.close()
except Exception as e:
    print(f"检索失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG生成经验摘要
ier_kg_summary() {
    local exp_id="${1:-}"
    if [ -z "$exp_id" ]; then
        echo -e "${RED}错误: 请提供经验ID${NC}"
        echo "用法: ./codedev.sh ier-kg-summary <经验ID>"
        return 1
    fi
    
    echo -e "${BLUE}生成经验摘要: ${exp_id}${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    summary = adapter.generate_experience_summary("$exp_id", "markdown")
    print(summary)
    
    adapter.close()
except Exception as e:
    print(f"生成摘要失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG批量生成摘要
ier_kg_summary_all() {
    echo -e "${BLUE}批量生成经验摘要${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("正在生成摘要报告...")
    report = adapter.batch_generate_summaries()
    
    if "error" in report:
        print(f"错误: {report['error']}")
    else:
        print("=" * 60)
        print("📋 经验摘要统计")
        print("=" * 60)
        print(f"总经验数: {report['total_experiences']}")
        print(f"平均完整度: {report['avg_completeness']:.0%}")
        print("\n完整度分布:")
        for level, count in report['completeness_distribution'].items():
            bar = '█' * count
            print(f"  {level}: {count:3d} {bar}")
        
        if report.get('top_complete'):
            print("\n🏆 完整度最高的经验:")
            for exp in report['top_complete']:
                print(f"  • {exp['name'][:30]:30s} {exp['completeness']:.0%}")
    
    adapter.close()
except Exception as e:
    print(f"生成失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# IER-KG解释排序
ier_kg_explain_rank() {
    local query="${1:-如何使用装饰器}"
    echo -e "${BLUE}解释检索排序: '${query}'${NC}"
    echo ""
    
    python3 << EOF
import sys
sys.path.insert(0, '$CODEDEV_DIR')
try:
    from ier_kg_adapter import create_ier_kg_adapter
    adapter = create_ier_kg_adapter(use_kg=True)
    
    explanations = adapter.explain_retrieval_ranking("$query")
    
    print("=" * 60)
    print(f"📊 排序解释: '${query}'")
    print("=" * 60)
    print()
    
    for i, exp in enumerate(explanations[:3], 1):
        print(exp)
        print()
    
    adapter.close()
except Exception as e:
    print(f"解释失败: {e}")
    import traceback
    traceback.print_exc()
EOF
}

# 显示帮助
help() {
    echo -e "${BLUE}CodeDev Agent - 基于ChatDev角色的代码开发Agent${NC}"
    echo ""
    echo "用法: ./codedev.sh [命令] [参数]"
    echo ""
    echo "基础命令:"
    echo "  start              启动服务"
    echo "  stop               停止服务"
    echo "  restart            重启服务"
    echo "  status             查看状态"
    echo "  logs               查看日志"
    echo "  dev '描述' [语言]   提交开发请求"
    echo "  result [ID]        查看结果"
    echo ""
    echo "IER经验系统命令:"
    echo "  ier-stats          查看IER统计"
    echo "  ier-list [类型]    列出经验 (类型: shortcut/pattern/anti_pattern/tool/lesson/optimization)"
    echo "  ier-maintain       运行经验维护（淘汰过时经验）"
    echo ""
    echo "IER-KG知识图谱命令 (增强版):"
    echo "  ier-kg-stats       查看IER-KG完整统计"
    echo "  ier-kg-search '查询' 多跳检索测试"
    echo "  ier-kg-link 源 目标 关系  添加经验关系"
    echo "  ier-kg-trace '名称'   查询经验溯源"
    echo "  ier-kg-export [文件] 导出图谱数据用于可视化"
    echo "  ier-kg-dedup       运行经验去重检查"
    echo "  ier-kg-usage       查看使用频率统计"
    echo "  ier-kg-mark-low    标记低频经验"
    echo "  ier-kg-entity-score 代码实体重要性评分"
    echo ""
    echo "长期优化功能:"
    echo "  ier-kg-build-index       构建向量索引"
    echo "  ier-kg-vector-search '查询'  向量语义检索"
    echo "  ier-kg-hybrid '查询'         混合检索(图谱+向量)"
    echo "  ier-kg-summary <ID>        生成经验摘要"
    echo "  ier-kg-summary-all         批量生成摘要统计"
    echo "  ier-kg-explain-rank '查询'   解释排序原因"
    echo ""
    echo "示例:"
    echo "  ./codedev.sh start"
    echo "  ./codedev.sh dev '创建一个HTTP请求重试装饰器' python"
    echo "  ./codedev.sh result CODEDEV_20260315_120000"
    echo "  ./codedev.sh ier-stats"
    echo "  ./codedev.sh ier-kg-stats"
    echo "  ./codedev.sh ier-kg-build-index"
    echo "  ./codedev.sh ier-kg-hybrid '装饰器缓存'"
    echo "  ./codedev.sh ier-kg-summary-all"
}

# 主入口
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    dev)
        dev "$2" "$3"
        ;;
    result)
        result "$2"
        ;;
    ier-stats)
        ier_stats
        ;;
    ier-list)
        ier_list "$2"
        ;;
    ier-maintain)
        ier_maintain
        ;;
    ier-kg-stats)
        ier_kg_stats
        ;;
    ier-kg-search)
        ier_kg_search "$2"
        ;;
    ier-kg-link)
        ier_kg_link "$2" "$3" "$4"
        ;;
    ier-kg-trace)
        ier_kg_trace "$2"
        ;;
    ier-kg-export)
        ier_kg_export "$2"
        ;;
    ier-kg-dedup)
        ier_kg_dedup
        ;;
    ier-kg-usage)
        ier_kg_usage
        ;;
    ier-kg-mark-low)
        ier_kg_mark_low
        ;;
    ier-kg-entity-score)
        ier_kg_entity_score
        ;;
    ier-kg-build-index)
        ier_kg_build_index
        ;;
    ier-kg-vector-search)
        ier_kg_vector_search "$2"
        ;;
    ier-kg-hybrid)
        ier_kg_hybrid "$2"
        ;;
    ier-kg-summary)
        ier_kg_summary "$2"
        ;;
    ier-kg-summary-all)
        ier_kg_summary_all
        ;;
    ier-kg-explain-rank)
        ier_kg_explain_rank "$2"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        help
        exit 1
        ;;
esac
