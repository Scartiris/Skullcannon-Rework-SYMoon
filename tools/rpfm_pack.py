"""Phase 0 组包：NewPack -> 建空表 -> ImportTSV -> SavePackAs（同 session 链式）。

用法：python rpfm_pack.py <source_db_dir> <out_pack>
表版本 pin 自 db.pack 实测（projectiles v53 / missile_weapons v11 / land_units v54）。
"""
import sys

from rpfm_baseline import send_many

TABLES = [
    # (tsv 文件名, 包内路径, 表名, 版本)
    ("projectiles_tables.tsv", "db/projectiles_tables/data__", "projectiles_tables", 53),
    ("missile_weapons_tables.tsv", "db/missile_weapons_tables/data__", "missile_weapons_tables", 11),
    ("land_units_tables.tsv", "db/land_units_tables/data__", "land_units_tables", 54),
]


def main(argv):
    src, out_pack = argv[1], argv[2]

    def need_key(idx):
        def go(prev):
            return idx(prev)
        return go

    cmds = [
        {"SetGameSelected": ["warhammer_3", True]},
        "NewPack",
        lambda prev: {"SetPackFileType": [prev[1]["String"], "Mod"]},
    ]
    for tsv, path, table, ver in TABLES:
        cmds.append(lambda prev, _p=path, _t=table, _v=ver: {"NewPackedFile": [prev[1]["String"], _p, {"DB": ["data__", _t, _v]}]})
    for tsv, path, _t, _v in TABLES:
        cmds.append(lambda prev, _p=path, _s=f"{src}/{tsv}": {"ImportTSV": [prev[1]["String"], _p, _s]})
    cmds.append(lambda prev: {"SavePackAs": [prev[1]["String"], out_pack]})
    cmds.append(lambda prev: {"ClosePack": prev[1]["String"]})

    session, resps = send_many(cmds)
    print(f"session: {session} pack: {resps[1]}")
    names = ["gamesel", "newpack", "settype"] + [f"newfile:{t}" for t, _p, _t, _v in TABLES] + [f"import:{t}" for t, _p, _t, _v in TABLES] + ["save", "close"]
    rc = 0
    for name, r in zip(names, resps):
        bad = isinstance(r, dict) and "Error" in r
        print(f"  {name}: {'ERROR ' + r['Error'][:300] if bad else str(r)[:200]}")
        rc = rc or (1 if bad else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
