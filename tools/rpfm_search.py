"""RPFM Server 批量任务：CA 包全局搜索（基线反查）。

流程（同一 session 内）：
  1. SetGameSelected warhammer_3（rebuild=True，载入依赖缓存）
  2. LoadAllCAPackFiles（合并 CA 官方包，key="CA PackFiles"）
  3. GlobalSearch 指定 pattern

用法：python rpfm_search.py <pattern> [out_json]
输出匹配的内部文件路径列表；可选存 JSON。
"""
import json
import sys

from rpfm_baseline import send_many


SEARCH_ON_FIELDS = [
    "anim", "anim_fragment_battle", "anim_pack", "anims_table", "atlas",
    "audio", "bmd", "db", "esf", "group_formations", "image", "loc",
    "matched_combat", "pack", "portrait_settings", "rigid_model",
    "sound_bank", "text", "uic", "unit_variant", "unknown", "video", "schema",
]
MATCHES_ARRAY_FIELDS = [f for f in SEARCH_ON_FIELDS if f != "schema"]


def empty_matches(pack_key):
    m = {f: [] for f in MATCHES_ARRAY_FIELDS}
    m["schema"] = {
        "path": "",
        "source": {"Pack": pack_key},
        "container_name": "",
        "matches": [],
    }
    return m


def build_config(pattern, pack_key="CA PackFiles"):
    on = {f: (f in ("db", "loc")) for f in SEARCH_ON_FIELDS}
    return {
        "pattern": pattern,
        "replace_text": "",
        "case_sensitive": False,
        "use_regex": False,
        "sources": ["GameFiles"],
        "search_on": on,
        "matches": empty_matches(pack_key),
        "game_key": "warhammer_3",
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    pattern = argv[1]
    out_path = argv[2] if len(argv) > 2 else None
    session, (schema_upd, schema_dl, sel, loaded, found) = send_many(
        [
            "CheckSchemaUpdates",
            "UpdateSchemas",
            {"SetGameSelected": ["warhammer_3", True]},
            "LoadAllCAPackFiles",
            {"SearchReferences": ["CA PackFiles", {}, pattern]},
        ]
    )
    print(f"session: {session}")
    print(f"schema: {json.dumps(schema_upd, ensure_ascii=True)[:300]} / dl={json.dumps(schema_dl, ensure_ascii=True)[:300]}")
    if isinstance(found, dict) and "Error" in found:
        print(f"ERROR: {found['Error']}")
        return 1
    refs = found["VecDataSourceStringStringStringUsizeUsize"]
    print(f"refs: {len(refs)}")
    for r in refs:
        print(f"  src={r[0]} pack={r[1] or '-'} path={r[2]} col={r[3]}:{r[4]} row={r[5]}")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(refs, f, ensure_ascii=False, indent=1)
        print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
