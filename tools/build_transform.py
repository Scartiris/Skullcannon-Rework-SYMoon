"""变身版构建：攻城形态单位链 + 部署往返能力 + 文本 + 爆炸强化。

以 paperpancake 回变行为底本（behaviour 空 + spawned_unit 固定 + 共享血量疲劳），
Caesar 式 land key 指向。active_time -1 无限驻留待实测。
用法：python build_transform.py <vanilla_dir> <source_db_dir>
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_phase0 import read_tsv, write_tsv, SRC_UNIT

SIEGE_LAND = "skc_rework_skullcannon_siege"
SIEGE_MAIN = "skc_rework_skullcannon_siege"
SIEGE_MOUNT = "skc_rework_mnt_siege"
SIEGE_ENTITY = "skc_rework_entity_siege"
SIEGE_WEAPON = "skc_rework_missile_siege"
DEPLOY_AB = "skc_rework_deploy_siege"
UNDEPLOY_AB = "skc_rework_undeploy"
SIEGE_SHORT = "skc_rework_siege_short"
SIEGE_LONG = "skc_rework_siege_long"
SRC_MOUNT = "wh3_main_kho_mnt_skullcannon"
SRC_ENTITY = "wh3_main_kho_vehicle_skullcannon"

PASSIVES = [
    "wh3_main_unit_passive_daemonic_instability_khorne",
    "wh3_main_unit_passive_daemonic_instability_khorne_ii",
    "wh3_main_unit_passive_gorefeast",
    "wh3_main_unit_passive_single_entity",
    "wh3_main_unit_passive_skullfeast",
]

GENERIC_VO = "vo_battle_special_ability_generic_response"


def write_loc_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["key", "text", "tooltip"])
        w.writerow(["#Loc;1;text/db/skc_rework.loc"])
        w.writerows(rows)


def main(argv):
    vanilla = Path(argv[1])
    outdir = Path(argv[2])
    log = []

    # --- siege entity：速度锁零 ---
    h, ver, rows = read_tsv(vanilla / "vanilla_entities.tsv")
    ent = next(r for r in rows if r[0] == SRC_ENTITY)
    ent = list(ent)
    ent[0] = SIEGE_ENTITY
    ent[h.index("walk_speed")] = "0.0"
    ent[h.index("run_speed")] = "0.0"
    ent[h.index("charge_speed")] = "0.0"
    ent[h.index("turn_speed")] = "5.0"
    write_tsv(outdir / "battle_entities_tables.tsv", h, ver, [ent])
    log.append(f"entity: {SIEGE_ENTITY} speed 0")

    # --- siege mount（variant 指回原版外观：同模型，无新美术） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_mounts.tsv")
    mnt = next(r for r in rows if r[0] == SRC_MOUNT)
    mnt = list(mnt)
    mnt[0] = SIEGE_MOUNT
    mnt[h.index("entity")] = SIEGE_ENTITY
    write_tsv(outdir / "mounts_tables.tsv", h, ver, [mnt])
    log.append(f"mount: {SIEGE_MOUNT} (variant reuse assault)")

    # --- unit_variants：攻城形态登记（卡面复用原版） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_unit_variants.tsv")
    base = next(r for r in rows if r[h.index("unit")] == SRC_UNIT)
    uv = list(base)
    uv[h.index("name")] = SIEGE_LAND
    uv[h.index("unit")] = SIEGE_LAND
    uv[h.index("unit_card")] = SRC_UNIT
    write_tsv(outdir / "unit_variants_tables.tsv", h, ver, [uv])
    log.append(f"variants: {SIEGE_LAND} (card reuse)")

    # --- siege land unit（并入 land_units_tables.tsv，与突击覆盖行同一文件） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_land_units.tsv")
    base = next(r for r in rows if r[h.index("key")] == SRC_UNIT)
    sl = list(base)
    sl[h.index("key")] = SIEGE_LAND
    sl[h.index("mount")] = SIEGE_MOUNT
    sl[h.index("primary_missile_weapon")] = SIEGE_WEAPON
    sl[h.index("short_description_text")] = SIEGE_SHORT
    sl[h.index("historical_description_text")] = SIEGE_LONG
    import csv as _csv
    mp = outdir / "land_units_tables.tsv"
    mrows = [r for r in _csv.reader(open(mp, encoding="utf-8"), delimiter="\t") if r]
    mh, mver, mdata = mrows[0], mrows[1], mrows[2:]
    mdata = [r for r in mdata if r[mh.index("key")] != SIEGE_LAND] + [sl]
    write_tsv(mp, mh, mver, mdata)
    log.append(f"land siege: {SIEGE_LAND} merged ({len(mdata)} rows)")

    # --- siege main unit（不招募，无建筑行） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_main_units.tsv")
    base = next(r for r in rows if r[h.index("unit")] == SRC_UNIT)
    sm = list(base)
    sm[h.index("unit")] = SIEGE_MAIN
    sm[h.index("land_unit")] = SIEGE_LAND
    sm[h.index("in_encyclopedia")] = "false"
    write_tsv(outdir / "main_units_tables.tsv", h, ver, [sm])
    log.append(f"main siege: {SIEGE_MAIN} (encyclopedia off)")

    # --- 部署往返能力（paperpancake 底本） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_pancake.tsv")
    base = rows[0]

    def mk_ability(key, wind_up, recharge, spawned, uid):
        r = list(base)
        r[0] = key
        # 驻留时长：默认 -1 无限；若引擎不接受变身无限驻留，用 SKC_ACTIVE_TIME 覆盖（如 3600）
        r[h.index("active_time")] = os.environ.get("SKC_ACTIVE_TIME", "-1.0")
        r[h.index("recharge_time")] = f"{recharge:.1f}"
        r[h.index("num_uses")] = "-1"
        r[h.index("wind_up_time")] = f"{wind_up:.1f}"
        r[h.index("initial_recharge")] = "-1.0"
        r[h.index("spawned_unit")] = spawned
        r[h.index("voiceover_state")] = GENERIC_VO
        r[h.index("unique_id")] = str(uid)
        return r

    dep = mk_ability(DEPLOY_AB, 5.0, 30.0, SIEGE_LAND, 810031201)
    unde = mk_ability(UNDEPLOY_AB, 4.0, 10.0, SRC_UNIT, 810031202)
    write_tsv(outdir / "unit_special_abilities_tables.tsv", h, ver, [dep, unde])
    log.append(f"abilities: {DEPLOY_AB}(5s) + {UNDEPLOY_AB}(4s) active {dep[h.index('active_time')]}")

    # --- 单位挂载：突击=部署+被动，攻城=收炮+被动 ---
    hl, verl, _ = read_tsv(vanilla / "vanilla_land_ability.tsv")
    order_l = list(hl)
    lj = []
    for ab in [DEPLOY_AB] + PASSIVES:
        lj.append([ab if c == "ability" else SRC_UNIT for c in order_l])
    for ab in [UNDEPLOY_AB] + PASSIVES:
        lj.append([ab if c == "ability" else SIEGE_LAND for c in order_l])
    write_tsv(outdir / "land_units_to_unit_abilites_junctions_tables.tsv", hl, verl, lj)
    log.append("land junction: assault 6 + siege 6")

    # --- 爆炸 + 攻城弹强化（沿用迫击炮放大思路） ---
    he, vere, erows = read_tsv(vanilla / "vanilla_explosions.tsv")
    mortar = next(r for r in erows if r[0] == "wh_main_emp_mortar_explosion")
    boom = list(mortar)
    boom[0] = "skc_rework_siege_explosion"
    boom[he.index("detonation_damage")] = "70.0000"
    boom[he.index("detonation_damage_ap")] = "20.0000"
    write_tsv(outdir / "projectiles_explosions_tables.tsv", he, vere, [boom])
    mp = outdir / "projectiles_tables.tsv"
    mrows = [r for r in csv.reader(open(mp, encoding="utf-8"), delimiter="\t") if r]
    mh, mver, mdata = mrows[0], mrows[1], mrows[2:]
    for r in mdata:
        if r[0] == "skc_rework_projectile_siege":
            r[mh.index("damage")] = "150"
            r[mh.index("ap_damage")] = "200"
            r[mh.index("explosion_type")] = "skc_rework_siege_explosion"
    write_tsv(mp, mh, mver, mdata)
    log.append("siege shell: 150+200 big explosion")

    # --- 文本（fresh loc，只含变身版条目） ---
    write_loc_tsv(outdir / "skc_rework.loc.tsv", [
        [f"unit_abilities_onscreen_name_{DEPLOY_AB}", "Deploy Siege Mode 架设攻城模式", "false"],
        [f"unit_abilities_tooltip_text_{DEPLOY_AB}",
         "Deploy into a fixed siege howitzer: extreme range and heavy shells, but cannot move. "
         "架设为固定攻城炮：超远射程重型炮弹，但无法移动。", "false"],
        [f"unit_abilities_onscreen_name_{UNDEPLOY_AB}", "Limber Up 收炮机动", "false"],
        [f"unit_abilities_tooltip_text_{UNDEPLOY_AB}",
         "Limber up and return to mobile assault gun. 收炮并返回机动突击炮。", "false"],
        [SIEGE_SHORT, "Skullcannon (Deployed) 颅骨魔炮（攻城架设）", "false"],
        [SIEGE_LONG,
         "Skullcannon deployed as a fixed siege howitzer. 架设为固定攻城炮的颅骨魔炮。",
         "false"],
    ])
    log.append("loc: abilities + siege unit texts")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
