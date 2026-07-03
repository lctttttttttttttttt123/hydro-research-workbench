#!/usr/bin/env python3
"""
hydro_pdf_probe.py —— 水利/水电论文 PDF 快速勘察工具

用途:对一篇学位论文/期刊论文/申请书 PDF,一次性输出可供 Claude 快速定位的"地图":
  - 基本信息(页数、大小、是否有文字层)
  - 章节结构(第X章 / n.n 小节标题及其所在页)
  - 图表清单(图 X.X / 表 X.X 题注)
  - 关键区块定位(摘要/ABSTRACT/目录/参考文献/结论 的大致页码)

用法:
  python3 hydro_pdf_probe.py <paper.pdf>
  python3 hydro_pdf_probe.py <paper.pdf> --dump-text out.txt   # 另存全文文字层

说明:仅做"勘察",不改动 PDF。抽取到的页码用于后续用 pdftotext -f/-l 精读某几页,
或用 pdftoppm 把含图公式的页转成图片交给视觉阅读。绝不臆造未在文中出现的内容。
"""
import re
import sys
import subprocess
import argparse


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except Exception as e:
        return f"[命令失败:{e}]"


def pdf_info(path):
    out = run(["pdfinfo", path])
    keep = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip() in ("Pages", "Page size", "Title", "Author", "File size"):
                keep[k.strip()] = v.strip()
    return keep


def full_text(path):
    # -layout 保留版式,便于识别标题缩进和页码
    return run(["pdftotext", "-layout", path, "-"])


# 章节标题:第X章 …… / n.n …… / n.n.n ……(排除图表行)
CHAP = re.compile(r"^\s*第[一二三四五六七八九十百]+章")
SEC = re.compile(r"^\s*\d+\.\d+(\.\d+)?\s+\S")
FIGTAB = re.compile(r"^\s*(图|表|Fig\.?|Table)\s*\d")
# 关键区块
BLOCKS = {
    "摘要": re.compile(r"^\s*摘\s*要\s*$"),
    "ABSTRACT": re.compile(r"^\s*ABSTRACT\s*$", re.I),
    "目录": re.compile(r"^\s*目\s*录\s*$"),
    "参考文献": re.compile(r"^\s*参\s*考\s*文\s*献\s*$"),
    "结论": re.compile(r"(结论与展望|总结与展望|主要结论)"),
    "关键词": re.compile(r"^\s*关键词[:：]"),
    "创新点": re.compile(r"创新点主要体现"),
    "技术路线": re.compile(r"技术路线"),
    "研究区概况": re.compile(r"研究区概况"),
    "应用实例": re.compile(r"应用实例"),
}


def analyze(text):
    # pdftotext 用 \f 分页,据此计算页码
    pages = text.split("\f")
    chapters, sections, figtabs = [], [], []
    blocks = {k: [] for k in BLOCKS}
    for pno, page in enumerate(pages, 1):
        for line in page.splitlines():
            s = line.rstrip()
            if not s.strip():
                continue
            if CHAP.match(s):
                chapters.append((pno, s.strip()))
            elif SEC.match(s) and not FIGTAB.match(s):
                sections.append((pno, s.strip()[:60]))
            if FIGTAB.match(s):
                figtabs.append((pno, s.strip()[:70]))
            for name, pat in BLOCKS.items():
                if pat.search(s):
                    blocks[name].append(pno)
    return pages, chapters, sections, figtabs, blocks


def dedup_pages(d):
    return {k: sorted(set(v)) for k, v in d.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dump-text", default=None)
    ap.add_argument("--max-sections", type=int, default=80)
    ap.add_argument("--max-figtabs", type=int, default=60)
    args = ap.parse_args()

    info = pdf_info(args.pdf)
    text = full_text(args.pdf)
    if args.dump_text:
        with open(args.dump_text, "w") as f:
            f.write(text)

    pages, chapters, sections, figtabs, blocks = analyze(text)
    blocks = dedup_pages(blocks)

    print("=" * 60)
    print("【基本信息】")
    for k, v in info.items():
        print(f"  {k}: {v}")
    has_text = len(text.strip()) > 200
    print(f"  文字层: {'有' if has_text else '无(可能为扫描件,需 pdftoppm 转图片阅读)'}")

    print("\n【关键区块页码】(用于 pdftotext -f/-l 精读)")
    for k in ["摘要", "ABSTRACT", "关键词", "目录", "技术路线", "研究区概况",
              "创新点", "应用实例", "结论", "参考文献"]:
        if k in blocks:
            print(f"  {k}: 第 {', '.join(map(str, blocks[k][:8]))} 页")

    print(f"\n【章标题】(共 {len(chapters)} 处)")
    for pno, t in chapters[:30]:
        print(f"  p{pno:>3}  {t}")

    print(f"\n【小节标题】(显示前 {args.max_sections},共 {len(sections)} 处)")
    for pno, t in sections[:args.max_sections]:
        print(f"  p{pno:>3}  {t}")

    print(f"\n【图表题注】(显示前 {args.max_figtabs},共 {len(figtabs)} 处)")
    for pno, t in figtabs[:args.max_figtabs]:
        print(f"  p{pno:>3}  {t}")

    print("\n" + "=" * 60)
    print("下一步建议:")
    print("  • 精读某节:pdftotext -layout -f <起页> -l <止页> file.pdf -")
    print("  • 看含图/公式的页:pdftoppm -jpeg -r 150 -f <页> -l <页> file.pdf /tmp/p")
    print("    然后用视觉方式阅读 /tmp/p-*.jpg")


if __name__ == "__main__":
    main()
