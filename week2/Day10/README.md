📅 Day 10 详细学习计划 — 错误处理 + 测试 + Week 2 收官
主题： 让 Agent 更健壮，完善错误处理和重试机制，整理代码，Week 2 完美收官
---
🎯 学习目标
- 掌握 Agent 场景下的错误处理策略
- 实现 LLM 感知工具失败后的重试逻辑
- 编写完整测试套件覆盖边界情况
- 整理项目结构，输出可复用的代码库
---
📖 理论部分（约 20 分钟）
Agent 错误的三种来源
| 来源 | 例子 | 处理策略 |
|------|------|---------|
| 工具执行失败 | 文件不存在、命令超时 | 返回结构化错误，让 LLM 决定重试还是放弃 |
| LLM 参数错误 | 传了不存在的参数名 |   dispatch_tool   捕获 TypeError，返回提示 |
| 网络/API 错误 | OpenAI 超时、限流 | 指数退避重试，超过次数报错 |
好的错误信息 vs 坏的错误信息
# ❌ 坏：LLM 看不懂，不知道怎么修正
{"status": "error", "message": "FileNotFoundError"}

# ✅ 好：LLM 能理解并采取行动
{"status": "error", "message": "文件不存在: /tmp/agent_workspace/hello.py，请先用 write_file 创建它"}
