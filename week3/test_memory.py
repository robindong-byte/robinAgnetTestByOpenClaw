from memory import (
    add_memory,
    query_memory,
    list_all_memories,
    update_memory,
    delete_memory,
    clear_all_memories
)

# ─────────────────────────────────────────────────
# 测试 add_memory
# ─────────────────────────────────────────────────
def test_add_memory():
    print("n── 测试 add_memory ──")

    # ✅ 正常添加
    r = add_memory("用户叫 Robin，是一名后端工程师")
    assert r["status"] == "success"
    assert "id" in r
    assert len(r["id"]) > 0
    print(f"✅ 添加成功，ID: {r['id']}")

    # ✅ 带 metadata 添加
    r = add_memory(
    "用户喜欢喝黑咖啡，不加糖",
    metadata={"source": "chat", "topic": "preference"}
    )
    assert r["status"] == "success"
    print("✅ 带 metadata 添加成功")

    # ✅ 中文内容
    r = add_memory("用户正在学习 AI Agent 开发，目前在 Week 3")
    assert r["status"] == "success"
    print("✅ 中文内容添加成功")

    # ✅ 重复内容（应该生成不同 ID，因为时间戳不同）
    r1 = add_memory("测试重复内容")
    r2 = add_memory("测试重复内容")
    assert r1["id"] != r2["id"]
    print("✅ 重复内容生成不同 ID")

    return r["id"] # 返回最后一个 ID 供后续测试用


# ─────────────────────────────────────────────────
# 测试 query_memory
# ─────────────────────────────────────────────────
def test_query_memory():
    print("n── 测试 query_memory ──")

    # ✅ 语义搜索：找用户名字
    r = query_memory("这个用户叫什么名字")
    assert r["status"] == "success"
    assert len(r["results"]) > 0
    print(f"✅ 语义搜索成功")
    print(f"   最相关: {r['results'][0]['text']}")
    print(f"   相似度距离: {r['results'][0]['distance']}")

    # ✅ 语义搜索：找喜好
    r = query_memory("用户喜欢喝什么")
    assert r["status"] == "success"
    assert len(r["results"]) > 0
    # 最相关的结果应该包含"咖啡"
    top_text = r["results"][0]["text"]
    print(f"✅ 喜好搜索成功，最相关: {top_text}")

    # ✅ 控制返回数量
    r = query_memory("用户信息", n_results=2)
    assert r["status"] == "success"
    assert len(r["results"]) <= 2
    print(f"✅ n_results=2 控制成功，返回 {len(r['results'])} 条")

    # ✅ 验证返回结构
    result = r["results"][0]
    assert "id" in result
    assert "text" in result
    assert "metadata" in result
    assert "distance" in result
    print("✅ 返回结构验证通过")

    # ✅ distance 越小越相似（应该在 0~2 之间）
    assert 0 <= result["distance"] <= 2
    print(f"✅ distance 值合理: {result['distance']}")


# ─────────────────────────────────────────────────
# 测试 list_all_memories
# ─────────────────────────────────────────────────
def test_list_all_memories():
    print("n── 测试 list_all_memories ──")

    r = list_all_memories()
    assert r["status"] == "success"
    assert "total" in r
    assert "results" in r
    assert isinstance(r["results"], list)
    assert r["total"] == len(r["results"])
    print(f"✅ 全量查询成功，共 {r['total']} 条记忆")

    # ✅ 验证每条记录的结构
    if r["results"]:
        item = r["results"][0]
        assert "id" in item
        assert "text" in item
        assert "metadata" in item
        assert "created_at" in item["metadata"]
    print("✅ 记录结构验证通过")


# ─────────────────────────────────────────────────
# 测试 update_memory
# ─────────────────────────────────────────────────
def test_update_memory():
    print("n── 测试 update_memory ──")

    # 先添加一条记忆
    r = add_memory("用户住在北京")
    doc_id = r["id"]
    print(f" 添加原始记忆，ID: {doc_id}")

    # ✅ 更新内容
    r = update_memory(doc_id, "用户住在上海，刚从北京搬过来")
    assert r["status"] == "success"
    assert r["id"] == doc_id
    print("✅ 更新成功")

    # ✅ 验证更新后语义搜索能找到新内容
    r = query_memory("用户住在哪里")
    assert r["status"] == "success"
    texts = [item["text"] for item in r["results"]]
    assert any("上海" in t for t in texts)
    print("✅ 更新后语义搜索验证通过")

    return doc_id


# ─────────────────────────────────────────────────
# 测试 delete_memory
# ─────────────────────────────────────────────────
def test_delete_memory(doc_id: str):
    print("n── 测试 delete_memory ──")

    # 记录删除前的数量
    before = list_all_memories()["total"]

    # ✅ 删除指定记忆
    r = delete_memory(doc_id)
    assert r["status"] == "success"
    assert r["id"] == doc_id
    print(f"✅ 删除成功，ID: {doc_id}")

    # ✅ 验证数量减少了 1
    after = list_all_memories()["total"]
    assert after == before - 1
    print(f"✅ 数量从 {before} 减少到 {after}")


# ─────────────────────────────────────────────────
# 测试空库边界情况
# ─────────────────────────────────────────────────
def test_empty_collection():
    print("n── 测试空库边界情况 ──")

    clear_all_memories()

    # ✅ 空库查询不报错
    r = query_memory("随便查点什么")
    assert r["status"] == "success"
    assert r["results"] == []
    assert "空" in r.get("message", "")
    print("✅ 空库查询正常返回，不报错")

    # ✅ 空库全量列出
    r = list_all_memories()
    assert r["status"] == "success"
    assert r["total"] == 0
    print("✅ 空库全量列出正常")


# ─────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 开始 ChromaDB CRUD 全流程测试")

    clear_all_memories()
    print("🗑️ 已清空记忆库，开始测试...n")

    test_add_memory()
    test_query_memory()
    test_list_all_memories()
    doc_id = test_update_memory()
    test_delete_memory(doc_id)
    test_empty_collection()

    print("🎉 Day 11 所有测试通过！ChromaDB CRUD 完整验证！")
