#!/usr/bin/env python3
"""
创新能力自动化系统集成

自动拦截关键操作，添加创新换路能力
"""

import sys
import os
from pathlib import Path

# 将创新引擎加入系统路径
WORKSPACE = Path("/root/.openclaw/workspace")
CLAW = WORKSPACE / ".claw-status"
sys.path.insert(0, str(CLAW))

def install_auto_innovation():
    """安装自动创新能力到系统"""
    
    # 1. 导入创新引擎
    try:
        from innovation_engine import InnovationEngine, GitPusher
        print("✅ 创新引擎加载成功")
    except ImportError as e:
        print(f"❌ 创新引擎加载失败: {e}")
        return False
    
    # 2. 设置环境变量，标记系统已启用自动创新
    os.environ["WDAI_AUTO_INNOVATION"] = "enabled"
    
    # 3. 添加到shell配置文件
    bashrc = Path.home() / ".bashrc"
    init_line = f"\n# WDAI 自动创新系统\nexport PYTHONPATH=\"{CLAW}:$PYTHONPATH\"\nexport WDAI_AUTO_INNOVATION=enabled\n"
    
    if bashrc.exists():
        content = bashrc.read_text()
        if "WDAI_AUTO_INNOVATION" not in content:
            with open(bashrc, 'a') as f:
                f.write(init_line)
            print("✅ 已添加到 ~/.bashrc")
    
    # 4. 创建快捷命令
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    git_push_script = bin_dir / "git-push-auto"
    git_push_script.write_text(f"""#!/bin/bash
cd {WORKSPACE}
python3 {CLAW}/innovation_engine.py
""")
    git_push_script.chmod(0o755)
    print(f"✅ 创建快捷命令: git-push-auto")
    
    # 5. 生成当前报告
    engine = InnovationEngine()
    report = engine.generate_report()
    
    report_file = CLAW / "innovation_report.md"
    report_file.write_text(report)
    print(f"✅ 报告已生成: {report_file}")
    
    return True


def check_status():
    """检查自动创新系统状态"""
    enabled = os.environ.get("WDAI_AUTO_INNOVATION") == "enabled"
    
    print("=" * 60)
    print("创新能力自动化系统状态")
    print("=" * 60)
    print(f"\n状态: {'✅ 已启用' if enabled else '❌ 未启用'}")
    
    if enabled:
        from innovation_engine import InnovationEngine
        engine = InnovationEngine()
        print(f"方法记录: {len(engine.method_stats)} 个")
        print(f"创新模式: {len(engine.patterns)} 个")
    
    return enabled


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WDAI 创新能力自动化系统")
    parser.add_argument("--install", action="store_true", help="安装到系统")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    
    args = parser.parse_args()
    
    if args.install:
        if install_auto_innovation():
            print("\n✅ 创新能力自动化系统安装完成")
            print("重启终端后生效")
        else:
            print("\n❌ 安装失败")
    
    elif args.status:
        check_status()
    
    elif args.demo:
        from innovation_engine import main
        main()
    
    else:
        parser.print_help()
