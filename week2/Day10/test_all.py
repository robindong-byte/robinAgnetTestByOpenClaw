import json
import os
from pathlib import Path
from tools import (
	run_shell, read_file, write_file,
	list_directory, path_exists, dispatch_tool
)

TEST_DIR = "/tmp/agent_workspace"
Path(TEST_DIR).mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────
# 测试 run_shell
# ─────────────────────────────────────────────────

def test_run_shell():
    print("n── 测试 run_shell ──")

    # ✅ 正常命令
    r = run_shell("echo hello")
    print ("{0}".format(r["message"]))
    assert r["status"] == "success"
    assert "hello" in r["data"]["stdout"]
    print("✅ 正常命令")

    # ✅ 超时控制
    r = run_shell("sleep 10", timeout=1)
    assert r["status"] == "error"
    assert "超时" in r["message"]
    print("✅ 超时控制")

    # ✅ 危险命令拦截
    r = run_shell("sudo rm -rf /")
    assert r["status"] == "error"
    assert "危险" in r["message"]
    print("✅ 危险命令拦截")

    # ✅ 注入攻击拦截
    r = run_shell("ls | bash")
    assert r["status"] == "error"
    print("✅ 注入攻击拦截")

    # ✅ 非零退出码（命令本身不存在，但工具正常运行）
    r = run_shell("not_a_real_command_xyz_123")
    assert r["status"] == "success"
    assert r["data"]["returncode"] != 0
    print("✅ 非零退出码处理")
    # ✅ 管道命令正常使用
    r = run_shell("echo 'hello world' | tr 'a-z' 'A-Z'")
    assert r["status"] == "success"
    assert "HELLO WORLD" in r["data"]["stdout"]
    print("✅ 管道命令正常使用")


# ─────────────────────────────────────────────────
# 测试 read_file
# ─────────────────────────────────────────────────
def test_read_file():
    print("n── 测试 read_file ──")
    test_path = f"{TEST_DIR}/test_read.txt"

    # 先写入测试文件
    Path(test_path).write_text("line1nline2nline3n", encoding="utf-8")

    # ✅ 正常读取
    r = read_file(test_path)
    assert r["status"] == "success"
    assert "line1" in r["data"]["content"]
    assert r["data"]["total_lines"] == 3
    print("✅ 正常读取")

    # ✅ max_lines 限制
    r = read_file(test_path, max_lines=2)
    assert r["status"] == "success"
    assert r["data"]["returned_lines"] == 2
    assert r["data"]["truncated"] is True
    print("✅ max_lines 截断")

    # ✅ 文件不存在
    r = read_file(f"{TEST_DIR}/ghost_file.txt")
    assert r["status"] == "error"
    assert "不存在" in r["message"]
    print("✅ 文件不存在错误处理")

    # ✅ 敏感路径拦截
    r = read_file("~/.ssh/id_rsa")
    assert r["status"] == "error"
    print("✅ 敏感路径拦截")

    # ✅ 白名单外路径拦截
    r = read_file("/etc/hostname")
    assert r["status"] == "error"
    assert "允许范围" in r["message"]
    print("✅ 白名单外路径拦截")


# ─────────────────────────────────────────────────
# 测试 write_file
# ─────────────────────────────────────────────────
def test_write_file():
    print("n── 测试 write_file ──")
    test_path = f"{TEST_DIR}/test_write.txt"

    # ✅ 覆盖写入
    r = write_file(test_path, "第一行n第二行n")
    assert r["status"] == "success"
    content = Path(test_path).read_text(encoding="utf-8")
    assert "第一行" in content
    print("✅ 覆盖写入")

    # ✅ 追加写入
    r = write_file(test_path, "第三行n", mode="append")
    assert r["status"] == "success"
    content = Path(test_path).read_text(encoding="utf-8")
    assert "第三行" in content
    assert "第一行" in content  # 原内容还在
    print("✅ 追加写入")

    # ✅ 自动创建子目录
    nested_path = f"{TEST_DIR}/subdir/nested.txt"
    r = write_file(nested_path, "nested content")
    assert r["status"] == "success"
    assert Path(nested_path).exists()
    print("✅ 自动创建子目录")

    # ✅ 无效 mode 参数
    r = write_file(test_path, "内容", mode="invalid_mode")
    assert r["status"] == "error"
    assert "mode" in r["message"]
    print("✅ 无效 mode 参数处理")

    # ✅ 拦截写入敏感路径
    r = write_file("/etc/hosts", "hack")
    assert r["status"] == "error"
    print("✅ 敏感路径写入拦截")


# ─────────────────────────────────────────────────
# 测试 list_directory
# ─────────────────────────────────────────────────
def test_list_directory():
    print("n── 测试 list_directory ──")

    # ✅ 正常列目录
    r = list_directory(TEST_DIR)
    assert r["status"] == "success"
    assert isinstance(r["data"]["items"], list)
    assert r["data"]["total"] >= 0
    print("✅ 正常列目录")

    # ✅ 返回结构包含 name / type / size
    items = r["data"]["items"]
    if items:
        assert "name" in items[0]
        assert "type" in items[0]
        assert items[0]["type"] in ("file", "dir")
    print("✅ 返回结构正确")

    # ✅ 目录不存在
    r = list_directory(f"{TEST_DIR}/nonexistent_dir")
    assert r["status"] == "error"
    assert "不存在" in r["message"]
    print("✅ 不存在目录错误处理")

    # ✅ 传入文件路径（不是目录）
    r = list_directory(f"{TEST_DIR}/test_write.txt")
    assert r["status"] == "error"
    assert "目录" in r["message"]
    print("✅ 非目录路径错误处理")


# ─────────────────────────────────────────────────
# 测试 path_exists
# ─────────────────────────────────────────────────
def test_path_exists():
    print("n── 测试 path_exists ──")

    # ✅ 目录存在
    r = path_exists(TEST_DIR)
    assert r["status"] == "success"
    assert r["data"]["exists"] is True
    assert r["data"]["type"] == "dir"
    print("✅ 目录存在检测")

    # ✅ 文件存在
    existing_file = f"{TEST_DIR}/test_write.txt"
    r = path_exists(existing_file)
    assert r["status"] == "success"
    assert r["data"]["exists"] is True
    assert r["data"]["type"] == "file"
    print("✅ 文件存在检测")

    # ✅ 路径不存在
    r = path_exists(f"{TEST_DIR}/totally_fake_xyz.txt")
    assert r["status"] == "success"
    assert r["data"]["exists"] is False
    assert r["data"]["type"] is None
    print("✅ 不存在路径检测")


# ─────────────────────────────────────────────────
# 测试 dispatch_tool
# ─────────────────────────────────────────────────
def test_dispatch_tool():
    print("n── 测试 dispatch_tool ──")

    # ✅ 正常调用
    r = json.loads(dispatch_tool("run_shell", {"command": "echo dispatch_ok"}))
    assert r["status"] == "success"
    assert "dispatch_ok" in r["data"]["stdout"]
    print("✅ 正常调用")

    # ✅ 未知工具
    r = json.loads(dispatch_tool("fake_tool_xyz", {}))
    assert r["status"] == "error"
    assert "未知工具" in r["message"]
    print("✅ 未知工具处理")

    # ✅ 参数错误（缺少必填参数）
    r = json.loads(dispatch_tool("run_shell", {"wrong_key": "xxx"}))
    assert r["status"] == "error"
    assert "参数错误" in r["message"]
    print("✅ 参数错误处理")

    #✅ 返回值是合法 JSON 字符串
    result_str = dispatch_tool("path_exists", {"path": TEST_DIR})
    parsed = json.loads(result_str)
    assert isinstance(parsed, dict)
    print("✅ 返回值是合法 JSON")
 
#─────────────────────────────────────────────────
#主入口
#─────────────────────────────────────────────────
if __name__ == "__main__":
    test_run_shell()
    test_read_file()
    test_write_file()
    test_list_directory()
    test_path_exists()
    test_dispatch_tool()
    #print("n" + "="50)
    print("🎉 所有测试通过！Week 2 收官！")
    #print("="50)

"""
到这里   test_all.py   完整结束，可以直接运行了 💪
"""
