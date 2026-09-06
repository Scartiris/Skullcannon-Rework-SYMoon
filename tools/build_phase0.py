"""Phase 0 构建：由原版 TSV 生成 MOD TSV（只含目标行）。

输入：tools 之前从 db.pack 导出的 vanilla TSV（放 Temp，不进仓）。
输出：source/db/*.tsv（进仓）+ 变更清单打印。

用法：python build_phase0.py <vanilla_dir> <source_db_dir>
"""
import csv
import sys
from pathlib import Path

ASSAULT = "skc_rework_projectile_assault"
SIEGE = "skc_rework_projectile_siege"
WEAPON = "skc_rework_missile_skullcannon"
SRC_PROJ = "wh3_main_kho_skullcannon_skull"
SRC_WEAPON = "wh3_main_kho_skullcannon_skull"
SRC_UNIT = "wh3_main_kho_veh_skullcannon_0"


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter="\t") if r]
    header, version_row, data = rows[0], rows[1], rows[2:]
    assert version_row[0].startswith("#"), version_row[0][:60]
    return header, version_row, data


def write_tsv(path, header, version_row, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 版本行内嵌路径必须与包内文件名一致（MOD 表用独立文件名，不用 data__）
    parts = version_row[0].split(";")
    parts[2] = f"db/{parts[0][1:]}/skc_rework_phase0"
    version_row = [";".join(parts)] + version_row[1:]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerow(version_row)
        w.writerows(rows)


def main(argv):
    vanilla = Path(argv[1])
    outdir = Path(argv[2])
    log = []

    # --- projectiles：1 原版行 -> assault + siege ---
    h, ver, rows = read_tsv(vanilla / "vanilla_projectiles.tsv")
    base = next(r for r in rows if r[0] == SRC_PROJ)
    assault = list(base)
    assault[0] = ASSAULT
    assault[h.index("effective_range")] = "280"
    assault[h.index("calibration_distance")] = "200"
    siege = list(base)
    siege[0] = SIEGE
    siege[h.index("shot_type")] = "artillery_explosive"
    siege[h.index("trajectory_sight")] = "fixed"
    siege[h.index("effective_range")] = "500"
    siege[h.index("minimum_range")] = "90"
    siege[h.index("max_elevation")] = "56"
    siege[h.index("fixed_elevation")] = "50"
    siege[h.index("gravity")] = "-1.0"
    siege[h.index("calibration_area")] = "380.0"
    siege[h.index("projectile_penetration")] = "low"
    siege[h.index("can_bounce")] = "false"
    siege[h.index("base_reload_time")] = "16.0"
    write_tsv(outdir / "projectiles_tables.tsv", h, ver, [assault, siege])
    log.append(f"projectiles: {SRC_PROJ} -> {ASSAULT}(range 280) + {SIEGE}(explosive/fixed/range 500/min 90/reload 16)")

    # --- missile_weapons：1 新行 ---
    h, ver, rows = read_tsv(vanilla / "vanilla_missile_weapons.tsv")
    base = next(r for r in rows if r[0] == SRC_WEAPON)
    weapon = list(base)
    weapon[0] = WEAPON
    weapon[h.index("default_projectile")] = ASSAULT
    write_tsv(outdir / "missile_weapons_tables.tsv", h, ver, [weapon])
    log.append(f"missile_weapons: new {WEAPON} default={ASSAULT}")

    # --- land_units：覆盖原版行 primary_missile_weapon（spike 临时指向，Phase 1 建独立单位后移除） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_land_units.tsv")
    unit = next(r for r in rows if r[h.index("key")] == SRC_UNIT)
    unit = list(unit)
    unit[h.index("primary_missile_weapon")] = WEAPON
    write_tsv(outdir / "land_units_tables.tsv", h, ver, [unit])
    log.append(f"land_units: {SRC_UNIT}.primary_missile_weapon -> {WEAPON}（spike 临时覆盖）")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
