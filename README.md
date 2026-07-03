# 水利/水电科研写作工作台(Cowork 插件)

把"读文献 → 综述 → 谋篇 → 写作 → 制图 → 审稿 → 成文"整条水利科研流水线打包成一个
Cowork 插件。装一次即拥有全部 9 个 skill(8 个专项 + 1 个总协调),默认按中文水利期刊
与河海大学学位论文惯例。

## 安装
- Claude 桌面版 / Cowork:打开 Customize → Plugins,上传本插件文件(或本文件夹),即可。
- 装好后各 skill 自动触发;也可在对话里点 "+" 或输入 "/" 查看可用 skill。

## 包含的 skill
- **hydro-workflow** —— 总协调:大任务的流程规划与默认设定(中文为主),分派给下列专项。
- **academic-writing** —— 论文/申请书的结构范式与文风(三体裁、两范式、水利/水电)。
- **literature-review** —— 文献综述:分主题、述评结合、凝练缺口。
- **pdf-explore** —— 论文 PDF 勘察精读、抽取要点(带脚本)。
- **figure-style** —— 图表规范:双语题注、编号、字体、配色、导出。
- **figure-composer** —— 用代码出图,SVG/PDF/PNG 导出(带脚本)。
- **paper-narrative** —— 论文叙事逻辑与谋篇。
- **hhu-thesis-docx** —— 按河海大学格式生成 Word 成品(带脚本)。
- **hhu-thesis-review** —— 河海博士论文五部分分级审稿并出 Word(带脚本)。

## 默认约定(中文为主)
默认中文学位论文/期刊/申请书;制图用四边框 + 中文宋体 + 英文 Times New Roman + 变量
斜体 + 双语题注;参考文献 GB/T 7714;河海学位论文走 hhu-thesis-* 成文与审稿。投英文
SCI 时切到国际期刊风格(figure `frame="minimal"` 等)。**全局铁律:绝不编造,缺口标待补。**

## 来源与致谢
- figure-* 的配色与矢量导出部分改编自 figures4papers / nature-figure(Apache-2.0)。
- hhu-thesis-* 为河海大学专用 skill,源自 hhuthesis 模板与《河海大学学位论文编写格式规定》。
