
📅 Day 9 详细学习计划 — 组合成完整 CLI Agent
主题： 把 Day 7+8 的工具整合进 Agent，接入 LLM，实现完整多轮对话循环
---
🎯 学习目标
- 理解 Agent 的核心运行循环（ReAct 模式）
- 把工具注册进 LLM 的 Tool Calling 机制
- 实现一个能在终端运行、真正干活的 CLI Agent
---
📖 理论部分（约 20 分钟）
Agent 运行循环（ReAct 模式）
用户输入
↓
LLM 思考（Reasoning）
↓
决定调用工具（Acting）
↓
执行工具，拿到结果
↓
LLM 再次思考（结果够了吗？）
↓
够了 → 生成最终回答
不够 → 继续调用工具（循环）
消息结构回顾
messages = [
{"role": "system", "content": "你是一个命令行助手..."},
{"role": "user", "content": "列出当前目录的文件"},
{"role": "assistant", "content": None, "tool_calls": [...]}, # LLM 决定调工具
{"role": "tool", "content": "文件列表...", "tool_call_id": "xxx"}, # 工具结果
{"role": "assistant", "content": "当前目录有以下文件：..."}, # 最终回答
]
---
