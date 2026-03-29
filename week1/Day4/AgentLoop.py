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

# ===== 工具定义 =====
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
        "name": "calculator",
        "description": "执行数学计算，支持加减乘除",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式，如 '12 * 5 + 3'"}
            },
            "required": ["expression"]
        }
    }
}
]

def convertcity(city_str:str) -> str:
    try:
        baidumap_key = os.getenv("BAIDU_MAP_AK")
        mapurl=f"https://api.map.baidu.com/geocoding/v3/?ak={baidumap_key}&address={city_str}&output=json"
        response=requests.get(mapurl)
        response.raise_for_status()
        local_data = response.json()
        lng=local_data["result"]["location"]["lng"]
        lat=local_data["result"]["location"]["lat"]
        return f"{lng},{lat}"
    except Exception as e:
        print (str(e))
        return ""

def get_weather(city:dict) -> str:
    API_URL="https://api.caiyunapp.com/v2.6"
    try:
        city_str = city["city"]
        lng_lat=convertcity(city_str)
        if lng_lat == "":
            return ""
        caiyun_api_key = os.getenv("CAIYUN_API_KEY")
        all_url=f"{API_URL}/{caiyun_api_key}/{lng_lat}/daily?dailysteps=1"
        response=requests.get(all_url)
        response.raise_for_status()
        weather_data = response.json()
        return str(weather_data["result"]["daily"])
    except requests.exceptions.RequestException as e:
        print (str(e))
        return {'error':str(e)}

def calculator(expression: dict) -> str:
    try:
        expression_str = expression["expression"]
        result = eval(expression_str)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错: {e}"

# ===== tool_map 分发器（比 if/elif 更优雅）=====
tool_map = {
    "get_weather": get_weather,
    "calculator": calculator,
}

# ===== 完整 Agent Loop =====
def run_agent(user_input: str):
    messages = [{"role": "user", "content": user_input}]

    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        print(f"finish_reason: {finish_reason}")

        # ✅ LLM 直接回答，结束循环
        if finish_reason == "stop":
            print(f"🤖 最终回答: {msg.content}")
            return msg.content

        # 🔧 需要调用工具
        elif finish_reason == "tool_calls":
            messages.append(msg)  # 把 assistant 消息加入历史

            # 遍历所有 tool_calls（可能同时调用多个！）
            for tc in msg.tool_calls:
                func_name = tc.function.name
                args = json.loads(tc.function.arguments)
                print(f"🔧 调用工具: {func_name}({args})")

                # 执行工具，出错也不崩溃
                try:
                    result = tool_map[func_name](args)
                except Exception as e:
                    result = f"工具执行失败: {e}"

                print(f"📤 工具结果: {result}")

                # 把结果加入 messages，tool_call_id 必须对应！
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result)
                })
            # 继续循环，让 LLM 处理工具结果

        else:
            print(f"未知 finish_reason: {finish_reason}")
            break

# ===== 测试 =====
run_agent("北京今天天气怎么样？")
run_agent("你好！")                              # 不调用工具
run_agent("上海气温是多少？把气温数字乘以3")     # 连续两次工具调用
