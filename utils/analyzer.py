# utils/analyzer.py
# 精准品牌识别（白名单 + 别名/模糊匹配 + 可选 NER），以及用户声音/信息源分析
from __future__ import annotations
import re
from collections import Counter
from typing import Dict, List
import pandas as pd

# ============== 1) 品牌白名单（标准写法）=============
# 可按需继续添加
KNOWN_POS_BRANDS = [
    # 主流/常见
    "Toast", "Square", "Clover", "Lightspeed", "RestoSuite", "Menusifu",
    "Revel", "SpotOn", "TouchBistro", "Upserve", "Aloha",
    "Lavu", "PAX", "Adyen", "Stripe", "PayPal", "Shopify",
    "POSBANK", "PAR", "Epos Now", "Heartland", "KwisPOS",
    "FocusPOS", "Xenial",

    # 你要求新增
    "Peblla", "Chowbus", "DinaTouch", "39miles",
]

# ============== 2) 品牌别名/常见写法（更鲁棒的匹配）=============
# key 是标准品牌名；value 是该品牌在文中可能出现的所有常见变体（小写即可）
BRAND_ALIASES: Dict[str, List[str]] = {
    "Toast": ["toast"],
    "Square": ["square", "block pos"],        # Square 公司母公司为 Block，可选
    "Clover": ["clover"],
    "Lightspeed": ["lightspeed", "light speed"],
    "RestoSuite": ["restosuite", "resto suite", "restosuite pos", "resto suite pos"],
    "Menusifu": ["menusifu", "menu sifu"],
    "Revel": ["revel"],
    "SpotOn": ["spoton", "spot on"],
    "TouchBistro": ["touchbistro", "touch bistro"],
    "Upserve": ["upserve"],
    "Aloha": ["aloha pos", "aloha"],
    "Lavu": ["lavu"],
    "PAX": ["pax"],
    "Adyen": ["adyen"],
    "Stripe": ["stripe"],
    "PayPal": ["paypal", "pay pal"],
    "Shopify": ["shopify", "shopify pos"],
    "POSBANK": ["posbank", "pos bank"],
    "PAR": ["par", "par tech", "partech"],
    "Epos Now": ["eposnow", "epos now"],
    "Heartland": ["heartland", "heartland pos"],
    "KwisPOS": ["kwispos", "kwis pos"],
    "FocusPOS": ["focuspos", "focus pos"],
    "Xenial": ["xenial"],

    # 新增
    "Peblla": ["peblla"],
    "Chowbus": ["chowbus", "chow bus", "chowbus pos"],
    "DinaTouch": ["dinatouch", "dina touch", "dinatouch pos"],
    "39miles": ["39miles", "39 miles", "39miles pos"],
}

# 预编译正则：为每个品牌生成一个 OR 模式，使用单词边界，忽略大小写
def _compile_brand_patterns() -> Dict[str, re.Pattern]:
    patterns: Dict[str, re.Pattern] = {}
    for canonical, aliases in BRAND_ALIASES.items():
        escaped = [re.escape(a) for a in aliases]
        # \b 边界对纯字母数字词可靠；对以数字开头的（如 39miles），额外加备选 (?<!\w) / (?!\w)
        # 这里采用宽松边界：(^|[^A-Za-z0-9_]) 与 (?=$|[^A-Za-z0-9_])，避免把 “my39milesX” 误算
        pattern = rf'(?i)(^|[^A-Za-z0-9_])(?:{"|".join(escaped)})(?=$|[^A-Za-z0-9_])'
        patterns[canonical] = re.compile(pattern)
    return patterns

BRAND_PATTERNS = _compile_brand_patterns()

# ============== 3) 可选：spaCy NER（ORG/PRODUCT 提示新品牌）=============
try:
    import spacy  # type: ignore
    try:
        _nlp = spacy.load("en_core_web_sm")  # 轻量模型足够做候选提取
    except Exception:
        _nlp = None
except Exception:
    _nlp = None

def _nlp_brand_candidates(text: str) -> List[str]:
    """从文本里抽取 ORG/PRODUCT 作为候选（仅做参考，不直接计数）。"""
    if not _nlp:
        return []
    doc = _nlp(text)
    cands = [ent.text.strip() for ent in doc.ents if ent.label_ in ("ORG", "PRODUCT")]
    # 去重，保留原序
    seen, out = set(), []
    for c in cands:
        k = c.lower()
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out

# ============== 4) 品牌分析 ==============
def brand_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    只统计白名单品牌（含别名），避免把普通英文词误当品牌。
    同时返回一列 nlp_candidates 供排查潜在新品牌（不计入 count）。
    """
    counter = Counter()
    nlp_pool = Counter()  # 仅用于参考展示

    for item in crawled:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        # ① 计数：白名单 + 别名（正则多次出现计多次）
        for canonical, pat in BRAND_PATTERNS.items():
            hits = pat.findall(text)
            if hits:
                counter[canonical] += len(hits)

        # ② 提示：可选 NER 候选（不参与计数）
        for cand in _nlp_brand_candidates(text):
            nlp_pool[cand] += 1

    df = pd.DataFrame(counter.items(), columns=["brand", "count"]).sort_values("count", ascending=False)
    df = df.reset_index(drop=True)

    # 附带一个可选参考表（不显示可注释）
    # cand_df = pd.DataFrame(nlp_pool.items(), columns=["candidate", "mentions"]).sort_values("mentions", ascending=False)

    return df

# ============== 5) 用户声音分析 ==============
def user_voice_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    抽取包含 keyword 的句段，后续可对 df['sentence'] 做情感/主题聚类。
    """
    out = []
    kw = keyword.lower()
    splitter = re.compile(r"[。！？!?\.]+")
    for item in crawled:
        src = item.get("source", "")
        text = (item.get("text") or "")
        for s in splitter.split(text):
            if kw in s.lower():
                out.append({"source": src, "sentence": s.strip()})
    df = pd.DataFrame(out)
    if not df.empty:
        df["sentiment"] = "待实现"  # 预留字段
    return df

# ============== 6) 信息源分析 ==============
def source_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    统计各来源站点对 keyword 的提及次数。
    """
    rows = []
    kw = keyword.lower()
    for item in crawled:
        src = item.get("source", "")
        txt = (item.get("text") or "").lower()
        rows.append({"source": src, "mentions": txt.count(kw)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = (
        df.groupby("source", as_index=False)["mentions"]
        .sum()
        .sort_values("mentions", ascending=False)
        .reset_index(drop=True)
    )
    return df
