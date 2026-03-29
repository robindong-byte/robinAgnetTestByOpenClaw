import json
import time
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError
from tools import tools, dispatch_tool
import os
import requests
from dotenv import load_dotenv

env_path="../../.env"
load_dotenv(env_path)

client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
)

SYSTEM_PROMPT = """你是一个运行在本地的命令行任务助手。
你可以使用工具完成用户的任务。

规则：
1. 遇到工具返回 error 时，分析原因后决定：修正参数重试 or 换一种方式 or 告知用户无法完成
2. 不要重复调用同一个工具超过 3 次
3.任务完成后简洁汇报结果
4. 所有文件操作只能在 /tmp/agent_workspace 目录下进行
"""

def call_llm_with_retry(messages: list, max_retries: int = 3) -> object:
    """
    调用 LLM，失败时指数退避重试。
    Args:
        messages: 消息历史列表
        max_retries: 最大重试次数
    Returns:
        API response 对象
    Raises:
        Exception: 超过重试次数后抛出
    """

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=30,
            )
            return response
        except RateLimitError:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"  ⚠️ 触发限流，{wait}s 后重试（{attempt+1}/{max_retries}）")
            time.sleep(wait)
	except APITimeoutError:
	    wait = 2 * attempt
	    print(f" ⚠️ API 超时，{wait}s 后重试（{attempt+1}/{max_retries}）")
    	    time.sleep(wait)

        except APIConnectionError as e:
	    raise Exception(f"网络连接失败，请检查网络: {e}")

	except Exception as e:
	    raise Exception(f"API 调用失败: {e}")

    raise Exception(f"API 调用失败，已重试 {max_retries} 次")


def run_agent(user_input: str, max_steps: int = 10) -> str:
    """完善版 Agent 主循环"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    # 记录每个工具的调用次数（防止 LLM 死循环）
    tool_call_counts = {}
    MAX_SAME_TOOL_CALLS = 3

    print(f"n{'='50}")
    print(f"📝 任务: {user_input}")
    print(f"{'='*50}")

    for step in range(max_steps):

    # ── 调用 LLM（带重试）────────────────────
    try:
        response = call_llm_with_retry(messages)
    except Exception as e:
        return f"❌ LLM 调用失败: {e}"

    message = response.choices[0].message

    # ── 无工具调用 → 返回最终答案 ────────────
    if not message.tool_calls:
        final = message.content or "（Agent 未返回内容）"
        print(f"n✅ 最终回答: {final}")
        return final

    # ── 有工具调用 → 执行工具 ─────────────────
    messages.append({
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in message.tool_calls
        ]
    })

    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name

    # 同一工具调用次数检查
    tool_call_counts[tool_name] = tool_call_counts.get(tool_name, 0) + 1
    if tool_call_counts[tool_name] > MAX_SAME_TOOL_CALLS:
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({
                "status": "error",
                "message": f"工具 {tool_name} 已调用 {MAX_SAME_TOOL_CALLS} 次，请换一种方式完成任务"
            }, ensure_ascii=False)
        })
        continue
    #解析参数
    try:
        tool_args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        tool_args = {}
        print(f"  ⚠️ 参数解析失败: {e}")
        print(f"n🔧 Step {step+1} | 工具: [{tool_name}] | 第 {tool_call_counts[tool_name]} 次")
        print(f" 参数: {json.dumps(tool_args, ensure_ascii=False)}")

    # 执行工具
    result = dispatch_tool(tool_name, tool_args)

    # 结果预览截断（终端显示用，不影响传给 LLM 的完整内容）
    result_preview = result[:300] + "..." if len(result) > 300 else result
    print(f" 结果: {result_preview}")

    # 工具结果写入消息历史（传完整内容给 LLM）
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    })

    # 超出最大步数限制
    return f"⚠️ 任务未完成：已执行 {max_steps} 步，超出限制"
'''
这就是   run_agent   的最后一段，函数到这里完整结束。
有一个细节值得注意：
# 终端预览用截断版（可读性）
result_preview = result[:300] + "..." if len(result) > 300 else result
print(f" 结果: {result_preview}")

# 但传给 LLM 的是完整内容！
messages.append({..

., "content": result})   # ← 不截断
预览截断 只是为了终端看着整洁，传给 LLM 的永远是完整结果，否则 LLM 会因为信息残缺做出错误判断。
接下来跑   test_all.py   收官 🚀
'''
