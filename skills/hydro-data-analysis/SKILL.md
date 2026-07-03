---
name: hydro-data-analysis
description: >
  从水利/水电的原始实测或模拟数据算出可画、可写的特征参量与统计量:泥沙级配特征
  (d10/d30/d50/d60、不均匀系数)、冲刷深度随时间的发展拟合、幂律/通用曲线拟合、拟合与
  预测优度(R2/RMSE/NSE/相对误差)、水电调度指标(发电量/弃水/峰谷差)等。当用户要
  "分析这组数据/算一下/拟合/清洗数据/算特征参量/评估模型精度/统计",或有 csv/xlsx 数据
  需要处理成结论或图的输入时,使用本技能。它补上"原始数据→图与结论"之间的分析环节。
  只算真实数据、绝不编造;结果登记进项目工作区以保证可复现。
---

# 水利/水电数据分析

补上工作台里"原始数据 → 可画可写"之间的一环:清洗、统计、拟合、算特征参量。产出既可交
figure-composer 出图,也可写进结论。

## 铁律
- **只算真实数据**:输入必须是作者提供的实测/模拟数据。**绝不编造数据、不用随机数填充
  缺测、不外推臆造**。数据不足以算某量时,报错或返回 NaN 并说明,不"猜"。
- **可复现**:分析写成 `scripts/` 里的脚本(不在对话里手算),派生结果存 `data/processed/`,
  并登记进项目工作区(project-steward)。同一脚本重跑应得同一结果。
- **方法透明**:每个结果连同所用方法/参数一起报告;模型选择、异常值处理等由作者定,
  本技能给方法、不替作者定性。

## 工具(scripts/hydro_analysis.py)
```python
import sys; sys.path.insert(0, "scripts")
import hydro_analysis as ha
df = ha.load_table("data/raw/scour.csv")        # 读数据,不改原始文件
ha.describe(df)                                  # 基本统计摘要
```
主要函数:
- `grain_size_params(d_mm, pct_finer)` —— 级配特征:d10/d30/d50/d60、Cu、Cc(超范围不外推)。
- `fit_scour_development(t, ds)` —— 冲刷深度随时间:d_s(t)=d_se·(1−e^(−t/T)),给 d_se、T 及优度。
- `fit_power_law(x, y)` —— 幂律 y=a·x^b(冲刷深度~流速/桩径等)。
- `fit_curve(func, x, y, p0)` —— 通用曲线拟合。
- `goodness_of_fit(obs, pred)` —— R²、RMSE、MAE、NSE(Nash-Sutcliffe)、平均相对误差。
- `dispatch_metrics(power_mw, dt_h, spill_m3s, level_end, level_target)` —— 水电调度指标:
  发电量、峰谷差、弃水量、期末水位偏差。

需要其它分析(频率分析、显著性检验、相关分析等)时,用 numpy/scipy/pandas 现写脚本,
同样遵守上面的铁律并登记归档。

## 典型流程
1. 读原始数据(`load_table`),`describe` 看清量纲、缺测、异常。
2. 需要清洗时,写脚本生成 `data/processed/` 的派生数据(不手改原始),记录清洗规则。
3. 算特征参量 / 拟合 / 评估优度;把关键数值(如 d_se、T、R²、RMSE)记下来。
4. 把结果交 figure-composer 出图、写进结论;用 project-steward 的 register 登记脚本、
   派生数据与图,写好 meta,保证可追溯。
5. 报告时给出方法、参数、优度与样本量;不确定处标 `【待核】` 交作者确认。

## 与其他技能的配合
- 出图 → hydro-figure-composer(把算出的曲线/参量画成规范图)。
- 归档与复现 → hydro-project-steward(登记脚本、派生数据、图 meta)。
- 结果写进论文 → hydro-academic-writing(量化表达:给数据、区间、误差、样本量)。
