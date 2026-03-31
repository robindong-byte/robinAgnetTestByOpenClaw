🤖 AI Agent 每日学习提醒 | robindong 晚上好！
---
🎯 今天是第 15 天 — Week 3 收官：多轮对话 + 上下文管理
本周你已经完成了 ChromaDB、Embedding、文档检索、QA 接入，今天是 Week 3 的压轴场：把它们串成一个能记住对话历史的完整 QA Agent！
---
📋 今日任务清单
- [ ] 实现多轮对话历史管理（conversation buffer）
- [ ] 把向量检索 + 对话历史一起喂给 LLM
- [ ] 处理上下文窗口超长时的截断/摘要策略
- [ ] 测试：问同一个问题，第二次回答是否能引用上一轮内容
- [ ] 整理 Week 3 代码，写一段 README
---
📚 关键代码示例：带记忆的 QA Agent
from openai import OpenAI
import chromadb

client = OpenAI()
chroma = chromadb.Client()
collection = chroma.get_collection("my_docs")

# 对话历史（内存中，可持久化到文件/DB）
conversation_history = []

def retrieve(query: str, n=3) -> list[str]:
    results = collection.query(query_texts=[query], n_results=n)
    return results["documents"][0]

def chat(user_input: str) -> str:
    # 1. 向量检索相关文档
    docs = retrieve(user_input)
    context = "
".join(docs)

    # 2. 构建带上下文的 system prompt
    system_prompt = f"""你是一个知识库 QA 助手。
根据以下检索到的文档片段回答问题：

{context}

如果文档中没有相关信息，请如实告知。"""

    # 3. 组装消息（system + 历史 + 新问题）
    messages = [{"role": "system", "content": system_prompt}]
    messages += conversation_history[-10:]  # 保留最近 5 轮
    messages.append({"role": "user", "content": user_input})

    # 4. 调用 LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    answer = response.choices[0].message.content

    # 5. 更新历史
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": answer})

    return answer

# 测试多轮
print(chat("什么是 Embedding？"))
print(chat("它和我上面问的有什么关系？"))  # 能引用上下文！
---
💡 今日实用小提示：上下文长度管理策略
当对话轮数增多，历史 tokens 会爆炸，常用两种方案：
| 策略 | 做法 | 适合场景 |
|------|------|----------|
| 滑动窗口 |   history[-N:]   只保留最近 N 轮 | 短对话、节省 tokens |
| 滚动摘要 | 把旧对话让 LLM 摘要成一段话替换 | 长对话、保留关键信息 |
推荐先用滑动窗口（简单！），需要时再升级成滚动摘要。
---
🏆 Week 3 完成后你将拥有：
一个能读文档、检索信息、记住对话的本地知识库问答 Agent，这已经是很多公司 MVP 级别的 RAG 产品了！
加油 robindong，Week 3 最后一关，冲！💪
今晚搞定它，明天就是 LangGraph 的新世界 🚀
