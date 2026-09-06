"""RPFM Server：导出 TSV。

用法：python rpfm_export.py <internal_path> <dest> [source] [pack_key]
默认 source=PackFile pack_key="CA PackFiles"（需先 LoadAllCAPackFiles）。
"""
import sys

from rpfm_baseline import send_many


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    path, dest = argv[1], argv[2]
    source = argv[3] if len(argv) > 3 else "PackFile"
    pack_key = argv[4] if len(argv) > 4 else "CA PackFiles"
    cmds = []
    if pack_key == "CA PackFiles":
        cmds += [
            {"SetGameSelected": ["warhammer_3", True]},
            "LoadAllCAPackFiles",
        ]
    cmds.append({"ExportTSV": [pack_key, path, dest, source]})
    session, resps = send_many(cmds)
    print(f"session: {session}")
    for r in resps:
        print(f"  {str(r)[:300]}")
        if isinstance(r, dict) and "Error" in r:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
