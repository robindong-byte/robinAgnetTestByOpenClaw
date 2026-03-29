import os
from openai import OpenAI
from dotenv import load_dotenv

env_path="../.env"
load_dotenv(env_path)

client = OpenAI(
	api_key=os.getenv("DEEPSEEK_API_KEY"),
	base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
	model="deepseek-chat",
	messages=[
		{"role":"system","content":"你是一个AI Agent学习助手"},
		{"role":"user","content":"你好！我今天刚开始学AI Agent，给我一句鼓励吧！"}
	]
)

print(response.choices[0].message.content)
