📅 Day 8 详细学习计划 — 实现文件读写工具
主题： 实现   read_file   和   write_file  ，加入路径安全检查
---
🎯 学习目标
- 实现安全可靠的文件读写工具
- 掌握路径安全检查（防止越权访问敏感目录）
- 理解文件操作中的常见边界情况处理
---
📖 理论部分（约 20 分钟）
文件操作的核心风险
| 风险 | 场景 | 防御手段 |
|------|------|---------|
| 路径穿越 |   ../../etc/passwd   | 转换为绝对路径后校验 |
| 敏感目录访问 |   ~/.ssh/id_rsa   | 路径黑名单 |
| 超大文件 | 读 1GB 日志撑爆内存 | 限制读取行数/字节数 |
| 二进制文件 | 读图片乱码 | 检测文件类型 |
| 编码错误 | GBK 文件用 UTF-8 读 | 指定编码 + 错误处理 |
 os.path   vs   pathlib   选哪个？
# 老写法 os.path（可读性差）
import os
abs_path = os.path.abspath(os.path.expanduser(path))

# 新写法 pathlib（推荐）
from pathlib import Path
abs_path = Path(path).expanduser().resolve()
Day 8 统一用   pathlib  ，更 Pythonic。
---
💻 实践部分（约 90 分钟）
任务 1：实现路径安全检查（公共函数）


# tools.py（续接 Day 7）

from pathlib import Path

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
Agent 允许操作的根目录（白名单模式，更严格）
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
已经被 resolve 处理了，但仍然拒绝含 .. 的路径（防御纵深）
        return False, f"路径中包含 '..' 穿越符，拒绝执行"
── 第四层：符号链接检查 ──────────────────────
防止通过软链接绕过路径检查
例如：/tmp/agent_workspace/evil_link -> /etc/shadow
    original = Path(path_str).expanduser()
    if original.is_symlink():
        real_target = original.resolve()
再次对真实目标路径做黑名单检查
        for sensitive in SENSITIVE_PATHS:
            try:
                real_target.relative_to(sensitive.resolve())
                return False, f"符号链接指向敏感路径，拒绝访问: {real_target}"
            except ValueError:
                pass
所有检查通过
    return True, ""

---
