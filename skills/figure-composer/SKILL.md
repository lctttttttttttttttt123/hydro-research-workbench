---
name: hydro-figure-composer
description: >
  用代码为水利/水电论文生成符合本领域规范的出版级插图:冲淤地形图、流场矢量图、涡量/紊动
  分布、冲刷深度等时程曲线、泥沙级配曲线、梯级调度/负荷/出力曲线等,自动带双语题注、规范
  坐标与色觉友好配色。当用户要"画一张/生成/绘制 XX 图""把这些数据做成图""重画这张图""做
  论文插图"时,务必使用本技能。它内置了已测试可用的 matplotlib 样式(含中文字体)与常见
  图型模板,只需把真实数据填入即可出图。
---

# 水利/水电论文插图生成

## 做什么
把作者的**真实数据**画成符合 hydro-figure-style 规范的出版级插图。内置一套已测试的
matplotlib 样式(中文字体、双语题注、色觉友好配色、出版参数)和常见水利/水电图型模板。

## 铁律:只画真实数据
图是用来支撑结论的证据。**绝不用编造/随机数据冒充实测或计算结果**。作者未提供数据时,
向作者索取,或标 `【待补:此图需作者提供 XX 数据】`,不要"先随便画一张占位"当成结果。
脚本里的 demo 数据仅用于自检样式,带"(示例)"字样,不得混入正式成果。

## 怎么用

样式模块 `scripts/hydro_style.py` 与图型模板 `scripts/hydro_templates.py`。基本用法:

```python
import sys; sys.path.insert(0, "scripts")
from hydro_style import (apply_style, bilingual_caption, lab, set_times_ticks,
                         SEQUENTIAL, DIVERGING)
import matplotlib.pyplot as plt

apply_style()                       # 出版样式:中文宋体 + 英文/数字 Times + 变量斜体
fig, ax = plt.subplots(figsize=(5.2, 3.8))
ax.plot(t, ds, "-o", markersize=4)  # ← 换成作者真实数据
ax.set_xlabel(lab("时间", "t", "h"))               # 中文正体 + 变量斜体 + 单位正体
ax.set_ylabel(lab("冲刷深度", r"d_\mathrm{s}", "cm"))  # 下标 s 正体
set_times_ticks(ax)                 # 刻度数字强制 Times
bilingual_caption(fig,
    "图 4.1 最大冲刷深度随时间的发展过程",
    "Fig. 4.1 Development of the maximum scour depth with time")
fig.savefig("fig4-1.png", dpi=300, bbox_inches="tight")  # 题注在图外,务必 tight
```

### 字体与变量约定(已内置)
- 中文 → 宋体类;英文/数字 → Times New Roman(本机若无则自动回退到度量兼容的
  Liberation Serif,外观一致;装有 TNR 的机器如 Windows 会直接用 TNR)。
- **变量斜体、下标规范**:用 `lab(中文, 变量, 单位)` 或直接写 mathtext(`$d_\mathrm{s}$`)。
  变量放 `$...$` 内即斜体;描述性下标用 `\mathrm{}` 保持正体(`d_\mathrm{s}`、`U_\mathrm{c}`),
  数字下标直接写(`d_{50}`)。
- 每张图画完调用 `set_times_ticks(ax)`,把刻度数字设为 Times。

## 配色与导出助手(在 hydro_style.py 中)
- `DEFAULT_COLORS` / `HYDRO_PALETTE` —— 色盲友好的语义化离散色序与命名色板(主对象冷色、
  对比对象暖色、增益/下降绿红、中性色)。多序列曲线/柱状默认已用此色序;需点名取色时用
  `HYDRO_PALETTE["main_dark"]` 等。物理场仍用 `SEQUENTIAL`/`DIVERGING` colormap。
- `save_pub(fig, "figures/fig4-1")` —— 一次导出 SVG(文本可编辑)+ PDF(矢量)+ PNG(300dpi)。
  **投稿优先交 SVG/PDF。**
- `tighten_ylim(ax, data)` —— 数值集中窄带时收紧 y 轴范围以显出差异。
- `uncertainty_band(ax, x, y, err)` —— 均值曲线 + 低透明度不确定性带(±标准差/置信区间)。
- `reference_line(ax, value)` —— 画临界值/设计标准/平衡值的淡化虚线基线。
- `text_contrast(rgb)` —— 按背景亮度返回黑/白文字色,用于柱内/色块内标注数值。
- `apply_style(frame="box")` —— 默认四边框(中文水利期刊惯例);`frame="minimal"` 切到
  仅左/下边框的国际期刊风格。
- `HATCHES` —— 灰度打印时柱状/面积的填充线纹,配色之外再加一层可辨性。

## 现成图型模板(在 hydro_templates.py 中)
把示例数据换成作者真实数据即可调用:
- `bed_scour_contour(X, Y, Z, ...)` —— 冲淤地形图/等值线云图(发散配色 + 零冲淤线)。
- `flow_field(X, Y, U, V, ...)` —— 流场矢量图(背景流速填色 + 速度矢量)。
- `time_series(t, [y1, y2], labels, ...)` —— 时程/发展过程曲线(线型+标记,黑白可辨)。
- `grain_size_curve(d_mm, pct_finer, ..., d50=...)` —— 泥沙级配曲线(对数横轴)。
- `dispatch_curve(t_h, [P1, P2], labels, ...)` —— 梯级调度/负荷/出力/库水位过程曲线。

涡量、紊动强度、TKE 等分布,用 `flow_field` 的填色思路换数据与色标即可(正负量用
`DIVERGING`,强度类用 `SEQUENTIAL`)。

## 自检
先跑一次 demo 确认环境与样式正常(会用占位示例数据出 5 张图):
```bash
cd scripts && python3 hydro_templates.py --outdir /tmp/figdemo
```
若提示缺中文字体,则安装 Noto Sans CJK / 思源黑体后重试;带上标单位用 mathtext
(`$^{-1}$`)可避免个别 CJK 字体缺上标字符。

## 规范一致性
出图前后对照 hydro-figure-style:双语题注(中上英下)、章.序编号、坐标含物理量与单位、
变量斜体、配色色觉友好且黑白可辨、导出 ≥300 dpi。图放进论文时须"先引后现·每图必解读"。

## 与其他技能的配合
- 规范定义在 hydro-figure-style;本技能是其代码实现。
- 数据来自 PDF 里的旧图 → 先用 hydro-pdf-explore 读出数据再重画。
- 图配文字解读、放进论文 → hydro-academic-writing / hydro-paper-narrative。

## 致谢与来源
配色原则、语义化色板与矢量导出策略部分改编自开源项目 figures4papers / nature-figure(Apache-2.0),并按中文水利期刊惯例调整(Times New Roman + 宋体、四边框可选、双语题注、变量斜体等)。
