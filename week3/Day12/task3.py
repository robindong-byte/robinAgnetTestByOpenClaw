mport chromadb

client_db = chromadb.Client()
collection = client_db.create_collection("day12_test")

docs = [
    "Python 是一种高级编程语言",
    "机器学习是 AI 的子领域",
    "深度学习依赖神经网络",
    "今天的股票涨了很多",
]

# 批量获取 embedding 并存储
embeddings = [get_embedding(d) for d in docs]
collection.add(
    documents=docs,
    embeddings=embeddings,
    ids=[f"doc_{i}" for i in range(len(docs))]
)

# 语义检索
query = "神经网络相关的技术"
q_embedding = get_embedding(query)
results = collection.query(query_embeddings=[q_embedding], n_results=2)
print("检索结果：", results['documents'])
