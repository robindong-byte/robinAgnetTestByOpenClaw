import os
import requests
import json

from openai import OpenAI
from dotenv import load_dotenv

env_path="../../.env"
load_dotenv(env_path)

#client = OpenAI(
#        api_key=os.getenv("DEEPSEEK_API_KEY"),
#        base_url="https://api.deepseek.com/v1"
#)


class ToolCallingAgent:
    def __init__(self, model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY")):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.tools = []          # OpenAI tools schema 列表
        self.tool_funcs = {}     # name -> callable 映射
        self.messages = []       # 对话历史

    def register_tool(self, name: str, description: str, parameters: dict, func):
        """注册一个工具"""
        self.tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        })
        self.tool_funcs[name] = func

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools or None,
            )
            msg = response.choices[0].message
            self.messages.append(msg)

            # 没有工具调用 → 直接返回
            if not msg.tool_calls:
                return msg.content

            # 执行每个工具调用
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                print(f"  🔧 调用工具: {fn_name}({fn_args})")
                result = self.tool_funcs[fn_name](fn_args)
                print(f"  📦 工具结果: {result}")

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

# ——— 使用示例 ———
def calculator(expression: dict) -> float:
    expression_str = expression["expression"] 
    return eval(expression_str)  # 生产环境请用 safer 实现

agent = ToolCallingAgent()
agent.register_tool(
    name="calculator",
    description="计算数学表达式",
    parameters={
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
    func=calculator,
)

answer = agent.run("(12345 * 678) + 9999 等于多少？")
print("最终答案:", answer)
