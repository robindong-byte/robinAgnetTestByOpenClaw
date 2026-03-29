import os
import requests
import json

from openai import OpenAI
from dotenv import load_dotenv

env_path="../.env"
load_dotenv(env_path)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)


# 1. 定义计算器工具
tools = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行基本数学运算，支持加减乘除",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '123 * 456' 或 '(10 + 5) / 3'"
                }
            },
            "required": ["expression"]
        }
    }
}]

# 2. 实现工具函数
def calculator(expression: str) -> str:
    try:
        result = eval(expression)  # 生产环境用 safer 方案
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错: {e}"

# 3. 完整调用循环
def run(user_input):
    print (f"{user_input}")
    messages = [{"role": "user", "content": user_input}]
    # 支持多轮工具调用（有些复杂任务会调用多次工具）
    while True:
        response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto"
        )

        choice = response.choices[0]
        msg = choice.message
        finish_reason = choice.finish_reason
        
        print(f"finish_reason: {finish_reason}")
        
        # ✅ 情况1：LLM 直接回答，不调用工具
        if finish_reason == "stop":
            print(f"最终回答: {msg.content}")
            break
        
        # ✅ 情况2：LLM 要调用工具
        elif finish_reason == "tool_calls":
            messages.append(msg)  # 把 LLM 的"我要调用工具"追加进去
            
            # 可能同时调用多个工具，逐一执行
            for tc in msg.tool_calls:
                func_name = tc.function.name
                args = json.loads(tc.function.arguments)
                
                print(f"调用工具: {func_name}({args})")
                
                # 执行工具
                if func_name == "calculator":
                    result = calculator(args["expression"])
                else:
                    result = f"未知工具: {func_name}"
                
                print(f"工具结果: {result}")
                
                # 把工具执行结果追加进消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
		"content": result
                })
            
            # 继续循环，让 LLM 根据工具结果生成最终回答
        
        # ✅ 情况3：其他异常情况
        else:
            print(f"未知 finish_reason: {finish_reason}")
            break

# 测试
#run("帮我算一下 1234 × 5678 等于多少？")  # 预期：触发 tool_calls
#run("你好！今天天气真好")                  # 预期：直接 stop，不调用工具
run("先算 100+200，再算结果乘以3")         # 预期：可能触发两次 tool_calls
