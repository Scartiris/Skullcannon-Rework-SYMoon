"""部署系统构建：架设/收炮双能力 + phase + 互斥组 + 单位挂载 + 攻城弹强化 + 能力文本。

输入：Temp 下 vanilla TSV。输出：source/db/*.tsv + source/db/skc_rework.loc.tsv 追加。
用法：python build_deploy.py <vanilla_dir> <source_db_dir>
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_phase0 import read_tsv, write_tsv

SIEGE_AB = "skc_rework_skullcannon_siege_mode"
ASSAULT_AB = "skc_rework_skullcannon_assault_mode"
TOGGLE_GROUP = "skc_rework_skullcannon_modes"
SRC_AB = "wh_dlc05_unit_abilities_storm_of_blades"
SRC_UNIT = "wh3_main_kho_veh_skullcannon_0"


def append_loc_tsv(path, rows):
    with open(path, encoding="utf-8", newline="") as f:
        existing = [r for r in csv.reader(f, delimiter="\t") if r]
    header, ver, data = existing[0], existing[1], existing[2:]
    keys = {r[0] for r in data}
    data += [r for r in rows if r[0] not in keys]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerow(ver)
        w.writerows(data)


def main(argv):
    vanilla = Path(argv[1])
    outdir = Path(argv[2])
    log = []

    # --- abilities：复刻舞姿切换（active -1 无限驻留，wind_up = 架设/收炮时间） ---
    h, ver, rows = read_tsv(vanilla / "vanilla_abilities.tsv")
    base = next(r for r in rows if r[0] == SRC_AB)

    def mk_ability(key, wind_up, recharge, uid):
        r = list(base)
        r[0] = key
        r[h.index("active_time")] = "-1.0"
        r[h.index("recharge_time")] = f"{recharge:.1f}"
        r[h.index("num_uses")] = "-1"
        r[h.index("wind_up_time")] = f"{wind_up:.1f}"
        r[h.index("initial_recharge")] = "-1.0"
        r[h.index("audio")] = ""
        r[h.index("additional_melee_cp")] = "0.0"
        r[h.index("unique_id")] = str(uid)
        return r

    siege_ab = mk_ability(SIEGE_AB, 5.0, 5.0, 810031101)
    assault_ab = mk_ability(ASSAULT_AB, 4.0, 4.0, 810031102)
    write_tsv(outdir / "unit_special_abilities_tables.tsv", h, ver, [siege_ab, assault_ab])
    log.append(f"abilities: {SIEGE_AB}(windup 5s) + {ASSAULT_AB}(windup 4s)")

    # --- phase 关联：列序以原版 TSV 为准（order, special_ability, target_self, target_friends, target_enemies, phase） ---
    hj, verj, _ = read_tsv(vanilla / "vanilla_phase_junc.tsv")
    jrows = []
    for ab in (SIEGE_AB, ASSAULT_AB):
        jrows.append([{"order": "1", "phase": ab, "special_ability": ab,
                       "target_self": "true", "target_friends": "false",
                       "target_enemies": "false"}[c] for c in hj])
    write_tsv(outdir / "special_ability_to_special_ability_phase_junctions_tables.tsv", hj, verj, jrows)
    log.append("phase_junctions: 2 rows")

    # --- phases：架设锁移动，无限驻留 ---
    hph, verph, phrows = read_tsv(vanilla / "vanilla_phases.tsv")
    base_ph = next(r for r in phrows if r[hph.index("id")] == SRC_AB)

    def mk_phase(pid, cant_move):
        r = list(base_ph)
        r[hph.index("id")] = pid
        r[hph.index("duration")] = "-1.0"
        r[hph.index("cant_move")] = "true" if cant_move else "false"
        return r

    write_tsv(outdir / "special_ability_phases_tables.tsv", hph, verph,
              [mk_phase(SIEGE_AB, True), mk_phase(ASSAULT_AB, False)])
    log.append("phases: siege cant_move + assault neutral")

    # --- phase 数值：架设速度锁零 ---
    hps, verps, _ = read_tsv(vanilla / "vanilla_phase_stats.tsv")
    order_ps = list(hps)
    stat_rows = []
    for pid, stat, val, how in [(SIEGE_AB, "scalar_speed", "0.0000", "mult")]:
        stat_rows.append([{"phase": pid, "stat": stat, "value": val, "how": how}[c] for c in order_ps])
    write_tsv(outdir / "special_ability_phase_stat_effects_tables.tsv", hps, verps, stat_rows)
    log.append("phase_stats: siege scalar_speed x0")

    # --- 互斥组 + 挂载 ---
    ht, vert, _ = read_tsv(vanilla / "vanilla_toggle_junc.tsv")
    order_t = list(ht)
    tj = []
    for ab in (SIEGE_AB, ASSAULT_AB):
        tj.append([TOGGLE_GROUP if c == "special_ability_toggle_groups" else ab for c in order_t])
    write_tsv(outdir / "unit_special_ability_to_special_ability_toggle_groups_junctions_tables.tsv", ht, vert, tj)
    hg, verg, _ = read_tsv(vanilla / "vanilla_toggle_groups.tsv")
    write_tsv(outdir / "special_ability_exclusive_toggle_groups_tables.tsv", hg, verg, [[TOGGLE_GROUP]])
    hl, verl, _ = read_tsv(vanilla / "vanilla_land_ability.tsv")
    order_l = list(hl)
    lj = []
    for ab in (SIEGE_AB, ASSAULT_AB):
        lj.append([ab if c == "ability" else SRC_UNIT for c in order_l])
    write_tsv(outdir / "land_units_to_unit_abilites_junctions_tables.tsv", hl, verl, lj)
    log.append(f"toggle group {TOGGLE_GROUP} + land junction 2 rows")

    # --- 攻城弹强化：更大更爆（爆炸复刻迫击炮放大） ---
    he, vere, erows = read_tsv(vanilla / "vanilla_explosions.tsv")
    mortar = next(r for r in erows if r[0] == "wh_main_emp_mortar_explosion")
    boom = list(mortar)
    boom[0] = "skc_rework_siege_explosion"
    boom[he.index("detonation_damage")] = "70.0000"
    boom[he.index("detonation_damage_ap")] = "20.0000"
    write_tsv(outdir / "projectiles_explosions_tables.tsv", he, vere, [boom])
    hp2, verp2, prows = read_tsv(vanilla / "vanilla_projectiles.tsv")
    # 注意：projectiles TSV 由 build_phase0 生成（含 assault/siege），直接改生成的 MOD TSV
    import csv as _csv
    mp = outdir / "projectiles_tables.tsv"
    mrows = [r for r in _csv.reader(open(mp, encoding="utf-8"), delimiter="\t") if r]
    mh, mver, mdata = mrows[0], mrows[1], mrows[2:]
    for r in mdata:
        if r[0] == "skc_rework_projectile_siege":
            r[mh.index("damage")] = "150"
            r[mh.index("ap_damage")] = "200"
            r[mh.index("explosion_type")] = "skc_rework_siege_explosion"
    write_tsv(mp, mh, mver, mdata)
    log.append("siege shell: 150+200, big explosion")

    # --- 能力文本追加进 loc ---
    append_loc_tsv(outdir / "skc_rework.loc.tsv", [
        [f"unit_abilities_onscreen_name_{SIEGE_AB}", "Deploy Siege Mode 架设攻城模式", "false"],
        [f"unit_abilities_tooltip_text_{SIEGE_AB}",
         "Deploy into a fixed siege howitzer: extreme range and heavy shells, but cannot move. "
         "架设为固定攻城炮：超远射程重型炮弹，但无法移动。", "false"],
        [f"unit_abilities_onscreen_name_{ASSAULT_AB}", "Return to Blood Hunt 返回血猎机动", "false"],
        [f"unit_abilities_tooltip_text_{ASSAULT_AB}",
         "Limber up and return to mobile assault gun. 收炮并返回机动突击炮。", "false"],
    ])
    log.append("loc: +4 ability rows")

    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
