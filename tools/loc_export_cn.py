"""从 local_cn.pack 导出中文底表（build_transform 的输入依赖）。用法：python loc_export_cn.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rpfm_baseline import send_many

P = r"T:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\local_cn.pack"
# 中文底表（27MB，不进仓；build_transform 的输入，丢了重跑本脚本）
DEST = r"C:\Users\admin\AppData\Local\Temp\opencode\loc_cn_all.tsv"

s, resps = send_many(
    [
        {"SetGameSelected": ["warhammer_3", True]},
        {"OpenPackFiles": [P]},
        lambda prev: {"ExportTSV": [prev[1]["StringContainerInfo"][0], "text/localisation__.loc", DEST, "PackFile"]},
    ]
)
print(resps[2])
