# hydro-litsearch —— 水利/水电文献检索 MCP 连接器

一个只走**开放 API**、**合规**的文献检索连接器。给你的 literature-review / academic-writing
补上"自动检索题录、筛选、核实 DOI、定位合法全文链接"的能力。**只检索公开元数据,不下载
全文;最终产出含 DOI 的相关文献清单,由你手动去授权渠道下载。**

## 它做什么 / 不做什么

**做(自动,合规):**
- `search_papers` —— 按主题检索(OpenAlex),返回题名/作者/年份/期刊/摘要/被引/DOI 供筛选。
- `get_paper_details` / `get_citations` —— 取单篇详情、顺引文关系找相关文献。
- `verify_reference` —— 用 Crossref 核实 DOI 真伪并给规范著录(GB/T 7714 参考),杜绝编造引用。
- `find_open_fulltext` —— 用 Unpaywall 找**合法**开放获取全文链接(只给链接,不下载)。
- `build_manual_query` —— 为知网/百度学术/WoS 生成检索式 + 人工检索步骤(**不访问**这些站点)。
- `wos_search` —— 预留;拿到学校 WoS API Key 后启用。

**不做(合规红线):**
- 不抓取知网(CNKI)、百度学术、Web of Science 等无开放 API 的订阅库/网站。
- 不下载、不缓存任何全文。
- 对上述订阅库,只"生成检索式给你、你本人手动检索",绝不自动化访问,以免违反订阅协议、
  连累全校访问权限。

## 数据源(均为公开、允许程序访问的 API)
- OpenAlex(检索主力,2 亿+文献,含中英文水利文献,免费)
- Crossref(DOI 权威核实与著录,免费)
- Semantic Scholar(摘要/被引补充,免费;大量调用可申请 Key)
- Unpaywall(合法 OA 全文定位,免费,需提供联系邮箱)

## 安装与运行(在联网环境)
```bash
cd hydro-litsearch-mcp
pip install -r requirements.txt          # 或 uv add mcp httpx
export LIT_MCP_EMAIL="your.name@hhu.edu.cn"   # 必填:OpenAlex 礼貌池 / Crossref / Unpaywall
python server.py                          # 以 stdio 方式运行,供 Cowork 连接
```

## 在 Cowork / Claude 里连上
把 `mcp.json.example` 的内容并入你的 MCP 配置(`.mcp.json`),改成 server.py 的**绝对路径**
和你的邮箱即可。连上后,literature-review 会自动调用这些工具。

## 与 literature-review 的配合(推荐流程)
1. 用 `search_papers` 按主题检索(先英文关键词走 OpenAlex,覆盖最广)。
2. literature-review 根据返回的**题名+摘要+被引**做相关性筛选(这是 agent 的判断,不是抓取)。
3. 对入选文献用 `verify_reference` 核实 DOI、`find_open_fulltext` 找合法全文链接。
4. 需要中文文献且开放 API 没覆盖到的:用 `build_manual_query(source='cnki')` 生成知网检索式,
   **你本人**去知网手动检索、下载,再把结果交回给 literature-review 综述。
5. 产出:一份精炼的相关文献清单(含 DOI 与合法全文链接),你据此手动下载全文。

## 关于 Web of Science 的正路
你们有 WoS 的 IP 订阅,但(据了解)没有 API 订阅。让**图书馆向 Clarivate 申请 Web of
Science API**(Starter 或 Expanded)——有 WoS 订阅通常可申请。拿到 Key 后设 `WOS_API_KEY`
环境变量即可启用 `wos_search`,把 WoS 也变成合规的自动检索一路。在此之前用
`build_manual_query(source='wos')` 生成检索式手动检索。

## 礼貌与稳健
- 已内置礼貌延时与带联系邮箱的 User-Agent,适合"小量、低频、精准"检索。
- 各工具都有错误处理;DOI 不存在会明确报错,防止误引。
