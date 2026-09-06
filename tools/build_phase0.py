"""Phase 0 构建（变身架构）：双弹丸 + 双武器，无原生切换按钮。

输入：Temp 下 vanilla TSV。输出：source/db/*.tsv。
- assault/siege 炮弹 display 均为 placeholder（不变身不切换，形态即弹种）。
- 突击武器默认突击弹，攻城武器默认攻城弹。
用法：python build_phase0.py <vanilla_dir> <source_db_dir>
"""
import csv
import sys
from pathlib import Path

ASSAULT = "skc_rework_projectile_assault"
SIEGE = "skc_rework_projectile_siege"
WEAPON = "skc_rework_missile_skullcannon"
SIEGE_WEAPON = "skc_rework_missile_siege"
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

    # --- projectiles：assault 280 直射 / siege 500 高抛（见 build_transform 强化伤害） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_projectiles.tsv")
    base = next(r for r in rows if r[0] == SRC_PROJ)
    assault = list(base)
    assault[0] = ASSAULT
    assault[h.index("effective_range")] = "280"
    assault[h.index("calibration_distance")] = "200"
    assault[h.index("projectile_shot_type_display")] = "placeholder"
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
    siege[h.index("projectile_shot_type_display")] = "placeholder"
    write_tsv(outdir / "projectiles_tables.tsv", h, ver, [assault, siege])
    log.append(f"projectiles: {ASSAULT}(280) + {SIEGE}(500 high-arc)")

    # --- missile_weapons：突击武器 + 攻城武器（各默认一发，无 junction 即无切换按钮） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_missile_weapons.tsv")
    base = next(r for r in rows if r[0] == SRC_WEAPON)
    weapon = list(base)
    weapon[0] = WEAPON
    weapon[h.index("default_projectile")] = ASSAULT
    siege_w = list(base)
    siege_w[0] = SIEGE_WEAPON
    siege_w[h.index("default_projectile")] = SIEGE
    write_tsv(outdir / "missile_weapons_tables.tsv", h, ver, [weapon, siege_w])
    log.append(f"missile_weapons: {WEAPON} + {SIEGE_WEAPON}")

    # --- land_units：原版突击形态指向突击武器 ---
    h, ver, rows = read_tsv(vanilla / "vanilla_land_units.tsv")
    unit = next(r for r in rows if r[h.index("key")] == SRC_UNIT)
    unit = list(unit)
    unit[h.index("primary_missile_weapon")] = WEAPON
    write_tsv(outdir / "land_units_tables.tsv", h, ver, [unit])
    log.append(f"land_units: {SRC_UNIT} -> {WEAPON}")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
