"""Phase 0 组包：NewPack -> 建空表 -> ImportTSV -> SavePackAs（同 session 链式）。

用法：python rpfm_pack.py <source_db_dir> <out_pack>
表版本 pin 自 db.pack 实测（projectiles v53 / missile_weapons v11 / land_units v54）。
"""
import sys

from rpfm_baseline import send_many

TABLES = [
    # (tsv 文件名, 包内路径, 表名, 版本)
    ("projectiles_tables.tsv", "db/projectiles_tables/skc_rework_phase0", "projectiles_tables", 53),
    ("missile_weapons_tables.tsv", "db/missile_weapons_tables/skc_rework_phase0", "missile_weapons_tables", 11),
    ("land_units_tables.tsv", "db/land_units_tables/skc_rework_phase0", "land_units_tables", 54),
    ("missile_weapons_to_projectiles_tables.tsv", "db/missile_weapons_to_projectiles_tables/skc_rework_phase0", "missile_weapons_to_projectiles_tables", 0),
    ("projectile_shot_type_displays_tables.tsv", "db/projectile_shot_type_displays_tables/skc_rework_phase0", "projectile_shot_type_displays_tables", 1),
]


def main(argv):
    src, out_pack = argv[1], argv[2]
    only = set(argv[3].split(",")) if len(argv) > 3 else None
    tables = [t for t in TABLES if (only is None or t[0] in only)]
    assert tables, "no tables selected"

    def need_key(idx):
        def go(prev):
            return idx(prev)
        return go

    cmds = [
        {"SetGameSelected": ["warhammer_3", True]},
        "NewPack",
        lambda prev: {"SetPackFileType": [prev[1]["String"], "Mod"]},
    ]
    for tsv, path, table, ver in tables:
        fname = path.split("/")[-1]
        cmds.append(lambda prev, _p=path, _t=table, _v=ver, _f=fname: {"NewPackedFile": [prev[1]["String"], _p, {"DB": [_f, _t, _v]}]})
    for tsv, path, _t, _v in tables:
        cmds.append(lambda prev, _p=path, _s=f"{src}/{tsv}": {"ImportTSV": [prev[1]["String"], _p, _s]})
    cmds.append(lambda prev: {"SavePackAs": [prev[1]["String"], out_pack]})
    cmds.append(lambda prev: {"ClosePack": prev[1]["String"]})

    session, resps = send_many(cmds)
    print(f"session: {session} pack: {resps[1]}")
    names = ["gamesel", "newpack", "settype"] + [f"newfile:{t}" for t, _p, _t, _v in tables] + [f"import:{t}" for t, _p, _t, _v in tables] + ["save", "close"]
    rc = 0
    for name, r in zip(names, resps):
        bad = isinstance(r, dict) and "Error" in r
        print(f"  {name}: {'ERROR ' + r['Error'][:300] if bad else str(r)[:200]}")
        rc = rc or (1 if bad else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
