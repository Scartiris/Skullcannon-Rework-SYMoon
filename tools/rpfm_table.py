"""RPFM Server 批量任务：从依赖取整表并本地过滤（含 skullcannon 的行）。

用法：python rpfm_table.py <table_name> [pattern]
"""
import json
import sys

from rpfm_baseline import send_many


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    table = argv[1]
    pattern = argv[2] if len(argv) > 2 else "skullcannon"
    session, (sel, tables) = send_many(
        [
            {"SetGameSelected": ["warhammer_3", True]},
            {"GetTablesFromDependencies": table},
        ]
    )
    print(f"session: {session}")
    if isinstance(tables, dict) and "Error" in tables:
        print(f"ERROR: {tables['Error']}")
        return 1
    rfiles = tables["VecRFile"]
    print(f"tables returned: {len(rfiles)}")
    for rf in rfiles:
        path = rf.get("path", "?")
        dec = rf.get("decoded", None)
        print(f"== {path} ==")
        if dec is None:
            print(f"   keys: {list(rf.keys())}")
            print(f"   raw: {json.dumps(rf, ensure_ascii=True)[:800]}")
            continue
        print(f"   decoded keys: {list(dec.keys()) if isinstance(dec, dict) else type(dec)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
