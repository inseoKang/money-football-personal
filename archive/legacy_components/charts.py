from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_player_radar(player: dict) -> None:
    import plotly.graph_objects as go

    labels = ["공격", "중원", "수비", "속도", "피지컬", "체력"]
    columns = [
        "attack_score",
        "midfield_score",
        "defense_score",
        "pace_score",
        "physical_score",
        "stamina_score",
    ]

    values = [int(player.get(col, 0)) for col in columns]

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill="toself",
            )
        ]
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=320,
        margin=dict(l=30, r=30, t=30, b=30),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_position_bar_chart(players: pd.DataFrame) -> None:
    if players.empty or "position" not in players.columns:
        st.info("포지션 차트를 표시할 데이터가 없습니다.")
        return

    chart_data = players["position"].value_counts().reset_index()
    chart_data.columns = ["position", "count"]

    fig = px.bar(
        chart_data,
        x="position",
        y="count",
        text="count",
        title="포지션별 선수 수",
    )

    fig.update_layout(height=330, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_bubble_chart(players: pd.DataFrame) -> None:
    required = {"overall", "market_value", "wage", "name"}

    if players.empty or not required.issubset(players.columns):
        st.info("버블 차트를 표시하려면 overall, market_value, wage, name 컬럼이 필요합니다.")
        return

    size_column = "overall"

    fig = px.scatter(
        players,
        x="wage",
        y="market_value",
        size=size_column,
        color="position" if "position" in players.columns else None,
        hover_name="name",
        hover_data=["club", "nation", "overall"] if {"club", "nation", "overall"}.issubset(players.columns) else None,
        title="연봉 대비 시장가치 버블 차트",
        labels={
            "wage": "연봉",
            "market_value": "시장가치",
            "overall": "종합 점수",
            "position": "포지션",
        },
    )

    fig.update_layout(height=560, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)