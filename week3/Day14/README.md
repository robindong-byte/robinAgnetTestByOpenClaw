Day 14：接入 LLM 实现 QA
所属阶段： Week 3 - 带记忆的 QA Agent
前置： Day 13 已完成文档导入 + 检索流程
---
🎯 今日目标
把 Day 13 的向量检索和 LLM 组合起来，实现真正的 RAG 问答系统：用户提问 → 检索相关文档片段 → 喂给 LLM → 得到基于文档的回答。
---
📚 理论部分（45分钟）
RAG 完整流程
用户问题
↓
[Embedding 化]
↓
[向量检索] → 找到 Top-K 相关片段
↓
[构建 Prompt] → "根据以下资料回答问题：{context}nn问题：{question}"
↓
[LLM 生成] → 得到答案
↓
返回给用户
为什么不直接把文档全塞给 LLM？
- 上下文窗口有限（GPT-4 128k tokens ≈ 10万字）
- 成本高，速度慢
- 相关性差，LLM 容易被无关内容干扰
- RAG 精准取用，只给最相关的 3-5 个片段
关键设计决策
- Top-K 取几个片段？通常 3-5，太少信息不足，太多引入噪音
- Prompt 如何组织？明确告知 LLM"只根据提供的资料回答"
- 检索不到时怎么办？让 LLM 说"根据现有资料无法回答"，而非瞎编
---
💻 实践部分（2小时）
环境准备
pip install openai chromadb tiktoken
Task 1：构建基础 RAG 类
from openai import OpenAI
import chromadb

client = OpenAI()

class SimpleRAG:
def __init__(self, collection_name="rag_docs"):
self.db = chromadb.Client()
self.collection = self.db.get_or_create_collection(collection_name)
        self.embed_model = "text-embedding-3-small"
        self.chat_model = "gpt-4o-mini"
    
    def get_embedding(self, text):
        response = client.embeddings.create(
            model=self.embed_model,
            input=text
        )
        return response.data[0].embedding
    
    def add_documents(self, docs: list[str], ids: list[str] = None):
        """批量导入文档"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(docs))]
        embeddings = [self.get_embedding(d) for d in docs]
        self.collection.add(
            documents=docs,
            embeddings=embeddings,
            ids=ids
        )
        print(f"✅ 已导入 {len(docs)} 条文档")
    
    def retrieve(self, query: str, top_k: int = 3):
        """检索最相关的文档片段"""q_embedding = self.get_embedding(query)
        results = self.collection.query(
            query_embeddings=[q_embedding],
            n_results=top_k
        )
        return results['documents'][0]  # 返回文档列表
    
    def ask(self, question: str, top_k: int = 3):
        """RAG 问答"""
1. 检索相关片段
        context_docs = self.retrieve(question, top_k)
        context = "nn".join([f"[片段{i+1}] {doc}" 
                                for i, doc in enumerate(context_docs)])
        
2. 构建 Prompt
        system_prompt = """你是一个专业的问答助手。
请严格根据提供的参考资料回答用户问题。
如果参考资料中没有相关信息，请明确说明"根据现有资料无法回答该问题"，不要编造内容。"""
        
        user_prompt = f"""参考资料：
{context}
问题：{question}"""
        
3. 调用 LLM
response = client.chat.completions.create(
model="gpt-4o-mini",
messages=[
{"role": "system", "content": system_prompt},
{"role": "user", "content": user_prompt}
]
)

return {
"question": question,
"answer": response.choices[0].message.content,
"context": [doc for doc, _ in filtered]
}

# 绑定到类
SimpleRAG.ask_with_source = ask_with_source

# 测试
result = rag.ask_with_source("ChromaDB 有什么特点？")
print(f"回答：{result['answer']}")
---
Task 4：从文件导入文档（实用版）
def load_from_file(filepath: str, chunk_size: int = 200) -> list[str]:
"""
读取文本文件并按 chunk_size 字符数切分
"""
with open(filepath, 'r', encoding='utf-8') as f:
text = f.read()

chunks = []
for i in range(0, len(text), chunk_size):
chunk = text[i:i+chunk_size].strip()
if chunk:
chunks.append(chunk)
return chunks

# 创建测试文件
with open("test_doc.txt", "w", encoding="utf-8") as f:
f.write("""机器学习是人工智能的一个子领域，专注于让计算机从数据中学习，
而不是通过明确编程来完成特定任务。机器学习算法通过分析训练数据，
识别模式，并基于这些模式做出预测或决策。

深度学习是机器学习的一个分支，使用多层神经网络来处理复杂的模式识别任务。
卷积神经网络（CNN）擅长图像识别，循环神经网络（RNN）擅长序列数据处理，
Transformer 架构则彻底改变了自然语言处理领域。

大语言模型（LLM）是基于 Transformer 架构的超大规模神经网络，
通过在海量文本数据上预训练，具备了强大的语言理解和生成能力。
GPT 系列、Claude、Gemini 都是典型的大语言模型。""")

# 导入文件并问答
rag2 = SimpleRAG("file_rag")
chunks = load_from_file("test_doc.txt", chunk_size=150)
rag2.add_documents(chunks)

result = rag2.ask("什么是深度学习？")
print(f"回答：{result['answer']}")
---
✅ 完成标准
- [ ] Task 1：  SimpleRAG   类能正常实例化，  add_documents   /   retrieve   /   ask   三个方法均可运行
- [ ] Task 2：5个问题中，有文档支撑的回答准确；"北京天气"类问题得到拒答响应
- [ ] Task 3：回答末尾出现"依据：片段X"的引用格式，相似度过低的片段被过滤掉
- [ ] Task 4：成功从文件读取、切分并导入，问答结果基于文件内容
---
💡 Tips
拒答测试最重要： Task 2 最后一问是验证系统可信度的关键。如果 LLM 编造了文档里没有的内容，需要在 System Prompt 里加更强的约束，例如："如果你不确定，请直接说不知道，绝对不要编造。"
距离阈值调参： Task 3 中   distance < 1.0   是经验值，可根据实际效果调整。ChromaDB
