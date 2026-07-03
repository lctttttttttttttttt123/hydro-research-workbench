#!/usr/bin/env python3
"""
hydro-litsearch MCP 服务端 —— 水利/水电文献检索连接器(仅走开放 API,合规)

设计原则(务必遵守):
  1. 只检索与提炼【公开元数据】(题名、作者、年份、期刊、摘要、被引、DOI),不下载全文。
  2. 只调用公开、允许程序访问的 API:OpenAlex、Crossref、Semantic Scholar、Unpaywall。
  3. 【不】抓取知网(CNKI)、百度学术、Web of Science 等无开放接口的订阅/网站——对这些库,
     本服务只用 build_manual_query 生成检索式与人工检索指引,由使用者手动检索,绝不自动访问。
  4. 最终产物是一份精炼的、含 DOI 的相关文献清单,供使用者手动下载全文。

对外暴露的工具:
  - search_papers          按主题检索文献(OpenAlex 为主),返回公开题录用于筛选
  - get_paper_details      取单篇详细公开元数据(OpenAlex + Crossref)
  - get_citations          取某文献的被引/参考文献(OpenAlex 引文图)
  - verify_reference       用 Crossref 核实 DOI 并返回规范著录(供 GB/T 7714 排版)
  - find_open_fulltext     用 Unpaywall 定位【合法】免费全文链接(只给链接,不下载)
  - build_manual_query     为知网/百度学术/WoS 生成检索式 + 人工检索步骤(不访问这些站点)
  - wos_search             预留:拿到学校 WoS API Key 后启用(默认未配置则提示如何申请)

环境变量:
  LIT_MCP_EMAIL   用于 OpenAlex 礼貌池、Crossref mailto、Unpaywall(必填 email);建议填单位邮箱
  S2_API_KEY      可选,Semantic Scholar API Key(提高速率)
  WOS_API_KEY     可选,Web of Science Starter/Expanded API Key(有则启用 wos_search)

运行:见 README.md(通常 `python server.py`,并在 Cowork/.mcp.json 里以 stdio 方式连上)。
"""
import os
import asyncio
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ── 配置 ──────────────────────────────────────────────────────────────────
EMAIL = os.environ.get("LIT_MCP_EMAIL", "").strip()
S2_API_KEY = os.environ.get("S2_API_KEY", "").strip()
WOS_API_KEY = os.environ.get("WOS_API_KEY", "").strip()
UA = f"hydro-litsearch-mcp/1.0 (mailto:{EMAIL or 'unknown'})"
TIMEOUT = httpx.Timeout(30.0)
# 礼貌延时(秒):小量、低频检索,做个人也不给对方服务器压力
POLITE_DELAY = 0.4

mcp = FastMCP("hydro-litsearch")


async def _get(url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=h) as client:
        await asyncio.sleep(POLITE_DELAY)
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def _reconstruct_abstract(inv_index: dict | None) -> str:
    """OpenAlex 的摘要是倒排索引,需还原成文本。"""
    if not inv_index:
        return ""
    positions = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def _fmt_openalex_work(w: dict) -> dict:
    """把 OpenAlex work 整理成统一的公开题录(不含全文)。"""
    doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
    authors = [a["author"]["display_name"]
               for a in w.get("authorships", []) if a.get("author")]
    src = (w.get("primary_location") or {}).get("source") or {}
    abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))
    return {
        "title": w.get("display_name"),
        "authors": authors,
        "year": w.get("publication_year"),
        "venue": src.get("display_name"),
        "doi": doi,
        "openalex_id": (w.get("id") or "").replace("https://openalex.org/", ""),
        "cited_by_count": w.get("cited_by_count"),
        "is_oa": (w.get("open_access") or {}).get("is_oa"),
        "abstract": abstract[:1200],  # 截断,只作筛选用途
    }


# ── 工具 1:检索 ───────────────────────────────────────────────────────────
@mcp.tool()
async def search_papers(query: str, from_year: Optional[int] = None,
                        to_year: Optional[int] = None, limit: int = 20,
                        venue: Optional[str] = None) -> dict:
    """按主题检索文献,返回公开题录(题名/作者/年份/期刊/摘要/被引/DOI)供筛选。
    数据源:OpenAlex(覆盖 2 亿+文献,含中英文水利文献)。不下载全文。
    query: 检索词(可中英文,如 "局部冲刷 群桩" 或 "local scour pile group")。
    from_year/to_year: 年份范围(可选)。limit: 返回条数(默认 20,上限 50)。
    venue: 期刊名过滤(可选,模糊匹配)。"""
    limit = max(1, min(int(limit), 50))
    params = {"search": query, "per-page": limit, "sort": "relevance_score:desc"}
    filters = []
    if from_year or to_year:
        lo = from_year or 1900
        hi = to_year or 2100
        filters.append(f"publication_year:{lo}-{hi}")
    if filters:
        params["filter"] = ",".join(filters)
    if EMAIL:
        params["mailto"] = EMAIL
    data = await _get("https://api.openalex.org/works", params=params)
    works = [_fmt_openalex_work(w) for w in data.get("results", [])]
    if venue:
        v = venue.lower()
        works = [w for w in works if w.get("venue") and v in w["venue"].lower()]
    return {
        "source": "OpenAlex",
        "query": query,
        "count": len(works),
        "results": works,
        "note": "以上为公开元数据,用于筛选;确定相关后用 verify_reference 核实 DOI、"
                "find_open_fulltext 找合法全文链接。全文请自行在授权渠道下载。",
    }


# ── 工具 2:单篇详情 ───────────────────────────────────────────────────────
@mcp.tool()
async def get_paper_details(doi_or_id: str) -> dict:
    """取单篇文献的详细公开元数据。可传 DOI(如 10.1061/xxx)或 OpenAlex ID(Wxxxx)。"""
    ident = doi_or_id.strip()
    if ident.lower().startswith("w") and ident[1:].isdigit():
        url = f"https://api.openalex.org/works/{ident}"
    else:
        doi = ident.replace("https://doi.org/", "")
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    params = {"mailto": EMAIL} if EMAIL else None
    w = await _get(url, params=params)
    return {"source": "OpenAlex", "paper": _fmt_openalex_work(w)}


# ── 工具 3:引文 ───────────────────────────────────────────────────────────
@mcp.tool()
async def get_citations(doi_or_id: str, direction: str = "cited_by",
                        limit: int = 20) -> dict:
    """取某文献的引文关系。direction='cited_by'(施引文献)或 'references'(参考文献)。
    用于顺藤摸瓜找相关文献。返回公开题录,不下载全文。"""
    limit = max(1, min(int(limit), 50))
    # 先拿到该文的 OpenAlex 记录
    detail = await get_paper_details(doi_or_id)
    oaid = detail["paper"]["openalex_id"]
    params = {"per-page": limit}
    if EMAIL:
        params["mailto"] = EMAIL
    if direction == "cited_by":
        params["filter"] = f"cites:{oaid}"
        data = await _get("https://api.openalex.org/works", params=params)
        works = [_fmt_openalex_work(w) for w in data.get("results", [])]
    else:  # references:该文引用了谁
        w_full = await _get(f"https://api.openalex.org/works/{oaid}",
                            params={"mailto": EMAIL} if EMAIL else None)
        ref_ids = [r.replace("https://openalex.org/", "")
                   for r in (w_full.get("referenced_works") or [])][:limit]
        works = []
        for rid in ref_ids:
            try:
                rw = await _get(f"https://api.openalex.org/works/{rid}",
                                params={"mailto": EMAIL} if EMAIL else None)
                works.append(_fmt_openalex_work(rw))
            except Exception:
                continue
    return {"source": "OpenAlex", "direction": direction,
            "count": len(works), "results": works}


# ── 工具 4:核实 DOI + 规范著录 ─────────────────────────────────────────────
@mcp.tool()
async def verify_reference(doi: str) -> dict:
    """用 Crossref 核实 DOI 是否真实存在,并返回规范著录字段(作者、题名、刊名、
    年、卷、期、页、DOI),供按 GB/T 7714—2015 排版参考文献。DOI 不存在会明确报错,
    以此杜绝"编造/写错引用"。"""
    d = doi.strip().replace("https://doi.org/", "")
    params = {"mailto": EMAIL} if EMAIL else None
    try:
        data = await _get(f"https://api.crossref.org/works/{d}", params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"doi": d, "valid": False,
                    "error": "Crossref 未找到该 DOI —— 可能拼写错误或该文献不存在,请勿引用。"}
        raise
    m = data.get("message", {})
    authors = [f'{a.get("family","")} {a.get("given","")}'.strip()
               for a in m.get("author", [])]
    issued = (m.get("issued", {}).get("date-parts") or [[None]])[0]
    return {
        "doi": d, "valid": True,
        "title": (m.get("title") or [None])[0],
        "authors": authors,
        "container_title": (m.get("container-title") or [None])[0],
        "year": issued[0] if issued else None,
        "volume": m.get("volume"), "issue": m.get("issue"),
        "page": m.get("page"), "publisher": m.get("publisher"),
        "type": m.get("type"),
        "note": "字段来自 Crossref,可直接用于 GB/T 7714 著录;缺失字段请核对原文。",
    }


# ── 工具 5:合法免费全文定位(只给链接,不下载) ────────────────────────────
@mcp.tool()
async def find_open_fulltext(doi: str) -> dict:
    """用 Unpaywall 查该 DOI 是否有【合法】的开放获取(OA)免费全文,返回链接(不下载)。
    需要设置环境变量 LIT_MCP_EMAIL。若无 OA 版本,提示改用学校订阅在授权渠道下载。"""
    if not EMAIL:
        return {"error": "未设置 LIT_MCP_EMAIL 环境变量;Unpaywall 需要一个联系邮箱。"}
    d = doi.strip().replace("https://doi.org/", "")
    try:
        data = await _get(f"https://api.unpaywall.org/v2/{d}", params={"email": EMAIL})
    except httpx.HTTPStatusError as e:
        return {"doi": d, "error": f"Unpaywall 查询失败(HTTP {e.response.status_code})。"}
    best = data.get("best_oa_location")
    if data.get("is_oa") and best:
        return {"doi": d, "is_oa": True,
                "oa_url": best.get("url_for_pdf") or best.get("url"),
                "version": best.get("version"), "license": best.get("license"),
                "host": best.get("host_type"),
                "note": "这是合法的开放获取版本链接,可直接访问。"}
    return {"doi": d, "is_oa": False,
            "note": "未找到合法免费全文。请在校园网/学校订阅等授权渠道手动下载全文。"}


# ── 工具 6:为订阅库/无 API 站点生成人工检索式(不访问这些站点) ────────────
@mcp.tool()
async def build_manual_query(topic: str, keywords_zh: Optional[list] = None,
                             keywords_en: Optional[list] = None,
                             source: str = "cnki") -> dict:
    """为【知网 CNKI / 百度学术 / Web of Science】等无开放 API 的库,生成一条精准检索式
    + 人工检索步骤。本工具【不】访问这些站点,只产出检索式,由使用者本人在授权网页手动检索。
    source: 'cnki' | 'baidu' | 'wos'。"""
    zh = keywords_zh or []
    en = keywords_en or []

    def _join(terms, op):
        return f" {op} ".join(f'"{t}"' for t in terms) if terms else ""

    if source == "wos":
        parts = []
        if en:
            parts.append(f"TS=({' OR '.join(en)})")
        q = " AND ".join(parts) if parts else f'TS=("{topic}")'
        steps = ["在校园网内打开 Web of Science 核心合集检索页",
                 "检索字段选 主题(Topic, TS)",
                 f"粘贴检索式:{q}",
                 "按年份/文献类型筛选后,人工挑选相关文献,记下其 DOI",
                 "把选中的 DOI 交回给 verify_reference 核实、find_open_fulltext 找 OA 版"]
    elif source == "baidu":
        q = " ".join([topic] + zh + en)
        steps = ["在浏览器打开百度学术,你本人手动检索",
                 f"检索词建议:{q}",
                 "按相关度/被引排序,人工筛选,记下有 DOI 的相关文献",
                 "把 DOI 交回给 verify_reference / find_open_fulltext 处理"]
    else:  # cnki
        expr = _join(zh, "AND") or f'"{topic}"'
        q = f"主题:({expr})"
        steps = ["在校园网内打开中国知网(CNKI),你本人手动检索",
                 "检索项选 主题 / 篇关摘",
                 f"检索式:{q}(可按需加 AND/OR 组合)",
                 "按学科/年份/来源类别(如核心、EI)筛选,人工挑相关文献",
                 "记下相关文献信息;有 DOI 的交回给 verify_reference 核实"]
    return {
        "source": source, "query": q, "manual_steps": steps,
        "important": "本工具只生成检索式;请【本人】在授权网页手动检索,勿用任何自动化手段"
                     "访问这些订阅库/网站,以免违反订阅协议、连累全校访问权限。",
    }


# ── 工具 7:预留 WoS API(拿到 Key 后启用) ──────────────────────────────────
@mcp.tool()
async def wos_search(query: str, limit: int = 20) -> dict:
    """【预留】用 Web of Science 官方 API 检索(需学校订阅对应的 WOS_API_KEY)。
    未配置 Key 时返回申请指引;不使用任何网页抓取。"""
    if not WOS_API_KEY:
        return {
            "enabled": False,
            "how_to_enable": "让图书馆向 Clarivate 申请 Web of Science API(Starter 或 "
                             "Expanded);有 WoS 订阅通常可申请。拿到 Key 后设为环境变量 "
                             "WOS_API_KEY 即可启用本工具。在此之前,请用 build_manual_query("
                             "source='wos') 生成检索式并手动检索。",
        }
    # 拿到 Key 后在此实现对 WoS Starter/Expanded API 的调用(端点/字段以 Clarivate 文档为准)。
    return {"enabled": True, "todo": "在此按 Clarivate WoS API 文档实现检索调用。",
            "query": query, "limit": limit}


if __name__ == "__main__":
    mcp.run()  # 默认以 stdio 传输运行,供 Cowork/Claude 以 .mcp.json 连接
