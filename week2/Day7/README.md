📅 Day 7 详细学习计划 — 实现 run_shell 工具 + 安全边界
主题： 用   subprocess   实现真正能执行命令的工具，并加入安全控制
---
🎯 学习目标
- 理解   subprocess   模块的核心用法
- 实现一个生产可用的   run_shell   工具
- 掌握安全边界设计思路（黑名单、超时、沙箱）
---
📖 理论部分（约 20 分钟）
subprocess 三种调用方式对比
| 方式 | 特点 | 推荐度 |
|------|------|--------|
|   os.system()   | 最简单，无法捕获输出 | ❌ 不推荐 |
|   subprocess.run()   | 同步阻塞，可捕获输出 | ✅ 推荐 |
|   subprocess.Popen()   | 异步，流式输出 | 进阶用 |
安全边界三原则
1. 黑名单拦截 — 禁止危险命令关键词
2. 超时控制 — 防止命令挂死
3. 工作目录限制 — 防止越权访问
---

💻 实践部分（约 90 分钟）
任务 1：实现基础版 run_shell
# tools.py

import subprocess

def run_shell(command: str, timeout: int = 10) -> dict:
"""执行 shell 命令，返回标准输出"""
    try:
        result = subprocess.run(
            command,
            shell=True, # 允许管道、通配符等 shell 特性
            capture_output=True, # 同时捕获 stdout 和 stderr
            text=True, # 返回字符串而非 bytes
            timeout=timeout # 超时自动终止
        )
        return {
            "status": "success",
            "data": {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"命令执行超时（>{timeout}秒）"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
---
### 任务 2：加入安全黑名单
tools.py（续）

import shlex
危险命令黑名单
DANGEROUS_COMMANDS = [
    "rm -rf", "rm -r", "rmdir",
    "sudo", "su ",
    "shutdown", "reboot", "halt", "poweroff",
    "mkfs", "dd if=",
    "chmod 777", "chown",
    "> /dev/",
    "curl | bash", "wget | bash",  # 远程执行
    ":(){ :|:& };:",               # Fork 炸弹
    "python -c", "exec(",          # 任意代码执行
]
def is_dangerous(command: str) -> tuple[bool, str]:
"""检查命令是否包含危险操作，返回 (是否危险, 原因)"""
