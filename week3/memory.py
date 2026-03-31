import chromadb
from chromadb.config import Settings
from datetime import datetime
from pathlib import Path

# 持久化存储路径
DB_PATH = str(Path.home() / "week3" / "chroma_db")

def get_client():
    """获取 ChromaDB 客户端（持久化模式）"""
    return chromadb.PersistentClient(path=DB_PATH)

def get_or_create_collection(name: str = "agent_memory"):
    """获取或创建 Collection"""
    client = get_client()
    collection = client.get_or_create_collection(
        name=name,
        metadata={"description": "Agent 长期记忆存储"}
    )
    return collection


# ── CREATE：添加记忆 ──
def add_memory(text: str, metadata: dict = None) -> dict:
    """
    添加一条记忆。

    Args:
    text: 要记住的文本内容
    metadata: 附加信息，如来源、时间等

    Returns:
    {"status": "success", "id": "..."}
    """
    collection = get_or_create_collection()

    # 生成唯一 ID（时间戳 + 内容哈希）
    import hashlib
    doc_id = hashlib.md5(
        f"{datetime.now().isoformat()}:{text}".encode()
    ).hexdigest()[:12]

    # 默认 metadata
    default_meta = {
        "created_at": datetime.now().isoformat(),
        "source": "user_input"
    }
    if metadata:
        default_meta.update(metadata)

    collection.add(
        ids=[doc_id],
        documents=[text],
        metadatas=[default_meta]
    )

    return {"status": "success", "id": doc_id, "text": text}


# ── READ：查询相似记忆 ────────────────────────────

def query_memory(query_text: str, n_results: int = 3) -> dict:
    """
    语义搜索：找出和 query_text 最相似的记忆。

    Args:
    query_text: 查询文本
    n_results: 返回结果数量

    Returns:
    {"status": "success", "results": [...]}
    """
    collection = get_or_create_collection()
    if collection.count() == 0:
        return {"status": "success", "results": [], "message": "记忆库为空"}
    actual_n = min(n_results, collection.count())
    results = collection.query(
        query_texts=[query_text],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"]
    )
    memories = []
    for i in range(len(results["ids"][0])):
        memories.append({
            "id":       results["ids"][0][i],
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": round(results["distances"][0][i], 4),
        })
    return {"status": "success", "results": memories}
 
#── READ：获取全部记忆 ────────────────────────────
def list_all_memories() -> dict:
    """列出所有记忆（全量返回，不做语义搜索）"""
    collection = get_or_create_collection()

    if collection.count() == 0:
        return {"status": "success", "total": 0, "results": []}

    all_data = collection.get(
        include=["documents", "metadatas"]
    )

    memories = []
    for i in range(len(all_data["ids"])):
        memories.append({
            "id": all_data["ids"][i],
            "text": all_data["documents"][i],
            "metadata": all_data["metadatas"][i],
        })

    return {"status": "success", "total": len(memories), "results": memories}


# ── UPDATE：更新记忆 ──────────────────────────────

def update_memory(doc_id: str, new_text: str, metadata: dict = None) -> dict:
    """更新指定 ID 的记忆内容"""
    collection = get_or_create_collection()

    update_meta = {
        "updated_at": datetime.now().isoformat()
    }
    if metadata:
        update_meta.update(metadata)

    collection.update(
        ids=[doc_id],
        documents=[new_text],
        metadatas=[update_meta]
    )

    return {"status": "success", "id": doc_id, "new_text": new_text}


# ── DELETE：删除记忆 ──────────────────────────────
def delete_memory(doc_id: str) -> dict:
    """删除指定 ID 的记忆"""
    collection = get_or_create_collection()

    collection.delete(ids=[doc_id])

    return {"status": "success", "id": doc_id, "message": "记忆已删除"}


def clear_all_memories() -> dict:
    """清空所有记忆（危险操作，谨慎使用）"""
    client = get_client()
    client.delete_collection("agent_memory")

    return {"status": "success", "message": "所有记忆已清空"}

