# source 说明（DB 源管理）

- `db/` 下按 RPFM 表名存放导出的 TSV（如 `main_units_tables/…tsv`），**只含目标行**，禁止整表覆盖（任务书 §7.1）。
- 工作流：RPFM 打开 `db.pack` → 找到目标行 → 右键复制行 → 粘贴到本 MOD pack → 改 key 为 `skc_rework_` 前缀 → 导出 TSV 备份到此目录。
- 预计涉及（以实测 schema 为准，§7.2）：
  `main_units_tables / land_units_tables / battle_entities_tables`、
  `building_units_allowed_tables`、
  `building_effects_junctions_tables + effects_tables`、
  `unit_sets / unit_set_to_unit_junctions` 及 effect bonus junction、
  `unit_abilities_tables / unit_special_abilities_tables`、
  `special_ability_to_special_ability_phase_junctions + special_ability_phases + special_ability_phase_stat_effects`、
  当前 Skullcannon 的 missile weapon / projectile 关联表、
  Loc（`localisation`）+ ability 图标引用。
- 二进制 `.pack` 不进 git，只留 TSV 文本，方便 diff 与回滚。
