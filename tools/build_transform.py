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


def write_loc_tsv(path, version_row, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["key", "text", "tooltip"])
        w.writerow([version_row])
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
    sl[h.index("primary_ammo")] = "20"
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

    # --- 部署往返能力（Caesar 底本整行照抄，只换 key/uid/目标/前摇/冷却/初始；
    # R2-R6 证实 pancake 系写法在我包必崩，Caesar 系（shares=false 等）能进） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_caesar_abilities.tsv")
    base = next(r for r in rows if r[0] == "wh3_main_lord_abilities_avatar_of_motherland")

    def mk_ability(key, wind_up, recharge, spawned, uid):
        r = list(base)
        r[0] = key
        r[h.index("wind_up_time")] = f"{wind_up:.1f}"
        r[h.index("recharge_time")] = f"{recharge:.1f}"
        r[h.index("initial_recharge")] = "0.0"
        r[h.index("spawned_unit")] = spawned
        r[h.index("audio_switch_ui_override")] = ""
        r[h.index("unique_id")] = str(uid)
        return r

    dep = mk_ability(DEPLOY_AB, 5.0, 30.0,
                     os.environ.get("SKC_SPAWNED_DEPLOY", SIEGE_LAND), 810031201)
    unde = mk_ability(UNDEPLOY_AB, 4.0, 10.0,
                      os.environ.get("SKC_SPAWNED_UNDEPLOY", SRC_UNIT), 810031202)
    # SKC_ABILITIES=deploy|undeploy|both，单行二分用
    which = os.environ.get("SKC_ABILITIES", "both")
    ab_rows = {"deploy": [dep], "undeploy": [unde], "both": [dep, unde]}[which]
    write_tsv(outdir / "unit_special_abilities_tables.tsv", h, ver, ab_rows)
    log.append("abilities done")

    # --- unit_abilities（战役侧 ability 定义：battle key 必须在此有对应行，否则启动 failfast；
    # RPFM 报 InvalidReference 即此。图标 guerrilla_deploy / redeploy 均为原版 UI 资源） ---
    hu, veru, urows = read_tsv(vanilla / "vanilla_unit_abilities.tsv")
    base_u = next(r for r in urows if r[0] == "wh3_dlc24_lord_abilities_formless_horror_changeling")

    def mk_camp_ability(key, icon):
        r = list(base_u)
        r[0] = key
        r[hu.index("icon_name")] = icon
        return r

    write_tsv(outdir / "unit_abilities_tables.tsv", hu, veru,
              [mk_camp_ability(DEPLOY_AB, "guerrilla_deploy"),
               mk_camp_ability(UNDEPLOY_AB, "redeploy")])
    log.append("unit_abilities: deploy/undeploy campaign rows")
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

    # --- 爆炸：攻城放大反步，突击缩小精准 ---
    he, vere, erows = read_tsv(vanilla / "vanilla_explosions.tsv")
    mortar = next(r for r in erows if r[0] == "wh_main_emp_mortar_explosion")
    boom = list(mortar)
    boom[0] = "skc_rework_siege_explosion"
    boom[he.index("detonation_radius")] = "7.0000"
    boom[he.index("detonation_damage")] = "85.0000"
    boom[he.index("detonation_damage_ap")] = "25.0000"
    skull = next(r for r in erows if r[0] == "wh3_main_kho_skullcannon_skull_explosion")
    snap = list(skull)
    snap[0] = "skc_rework_assault_explosion"
    snap[he.index("detonation_radius")] = "2.0000"
    snap[he.index("detonation_damage")] = "5.0000"
    snap[he.index("detonation_damage_ap")] = "12.0000"
    write_tsv(outdir / "projectiles_explosions_tables.tsv", he, vere, [boom, snap])
    mp = outdir / "projectiles_tables.tsv"
    mrows = [r for r in csv.reader(open(mp, encoding="utf-8"), delimiter="\t") if r]
    mh, mver, mdata = mrows[0], mrows[1], mrows[2:]
    for r in mdata:
        if r[0] == "skc_rework_projectile_siege":
            r[mh.index("damage")] = "150"
            r[mh.index("ap_damage")] = "200"
            r[mh.index("explosion_type")] = "skc_rework_siege_explosion"
            r[mh.index("bonus_v_infantry")] = "40"
        elif r[0] == "skc_rework_projectile_assault":
            r[mh.index("explosion_type")] = "skc_rework_assault_explosion"
    write_tsv(mp, mh, mver, mdata)
    log.append("shells: siege 150+200 r7 anti-inf40 / assault small blast")

    # --- 描述文本注册表（land 文本列引用它们，loc 键同名直解） ---
    hs, vers, _ = read_tsv(vanilla / "vanilla_short_texts.tsv")
    write_tsv(outdir / "unit_description_short_texts_tables.tsv", hs, vers, [[SIEGE_SHORT]])
    hl, verl, _ = read_tsv(vanilla / "vanilla_long_texts.tsv")
    write_tsv(outdir / "unit_description_historical_texts_tables.tsv", hl, verl, [[SIEGE_LONG]])
    log.append("text registry: siege short/long")

    # --- 文本：文案源 loc/skc_rework_text.csv 生成英文表 + 中文表（与原版 I18N 布局一致） ---
    csv_path = Path(__file__).parent.parent / "loc" / "skc_rework_text.csv"
    strings = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if not r or r[0].startswith("#") or r[0] == "key":
                continue
            strings.append(r)
    write_loc_tsv(outdir / "skc_rework.loc.tsv", "#Loc;1;text/db/skc_rework.loc",
                  [[k, en, "false"] for k, en, zh, *_ in strings])
    write_loc_tsv(outdir / "skc_rework_cn.loc.tsv", "#Loc;1;text/localisation__.loc",
                  [[k, zh, "false"] for k, en, zh, *_ in strings])
    log.append("loc: EN db file + CN localisation file")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
