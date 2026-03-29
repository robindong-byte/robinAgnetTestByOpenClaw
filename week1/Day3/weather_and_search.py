import os
import requests
import json

from openai import OpenAI
from dotenv import load_dotenv

env_path="../../.env"
load_dotenv(env_path)

client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
)


# 定义两个工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如北京、上海"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网上的信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]

# 模拟工具执行
def execute_tool(name, args):
    if name == "get_weather":
        return {"city": args["city"], "temp": "22°C", "condition": "晴"}
    elif name == "web_search":
        return {"results": [f"关于 '{args['query']}' 的搜索结果1", "结果2"]}

# 完整调用循环
def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )
        msg = response.choices[0].message
        
        # 没有工具调用 → 直接返回
        if not msg.tool_calls:
            return msg.content
        
        # 有工具调用 → 执行并追加结果
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

# 测试
print ("上海今天天气怎么样？")
print(run_agent("上海今天天气怎么样？"))
print ("LangGraph 是什么？")
print(run_agent("LangGraph 是什么？"))
