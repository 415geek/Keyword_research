# utils/analyzer.py

import re
import pandas as pd
from collections import Counter
from typing import List, Dict

# ---- 基础统计 ----
def brand_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    简单品牌提及统计（示例规则：抓取首字母大写词及带 POS/System/Suite 等后缀）
    生产建议：用 NER/实体词典替换此正则。
    """
    pattern = re.compile(r"\b[A-Z][A-Za-z0-9]+(?:\s+(?:POS|System|Suite|Pay|PayOS|ERP|Cloud|POS系统))?\b")
    counter = Counter()
    for item in crawled:
        text = (item.get("text") or "").strip()
        for m in pattern.findall(text):
            counter[m] += 1
    df = pd.DataFrame(counter.items(), columns=["brand", "count"]).sort_values("count", ascending=False)
    return df.reset_index(drop=True)

def user_voice_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    提取包含 keyword 的句子，做后续情感/主题挖掘的原始素材。
    """
    out = []
    kw = keyword.lower()
    for item in crawled:
        source = item.get("source", "")
        text = (item.get("text") or "")
        # 句子粗切分
        sentences = re.split(r"[。！？!?\.]", text)
        for s in sentences:
            if kw in s.lower():
                out.append({"source": source, "sentence": s.strip()})
    df = pd.DataFrame(out)
    if not df.empty:
        df["sentiment"] = "待实现"   # 占位字段
    return df

def source_analysis(crawled: List[Dict], keyword: str) -> pd.DataFrame:
    """
    统计每个来源对 keyword 的提及次数
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
    df = df.groupby("source", as_index=False)["mentions"].sum().sort_values("mentions", ascending=False)
    return df
