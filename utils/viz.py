# utils/viz.py

import pandas as pd

# ---- Plotly ----
import plotly.express as px

def plot_brand_plotly(df: pd.DataFrame):
    if df.empty:
        return None
    fig = px.bar(
        df.head(30),
        x="count",
        y="brand",
        orientation="h",
        title="品牌提及次数（Top 30）",
        labels={"count": "次数", "brand": "品牌"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=40, b=10))
    return fig

def plot_sources_plotly(df: pd.DataFrame):
    if df.empty:
        return None
    fig = px.bar(
        df,
        x="source",
        y="mentions",
        title="信息源对关键词的提及次数",
        labels={"source": "来源站点", "mentions": "提及次数"},
    )
    fig.update_layout(xaxis_tickangle=-30, margin=dict(l=10, r=10, t=40, b=80))
    return fig

# ---- Altair ----
import altair as alt
alt.data_transformers.disable_max_rows()  # 大表格时不截断

def plot_brand_altair(df: pd.DataFrame):
    if df.empty:
        return None
    chart = (
        alt.Chart(df.head(30))
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="次数"),
            y=alt.Y("brand:N", sort="-x", title="品牌"),
            tooltip=["brand:N", "count:Q"],
        )
        .properties(title="品牌提及次数（Top 30）")
    )
    return chart

def plot_sources_altair(df: pd.DataFrame):
    if df.empty:
        return None
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("source:N", sort="-y", title="来源站点"),
            y=alt.Y("mentions:Q", title="提及次数"),
            tooltip=["source:N", "mentions:Q"],
        )
        .properties(title="信息源对关键词的提及次数")
    )
    return chart
