"""校验 MOD TSV 的引用完整性（单 session 批量拉取版）。

用法：python rpfm_validate.py <source_db_dir>
两轮：先拉 MOD 涉及表拿 is_reference 声明，再拉被引用表，最后本地核对。
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rpfm_baseline import send_many
from rpfm_pack import TABLES


def norm(x):
    if isinstance(x, dict):
        x = next(iter(x.values()))
    if x is None:
        return ""
    s = str(x)
    try:
        return ("f", round(float(s), 6))
    except (ValueError, TypeError):
        return ("s", s.strip().lower())


def cell_val(cell):
    if isinstance(cell, dict):
        return next(iter(cell.values()))
    return cell


def batch_fetch(tables):
    cmds = [{"SetGameSelected": ["warhammer_3", True]}]
    cmds += [{"GetTablesFromDependencies": t} for t in tables]
    _s, resps = send_many(cmds)
    out = {}
    for t, r in zip(tables, resps[1:]):
        if isinstance(r, dict) and "Error" in r:
            print(f"  !! {t}: {r['Error'][:120]}")
            continue
        files = r.get("VecRFile", [])
        if not files:
            print(f"  !! {t}: empty")
            continue
        rf = next((c for c in files if c.get("container_name") == "db.pack"), files[0])
        out[t] = rf["data"]["Decoded"]["DB"]["table"]
    return out


def main(argv):
    src = Path(argv[1])
    mod = {}
    for tsv, _path, table, kind in TABLES:
        if kind != "DB":
            continue
        with open(src / tsv, encoding="utf-8", newline="") as f:
            rows = [r for r in csv.reader(f, delimiter="\t") if r]
        mod[table] = (rows[0], rows[2:])
    print(f"== pass1: {len(mod)} mod tables ==")
    dep1 = batch_fetch(list(mod.keys()))
    refs_needed = set()
    for table, t in dep1.items():
        for f in t["definition"]["fields"]:
            ref = f.get("is_reference")
            if ref:
                pairs = ref if (isinstance(ref, list) and ref and isinstance(ref[0], list)) else [ref]
                refs_needed.update(rt for rt, _rc in pairs)
    refs_needed -= set(dep1.keys())
    print(f"== pass2: {len(refs_needed)} referenced tables ==")
    dep2 = batch_fetch(sorted(refs_needed))
    dep = {**dep1, **dep2}

    def pool_for(rtable, rcol):
        pool = set()
        if rtable in dep:
            t = dep[rtable]
            fields = [f["name"] for f in t["definition"]["fields"]]
            if rcol in fields:
                pool = {norm(cell_val(r[fields.index(rcol)])) for r in t["table_data"]}
        if rtable in mod:
            mf, mrows = mod[rtable]
            if rcol in mf:
                pool |= {norm(r[mf.index(rcol)]) for r in mrows}
        return pool

    problems = []
    nchecks = 0
    for table, (fields, data) in mod.items():
        t = dep.get(table)
        if t is None:
            continue
        refs = {f["name"]: f.get("is_reference") for f in t["definition"]["fields"]}
        for ri, row in enumerate(data):
            for ci, col in enumerate(fields):
                ref = refs.get(col)
                if not ref:
                    continue
                pairs = ref if (isinstance(ref, list) and ref and isinstance(ref[0], list)) else [ref]
                val = norm(row[ci])
                if val == ("s", ""):
                    continue
                nchecks += 1
                ok = any(val in pool_for(rt, rc) for rt, rc in pairs)
                if not ok:
                    problems.append(f"{table}#{ri} {col}={row[ci]!r} not in {[f'{a}.{b}' for a, b in pairs]}")
    print(f"checks: {nchecks}, problems: {len(problems)}")
    for p in problems[:60]:
        print("  MISSING:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
