"""RPFM Server 批量任务：基线反查（Phase 0 前置）。

流程：
  1. SetGameSelected warhammer_3（rebuild=false，先看自动检测到的路径）
  2. LoadAllCAPackFiles（合并 CA 官方包）
  3. GlobalSearch 指定 pattern
  4. 打印匹配的文件路径列表

用法：python rpfm_baseline.py [pattern]
"""
import json
import socket
import subprocess
import sys
import time

import websocket
from rpfm_client import call as _call  # noqa: F401  (同目录导入)

SERVER_EXE = r"C:\Users\admin\AppData\Local\Temp\opencode\rpfm\rpfm_server.exe"
SERVER_DIR = r"C:\Users\admin\AppData\Local\Temp\opencode\rpfm"
SERVER_HOST, SERVER_PORT = "127.0.0.1", 45127


def ensure_server(timeout=120):
    """server 不在就启动一个（DETACHED），等端口就绪后返回 Popen 或 None。"""
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.close()
        return None
    except OSError:
        pass
    finally:
        s.close()
    proc = subprocess.Popen(
        [SERVER_EXE],
        cwd=SERVER_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS,
    )
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.close()
            return proc
        except OSError:
            time.sleep(1)
        finally:
            s.close()
    raise RuntimeError("rpfm_server 启动超时")


def send_many(commands, ws_url="ws://127.0.0.1:45127/ws", timeout=900):
    ensure_server()
    ws = websocket.create_connection(ws_url, timeout=timeout)
    hello = json.loads(ws.recv())
    session = hello["data"]["SessionConnected"]
    out = []
    for i, cmd in enumerate(commands, start=1):
        ws.send(json.dumps({"id": i, "data": cmd}))
        resp = json.loads(ws.recv())
        assert resp["id"] == i, resp
        out.append(resp["data"])
    nxt = len(commands) + 1
    ws.send(json.dumps({"id": nxt, "data": "ClientDisconnecting"}))
    ws.close()
    return session, out


def main(argv):
    pattern = argv[1] if len(argv) > 1 else "wh3_main_kho_veh_skullcannon_0"
    session, (cache,) = send_many(
        [
            "GenerateDependenciesCache",
        ]
    )
    print(f"session: {session}")
    print("== GenerateDependenciesCache ==")
    s = json.dumps(cache, ensure_ascii=False)
    print(s[:3000])
    info = cache.get("DependenciesInfo", {})
    for k, v in info.items():
        n = len(v) if isinstance(v, list) else v
        print(f"  {k}: {n if isinstance(v, list) else v}")
        if isinstance(v, list) and v:
            print(f"    e.g. {json.dumps(v[:5], ensure_ascii=False)[:500]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
