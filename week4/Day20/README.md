🤖 AI Agent 每日学习提醒 | 晚上好，robindong！
---
🎯 今天是第 20 天 — LangGraph 可视化调试
你已经走完了整整 4 周的 Agent 学习旅程！今天是 Week 4 的最后一天，也是这一阶段的收官之战。
---
📋 今日任务清单
- [ ] 掌握 LangGraph 的可视化调试方法
- [ ] 使用   draw_mermaid_png()   或   draw_ascii()   输出图结构
- [ ] 接入 LangSmith 查看实时 trace 追踪
- [ ] 回顾 Day 16-19 的完整 Graph，确保逻辑清晰
- [ ] 为 Week 4 写一份简短总结笔记，记到 plan.md 笔记区
---
📚 关键代码示例
① 可视化图结构（无需外部服务）
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    next_step: str

graph = StateGraph(AgentState)
# ... 添加你的节点和边 ...

# 方式1：输出 ASCII 图（终端直接看）
print(graph.get_graph().draw_ascii())

# 方式2：输出 Mermaid 图（粘贴到 mermaid.live 查看）
print(graph.get_graph().draw_mermaid())

# 方式3：导出 PNG（需要 pygraphviz）
graph.get_graph().draw_mermaid_png(output_file_path="agent_graph.png")
② 接入 LangSmith 追踪（推荐！）
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your_langsmith_key"
os.environ["LANGCHAIN_PROJECT"] = "my-agent-week4"

# 之后正常运行你的 graph，自动上报 trace
result = compiled_graph.invoke({"messages": ["帮我查一下天气"]})
③ 手动打印每一步的状态（最简单的调试方式）
for step in compiled_graph.stream({"messages": ["查询文件列表"]}):
    print("---")
    for node_name, node_output in step.items():
        print(f"[节点: {node_name}]")
        print(node_output)
④ 检查 Graph 的边和节点
g = compiled_graph.get_graph()
print("节点:", list(g.nodes.keys()))
print("边:", [(e.source, e.target) for e in g.edges])
---
💡 今日实用小提示
 stream()   是调试的好朋友！相比   invoke()   直接拿结果，用   stream()   可以看到每个节点的中间输出，方便定位是哪一步出了问题。调试完再换回   invoke()   即可。
---
🎉 加油，robindong！
20 天了，你从零开始搭环境、写工具调用、构建 CLI Agent、再到用 LangGraph 实现有分支和循环的 Agent，这进步真的很扎实！今天把可视化和调试搞明白，Week 4 就完美收官啦 💪
下周 Week 5-6 是研究型 Agent，会接入真实搜索 API，期待你的成果！
