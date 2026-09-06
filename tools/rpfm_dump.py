"""RPFM Server 批量任务：取依赖表并过滤行。

用法：python rpfm_dump.py <table_name> [pattern] [out_json]
- 无 pattern：打印列名 + 总行数 + 前 2 行
- 有 pattern：打印所有含 pattern（大小写不敏感）的行（列名: 值）
"""
import json
import sys

from rpfm_baseline import send_many


def fetch_table(table):
    _s, (sel, tables) = send_many(
        [
            {"SetGameSelected": ["warhammer_3", True]},
            {"GetTablesFromDependencies": table},
        ]
    )
    if isinstance(tables, dict) and "Error" in tables:
        raise RuntimeError(tables["Error"])
    rfiles = tables["VecRFile"]
    # 依赖可能返回多个 pack 的同名表；选 db.pack 的
    for rf in rfiles:
        if rf.get("container_name") == "db.pack":
            return rf
    return rfiles[0]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    table_name, pattern = argv[1], (argv[2] if len(argv) > 2 else None)
    out_path = argv[3] if len(argv) > 3 else None
    rf = fetch_table(table_name)
    t = rf["data"]["Decoded"]["DB"]["table"]
    fields = [f["name"] for f in t["definition"]["fields"]]
    td = t.get("table_data")
    print(f"table_data type: {type(td).__name__} len={len(td) if hasattr(td, '__len__') else '?'}")
    if isinstance(td, dict):
        print(f"table_data keys: {list(td.keys())}")
        return 0
    rows = td
    print(f"table: {t.get('table_name')} v{t['definition'].get('version')} container={rf.get('container_name')}")
    print(f"columns({len(fields)}): {', '.join(fields)}")
    print(f"rows: {len(rows)}")

    def cells_of(r):
        return r if isinstance(r, list) else list(r.values())

    if pattern is None or pattern == "*":
        for r in rows:
            print(json.dumps(dict(zip(fields, cells_of(r))), ensure_ascii=True)[:2000])
        return 0
    pat = pattern.lower()

    hits = [r for r in rows if any(pat in str(x).lower() for x in cells_of(r))]
    print(f"hits for {pattern!r}: {len(hits)}")
    for r in hits:
        print(json.dumps(dict(zip(fields, cells_of(r))), ensure_ascii=True))
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([dict(zip(fields, cells_of(r))) for r in hits], f, ensure_ascii=False, indent=1)
        print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
