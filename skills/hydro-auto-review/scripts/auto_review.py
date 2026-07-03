#!/usr/bin/env python3
"""
auto_review.py —— 成稿后自动审查(只标问题,不改动)

对一个 project-steward 项目工作区做"机器可查"的硬伤扫描,输出分级报告。它是【审查者,
不是修改者】:只发现并定位问题,绝不自动改文稿。学术判断(创新点读不读得出、论证是否
充分)仍交给人和 hhu-thesis-review。

检查项:
  [可追溯]  figures/ 里的图缺同名 .meta.json(来源不明,不可信)
  [待补]    manifest.pending 未清零;drafts/outputs 里残留【待补/待核/润色存疑】标注
  [一致性]  manifest.artifacts 登记的产出文件在磁盘上找不到
  [AI味]    drafts 里残留高频中文学术 AI 腔(套话拔高、空转过渡、机械排比等)
  [格式]    drafts 里残留 AI 痕迹标点:成对花引号、表情符号、疑似滥用的破折号堆叠
  [复现]    env/requirements.txt 未锁定

用法:
  python3 auto_review.py --root <项目目录>
  python3 auto_review.py --root <项目目录> --out logs/review_report.md   # 另存报告
退出码:发现"硬伤"返回 1,否则 0(便于接入自动流程/定时任务)。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

# 中文学术高频 AI 腔(命中即提示用 hydro-deai-polish 顺一遍;非硬伤)
AI_PHRASES = [
    "综上所述", "总而言之", "总的来说", "由此可见", "不难看出", "值得注意的是",
    "需要指出的是", "众所周知", "具有重要的理论与现实意义", "具有重要意义",
    "发挥着重要作用", "扮演着重要的角色", "奠定了坚实的基础", "提供了新的思路",
    "随着", "在……的背景下", "日益受到广泛关注", "越来越受到重视",
    "进行了深入的研究", "进行了全面的分析", "值得一提的是", "不仅……而且",
]
PENDING_MARKERS = ["【待补", "【待核", "【润色存疑"]
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]")
CURLY = ["“", "”", "‘", "’"]
TEXT_EXT = (".md", ".txt", ".tex")


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _iter_text_files(root, subdirs=("drafts", "outputs")):
    for sub in subdirs:
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, _, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith(TEXT_EXT):
                    yield os.path.join(dirpath, fn)


def review(root):
    hard, advice, hint = [], [], []

    # [可追溯] 图缺 meta
    figdir = os.path.join(root, "figures")
    if os.path.isdir(figdir):
        for fn in os.listdir(figdir):
            if fn.lower().endswith((".png", ".svg", ".pdf")) and not fn.startswith("_"):
                meta = os.path.splitext(os.path.join(figdir, fn))[0] + ".meta.json"
                if not os.path.exists(meta):
                    hard.append(f"[可追溯] 图缺 meta,来源不明:figures/{fn}")

    # [待补] manifest.pending + 文稿标注
    mpath = os.path.join(root, "manifest.json")
    if os.path.exists(mpath):
        m = json.loads(_read(mpath) or "{}")
        if m.get("pending"):
            hard.append(f"[待补] manifest 仍有 {len(m['pending'])} 条待补/待核未清零")
        # [一致性] 登记的产出文件是否存在
        for art in m.get("artifacts", []):
            p = art.get("path", "")
            if p and not os.path.exists(os.path.join(root, p)):
                hard.append(f"[一致性] 清单登记的产出在磁盘找不到:{p}")
    for fp in _iter_text_files(root):
        txt = _read(fp)
        rel = os.path.relpath(fp, root)
        for mk in PENDING_MARKERS:
            if mk in txt:
                hard.append(f"[待补] {rel} 残留未处理标注:{mk}...】")
                break

    # [AI味] + [格式] 扫描文稿
    for fp in _iter_text_files(root):
        txt = _read(fp); rel = os.path.relpath(fp, root)
        hits = sorted({ph for ph in AI_PHRASES if ph.replace("……", "") in txt
                       or ph in txt})
        if hits:
            advice.append(f"[AI味] {rel} 命中中文 AI 腔 {len(hits)} 类"
                          f"(如 {', '.join(list(hits)[:4])}…)→ 建议用 hydro-deai-polish 顺一遍")
        if EMOJI.search(txt):
            advice.append(f"[格式] {rel} 含表情符号,学术文本应移除")
        if any(c in txt for c in CURLY):
            hint.append(f"[格式] {rel} 含成对花引号,按需统一为直角/直引号")
        if txt.count("——") >= 5:
            hint.append(f"[格式] {rel} 破折号较多({txt.count('——')} 处),核查是否 AI 式滥用")

    # [复现] env
    envf = os.path.join(root, "env", "requirements.txt")
    if not os.path.exists(envf) or os.path.getsize(envf) < 80:
        advice.append("[复现] env/requirements.txt 未锁定,换机器可能无法复现(建议 freeze)")

    return hard, advice, hint


def format_report(root, hard, advice, hint):
    lines = [f"# 自动审查报告", f"", f"- 项目:{root}",
             f"- 时间:{datetime.now():%Y-%m-%d %H:%M}",
             f"- 结论:{'发现硬伤,需处理' if hard else '未发现硬伤'}", ""]
    lines.append(f"## 硬伤(必须处理,共 {len(hard)})")
    lines += [f"- {x}" for x in hard] or ["- 无"]
    lines.append(f"\n## 建议(宜处理,共 {len(advice)})")
    lines += [f"- {x}" for x in advice] or ["- 无"]
    lines.append(f"\n## 提示(可选,共 {len(hint)})")
    lines += [f"- {x}" for x in hint] or ["- 无"]
    lines.append("\n> 本报告只标问题、不改文稿。学术判断(创新点、论证充分性)仍需人工与"
                 "hhu-thesis-review。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    hard, advice, hint = review(a.root)
    report = format_report(a.root, hard, advice, hint)
    print(report)
    if a.out:
        outp = os.path.join(a.root, a.out) if not os.path.isabs(a.out) else a.out
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        with open(outp, "w", encoding="utf-8") as f:
            f.write(report)
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
