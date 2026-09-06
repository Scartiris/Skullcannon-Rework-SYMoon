"""铸造厂加成构建：单位组 + 新效果 + 映射 + 隐藏包（Lua 计数器独占施加防叠加）。

T4（vehicle_2，需主城4）：弹药 +20，破甲 +25
T5（vehicle_3，需主城5）：弹药 +40，破甲 +50（全额值，非增量；Lua 只挂最高档）
用法：python build_foundry.py <vanilla_dir> <source_db_dir>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_phase0 import read_tsv, write_tsv, SRC_UNIT

SET = "skc_rework_skullcannon_unit_set"
EFF_AMMO = "skc_rework_effect_ammo"
EFF_AP = "skc_rework_effect_ap"
BUNDLE_T4 = "skc_rework_foundry_t4"
BUNDLE_T5 = "skc_rework_foundry_t5"
SIEGE_MAIN = "skc_rework_skullcannon_siege"
SRC_AMMO_FX = "wh_main_effect_force_stat_ammunition_artillery"
SRC_AP_FX = "wh2_dlc12_effect_force_stat_ap_missile_damage_warplock_jezzails"


def main(argv):
    vanilla = Path(argv[1])
    outdir = Path(argv[2])
    log = []

    # --- effects：复刻原版语义（弹药图标/优先级，破甲远程图标/优先级） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_effects.tsv")
    base_ammo = next(r for r in rows if r[0] == SRC_AMMO_FX)
    base_ap = next(r for r in rows if r[0] == SRC_AP_FX)
    fx_ammo = list(base_ammo)
    fx_ammo[0] = EFF_AMMO
    fx_ap = list(base_ap)
    fx_ap[0] = EFF_AP
    write_tsv(outdir / "effects_tables.tsv", h, ver, [fx_ammo, fx_ap])
    log.append(f"effects: {EFF_AMMO} + {EFF_AP}")

    # --- unit_set + 挂载双形态主单位 ---
    h, ver, rows = read_tsv(vanilla / "vanilla_unitsets.tsv")
    base = next(r for r in rows if r[0] == "all_land_artillery")
    us = list(base)
    us[0] = SET
    write_tsv(outdir / "unit_sets_tables.tsv", h, ver, [us])
    hj, verj, jrows = read_tsv(vanilla / "vanilla_set_junc.tsv")
    template = next(r for r in jrows if r[hj.index("unit_record")] != "")
    jx = []
    for main in (SRC_UNIT, SIEGE_MAIN):
        r = list(template)
        r[hj.index("unit_record")] = main
        r[hj.index("unit_set")] = SET
        jx.append(r)
    write_tsv(outdir / "unit_set_to_unit_junctions_tables.tsv", hj, verj, jx)
    log.append(f"unit_set: {SET} (2 mains)")

    # --- effect 到单位组的映射 ---
    hi, veri, irows = read_tsv(vanilla / "vanilla_ids_unitsets.tsv")
    base_i = next(r for r in irows if r[hi.index("effect")] == SRC_AMMO_FX)
    ia = list(base_i)
    ia[hi.index("bonus_value_id")] = "skc_ammo"
    ia[hi.index("effect")] = EFF_AMMO
    ia[hi.index("unit_set")] = SET
    ib = list(base_i)
    ib[hi.index("bonus_value_id")] = "skc_ap"
    ib[hi.index("effect")] = EFF_AP
    ib[hi.index("unit_set")] = SET
    write_tsv(outdir / "effect_bonus_value_ids_unit_sets_tables.tsv", hi, veri, [ia, ib])
    log.append("ids_unit_sets: ammo/ap -> set")

    # --- 隐藏包（Lua 独占施加；标题直接写中英，空描述不进 loc） ---
    hb, verb, brows = read_tsv(vanilla / "vanilla_bundles.tsv")
    b4 = [""] * len(hb)
    b4[hb.index("key")] = BUNDLE_T4
    b4[hb.index("localised_title")] = "Blood-Forged Shells 血铸炮弹"
    b4[hb.index("localised_description")] = "Foundry blessing: +ammunition and armour-piercing damage for Skullcannons. 炼狱祝福：颅骨魔炮弹药与破甲提升。"
    b4[hb.index("bundle_target")] = "faction"
    b4[hb.index("priority")] = "0"
    b4[hb.index("ui_icon")] = ""
    b4[hb.index("is_global_effect")] = "true"
    b4[hb.index("show_in_3d_space")] = "false"
    b4[hb.index("owner_only")] = "true"
    b5 = list(b4)
    b5[hb.index("key")] = BUNDLE_T5
    b5[hb.index("localised_title")] = "Skull-Forged Shells 颅铸炮弹"
    b5[hb.index("localised_description")] = "Greater foundry blessing. 更强炼狱祝福。"
    write_tsv(outdir / "effect_bundles_tables.tsv", hb, verb, [b4, b5])

    # --- 包内效果行（T4/T5 全额值；scope 派系全军） ---
    hx, verx, xrows = read_tsv(vanilla / "vanilla_bundle_fx.tsv")
    stage = xrows[0][hx.index("advancement_stage")]

    def fxrow(bundle, effect, value):
        r = [""] * len(hx)
        r[hx.index("effect_bundle_key")] = bundle
        r[hx.index("effect_key")] = effect
        r[hx.index("effect_scope")] = "faction_to_force_own"
        r[hx.index("value")] = str(value)
        r[hx.index("advancement_stage")] = stage
        return r

    write_tsv(outdir / "effect_bundles_to_effects_junctions_tables.tsv", hx, verx, [
        fxrow(BUNDLE_T4, EFF_AMMO, 20),
        fxrow(BUNDLE_T4, EFF_AP, 25),
        fxrow(BUNDLE_T5, EFF_AMMO, 40),
        fxrow(BUNDLE_T5, EFF_AP, 50),
    ])
    log.append("bundles: T4(+20/+25) T5(+40/+50)")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
