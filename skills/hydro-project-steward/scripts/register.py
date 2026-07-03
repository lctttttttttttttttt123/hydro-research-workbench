#!/usr/bin/env python3
"""
register.py —— 可复现工作区的登记与自检助手

配合 init_project.py 生成的项目使用,让"归档"可脚本化、可靠:
  - register     把一张图/一份成品登记进 manifest.json,并可写出图的 .meta.json
  - pending      往 manifest + worklog 汇总一条待补/待核项
  - log          往 logs/worklog.md 追加一条工作记录
  - freeze       把当前依赖写进 env/requirements.txt(pip freeze)
  - check        复现完整性自检:图有没有 meta、processed 有没有对应脚本、待补是否清零

用法示例:
  python3 register.py register --root <项目目录> --type figure \\
      --path figures/fig_3-1.png --data data/processed/scour.csv \\
      --script scripts/plot_scour.py --params '{"dpi":300}' \\
      --title-zh "冲刷深度随时间" --title-en "Scour depth vs time"
  python3 register.py pending  --root <项目目录> --note "缺 3 组冲刷实测数据"
  python3 register.py log      --root <项目目录> --note "完成综述初稿,待精读全文核实"
  python3 register.py freeze   --root <项目目录>
  python3 register.py check    --root <项目目录>
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def _load(root):
    with open(os.path.join(root, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def _save(root, m):
    with open(os.path.join(root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def _append_log(root, line):
    p = os.path.join(root, "logs", "worklog.md")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"\n### {datetime.now():%Y-%m-%d %H:%M} {line}\n")


def cmd_register(a):
    m = _load(a.root)
    params = json.loads(a.params) if a.params else {}
    entry = {
        "type": a.type, "path": a.path,
        "source_data": [a.data] if a.data else [],
        "script": a.script, "params": params,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    m["artifacts"].append(entry)
    _save(a.root, m)
    # 若是图,顺便写出 .meta.json,保证"图可追溯"
    if a.type == "figure" and a.path:
        meta = dict(entry)
        meta["title_zh"] = a.title_zh or ""
        meta["title_en"] = a.title_en or ""
        base = os.path.splitext(os.path.join(a.root, a.path))[0]
        with open(base + ".meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    _append_log(a.root, f"登记产出:{a.type} {a.path}")
    print(f"✓ 已登记:{a.type} {a.path}")


def cmd_pending(a):
    m = _load(a.root)
    m.setdefault("pending", []).append(
        {"note": a.note, "added": datetime.now().isoformat(timespec="seconds")})
    _save(a.root, m)
    _append_log(a.root, f"待补:{a.note}")
    print(f"✓ 已记待补:{a.note}")


def cmd_log(a):
    _append_log(a.root, a.note)
    print("✓ 已写入日志")


def cmd_freeze(a):
    out = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                         capture_output=True, text=True)
    p = os.path.join(a.root, "env", "requirements.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(out.stdout)
    print(f"✓ 已写 {p}")


def cmd_check(a):
    root = a.root
    problems = []
    # 1) figures 里的图都要有 .meta.json
    figdir = os.path.join(root, "figures")
    if os.path.isdir(figdir):
        for fn in os.listdir(figdir):
            if fn.lower().endswith((".png", ".svg", ".pdf")) and not fn.startswith("_"):
                meta = os.path.splitext(os.path.join(figdir, fn))[0] + ".meta.json"
                if not os.path.exists(meta):
                    problems.append(f"图缺 meta(不可追溯):figures/{fn}")
    # 2) processed 数据应有脚本(启发式:提示核对)
    procdir = os.path.join(root, "data", "processed")
    if os.path.isdir(procdir):
        proc = [f for f in os.listdir(procdir) if not f.startswith("_")]
        if proc and not os.listdir(os.path.join(root, "scripts")):
            problems.append("data/processed 有派生数据,但 scripts/ 为空——派生数据应由脚本生成")
    # 3) 待补是否清零
    m = _load(root)
    if m.get("pending"):
        problems.append(f"仍有 {len(m['pending'])} 条待补/待核未清零(见 manifest.pending)")
    # 4) env 是否更新
    envf = os.path.join(root, "env", "requirements.txt")
    if os.path.exists(envf) and os.path.getsize(envf) < 80:
        problems.append("env/requirements.txt 似乎未更新(建议 freeze 以便复现)")

    if problems:
        print("自检发现问题:")
        for p in problems:
            print("  ✗ " + p)
        sys.exit(1)
    print("✓ 复现完整性自检通过:图可追溯、派生数据有脚本、待补已清、环境已锁。")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("register"); r.set_defaults(func=cmd_register)
    r.add_argument("--root", required=True)
    r.add_argument("--type", required=True, choices=["figure", "output", "dataset", "draft"])
    r.add_argument("--path", required=True)
    r.add_argument("--data", default="")
    r.add_argument("--script", default="")
    r.add_argument("--params", default="")
    r.add_argument("--title-zh", default="")
    r.add_argument("--title-en", default="")

    p = sub.add_parser("pending"); p.set_defaults(func=cmd_pending)
    p.add_argument("--root", required=True); p.add_argument("--note", required=True)

    l = sub.add_parser("log"); l.set_defaults(func=cmd_log)
    l.add_argument("--root", required=True); l.add_argument("--note", required=True)

    fz = sub.add_parser("freeze"); fz.set_defaults(func=cmd_freeze)
    fz.add_argument("--root", required=True)

    c = sub.add_parser("check"); c.set_defaults(func=cmd_check)
    c.add_argument("--root", required=True)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
