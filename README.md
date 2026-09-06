# 颅骨魔炮重做 Skullcannon Rework [SYMoon]

> 把颅骨魔炮重做为“恐怖版攻城坦克”：高机动野战突击炮 / 可架设高抛攻城炮 / 近战收集颅骨补给 / 魔法之风驱动火力。
> Rework the Skullcannon into a terror siege-tank: mobile assault gun, deployable siege howitzer, melee Skullfeast resupply, Winds of Magic driven firepower.

- 游戏（Game）：Total War: WARHAMMER III
- 对象（Target）：`wh3_main_kho_veh_skullcannon_0`（原版恐虐颅骨魔炮）
- 范围（Scope）：首版仅原版，不含 SFO、不含荣誉兵种、不做新模型（见任务书 §12）
- 任务书（Spec）：`颅骨魔炮重做_MOD施工任务书_v1.0.docx`
- 施工日志（Log）：`docs/施工日志.md`
- 验收清单（Checklist）：`docs/验收清单.md`

## 目录结构（Layout）

```text
./
├── docs/            施工日志、验收清单（纯文本进 git）
├── source/db/       RPFM 导出的 TSV（只含目标行，不整表覆盖）
├── loc/             EN+CN 文本草稿（CSV）与说明
├── script/          Lua（如需要，campaign/battle 分离，可一键剥离）
├── pack/            构建出的 .pack（ verbal 二进制不进 git，由 RPFM 构建）
├── tools/           工具版本 pin（RPFM 版本等）
└── 颅骨魔炮重做_MOD施工任务书_v1.0.docx  原始任务书 v1.0
```

## 工作流（Workflow）

1. 以 `T:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\db.pack` 为基线，
   用 RPFM Global Search 从 `wh3_main_kho_veh_skullcannon_0` 与 `Foundry of Blood` 反向找真实关联。
2. 在 RPFM 中只复制目标行，所有新 key 用 `skc_rework_` 前缀（见任务书 §7.1）。
3. 每 Phase 独立提交；任何 Lua 必须与 DB 分离，保证可一键退回纯 DB 版（§9.1）。
4. 每个阶段按 `docs/验收清单.md` 逐项验收，保留截图/日志/关键 DB key。

## 阶段（Phases）

- Phase 0：技术 Spike——同一台车、同一血量弹药池来回切弹道（纯 DB，方案 A）
- Phase 1：T3 基础单位（下放、280 射程、高机动、Skullfeast 基础补给）
- Phase 2：T4 攻城模式（建筑 enable 能力、500 高抛、90 死区、架设/收炮）
- Phase 3：WoM 肉心（五档快照 + hidden bundle）
- Phase 4：T5 过压（顶档上限、补弹效率、切换质量，单份不堆叠）
- Phase 5：文本/AI/平衡（EN+CN Loc、AI fallback、成本微调）

## 构建（Build）

- RPFM 版本见 `tools/README.md`。
- 用 RPFM 新建 pack（如 `skc_skullcannon_rework.pack`），把 `source/db` 的 TSV 导入，
  输出到 `pack/`（本地构建产物，不提交）。
- 进游戏用自定义战斗验证（见验收清单）。

## 兼容性（Compatibility）

- 不复制整个 vanilla 表进 pack，只复制目标行/关联行。
- 不直接改共享 vanilla projectile；assault/siege 各用独立 key。
- 基础 MOD 不引用 SFO；SFO 兼容在核心稳定后另做 submod。
