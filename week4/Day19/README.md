🤖 AI Agent 每日学习提醒 | 晚上好，robindong！
---
🎯 今天是第 19 天 — Week 4：LangGraph 加入循环 + 失败重试
你已经完成了 LangGraph 的核心概念和条件分支，今天进入关键一步——让 Agent 在失败时能自动重试！
---
📋 今日任务清单
- [ ] 在 LangGraph 图中加入循环边（cycle）
- [ ] 实现失败检测节点（判断工具调用是否出错）
- [ ] 加入最大重试次数限制，防止死循环
- [ ] 测试：主动让某工具报错，观察 Agent 重试行为
- [ ] 在 State 中追踪 retry_count 字段
---
📚 关键代码示例
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 1. 定义包含 retry_count 的 State
class AgentState(TypedDict):
    messages: list
    retry_count: int
    last_error: str | None

# 2. 失败检测节点
def check_result(state: AgentState):
    last_msg = state["messages"][-1]
    if "Error" in str(last_msg):
        return {
            "last_error": str(last_msg),
            "retry_count": state["retry_count"] + 1
        }
    return {"last_error": None}

# 3. 条件路由 — 核心！
def should_retry(state: AgentState) -> str:
    if state["last_error"] and state["retry_count"] < 3:
        return "retry"      # → 回到执行节点
    elif state["last_error"]:
        return "fail"       # → 超过重试次数，终止
    else:
        return "success"    # → 正常结束

# 4. 构建带循环的图
graph = StateGraph(AgentState)
graph.add_node("execute", execute_tool)
graph.add_node("check", check_result)
graph.add_node("report_fail", lambda s: print(f"❌ 最终失败: {s['last_error']}"))

graph.set_entry_point("execute")
graph.add_edge("execute", "check")
graph.add_conditional_edges(
    "check",
    should_retry,
    {
        "retry": "execute",   # ← 这里形成循环！
        "fail": "report_fail",
        "success": END
    }
)
graph.add_edge("report_fail", END)

app = graph.compile()

# 5. 运行测试
result = app.invoke({
    "messages": [],
    "retry_count": 0,
    "last_error": None
})
---
💡 实用小提示
退避策略（Exponential Backoff）：重试时加入延迟，避免瞬间打爆 API：
import time

def execute_with_backoff(state):
    if state["retry_count"] > 0:
        wait = 2 ** state["retry_count"]  # 1s, 2s, 4s...
        print(f"⏳ 第 {state['retry_count']} 次重试，等待 {wait}s")
        time.sleep(wait)
    # ... 执行工具逻辑
这是生产级 Agent 必备的健壮性设计！
---
💪 加油！
Day 19 了，明天 Day 20 就是 Week 4 的收官——可视化调试，届时你的 LangGraph Agent 将真正"看得见"自己的执行路径。坚持住，Week 5 的研究型 Agent 已在眼前！🚀
进度：▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░ 47.5% (Day 19/40)
