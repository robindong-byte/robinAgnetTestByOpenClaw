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

def get_embedding(text):
    response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
    )
    return response.data[0].embedding

# 测试
vec = get_embedding("今天天气很好")
print(f"维度：{len(vec)}") # 1536
print(f"前5个值：{vec[:5]}")
