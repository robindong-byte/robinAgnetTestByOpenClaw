Day 12：文本 Embedding 原理 + 实践
所属阶段： Week 3 - 带记忆的 QA Agent
前置： Day 11 需完成 ChromaDB 安装 + 基本 CRUD
---
🎯 今日目标
理解什么是 Embedding，为什么它是 RAG 的核心，并动手跑通文本向量化的完整流程。
---
📚 理论部分（1小时）
1. 什么是 Embedding？
- 把文本映射到高维向量空间（如 768维、1536维）
- 语义相近的句子，向量距离也近（余弦相似度）
- 例："苹果是水果" 和 "Apple is a fruit" 的向量会非常接近
2. 为什么需要 Embedding？
- LLM 上下文有限，不能把所有文档塞进去
- Embedding + 向量数据库 = 语义检索，只取最相关片段
- RAG = Retrieve（向量检索）+ Augment（补充上下文）+ Generate（LLM 回答）
3. 常用 Embedding 模型
| 模型 | 维度 | 特点 |
|------|------|------|
|   text-embedding-3-small   | 1536 | OpenAI，性价比高 |
|   text-embedding-ada-002   | 1536 | OpenAI，经典款 |
|   BAAI/bge-m3   | 1024 | 开源，中英双语 |
|   sentence-transformers   | 384+ | 本地，免费 |
---
