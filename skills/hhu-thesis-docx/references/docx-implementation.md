# python-docx 实现关键点

河海格式有几个 python-docx 不直接支持、必须操作 XML 的点。逐条照做可避免返工。

## 1. 中文字体必须设置 eastAsia

只设 `run.font.name` 只影响西文。中文需要额外设置 `w:eastAsia`，否则 Word 中中文回落为默认字体：

```python
from docx.oxml.ns import qn

def set_run_font(run, zh_font='宋体', en_font='Times New Roman', size_pt=12, bold=False):
    run.font.name = en_font                     # 西文字体
    run._element.rPr.rFonts.set(qn('w:eastAsia'), zh_font)  # 中文字体
    run.font.size = Pt(size_pt)
    run.font.bold = bold
```

对样式同样处理：`style.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')`。
标准字体名：宋体、黑体、仿宋_GB2312（或 仿宋）、楷体_GB2312。

## 2. 固定行距 20 磅

```python
from docx.enum.text import WD_LINE_SPACING
pf = paragraph.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
pf.line_spacing = Pt(20)
```

注意固定 20 磅行距下，超过 20pt 高的内嵌图片会被裁剪——**包含图片的段落必须改为单倍行距**。

## 3. 首行缩进 2 字符（用 firstLineChars，不用厘米）

python-docx 无 API，直接写 XML：

```python
def set_first_line_indent_chars(paragraph, chars=200):  # 200 = 2.00 字符
    pPr = paragraph._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = pPr.makeelement(qn('w:ind'), {})
        pPr.append(ind)
    ind.set(qn('w:firstLineChars'), str(chars))
    ind.set(qn('w:firstLine'), '480')  # 兜底值: 2*12pt=24pt=480 twips
```

标题、图题表题、摘要关键词行、参考文献条目**不缩进**（设 firstLineChars=0）。

## 4. 页面设置与分节

至少 3 个节 (section)：

| 节 | 内容 | 页码 | 页眉 |
|---|---|---|---|
| 1 | 封面、题名页、英文扉页、声明页 | 无 | 无 |
| 2 | 前言/摘要 ~ 附表清单 | 大写罗马 I, II… | 有 |
| 3 | 正文第一章 ~ 附录 | 阿拉伯，从 1 重新开始 | 有 |

```python
from docx.enum.section import WD_SECTION_START
sec = doc.add_section(WD_SECTION_START.ODD_PAGE)  # 章起奇数页；简化可用 NEW_PAGE
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.7)
sec.header_distance, sec.footer_distance = Cm(1.5), Cm(1.8)
```

页码格式与重新编号（写 sectPr 的 pgNumType）：

```python
def set_page_number_format(section, fmt='upperRoman', start=1):
    # fmt: 'upperRoman' 或 'decimal'
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn('w:pgNumType'))
    if pgNumType is None:
        pgNumType = sectPr.makeelement(qn('w:pgNumType'), {})
        sectPr.append(pgNumType)
    pgNumType.set(qn('w:fmt'), fmt)
    if start is not None:
        pgNumType.set(qn('w:start'), str(start))
```

新节默认继承上一节页眉页脚，记得 `section.header.is_linked_to_previous = False`（footer 同理，偶数页 even_page_header 同理）。

## 5. 奇偶页不同的页眉

```python
doc.settings.element.append(doc.settings.element.makeelement(qn('w:evenAndOddHeaders'), {}))
# 或检查已存在；之后:
# section.header → 奇数页页眉; section.even_page_header → 偶数页页眉
```

偶数页页眉固定文字（如"河海大学博士学位论文"）；奇数页页眉应随章变化。Word 原生用 STYLEREF 域引用 Heading 1 实现自动跟随：

```python
def add_styleref_field(paragraph, style_name='标题 1'):
    """在段落中插入 { STYLEREF "标题 1" } 域，自动显示当前章标题"""
    from docx.oxml import OxmlElement
    for t, attrs, text in [('w:fldChar', {'w:fldCharType': 'begin'}, None),
                           ('w:instrText', {'xml:space': 'preserve'}, f' STYLEREF "{style_name}" \\* MERGEFORMAT '),
                           ('w:fldChar', {'w:fldCharType': 'end'}, None)]:
        run = paragraph.add_run()
        el = OxmlElement(t)
        for k, v in attrs.items(): el.set(qn(k), v)
        if text: el.text = text
        run._r.append(el)
```

注意：若章标题编号"第一章"是手动输入在标题文字里的，STYLEREF 直接显示完整标题；中文 Word 中样式名通常为"标题 1"，英文环境为"Heading 1"——两种都可能，生成后需验证。简化方案：每章单独分节、手写该章页眉（更可控，推荐内容较少时使用）。

## 6. 页眉双横线（上粗 1 磅下细 0.5 磅）

给页眉段落设下边框，用 thickThinSmallGap 双线：

```python
def set_header_double_border(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.makeelement(qn('w:pBdr'), {})
    bottom = pPr.makeelement(qn('w:bottom'), {})
    bottom.set(qn('w:val'), 'thickThinSmallGap')
    bottom.set(qn('w:sz'), '12')   # 1.5pt 组合线，视觉接近上1磅下0.5磅
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)
```

## 7. 页脚页码域

```python
def add_page_number(paragraph):
    from docx.oxml import OxmlElement
    run = paragraph.add_run()
    for t, attr, text in [('w:fldChar', 'begin', None),
                          ('w:instrText', None, ' PAGE \\* MERGEFORMAT '),
                          ('w:fldChar', 'end', None)]:
        el = OxmlElement(t)
        if attr: el.set(qn('w:fldCharType'), attr)
        if text:
            el.set(qn('xml:space'), 'preserve'); el.text = text
        run._r.append(el)
    set_run_font(run, '宋体', 'Times New Roman', 9)  # 小五
```

## 8. 目录域

自动目录插入 TOC 域（用户打开后按 F9 更新，或用 Word/LibreOffice 刷新一次）：

```python
instrText.text = ' TOC \\o "1-2" \\h \\z \\u '   # 只列到第2级(节)
```

也可手工排版目录（条目+制表位点线引导+页码），打印效果可控但页码需最后核对。手工目录的制表位：右对齐制表位设在版心右缘（约 15.6cm），前导符 dots。

## 9. 样式组织建议

在文档中预定义以下样式（脚本 create_hhu_template.py 已创建）：

| 样式名 | 用途 |
|---|---|
| HHU正文 | 宋体/TNR 小四，20磅行距，首行缩进2字符，两端对齐 |
| 标题 1 (Heading 1) | 黑体三号加粗居中，段前16磅段后32磅，章 |
| 标题 2 (Heading 2) | 黑体四号加粗左对齐，段前后10磅，节 |
| 标题 3/4 | 黑体小四加粗左对齐，段前后10磅 |
| HHU图题 / HHU表题 | 五号加粗居中，不缩进 |
| HHU参考文献 | 五号，悬挂缩进，不首行缩进 |

修改内置 Heading 样式而非新建，能保证 TOC 域和 STYLEREF 域正常工作。同时清除内置样式的 outline 继承色（蓝色）：设 `style.font.color.rgb = RGBColor(0,0,0)`。

## 10. 三线表

```python
table.style = 'Normal Table'   # 先去掉默认网格线
# 然后给首行上边框(1.5pt)、表头下边框(0.75pt)、末行下边框(1.5pt)写 tcBorders 或 tblBorders
```

sz 单位为 1/8 磅：1.5磅 → sz=12；0.75磅 → sz=6。

## 11. 公式编号右顶格

1 行 2 列无边框表（首列居中放公式，第二列窄、右对齐放编号），或制表位方案：段落设居中制表位(7.8cm)+右制表位(15.6cm)，`\t公式\t(1.2.1)`。

## 12. 生成后验证清单

用 python-docx 重新打开文档逐项断言：页面边距、节数与页码格式、正文样式字号 12pt 与行距 Pt(20) EXACTLY、Heading1 为 16pt 黑体居中、奇偶页眉已启用、图题在图下/表题在表上、参考文献为上标引用。
