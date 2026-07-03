#!/usr/bin/env python3
"""
hydro_style.py —— 水利/水电论文插图的 matplotlib 出版级样式与助手

导入即用:
    from hydro_style import apply_style, bilingual_caption, DIVERGING, SEQUENTIAL
    apply_style()                     # 应用出版样式 + 中文字体
    # 带上标的单位用 mathtext,避免 CJK 字体缺上标字符,例如:
    #   ax.set_ylabel(r"流速 $|U|$ / (m·s$^{-1}$)")
    fig, ax = plt.subplots()
    ...
    bilingual_caption(fig,
        "图 3.13 冲刷纵剖面随时间的变化过程",
        "Fig. 3.13 Variation of the scour longitudinal profile with time")
    fig.savefig("fig.png", dpi=300, bbox_inches="tight")

设计目标(对齐 hydro-figure-style 规范):
  - 中文可渲染(自动挑选系统里的 Noto/思源等 CJK 字体;找不到则告警并退回默认)
  - 双语题注(中文在上、英文在下,居中置于图下方)
  - 色觉友好、黑白可辨的默认配色
  - 坐标/线宽/字号等出版参数
"""
import warnings
import logging
import matplotlib
matplotlib.use("Agg")  # 无显示环境
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 静音 findfont 的回退提示:本机若无 Times New Roman 会回退到度量兼容的 Liberation
# Serif(外观一致);在装有 Times New Roman 的机器(如 Windows)上会直接使用 TNR。
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# 色觉友好配色:顺序场用 viridis,正负发散量用 RdBu_r
SEQUENTIAL = "viridis"
DIVERGING = "RdBu_r"
# 多曲线线型循环(保证黑白可辨)
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]
MARKERS = ["o", "s", "^", "D", "v", "x"]

# ── 语义化调色板(改编自 figures4papers / nature-figure, Apache-2.0) ──
# 用于"多序列对比"类曲线/柱状图。原则:同族保持一致、对比对象用暖色、主对象用冷色、
# 中性色作参照。物理场(流速/涡量/紊动)仍用上面的感知均匀 colormap,不用这里的离散色。
HYDRO_PALETTE = {
    # 主对象(如本文提出的结构/方法、重点工况)——深冷色
    "main_dark":   "#0F4D92",   # 深蓝,主对象
    "main_mid":    "#3775BA",   # 中蓝,次要主对象
    # 对比对象(如单桩、常规方法、基准工况)——暖色
    "cmp_strong":  "#B64342",   # 深红,主要对比
    "cmp_soft":    "#E9A6A1",   # 浅红
    # 正向/增益(如改善、达标)——绿;负向/下降——红
    "up":          "#2E9E44",
    "down":        "#E53935",
    # 中性/参照/背景
    "neutral_light": "#CFCECE",
    "neutral_mid":   "#767676",
    "neutral_dark":  "#4D4D4D",
    # 点缀(少量使用)
    "teal":   "#42949E",
    "violet": "#9A4D8E",
    "gold":   "#FFD700",
}
# 色盲友好、黑白打印可辨的默认离散色序(多序列曲线/柱状按此取色)
DEFAULT_COLORS = ["#0F4D92", "#B64342", "#2E9E44", "#42949E", "#9A4D8E", "#767676"]
# 灰度打印时的填充线纹(柱状/面积区分,不依赖颜色)
HATCHES = ["/", "\\", ".", "x", "o", "+"]


def _find_cjk_font():
    """在系统字体里找一个可用的中文【衬线】字体族名(宋体类,与 Times 搭配)。"""
    prefer = ["Noto Serif CJK SC", "Source Han Serif SC", "Noto Serif CJK JP",
              "SimSun", "STSong", "Noto Sans CJK SC", "WenQuanYi Zen Hei"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in prefer:
        if name in available:
            return name
    for f in font_manager.fontManager.ttflist:
        if any(k in f.name for k in ("CJK", "Han", "Song", "Hei")):
            return f.name
    return None


# 英文/数字的 Times New Roman 及其兼容替代(Liberation Serif 与 TNR 度量兼容)
_LATIN_SERIF = ["Times New Roman", "Liberation Serif", "Nimbus Roman",
                "FreeSerif", "DejaVu Serif"]


def apply_style(frame="box"):
    """应用出版级 rcParams。
    字体约定(中文期刊惯例):
      - 中文 → 宋体类衬线体;英文/数字 → Times New Roman(或度量兼容的 Liberation Serif);
      - 变量斜体、上下标规范 → 用 mathtext(stix,Times 风格)渲染。
    frame:
      - "box"(默认)→ 四边框 + 内向刻度,符合中文水利期刊(如水利学报)惯例;
      - "minimal" → 仅左/下边框、无上/右框,符合部分国际期刊(Nature 风格)。
    矢量导出:默认设 svg.fonttype='none'、pdf.fonttype=42,保证 SVG/PDF 文本可在
    Illustrator/Inkscape 里编辑(改编自 nature-figure, Apache-2.0)。
    实现要点见下;返回所用中文字体名(或 None)。"""
    cjk = _find_cjk_font()
    serif_stack = ([cjk] if cjk else []) + _LATIN_SERIF  # 中文优先
    if not cjk:
        warnings.warn("未找到中文字体,中文可能显示为方块。请安装 Noto Serif CJK / 宋体。")
    minimal = (frame == "minimal")
    rc = {
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "font.family": "serif",
        "font.serif": serif_stack,
        "mathtext.fontset": "stix",      # 变量斜体、上下标,Times 风格
        "svg.fonttype": "none",          # SVG 文本保持为可编辑 <text> 节点
        "pdf.fonttype": 42,              # PDF 内嵌可编辑 TrueType 文本
        "axes.prop_cycle": plt.cycler(color=DEFAULT_COLORS),  # 色盲友好默认色序
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.linewidth": 0.9,
        "lines.linewidth": 1.6,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": not minimal,
        "ytick.right": not minimal,
        "axes.spines.top": not minimal,
        "axes.spines.right": not minimal,
        "axes.grid": False,
        "legend.frameon": False,
        "figure.autolayout": False,
        "axes.unicode_minus": False,
    }
    matplotlib.rcParams.update(rc)
    return cjk


# 刻度数字强制使用的 Times 字体族(Times New Roman 或兼容替代)
_TIMES_FP = font_manager.FontProperties(family=_LATIN_SERIF)


def set_times_ticks(ax):
    """把坐标轴刻度数字强制为 Times New Roman(或兼容体)。每张图画完后调用一次。"""
    for lab_ in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lab_.set_fontproperties(_TIMES_FP)


def lab(zh, var=None, unit=None):
    """构造中文期刊风格的坐标轴标签:中文在外(宋体),变量与单位在 mathtext 内
    (变量 Times 斜体、单位 Times 正体)。
      lab("冲刷深度", r"d_\\mathrm{s}", "cm")  -> '冲刷深度 $d_\\mathrm{s}\\ /\\ \\mathrm{cm}$'
      lab("小于某粒径百分数", unit=r"\\%")       -> 只有单位
    unit 可写 mathtext 片段(如 r'm{\\cdot}s^{-1}')。"""
    if var and unit:
        return rf"{zh} ${var}\ /\ \mathrm{{{unit}}}$"
    if var:
        return rf"{zh} ${var}$"
    if unit:
        return rf"{zh} $/\ \mathrm{{{unit}}}$"
    return zh


def var(name):
    """把变量名包成 mathtext 斜体。"""
    return f"${name}$"


def bilingual_caption(fig, zh, en, y=-0.02):
    """在图下方居中放置双语题注:中文在上(宋体)、英文在下(Times)。
    调用前确保已 apply_style();保存时用 bbox_inches='tight' 以免裁掉题注。"""
    fig.text(0.5, y, zh, ha="center", va="top", fontsize=10.5)
    fig.text(0.5, y - 0.05, en, ha="center", va="top", fontsize=9.5,
             style="italic", fontproperties=font_manager.FontProperties(
                 family=_LATIN_SERIF, style="italic"))


def multi_line_kwargs(i):
    """给第 i 条曲线返回线型+标记,保证黑白可辨。"""
    return dict(linestyle=LINESTYLES[i % len(LINESTYLES)],
                marker=MARKERS[i % len(MARKERS)], markersize=4, markevery=0.15)


# ── 出版导出与实用助手(部分改编自 nature-figure, Apache-2.0) ──
import os


def save_pub(fig, path_no_ext, dpi=300, formats=("png", "svg", "pdf")):
    """按出版要求导出:SVG(文本可编辑)、PDF(矢量)、PNG(位图预览)。
    传入不含扩展名的路径,如 save_pub(fig, "figures/fig4-1")。
    SVG/PDF 为矢量且文本可在 Illustrator/Inkscape 里对齐编辑(依赖 apply_style 设置的
    svg.fonttype='none'、pdf.fonttype=42);投稿密集多子图柱状图可将 dpi 提到 600。"""
    d = os.path.dirname(path_no_ext)
    if d:
        os.makedirs(d, exist_ok=True)
    for fmt in formats:
        kw = {"bbox_inches": "tight"}
        if fmt == "png":
            kw["dpi"] = dpi
        fig.savefig(f"{path_no_ext}.{fmt}", **kw)
    return [f"{path_no_ext}.{fmt}" for fmt in formats]


def text_contrast(rgb):
    """按背景亮度返回可读文字颜色('black'/'white')。用于在色块/柱内标注数值。
    rgb 为 0~1 的 (r,g,b) 或 (r,g,b,a)。"""
    r, g, b = rgb[0], rgb[1], rgb[2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return "white" if lum < 0.5 else "black"


def tighten_ylim(ax, data, margin_frac=0.08):
    """把 y 轴范围收紧到数据范围(留边距),避免数值集中在窄带时用 0~100 造成"看不出差异"。
    data 为一维数组或多序列的并集。"""
    import numpy as np
    arr = np.asarray(data, dtype=float)
    lo, hi = np.nanmin(arr), np.nanmax(arr)
    m = (hi - lo) * margin_frac or abs(hi) * margin_frac or 1.0
    ax.set_ylim(lo - m, hi + m)


def uncertainty_band(ax, x, y, err, color=None, alpha=0.15, **line_kw):
    """画均值曲线 + 不确定性带(如 ±标准差 / 置信区间)。带的 alpha 保持低(0.1~0.2),
    以免盖过主曲线。err 可为标量或与 y 等长的数组。"""
    import numpy as np
    x = np.asarray(x); y = np.asarray(y); err = np.asarray(err)
    (ln,) = ax.plot(x, y, color=color, **line_kw)
    c = ln.get_color()
    ax.fill_between(x, y - err, y + err, color=c, alpha=alpha, linewidth=0)
    return ln


def reference_line(ax, value, axis="y", label=None):
    """画参照基线(如临界值、设计标准、平衡值),虚线、淡化,不抢主数据。"""
    kw = dict(linestyle="--", linewidth=1.0, color="#767676", alpha=0.7)
    (ax.axhline if axis == "y" else ax.axvline)(value, **kw)
    if label:
        if axis == "y":
            ax.text(ax.get_xlim()[1], value, f" {label}", va="center",
                    ha="left", fontsize=9, color="#4D4D4D")
