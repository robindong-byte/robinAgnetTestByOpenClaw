🤖 AI Agent 每日学习提醒 | 晚上好，robindong！
---
🎯 今天是第 17 天 — LangGraph：用图重写命令行 Agent
你已经完成了 Tool Calling + 命令行助手的基础，现在进入更强大的 LangGraph 框架！
---
📋 今日任务清单
- [ ] 回顾昨天学的 LangGraph 核心概念（节点/边/状态）
- [ ] 把 Week 2 写的命令行 Agent 用 LangGraph 重新实现
- [ ] 用 StateGraph 管理对话状态
- [ ] 用 ToolNode 处理工具调用
- [ ] 对比新旧实现，感受图结构的优势
---
📚 核心代码示例：用 LangGraph 重写命令行 Agent
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from typing import TypedDict, Annotated
import operator
import subprocess

# 1. 定义状态结构
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

# 2. 定义工具
def run_shell(command: str) -> str:
    """安全执行 shell 命令（白名单限制）"""
    ALLOWED = ["ls", "pwd", "echo", "cat", "find", "grep"]
    cmd = command.strip().split()[0]
    if cmd not in ALLOWED:
        return f"❌ 拒绝执行：{cmd} 不在白名单中"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout or result.stderr

tools = [run_shell]

# 3. 创建 LLM + 绑定工具
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)

# 4. 定义节点函数
def call_model(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    last = state["messages"][-1]
    if last.tool_calls:
        return "tools"
    return END

# 5. 构建图
tool_node = ToolNode(tools)
graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")  # 工具执行后回到 agent
app = graph.compile()

# 6. 运行测试
result = app.invoke({
    "messages": [HumanMessage(content="列出当前目录下的文件")]
})
print(result["messages"][-1].content)
对比 Week 2 的手写循环，LangGraph 的好处一目了然：
- ✅ 状态管理更清晰（TypedDict 定义）
- ✅ 流程逻辑图形化（节点 + 边）
- ✅ 条件分支更直观（conditional_edges）
- ✅ 内置工具节点（ToolNode 省掉大量样板代码）
---
💡 今日小提示
 add_conditional_edges   是 LangGraph 的精髓——让 LLM 来决定下一步走哪条路。这就是 Agent 和普通 LLM 调用的核心区别：Agent 有自主决策能力，而不是固定流程。
---
💪 你已经走完了 17 天，快到第 3 周的终点了！LangGraph 是 Agent 开发的行业标准，掌握它你就掌握了构建复杂 Agent 系统的基础。坚持住，离"研究型 Agent"只差几步！加油 🔥
