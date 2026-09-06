"""验证：打开 MOD pack，回读表 key 列表（同 session 链式）。

用法：python rpfm_verify.py <pack_path>
"""
import csv
import sys
from pathlib import Path

from rpfm_baseline import send_many

TABLES = [
    "db/projectiles_tables/skc_rework_phase0",
    "db/missile_weapons_tables/skc_rework_phase0",
    "db/land_units_tables/skc_rework_phase0",
    "db/missile_weapons_to_projectiles_tables/skc_rework_phase0",
    "db/projectile_shot_type_displays_tables/skc_rework_phase0",
]
TMP = Path(r"C:\Users\admin\AppData\Local\Temp\opencode\verify")


def main(argv):
    pack = argv[1]
    TMP.mkdir(exist_ok=True)
    cmds = [
        {"SetGameSelected": ["warhammer_3", True]},
        {"OpenPackFiles": [pack]},
    ]
    for p in TABLES:
        dest = str(TMP / (Path(p).parent.name + ".tsv"))
        cmds.append(lambda prev, _p=p, _d=dest: {"ExportTSV": [prev[1]["StringContainerInfo"][0], _p, _d, "PackFile"]})
    cmds.append(lambda prev: {"ClosePack": prev[1]["StringContainerInfo"][0]})
    session, resps = send_many(cmds)
    print(f"session: {session} opened: {resps[1]}")
    rc = 0
    for p, r in zip(TABLES, resps[2:-1]):
        bad = isinstance(r, dict) and "Error" in r
        print(f"  export {p}: {'ERROR ' + r['Error'][:200] if bad else r}")
        rc = rc or (1 if bad else 0)
    if rc:
        return rc
    for p in TABLES:
        f = TMP / (Path(p).parent.name + ".tsv")
        rows = [x for x in csv.reader(open(f, encoding="utf-8"), delimiter="\t") if x]
        print(f"  {Path(p).parent.name}: {[x[0] for x in rows[2:]]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
