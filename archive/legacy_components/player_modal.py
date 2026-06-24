from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


def render_player_detail_modal(player: dict) -> None:
    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    if dialog is None:
        st.warning("현재 Streamlit 버전에서는 모달 기능을 지원하지 않습니다.")
        return

    @dialog(f"{player.get('name', '선수')} 상세 정보")
    def _player_detail_dialog() -> None:
        col1, col2 = st.columns([1, 2])

        with col1:
            image_path = str(player.get("image_path", "")).strip()

            if image_path and Path(image_path).exists():
                st.image(image_path, width=140)
            else:
                st.markdown(
                    f"""
                    <div class="modal-avatar">
                      {player.get("number", "")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown(f"### {player.get('name', '-')}")
            st.write(f"**등번호:** {player.get('number', '-')}")
            st.write(f"**주 포지션:** {player.get('position', '-')}")
            st.write(f"**상세 포지션:** {player.get('detail_position', '-')}")
            st.write(f"**키:** {player.get('height', '-')} cm")
            st.write(f"**소속:** {player.get('club', '-')}")
            st.write(f"**국가:** {player.get('nation', '-')}")
            st.write(f"**종합 점수:** {player.get('overall', '-')}")

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
                    name=str(player.get("name", "")),
                )
            ]
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=340,
            margin=dict(l=30, r=30, t=30, b=30),
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 선수 코멘트")
        comment = player.get("comment", "")

        if comment:
            st.info(comment)
        else:
            st.info(
                f"{player.get('name', '해당 선수')}는 "
                f"{player.get('detail_position', player.get('position', ''))} 포지션에서 활용할 수 있는 선수입니다."
            )

        if st.button("닫기", use_container_width=True):
            st.rerun()

    _player_detail_dialog()