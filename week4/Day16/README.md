🤖 AI Agent 每日学习提醒 | 第16天
---
🎯 今天是第 16 天 — LangGraph 核心概念
Week 4 正式开启！从今天起你将用图的思维重构 Agent，迈向更强大的框架。
---
📋 今日任务清单
- [ ] 理解 LangGraph 三大核心概念：节点（Node）/ 边（Edge）/ 状态（State）
- [ ] 安装 LangGraph：  pip install langgraph  
- [ ] 阅读官方文档 Quick Start：https://langchain-ai.github.io/langgraph/
- [ ] 手写一个最简单的 LangGraph 应用（2节点流程）
- [ ] 对比：用 LangGraph vs 之前手写 Agent 循环，有何不同？
---
📚 关键概念 + 代码示例
① 核心三元素
State  = 贯穿整个图的共享状态（dict/TypedDict）
Node   = 接收 State、处理、返回更新后的 State 的函数
Edge   = 决定"下一步去哪个节点"的路由规则
② 最简 LangGraph 示例
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. 定义状态
class AgentState(TypedDict):
    messages: list
    step: int

# 2. 定义节点函数
def think_node(state: AgentState) -> AgentState:
    print(f"[Think] Step {state['step']}")
    return {"messages": state["messages"], "step": state["step"] + 1}

def act_node(state: AgentState) -> AgentState:
    print(f"[Act] Executing action at step {state['step']}")
    return {"messages": state["messages"] + ["done"], "step": state["step"]}

# 3. 构建图
graph = StateGraph(AgentState)
graph.add_node("think", think_node)
graph.add_node("act", act_node)

# 4. 添加边（控制流）
graph.set_entry_point("think")
graph.add_edge("think", "act")
graph.add_edge("act", END)

# 5. 编译 & 运行
app = graph.compile()
result = app.invoke({"messages": [], "step": 0})
print(result)
③ 条件边（明天会深入，今天先看懂）
def should_continue(state: AgentState) -> str:
    if state["step"] < 3:
        return "think"  # 继续循环
    return "end"        # 结束

graph.add_conditional_edges("act", should_continue, {
    "think": "think",
    "end": END
})
---
💡 今日实用小提示
LangGraph 的精髓是：State 是真理之源。每个节点只做一件事——读取 State、计算、返回新的 State。节点之间不直接通信，全靠 State 传递信息。这个设计让 Agent 逻辑变得极易调试和追踪。
---
🔥 已经坚持 16 天了，从零环境到 Tool Calling 到命令行 Agent，一路都没放弃！LangGraph 是真正工业级 Agent 的入口，加油 robindong！今天学完，明天就能用图来重写你的命令行 Agent 💪
