    好的，这是我基于命令行 Agent 场景设计的完整工具集 JSON Schema，包含注释说明：
# tools.py

tools = [
# ─────────────────────────────────────────
# 工具 1：执行 Shell 命令
# ─────────────────────────────────────────
{
    "type": "function",
    "function": {
        "name": "run_shell",
        "description": (
            "在本地终端执行一条 shell 命令并返回标准输出。"
            "适用于：列出目录、查看进程、运行脚本等操作。"
            "禁止执行危险命令（如 rm -rf、sudo、shutdown 等）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 shell 命令，例如：ls -la 或 python3 script.py"
                },
                "timeout": {
                    "type": "integer",
                    "description": "命令最长执行时间（秒），超时自动终止，默认 10 秒",
                    "default": 10
                }
            },
            "required": ["command"]
        }
    }
},
# ─────────────────────────────────────────
# 工具 2：读取文件内容
# ─────────────────────────────────────────
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "读取本地文件的文本内容并返回。"
            "适用于：查看代码、配置文件、日志等文本文件。"
            "不支持二进制文件（图片、PDF 等）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径，支持绝对路径或相对路径，例如：./config.py 或 /home/user/app.py"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码，默认 utf-8",
                    "default": "utf-8"
                },
                "max_lines": {
                    "type": "integer",
                    "description": "最多读取行数，避免超大文件撑爆上下文，默认 200 行",
                    "default": 200
                }
            },
            "required": ["path"]
        }
    }
},

# ─────────────────────────────────────────
# 工具 3：写入文件内容
# ─────────────────────────────────────────
{
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "将文本内容写入指定文件。文件不存在时自动创建，已存在时根据 mode 参数决定覆盖或追加。"
            "适用于：生成代码文件、写入配置、保存报告等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目标文件路径，例如：./output.txt 或 /tmp/result.py"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的文本内容"
                },
                "mode": {
                    "type": "string",
                    "enum": ["overwrite", "append"],
                    "description": "写入模式：overwrite 覆盖全文，append 追加到末尾，默认 overwrite",
                    "default": "overwrite"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码，默认 utf-8",
                    "default": "utf-8"
                }
            },
            "required": ["path", "content"]
        }
    }
} 
]
