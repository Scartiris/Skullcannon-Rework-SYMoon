"""Phase 0 组包：NewPack -> 建空表 -> ImportTSV -> SavePackAs（同 session 链式）。

用法：python rpfm_pack.py <source_db_dir> <out_pack>
表版本 pin 自 db.pack 实测（projectiles v53 / missile_weapons v11 / land_units v54）。
"""
import sys

from rpfm_baseline import send_many

TABLES = [
    # (tsv 文件名, 包内路径, 表名/类型名, 种类型 DB/Loc；版本从 TSV 版本行自动读)
    # 注意：abilities 放首位（包内互作排查：R1+能力单包崩、双包行，怀疑创建顺序/索引互作）
    ("unit_special_abilities_tables.tsv", "db/unit_special_abilities_tables/skc_rework_phase0", "unit_special_abilities_tables", "DB"),
    ("projectiles_tables.tsv", "db/projectiles_tables/skc_rework_phase0", "projectiles_tables", "DB"),
    ("missile_weapons_tables.tsv", "db/missile_weapons_tables/skc_rework_phase0", "missile_weapons_tables", "DB"),
    ("land_units_tables.tsv", "db/land_units_tables/skc_rework_phase0", "land_units_tables", "DB"),
    ("battle_entities_tables.tsv", "db/battle_entities_tables/skc_rework_phase0", "battle_entities_tables", "DB"),
    ("mounts_tables.tsv", "db/mounts_tables/skc_rework_phase0", "mounts_tables", "DB"),
    ("unit_variants_tables.tsv", "db/unit_variants_tables/skc_rework_phase0", "unit_variants_tables", "DB"),
    ("main_units_tables.tsv", "db/main_units_tables/skc_rework_phase0", "main_units_tables", "DB"),
    ("land_units_to_unit_abilites_junctions_tables.tsv", "db/land_units_to_unit_abilites_junctions_tables/skc_rework_phase0", "land_units_to_unit_abilites_junctions_tables", "DB"),
    ("projectiles_explosions_tables.tsv", "db/projectiles_explosions_tables/skc_rework_phase0", "projectiles_explosions_tables", "DB"),
    ("skc_rework.loc.tsv", "text/db/skc_rework.loc", "skc_rework", "Loc"),
]
# 磁盘源文件 -> 包内文本路径（AddPackedFiles 直塞，不经过 TSV）
RAW_FILES = [
    ("script/battle/mod/skc_rework.lua", "script/battle/mod/skc_rework.lua"),
]


def tsv_version(tsv_path):
    with open(tsv_path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln]
    ver_line = lines[1]
    assert ver_line.startswith("#"), ver_line[:60]
    return int(ver_line.split(";")[1])


def main(argv):
    src, out_pack = argv[1], argv[2]
    only = set(argv[3].split(",")) if len(argv) > 3 else None
    no_raw = len(argv) > 4 and argv[4] == "nolua"
    tables = [t for t in TABLES if (only is None or t[0] in only)]
    assert tables, "no tables selected"
    raw_files = [] if no_raw else RAW_FILES

    def need_key(idx):
        def go(prev):
            return idx(prev)
        return go

    cmds = [
        {"SetGameSelected": ["warhammer_3", True]},
        "NewPack",
        lambda prev: {"SetPackFileType": [prev[1]["String"], "Mod"]},
    ]
    for tsv, path, table, kind in tables:
        fname = path.split("/")[-1]
        if kind == "Loc":
            spec = {"Loc": table}
        else:
            ver = tsv_version(f"{src}/{tsv}")
            spec = {"DB": [fname, table, ver]}
        cmds.append(lambda prev, _p=path, _s=spec: {"NewPackedFile": [prev[1]["String"], _p, _s]})
    for tsv, path, _t, _k in tables:
        cmds.append(lambda prev, _p=path, _s=f"{src}/{tsv}": {"ImportTSV": [prev[1]["String"], _p, _s]})
    import os as _os
    _root = _os.path.dirname(_os.path.dirname(__file__))
    for disk_rel, dest in raw_files:
        disk = _os.path.join(_root, *disk_rel.split("/"))
        cmds.append(lambda prev, _d=disk, _t={"File": dest}: {"AddPackedFiles": [prev[1]["String"], [_d], [_t], None]})
    cmds.append(lambda prev: {"SavePackAs": [prev[1]["String"], out_pack]})
    cmds.append(lambda prev: {"ClosePack": prev[1]["String"]})

    session, resps = send_many(cmds)
    print(f"session: {session} pack: {resps[1]}")
    names = ["gamesel", "newpack", "settype"] + [f"newfile:{t}" for t, _p, _t, _k in tables] + [f"import:{t}" for t, _p, _t, _k in tables] + [f"raw:{d}" for _s, d in raw_files] + ["save", "close"]
    rc = 0
    for name, r in zip(names, resps):
        bad = isinstance(r, dict) and "Error" in r
        print(f"  {name}: {'ERROR ' + r['Error'][:300] if bad else str(r)[:200]}")
        rc = rc or (1 if bad else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
