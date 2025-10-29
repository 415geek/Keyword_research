# app.py

import streamlit as st
import pandas as pd

from utils.config import DATA_SOURCES, DEFAULT_MAX_PAGES
from utils.crawler import crawl_keyword_from_sources, RedditCrawler
from utils.analyzer import brand_analysis, user_voice_analysis, source_analysis
from utils.viz import (
    plot_brand_plotly, plot_sources_plotly,
    plot_brand_altair, plot_sources_altair,
)
from utils.summarizer import generate_report

st.set_page_config(page_title="市场调研智能分析系统", layout="wide")
st.title("🔍 市场调研智能分析系统")

# ---- 侧边栏：参数 & 可视化引擎 ----
with st.sidebar:
    st.header("设置")
    vis_engine = st.radio("可视化库", ["Plotly", "Altair"], index=0)
    max_pages = st.slider("每站点最大抓取页数", 1, 5, DEFAULT_MAX_PAGES)
    st.markdown("---")
    st.caption("（可选）Reddit 抓取凭证/UA：")
    reddit_user_agent = st.text_input("user_agent", value="market-research-app/0.1 by yourname")
    reddit_client_id = st.text_input("client_id（可留空）", type="password")
    reddit_client_secret = st.text_input("client_secret（可留空）", type="password")

keyword = st.text_input("输入关键词（如：POS系统）")

level = st.radio("选择分析维度", ["品牌分析", "用户声音", "信息源分析"], horizontal=True)

if st.button("开始分析", type="primary") and keyword:
    with st.spinner("正在采集数据…"):
        crawled = crawl_keyword_from_sources(DATA_SOURCES, keyword, max_pages=max_pages)

        # Reddit（可选）
        if reddit_user_agent:
            rc = RedditCrawler(
                user_agent=reddit_user_agent,
                client_id=reddit_client_id or None,
                client_secret=reddit_client_secret or None,
            )
            posts = rc.search(keyword, limit=50)
            # 只存少量关键字段，避免页面太重
            for p in posts:
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                crawled.append({"source": "reddit", "text": f"{title}\n{selftext}"})

    if not crawled:
        st.warning("未在预设数据源中检索到相关内容。请更换关键词或增添数据源。")
        st.stop()

    # -------- 分析与可视化 --------
    if level == "品牌分析":
        df = brand_analysis(crawled, keyword)
        st.subheader("品牌提及统计")
        if vis_engine == "Plotly":
            fig = plot_brand_plotly(df)
            if fig: st.plotly_chart(fig, use_container_width=True)
        else:
            chart = plot_brand_altair(df)
            if chart: st.altair_chart(chart, use_container_width=True)

        st.markdown("**数据表**")
        st.dataframe(df)

        st.markdown("### 结果分析")
        st.write(generate_report(df, "brand", keyword))

    elif level == "用户声音":
        df = user_voice_analysis(crawled, keyword)
        st.subheader("用户讨论摘录")
        st.dataframe(df if not df.empty else pd.DataFrame(columns=["source","sentence","sentiment"]), use_container_width=True)

        st.markdown("### 结果分析")
        st.write(generate_report(df, "voice", keyword))

    else:  # 信息源分析
        df = source_analysis(crawled, keyword)
        st.subheader("信息源分布")
        if vis_engine == "Plotly":
            fig = plot_sources_plotly(df)
            if fig: st.plotly_chart(fig, use_container_width=True)
        else:
            chart = plot_sources_altair(df)
            if chart: st.altair_chart(chart, use_container_width=True)

        st.markdown("**数据表**")
        st.dataframe(df)

        st.markdown("### 结果分析")
        st.write(generate_report(df, "source", keyword))

else:
    st.info("输入关键词并点击『开始分析』。")
