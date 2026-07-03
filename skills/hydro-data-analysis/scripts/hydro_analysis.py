#!/usr/bin/env python3
"""
hydro_analysis.py —— 水利/水电常用数据分析模板

从原始实测/模拟数据算出"可画、可写"的特征参量与统计量。配 figure-composer 出图、
project-steward 归档。设计原则:

  1. 只算【真实数据】,绝不编造或用随机数填充缺测。缺数据就报错或返回 NaN 并说明,
     不"猜"。
  2. 每个函数返回结构化结果(含所用方法/参数),便于登记进项目工作区、保证可复现。
  3. 不确定的模型选择、异常值处理等,交由使用者决定;本模块给方法、不替作者定性。

含:
  load_table              读 csv/tsv/xlsx 为 DataFrame(不改原始数据)
  describe                基本统计摘要
  grain_size_params       泥沙级配特征:d10/d30/d50/d60、不均匀系数 Cu、曲率系数 Cc
  fit_scour_development   冲刷深度随时间的指数逼近拟合 d_s(t)=d_se*(1-exp(-t/T))
  fit_power_law           幂律拟合 y = a * x^b(常用于冲刷深度~流速/直径等关系)
  fit_curve               通用曲线拟合(传入自定义函数)
  goodness_of_fit         拟合/预测优度:R2、RMSE、MAE、NSE(Nash-Sutcliffe)、平均相对误差
  dispatch_metrics        水电调度类指标:发电量、弃水率、峰谷差、期末水位偏差
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy import interpolate


def load_table(path, **kw):
    """读 csv/tsv/xlsx。不修改原始文件。"""
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path, **kw)
    sep = "\t" if path.lower().endswith(".tsv") else ","
    return pd.read_csv(path, sep=sep, **kw)


def describe(df, cols=None):
    """基本统计摘要(计数、均值、标准差、极值、分位数)。"""
    d = df[cols] if cols else df
    return d.describe().to_dict()


def grain_size_params(d_mm, pct_finer):
    """泥沙级配特征参数。d_mm: 粒径(mm),pct_finer: 小于该粒径的百分数(%)。
    用对数粒径上的单调插值求 d10/d30/d50/d60,并算 Cu=d60/d10、Cc=d30^2/(d10*d60)。
    要求数据覆盖到所需百分位,否则该分位返回 NaN 并在 note 里说明,不外推臆造。"""
    d = np.asarray(d_mm, float); p = np.asarray(pct_finer, float)
    order = np.argsort(p)
    p, d = p[order], d[order]
    logd = np.log10(d)
    notes = []

    def dx(x):
        if x < p.min() or x > p.max():
            notes.append(f"d{int(x)} 超出数据范围({p.min():.0f}%~{p.max():.0f}%),未外推")
            return float("nan")
        return float(10 ** np.interp(x, p, logd))

    d10, d30, d50, d60 = dx(10), dx(30), dx(50), dx(60)
    cu = d60 / d10 if d10 and not np.isnan(d10) and not np.isnan(d60) else float("nan")
    cc = (d30 ** 2) / (d10 * d60) if all(not np.isnan(v) and v for v in (d10, d30, d60)) else float("nan")
    return {"d10": d10, "d30": d30, "d50": d50, "d60": d60,
            "Cu": cu, "Cc": cc, "method": "对数粒径线性插值", "notes": notes}


def fit_scour_development(t, ds):
    """冲刷深度随时间的指数逼近拟合:d_s(t) = d_se * (1 - exp(-t/T))。
    返回平衡冲刷深度 d_se、时间尺度 T 及拟合优度。t、ds 为等长数组(真实实测/模拟值)。"""
    t = np.asarray(t, float); ds = np.asarray(ds, float)
    if len(t) < 3:
        return {"error": "数据点少于 3,无法拟合"}

    def model(tt, dse, T):
        return dse * (1 - np.exp(-tt / T))

    p0 = [np.nanmax(ds), max(np.nanmax(t) / 3, 1e-6)]
    popt, pcov = curve_fit(model, t, ds, p0=p0, maxfev=10000)
    pred = model(t, *popt)
    gof = goodness_of_fit(ds, pred)
    perr = np.sqrt(np.diag(pcov))
    return {"model": "d_s = d_se*(1-exp(-t/T))",
            "d_se": float(popt[0]), "T": float(popt[1]),
            "param_std": {"d_se": float(perr[0]), "T": float(perr[1])},
            "goodness": gof}


def fit_power_law(x, y):
    """幂律拟合 y = a * x^b(如冲刷深度与流速、桩径的关系)。"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3:
        return {"error": "数据点少于 3,无法拟合"}

    def model(xx, a, b):
        return a * np.power(xx, b)

    popt, pcov = curve_fit(model, x, y, p0=[1.0, 1.0], maxfev=10000)
    pred = model(x, *popt)
    return {"model": "y = a*x^b", "a": float(popt[0]), "b": float(popt[1]),
            "goodness": goodness_of_fit(y, pred)}


def fit_curve(func, x, y, p0=None):
    """通用曲线拟合。func 为 f(x, *params);返回参数、协方差与优度。"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    popt, pcov = curve_fit(func, x, y, p0=p0, maxfev=10000)
    pred = func(x, *popt)
    return {"params": [float(v) for v in popt],
            "param_std": [float(v) for v in np.sqrt(np.diag(pcov))],
            "goodness": goodness_of_fit(y, pred)}


def goodness_of_fit(obs, pred):
    """拟合/预测优度:R2、RMSE、MAE、NSE(Nash-Sutcliffe 效率系数)、平均相对误差(%)。
    obs 实测/参考值,pred 拟合/预测值,等长。"""
    obs = np.asarray(obs, float); pred = np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    obs, pred = obs[mask], pred[mask]
    n = len(obs)
    if n < 2:
        return {"error": "有效点不足"}
    resid = pred - obs
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((obs - obs.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    mae = float(np.mean(np.abs(resid)))
    nse = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")  # 与 R2 同式,水文习惯单列
    nz = obs != 0
    mre = float(np.mean(np.abs(resid[nz] / obs[nz])) * 100) if nz.any() else float("nan")
    return {"n": int(n), "R2": float(r2), "RMSE": rmse, "MAE": mae,
            "NSE": float(nse), "mean_rel_err_%": mre}


def dispatch_metrics(power_mw, dt_h=1.0, spill_m3s=None, level_end=None, level_target=None):
    """水电调度类指标(用真实调度/出力序列)。
    power_mw: 各时段出力(MW);dt_h: 时段长(h);spill_m3s: 各时段弃水流量(可选);
    level_end/level_target: 期末水位与目标水位(可选)。"""
    p = np.asarray(power_mw, float)
    energy = float(np.sum(p) * dt_h)                     # 总发电量 MW·h
    res = {"total_energy_MWh": energy,
           "peak_MW": float(np.nanmax(p)), "valley_MW": float(np.nanmin(p)),
           "peak_valley_diff_MW": float(np.nanmax(p) - np.nanmin(p)),
           "mean_MW": float(np.nanmean(p))}
    if spill_m3s is not None:
        s = np.asarray(spill_m3s, float)
        res["total_spill_m3"] = float(np.sum(s) * dt_h * 3600)
    if level_end is not None and level_target is not None:
        res["level_end_dev_m"] = float(level_end - level_target)
    return res


def _selftest():
    print("== 级配 ==")
    d = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]; p = [2, 8, 25, 50, 75, 92, 100]
    print(grain_size_params(d, p))
    print("== 冲刷发展拟合 ==")
    t = np.linspace(0, 24, 30); ds = 12 * (1 - np.exp(-t / 4)) + np.random.default_rng(0).normal(0, 0.1, 30)
    r = fit_scour_development(t, ds); print({k: r[k] for k in ("d_se", "T")}, r["goodness"])
    print("== 优度 ==")
    print(goodness_of_fit([1, 2, 3, 4], [1.1, 1.9, 3.2, 3.8]))
    print("== 调度指标 ==")
    print(dispatch_metrics([200, 260, 180, 320], dt_h=1, level_end=145.2, level_target=145.0))


if __name__ == "__main__":
    _selftest()
