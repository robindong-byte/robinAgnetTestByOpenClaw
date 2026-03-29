📅 Day 6 详细学习计划 — 设计工具集
主题： 为命令行 Agent 设计工具集（shell/read/write）
---
🎯 学习目标
理解"工具"在 Agent 中的角色，设计出结构清晰、可扩展的工具接口，为后续几天的实现打好基础。
---
📖 理论部分（约 30 分钟）
1. 为什么 Agent 需要工具？
- LLM 本身只能"说话"，无法执行真实操作
- 工具 = LLM 的"手"，让它能操作文件系统、执行命令、调用 API
- Tool Calling 就是 LLM 决定"调用哪个工具、传什么参数"
2. 命令行 Agent 需要哪些能力？
| 工具名 | 作用 |
|--------|------|
|   run_shell   | 执行 shell 命令 |
|   read_file   | 读取文件内容 |
|   write_file   | 写入/创建文件 |
---
💻 实践部分（约 60-90 分钟）
任务 1：定义工具 Schema
按 OpenAI Tool Calling 格式，为三个工具写 JSON Schema：
tools = [
{
    "type": "function",
    "function": {
        "name": "run_shell",
        "description": "执行一条 shell 命令，返回输出结果",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 shell 命令，如 ls -la"
                }
            },
            "required": ["command"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取指定路径的文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件的绝对或相对路径"
                }
            },
            "required": ["path"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "将内容写入指定路径的文件（不存在则创建）",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目标文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的文本内容"
                }
            },
            "required": ["path", "content"]
        }
    }
}
]
