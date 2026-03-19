#!/usr/bin/env python3
"""
网络诊断工具 - 快速版
"""

import socket
import ssl
import sys

def check_dns(hostname):
    """检查DNS解析"""
    try:
        ip = socket.getaddrinfo(hostname, None)[0][4][0]
        return True, ip
    except Exception as e:
        return False, str(e)

def check_tcp(hostname, port=443, timeout=5):
    """检查TCP连接"""
    try:
        sock = socket.create_connection((hostname, port), timeout=timeout)
        sock.close()
        return True, "TCP连接成功"
    except socket.timeout:
        return False, "连接超时"
    except Exception as e:
        return False, str(e)

print("=" * 60)
print("🔧 网络快速诊断")
print("=" * 60)

targets = [
    ("api.search.brave.com", "Brave API"),
    ("www.google.com", "Google"),
    ("api.github.com", "GitHub API"),
    ("www.baidu.com", "百度"),
]

print("\n📋 诊断结果:\n")
for host, name in targets:
    # DNS
    dns_ok, dns_result = check_dns(host)
    dns_status = "✅" if dns_ok else "❌"
    
    # TCP
    if dns_ok:
        tcp_ok, tcp_result = check_tcp(host)
        tcp_status = "✅" if tcp_ok else "❌"
    else:
        tcp_ok, tcp_result = False, "DNS失败，跳过"
        tcp_status = "⏸️"
    
    print(f"{name:15} │ DNS: {dns_status} │ TCP: {tcp_status} │ {dns_result if dns_ok else dns_result[:30]}")

print("\n" + "=" * 60)
print("📊 分析:")
print("=" * 60)

print("""
可能的问题及解决方案:

1️⃣ DNS解析失败
   症状: api.search.brave.com 无法解析
   解决: 修改 /etc/resolv.conf 使用公共DNS
         echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf

2️⃣ TCP连接超时  
   症状: DNS成功但TCP超时
   原因: 防火墙/网络策略阻止出境443端口
   解决: 
   • 联系管理员开放端口
   • 使用代理服务器
   • 换网络环境

3️⃣ 仅特定网站超时
   症状: 百度能连，Brave不能
   原因: 特定IP/域名被墙或限制
   解决: 使用代理/VPN

4️⃣ 全部超时
   症状: 所有外部连接都失败
   原因: 无外部网络或代理配置错误
   解决: 检查网络连接或配置代理
""")

print("=" * 60)
print("建议下一步:")
print("=" * 60)
print("  A. 如果是云服务器，检查安全组规则")
print("  B. 如果有代理，配置HTTP_PROXY环境变量")
print("  C. 如果都不行，继续使用kimi_search ✅")
print("=" * 60)
