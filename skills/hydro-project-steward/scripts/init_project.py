#!/usr/bin/env python3
"""
init_project.py —— 水利/水电科研项目脚手架

一条命令生成一个"可复现、可审计"的标准项目目录:数据、脚本、图、文献、稿件、日志分开,
并写好说明、模板与一份"项目清单(manifest)"。目的是让之后每一步产出都能追溯到它的
数据、代码、参数与决策——把 Claude Science 式的"可复现"落成实际目录规范。

用法:
    python3 init_project.py "非恒定降雨城市路面颗粒物输移"
    python3 init_project.py "梯级水电站负荷分配" --dir /path/to/projects --author "颜敏"

生成结构:
    <项目名>_<日期>/
      README.md            项目说明与使用约定
      manifest.json        项目清单(元信息 + 产出登记表,机器可读)
      data/                原始数据(只读,不改;每个数据集配 .source.md 说明来源)
        raw/               原始数据
        processed/         清洗/派生数据(由 scripts 生成,不手改)
      scripts/             所有分析/绘图脚本(可复现结果的唯一来源)
      figures/             图(每张图配同名 .meta.json:来源数据+脚本+参数)
      refs/                文献:检索结果、DOI 清单、参考文献库
      drafts/              各版本文稿(综述/章节/摘要/申请书/审稿意见)
      outputs/             最终成品(docx/pdf 等)
      logs/                工作日志(每步做了什么、决策、待补)
      env/                 复现环境信息(依赖版本、Python 版本)
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime


DIRS = [
    "data/raw", "data/processed", "scripts", "figures", "refs",
    "drafts", "outputs", "logs", "env",
]


def slugify(name: str) -> str:
    s = re.sub(r"\s+", "_", name.strip())
    s = re.sub(r'[/\\:*?"<>|]', "", s)
    return s[:60]


README_TMPL = """# {name}

- 建立日期:{today}
- 负责人:{author}
- 项目 slug:{slug}

本项目采用"可复现工作区"规范:**每个结果都能追溯到它的数据、脚本、参数与决策**。

## 目录约定
- `data/raw/` —— 原始数据,**只读、不手改**。每个数据集旁放一个 `<名>.source.md`,
  写清来源、采集/模拟条件、单位、字段含义。
- `data/processed/` —— 清洗或派生数据,**只能由 `scripts/` 里的脚本生成**,不手动编辑;
  这样任何派生数据都可由脚本重跑复现。
- `scripts/` —— 所有分析与绘图脚本。**结果的唯一合法来源**:凡 `figures/`、`processed/`
  里的东西,都应能由这里某个脚本重跑得到。
- `figures/` —— 图。每张图 `fig_xxx.(png/svg/pdf)` 旁配同名 `fig_xxx.meta.json`,记录:
  用了哪个数据、哪个脚本、什么参数、生成时间。**没有 meta 的图视为不可信、需补。**
- `refs/` —— 文献:检索结果、DOI 清单、参考文献库(BibTeX/文本)。
- `drafts/` —— 各版本文稿(综述、章节、摘要、审稿意见、去AI味前后各存一版)。
- `outputs/` —— 最终成品(docx/pdf)。
- `logs/` —— 工作日志(见 `logs/worklog.md`),每个工作段落记:做了什么、关键决策、待补项。
- `env/` —— 复现环境:`pip freeze`、Python 版本等。

## 铁律
- **数据、图、结论只要不是实测/计算得来,一律标 `【待补:...】`,不编造。**
- 每产出一张图或一份成品,登记进 `manifest.json` 的 `artifacts`,并写好其 meta。
- 文风润色(去AI味)只改文风、不改数据/公式/术语/引文/分条结论。

## 快速自查(交付前)
- [ ] 每张图都有 `.meta.json` 且能由脚本重跑?
- [ ] `data/processed` 里的东西都有对应脚本?
- [ ] `manifest.json` 的产出登记表与 `outputs/`、`figures/` 一致?
- [ ] 所有 `【待补/待核/润色存疑】` 已汇总在 `logs/worklog.md`?
- [ ] `env/requirements.txt` 已更新(便于换机器复现)?
"""

WORKLOG_TMPL = """# 工作日志 —— {name}

> 每个工作段落追加一条:时间、做了什么、关键决策/参数、产出、待补项。
> 这是"可审计"的核心:几个月后靠它复原"当时为什么这么做"。

## {today} 项目建立
- 建立标准项目结构。
- 待补:导入原始数据到 data/raw/,并为每个数据集写 .source.md。

---
<!-- 新条目追加到下方 -->
"""

SOURCE_TMPL = """# 数据来源说明(模板)

- 数据集名称:
- 来源(实测/数值模拟/文献/公开数据集):
- 采集或模拟条件(工况、时间、地点、设备/模型):
- 字段与单位:
- 已知问题/缺测:
- 关联脚本(谁清洗、谁用它):
"""

FIG_META_TMPL = {
    "figure": "fig_example.png",
    "title_zh": "",
    "title_en": "",
    "source_data": ["data/processed/xxx.csv"],
    "script": "scripts/plot_xxx.py",
    "params": {},
    "generated_at": "",
    "note": "示例 meta。真实图请由绘图脚本自动写出对应 .meta.json。",
}


def make_manifest(name, slug, author):
    return {
        "project": name,
        "slug": slug,
        "author": author,
        "created": datetime.now().isoformat(timespec="seconds"),
        "reproducibility": {
            "principle": "每个结果可追溯到 数据+脚本+参数;派生数据与图只由脚本生成。",
            "no_fabrication": "数据/图/结论非实测或计算得来,一律标【待补】,不编造。",
        },
        "artifacts": [],   # 产出登记表:{type, path, source_data, script, params, created}
        "pending": [],     # 待补/待核清单汇总
        "env": {"python": sys.version.split()[0]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="项目名称,如 '非恒定降雨城市路面颗粒物输移'")
    ap.add_argument("--dir", default=".", help="在哪个目录下建项目(默认当前目录)")
    ap.add_argument("--author", default="", help="负责人")
    args = ap.parse_args()

    slug = slugify(args.name)
    root = os.path.join(args.dir, f"{slug}_{date.today().isoformat()}")
    if os.path.exists(root):
        print(f"⚠ 目录已存在:{root}")
        sys.exit(1)
    for d in DIRS:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    ctx = {"name": args.name, "slug": slug, "author": args.author or "(未填)",
           "today": date.today().isoformat()}
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as f:
        f.write(README_TMPL.format(**ctx))
    with open(os.path.join(root, "logs", "worklog.md"), "w", encoding="utf-8") as f:
        f.write(WORKLOG_TMPL.format(**ctx))
    with open(os.path.join(root, "data", "raw", "_TEMPLATE.source.md"), "w",
              encoding="utf-8") as f:
        f.write(SOURCE_TMPL)
    with open(os.path.join(root, "figures", "_TEMPLATE.meta.json"), "w",
              encoding="utf-8") as f:
        json.dump(FIG_META_TMPL, f, ensure_ascii=False, indent=2)
    with open(os.path.join(root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(make_manifest(args.name, slug, args.author), f,
                  ensure_ascii=False, indent=2)
    with open(os.path.join(root, "env", "requirements.txt"), "w",
              encoding="utf-8") as f:
        f.write("# 用 `pip freeze > env/requirements.txt` 覆盖此文件以锁定复现环境\n")

    print(f"✓ 已创建可复现项目:{root}")
    print("  下一步:把原始数据放进 data/raw/ 并为每个数据集写 .source.md;")
    print("  之后每产出一张图/一份成品,登记进 manifest.json 并写好 meta。")


if __name__ == "__main__":
    main()
