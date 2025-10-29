# utils/summarizer.py

import pandas as pd

def generate_report(df: pd.DataFrame, mode: str, keyword: str) -> str:
    if mode == "brand":
        if df.empty:
            return f"在当前采样中，尚未检索到与“{keyword}”相关的品牌提及。建议扩大数据源或延长采样时段。"
        top = df.iloc[0]
        return (
            f"【品牌分析】围绕“{keyword}”，采样中提及最频繁的品牌为 **{top['brand']}** "
            f"（{top['count']} 次）。建议进一步对高频品牌做功能、定价、案例与口碑对比，"
            f"并结合渠道（论坛/广告/资讯）拆分声量构成，识别真实口碑 vs 营销曝光。"
        )
    elif mode == "voice":
        n = len(df)
        return (
            f"【用户声音】共抽取得到 {n} 条包含“{keyword}”的用户句段。"
            f"建议对其进行情感分类（正/负/中立）与主题聚类（功能、售后、价格、稳定性等），"
            f"并对高频痛点设计 FAQ/内容回应与产品改进路线。"
        )
    elif mode == "source":
        if df.empty:
            return f"【信息源分析】尚未发现信息源对“{keyword}”的有效提及。"
        top = df.iloc[0]
        return (
            f"【信息源分析】对“{keyword}”提及最高的来源为 **{top['source']}**（{top['mentions']} 次）。"
            f"建议优先深挖头部来源的用户画像、调性与内容形式，并建立定期监测。"
        )
    return "（暂无可生成的报告）"
