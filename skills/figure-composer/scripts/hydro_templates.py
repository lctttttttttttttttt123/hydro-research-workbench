#!/usr/bin/env python3
"""
hydro_templates.py —— 水利/水电论文常见图型模板

每个函数把"真实数据"画成一张符合 hydro-figure-style 规范的图:
  - 中文题注/标签用宋体,英文与数字用 Times New Roman(或兼容体)
  - 变量斜体、上下标规范(经 mathtext 渲染)
  - 双语题注(中上英下)、色觉友好且黑白可辨的配色
这些是模板:把示例数据换成作者真实数据即可。绝不用编造数据冒充实测/计算结果。

直接运行会用"占位示例数据"各生成一张 demo 图,验证样式可跑通:
    python3 hydro_templates.py --outdir /tmp/figdemo
"""
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from hydro_style import (apply_style, bilingual_caption, multi_line_kwargs,
                         set_times_ticks, lab, save_pub, SEQUENTIAL, DIVERGING)


def _finish(fig, ax, zh, en, outpath):
    if isinstance(ax, (list, tuple, np.ndarray)):
        for a in np.ravel(ax):
            set_times_ticks(a)
    else:
        set_times_ticks(ax)
    bilingual_caption(fig, zh, en)
    # 同时导出 PNG(预览)+ SVG/PDF(可编辑矢量)。outpath 传入 .png 时自动去扩展名。
    base = outpath[:-4] if outpath.lower().endswith(".png") else outpath
    save_pub(fig, base, dpi=300)
    plt.close(fig)


def bed_scour_contour(X, Y, Z, zh, en, outpath, zlabel=None):
    """冲淤地形图/等值线云图。Z>0 淤积、Z<0 冲刷,发散配色以零线分色。"""
    apply_style()
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    vmax = np.nanmax(np.abs(Z))
    cf = ax.contourf(X, Y, Z, levels=21, cmap=DIVERGING, vmin=-vmax, vmax=vmax)
    ax.contour(X, Y, Z, levels=[0], colors="k", linewidths=0.8)
    ax.set_xlabel(lab("顺水流方向", "x", "cm"))
    ax.set_ylabel(lab("横向", "y", "cm"))
    ax.set_aspect("equal")
    cb = fig.colorbar(cf, ax=ax, shrink=0.85, pad=0.03)
    cb.set_label(zlabel or lab("床面冲淤", r"\Delta z", "cm"))
    for t in cb.ax.get_yticklabels():
        t.set_fontproperties(plt.matplotlib.font_manager.FontProperties(
            family=["Times New Roman", "Liberation Serif"]))
    _finish(fig, ax, zh, en, outpath)


def flow_field(X, Y, U, V, zh, en, outpath):
    """流场矢量图:背景填色为流速大小,叠加速度矢量。"""
    apply_style()
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    speed = np.sqrt(U**2 + V**2)
    pc = ax.pcolormesh(X, Y, speed, cmap=SEQUENTIAL, shading="auto")
    step = max(1, X.shape[0] // 18)
    ax.quiver(X[::step, ::step], Y[::step, ::step],
              U[::step, ::step], V[::step, ::step], width=0.004, color="k")
    ax.set_xlabel(lab("顺水流方向", "x", "cm"))
    ax.set_ylabel(lab("垂向", "z", "cm"))
    cb = fig.colorbar(pc, ax=ax, shrink=0.85, pad=0.03)
    cb.set_label(lab("流速", r"|U|", r"m{\cdot}s^{-1}"))
    for t in cb.ax.get_yticklabels():
        t.set_fontproperties(plt.matplotlib.font_manager.FontProperties(
            family=["Times New Roman", "Liberation Serif"]))
    _finish(fig, ax, zh, en, outpath)


def time_series(t, series, labels, zh, en, outpath,
                xlabel=None, ylabel=None):
    """时程/发展过程曲线:如冲刷深度随时间。多条曲线用线型+标记区分(黑白可辨)。"""
    apply_style()
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    for i, (y, l) in enumerate(zip(series, labels)):
        ax.plot(t, y, label=l, **multi_line_kwargs(i))
    ax.set_xlabel(xlabel or lab("时间", "t", "h"))
    ax.set_ylabel(ylabel or lab("冲刷深度", r"d_\mathrm{s}", "cm"))
    ax.legend()
    _finish(fig, ax, zh, en, outpath)


def grain_size_curve(d_mm, pct_finer, zh, en, outpath, d50=None):
    """泥沙级配曲线:横轴粒径(对数),纵轴小于某粒径百分数。"""
    apply_style()
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    ax.semilogx(d_mm, pct_finer, "-o", markersize=4)
    if d50 is not None:
        ax.axhline(50, color="0.6", lw=0.8, ls="--")
        ax.axvline(d50, color="0.6", lw=0.8, ls="--")
        ax.annotate(rf"$d_{{50}}$ = {d50:g} mm", (d50, 50),
                    textcoords="offset points", xytext=(6, 6))
    ax.set_xlabel(lab("粒径", "d", "mm"))
    ax.set_ylabel(lab("小于某粒径百分数", unit=r"\%"))
    ax.set_ylim(0, 100)
    _finish(fig, ax, zh, en, outpath)


def dispatch_curve(t_h, series, labels, zh, en, outpath,
                   xlabel=None, ylabel=None):
    """水电系统类:负荷分配/出力过程/库水位过程等调度曲线。"""
    apply_style()
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    for i, (y, l) in enumerate(zip(series, labels)):
        ax.step(t_h, y, where="mid", label=l,
                linestyle=["-", "--", "-.", ":"][i % 4])
    ax.set_xlabel(xlabel or lab("时间", "t", "h"))
    ax.set_ylabel(ylabel or lab("出力", "P", "MW"))
    ax.legend(ncol=2)
    _finish(fig, ax, zh, en, outpath)


def _demo(outdir):
    """占位示例数据各画一张,验证样式可跑通(带'(示例)',非真实结果)。"""
    os.makedirs(outdir, exist_ok=True)
    x = np.linspace(-20, 30, 120); y = np.linspace(-25, 25, 100)
    X, Y = np.meshgrid(x, y)
    Z = -8*np.exp(-((X)**2+(Y)**2)/120) + 2*np.exp(-((X-18)**2+Y**2)/200)
    bed_scour_contour(X, Y, Z,
        "图 3.1 平衡时期基础周围地形冲淤图(示例)",
        "Fig. 3.1 Bed scour and deposition around the foundation (demo)",
        os.path.join(outdir, "1_bed_scour.png"))

    xf = np.linspace(0, 30, 60); zf = np.linspace(0, 15, 40)
    Xf, Zf = np.meshgrid(xf, zf)
    U = 0.6*(1-np.exp(-Zf/4)); V = 0.05*np.sin(Xf/5)
    flow_field(Xf, Zf, U, V,
        "图 5.3 基础周围时均流场(示例)",
        "Fig. 5.3 Time-averaged flow field around the foundation (demo)",
        os.path.join(outdir, "2_flow_field.png"))

    t = np.linspace(0, 24, 60)
    s1 = 12*(1-np.exp(-t/4)); s2 = 8*(1-np.exp(-t/3))
    time_series(t, [s1, s2], ["高桩承台 HRSF", "单桩 Monopile"],
        "图 4.1 最大冲刷深度随时间的发展过程(示例)",
        "Fig. 4.1 Development of the maximum scour depth with time (demo)",
        os.path.join(outdir, "3_time_series.png"))

    d = np.array([0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0])
    pf = np.array([2, 8, 25, 50, 75, 92, 100])
    grain_size_curve(d, pf,
        "图 2.8 实验床沙粒径级配曲线(示例)",
        "Fig. 2.8 Grain size distribution of the bed material (demo)",
        os.path.join(outdir, "4_grain_size.png"), d50=0.5)

    th = np.arange(0, 24)
    p1 = 200+120*np.sin((th-6)/24*2*np.pi); p2 = 150+80*np.sin((th-8)/24*2*np.pi)
    dispatch_curve(th, [p1, p2], ["电站A Station A", "电站B Station B"],
        "图 5.6 梯级各电站小时级出力过程(示例)",
        "Fig. 5.6 Hourly power output of cascade stations (demo)",
        os.path.join(outdir, "5_dispatch.png"))
    print(f"已生成 5 张 demo 图到:{outdir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/tmp/figdemo")
    _demo(ap.parse_args().outdir)
