# tools 说明（工具版本 pin）

- RPFM：v5.0.6（2026-08-11 发布，`CheckSchemaUpdates`/`UpdateSchemas` 已拉取最新 schema）。
  本地解压在 `C:\Users\admin\AppData\Local\Temp\opencode\rpfm\`（不进 git）。
  官网：https://github.com/Frodo45127/rpfm
- 游戏基线：`T:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\db.pack`
- RPFM 可执行文件放本地，不进 git（见 `.gitignore`）。

## 自研脚本（进 git，可复现反查与构建）

v5 移除了 CLI，改用 `rpfm_server.exe` + WebSocket API（`ws://127.0.0.1:45127/ws`，
协议见 https://github.com/Frodo45127/rpfm/tree/v5.0.6/docs/server）。
脚本会自动起 server（`ensure_server`），用完发 `ClientDisconnecting`，无 session 时 server 自动退出。

| 脚本 | 用途 |
|---|---|
| `rpfm_client.py` | 最小客户端：发单条命令（JSON 经文件/代码传，不经 shell 引号） |
| `rpfm_baseline.py` | `send_many` + `ensure_server` 公共库；早期基线探查脚本 |
| `rpfm_search.py` | 引用反查（`SearchReferences`；`GlobalSearch` 配置构造保留备用） |
| `rpfm_dump.py` | 从依赖取整表并按 pattern 过滤行：`python rpfm_dump.py <表名> [pattern] [out_json]` |
| `rpfm_export.py` | 导出 TSV：`python rpfm_export.py <包内路径> <输出> [source] [pack_key]` |

## Phase 0 施工链（已验证）

`ExportTSV` 原版表 → Python 改写（只留目标行，新 `skc_rework_` key）
→ `NewPack` → `NewPackedFile` 建空表 → `ImportTSV` → `SavePackAs` → `pack/` 本地测试。
仓库 `source/db/` 只留改写后的 TSV 文本，方便 diff 与回滚。
