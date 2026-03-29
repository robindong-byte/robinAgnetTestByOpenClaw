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

def convertcity(city:str) -> str:
    try:
        baidumap_key = os.getenv("BAIDU_MAP_AK")
        mapurl=f"https://api.map.baidu.com/geocoding/v3/?ak={baidumap_key}&address={city}&output=json"
        response=requests.get(mapurl)
        response.raise_for_status()
        local_data = response.json()
        lng=local_data["result"]["location"]["lng"]
        lat=local_data["result"]["location"]["lat"]
        return f"{lng},{lat}"
    except Exception as e:
        print (str(e))
        return ""

def get_weather(city:str) -> str:
    API_URL="https://api.caiyunapp.com/v2.6"
    try:
        lng_lat=convertcity(city)
        if lng_lat == "":
            return ""
        caiyun_api_key = os.getenv("CAIYUN_API_KEY")
        all_url=f"{API_URL}/{caiyun_api_key}/{lng_lat}/daily?dailysteps=1"
        response=requests.get(all_url)
        response.raise_for_status()
        weather_data = response.json()
        return str(weather_data["result"]["daily"])
    except requests.exceptions.RequestException as e:
        return {'error':str(e)}

def get_weather_2(city:str) -> str:
    try:
        url = f"https://wttr.in/{city}?format=3&lang=zh"
        resp = requests.get(url, timeout=5)
        return resp.test
    except Exception as e:
        return f"获取天气失败: {e}"
    

tools = [
    {
        "type":"function",
        "function":{
            "name":"get_weather",
            "description":"获取指定城市实时天气。city参数从用户输入中提取城市名称,如'北京'、'上海'，不要带有市字",
            "paramters":{
                "type":"object",
                "properties": {
                    "city":{"type":"string","description":"城市名, 如 北京、上海"}
                },
                "required":["city"]
            }
        }
    }
]


def get_answer_by_LLM(content:str):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":content}],
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = get_weather(args["city"])
        if result == "":
            print ("get_weather  error")
            exit (1)
        messages = [
            {"role":"user","content":content},
            msg,
            {"role":"tool","tool_call_id":tool_call.id, "content":result}
        ]
        final = client.chat.completions.create(model="deepseek-chat", messages=messages)
        print (final.choices[0].message.content)





def main():
    import sys
    # 提示用户输入
    print("请输入你想说的话：")
    lines = []
    while True:
        line = input()
        if line == '':
            break  # 检测到空行，结束循环
        lines.append(line)
    
    # 将所有输入拼接成一个字符串
    user_input = '\n'.join(lines)
    
    get_answer_by_LLM(user_input)

if __name__ == "__main__":
    main()
