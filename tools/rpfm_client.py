"""RPFM Server 最小 WebSocket 客户端（RPFM v5 Server API）。

用法：
    python rpfm_client.py '<JSON命令data>' [--host 127.0.0.1] [--port 45127]

示例：
    python rpfm_client.py '"ListOpenPacks"'
    python rpfm_client.py '{"SetGameSelected": ["warhammer_3", true]}'

协议见 https://github.com/Frodo45127/rpfm/tree/v5.0.6/docs/server
消息信封 {"id": N, "data": <Command>}，响应按 id 配对。
"""
import json
import sys

import websocket

DEFAULT_WS = "ws://127.0.0.1:45127/ws"


def call(command_data, ws_url=DEFAULT_WS, timeout=600):
    ws = websocket.create_connection(ws_url, timeout=timeout)
    # 首条是主动推送的 SessionConnected（id=0）
    hello = json.loads(ws.recv())
    assert hello["id"] == 0, hello
    session_id = hello["data"]["SessionConnected"]
    ws.send(json.dumps({"id": 1, "data": command_data}))
    resp = json.loads(ws.recv())
    assert resp["id"] == 1, resp
    # 优雅断开
    ws.send(json.dumps({"id": 2, "data": "ClientDisconnecting"}))
    ws.close()
    return session_id, resp["data"]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    command_data = json.loads(argv[1])
    session_id, data = call(command_data)
    print(f"session: {session_id}")
    print(json.dumps(data, ensure_ascii=False, indent=1)[:12000])
    if isinstance(data, dict) and "Error" in data:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
