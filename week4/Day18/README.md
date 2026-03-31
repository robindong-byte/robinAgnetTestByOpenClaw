🤖 AI Agent 每日学习提醒 | 晚上好，robindong！
---
🎯 今天是第 18 天 — Week 4：LangGraph 条件分支
从开始学习至今已经 18 天了！目前正处于 Week 4 LangGraph 框架阶段，今天的主题是：给 Agent 加入条件分支，让它能根据情况走不同路径。
---
📋 今日任务清单
- [ ] 理解 LangGraph 的   conditional_edges   概念
- [ ] 实现一个带条件路由的 Agent（例如：工具调用 vs 直接回答）
- [ ] 写一个   should_continue   判断函数
- [ ] 测试不同输入走不同分支的行为
---
📚 今日核心代码示例
带条件分支的 LangGraph Agent：
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

# 定义状态
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 判断是否需要继续（调用工具 or 结束）
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    # 如果最后一条消息有 tool_calls，说明需要继续
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"  # 走工具执行分支
    return "end"           # 走结束分支

# 构建图
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tools)

# 设置入口
workflow.set_entry_point("agent")

# ⭐ 条件边：根据 should_continue 的返回值决定走哪条路
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",  # 有工具调用 → 执行工具
        "end": END             # 没有 → 结束
    }
)

# 工具执行完 → 回到 agent 继续思考
workflow.add_edge("action", "agent")

app = workflow.compile()
执行并追踪分支走向：
# 运行并观察每一步走了哪个分支
for event in app.stream({"messages": [HumanMessage(content="帮我查一下今天天气")]}):
    for key, value in event.items():
        print(f"📍 当前节点: {key}")
        print(f"   消息: {value['messages'][-1].content[:100]}")
---
💡 今日实用小提示
 add_conditional_edges   的第三个参数是一个 映射字典：函数返回值 → 下一个节点名。返回   END   表示流程结束。把判断逻辑抽成独立函数（如   should_continue  ），比写 lambda 更易读、更易测试。
---
🔥 18 天了，你已经从零搭环境、掌握 Tool Calling、写出 CLI Agent，现在正在征服 LangGraph！每一天的积累都在构建你的 Agent 开发体系。坚持下去，Week 5 的研究型 Agent 在向你招手 💪
加油，robindong！今晚搞定条件分支，明天就能玩循环和失败重试了！🚀
