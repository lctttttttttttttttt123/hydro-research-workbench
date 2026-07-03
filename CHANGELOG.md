# Changelog

## [1.1.0] — 2026-07-03

### ✨ 新增

- **humanizer-zh** — 中文文本"去 AI 味"引擎:检测并修复 24 种 AI 写作模式(意义拔高、宣传腔、破折号滥用、三段式、AI 词汇等),带 5 维度质量评分
- **hydro-deai-polish** — 水利学术"去 AI 味"润色层:以中性学术模式驱动 humanizer-zh,关闭个性注入,硬保护数据/公式/术语/引文/图表题注与分条量化结论。定位在写作+制图+审稿完成后、出 Word 前的最后一道文字工序

### 🔄 更新

- **hydro-workflow** — 流程链新增第 7 步"去 AI 味润色 → hydro-deai-polish",成文推为第 8 步;新增 Sci-Hub 禁令条款(全文只走合法 OA 或学校授权渠道)
- **academic-writing** — SKILL.md 补全 references 模板引用路径(domain-terms / genre-dissertation / genre-journal / genre-grant / style-conventions);交付格式新增"成文前去 AI 味润色"环节

### 🗺️ 完整流程 (v1.1)

读文献 → 综述 → 谋篇 → 写作 → 制图 → 审稿 → **去 AI 味润色** → 成文

---

## [1.0.0] — 2026-07-03

### 🎉 首次发布

9 个 skill 的首个完整版本,覆盖水利/水电科研写作全流程:

- **hydro-workflow** — 总协调:大任务的流程规划、默认约定与 skill 分派
- **academic-writing** — 论文/申请书的结构范式与文风(三体裁:学位论文/期刊/基金)
- **literature-review** — 文献综述:分主题、述评结合、凝练缺口
- **pdf-explore** — 论文 PDF 勘察精读(带 hydro_pdf_probe.py 脚本)
- **figure-style** — 图表规范:双语题注、编号、字体、配色、导出
- **figure-composer** — 代码出图(带 hydro_style.py / hydro_templates.py 脚本)
- **paper-narrative** — 论文叙事逻辑与谋篇
- **hhu-thesis-docx** — 按河海大学学位论文格式生成 Word
- **hhu-thesis-review** — 河海博士论文五部分分级审稿并出 Word

默认按中文水利期刊与河海大学学位论文惯例(Times New Roman + 宋体、四边框、双语题注、GB/T 7714 顺序编码制)。
