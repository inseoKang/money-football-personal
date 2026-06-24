from __future__ import annotations

import html
import json
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.coach.formations import FORMATIONS


def _get_player_lookup(players: pd.DataFrame) -> dict[str, dict]:
    if players.empty or "name" not in players.columns:
        return {}

    return {
        str(row["name"]): row.to_dict()
        for _, row in players.iterrows()
    }


def _safe_key(value: str) -> str:
    return (
        str(value)
        .replace(" ", "_")
        .replace("-", "_")
        .replace(":", "_")
        .replace("/", "_")
    )


def _slot_href(page_key: str, slot_id: str, lineup: dict | None = None) -> str:
    href = f"?page={quote(str(page_key))}&slot={quote(str(slot_id))}"

    if lineup:
        lineup_json = json.dumps(lineup, ensure_ascii=False, separators=(",", ":"))
        href += f"&lineup={quote(lineup_json)}"

    return href


def _line_label(line: str) -> str:
    labels = {
        "FW": "공격진",
        "AM": "공격형 미드필더",
        "MF": "미드필더",
        "DM": "수비형 미드필더",
        "DF": "수비진",
        "GK": "골키퍼",
    }
    return labels.get(str(line).upper(), line)


def _line_order(line: str) -> int:
    order = {
        "FW": 1,
        "AM": 2,
        "MF": 3,
        "DM": 4,
        "DF": 5,
        "GK": 6,
    }
    return order.get(str(line).upper(), 99)


def _used_lines(slots: list[dict]) -> list[str]:
    lines = []

    for slot in slots:
        line = str(slot.get("line", "MF")).upper()
        if line not in lines:
            lines.append(line)

    lines.sort(key=_line_order)
    return lines


def _build_slot_label(
    *,
    slot_id: str,
    role: str,
    player_name: str,
    player_lookup: dict[str, dict],
) -> str:
    display_position = str(slot_id or role)

    if not player_name:
        return f"{display_position}\n선택"

    player = player_lookup.get(str(player_name), {})
    number = player.get("number", "")

    number_text = f"#{number}" if number not in [None, ""] else "#-"

    short_name = str(player_name)
    if len(short_name) > 8:
        short_name = short_name[:8] + "…"

    return f"{display_position}\n{short_name}\n{number_text}"


def _payload_slot_label(slot: dict) -> str:
    slot_id = str(slot.get("slotId", slot.get("slot_id", "")))
    role = str(slot.get("role", slot_id))
    display_position = slot_id or role

    player = slot.get("player")
    fit_score = slot.get("roleFitScore", 0)

    if not player:
        return f"{display_position}\n선택"

    name = str(player.get("name", "-"))
    if len(name) > 8:
        name = name[:8] + "…"

    position = str(player.get("positionGroup", "-"))

    try:
        fit = int(round(float(fit_score)))
    except (TypeError, ValueError):
        fit = 0

    return f"{display_position}\n{name}\n{position} · {fit}"


def _render_pitch_css(container_key: str) -> None:
    st.markdown(
        f"""
        <style>
        .mf-pitch-{container_key} {{
            position: relative;
            width: 100%;
            height: 690px;
            border: 2px solid rgba(173, 255, 199, .45);
            border-radius: 14px;
            box-shadow: inset 0 0 0 14px rgba(255,255,255,.035);
            overflow: hidden;

            background:
                radial-gradient(circle at 50% 50%, rgba(209,255,220,.65) 0 4px, transparent 5px),
                radial-gradient(circle at 50% 50%, transparent 0 63px, rgba(209,255,220,.37) 64px 65px, transparent 66px),

                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) center 113px / 50% 2px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 25% 18px / 2px 95px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 75% 18px / 2px 95px no-repeat,

                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) center 54px / 24% 2px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 38% 18px / 2px 36px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 62% 18px / 2px 36px no-repeat,

                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) center calc(100% - 113px) / 50% 2px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 25% calc(100% - 20px) / 2px 95px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 75% calc(100% - 20px) / 2px 95px no-repeat,

                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) center calc(100% - 54px) / 24% 2px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 38% calc(100% - 20px) / 2px 36px no-repeat,
                linear-gradient(rgba(209,255,220,.37), rgba(209,255,220,.37)) 62% calc(100% - 20px) / 2px 36px no-repeat,

                repeating-linear-gradient(
                    0deg,
                    rgba(255,255,255,.025) 0 58px,
                    rgba(0,0,0,.06) 58px 116px
                ),
                linear-gradient(180deg, #176937 0%, #0f572f 100%);
        }}

        .mf-pitch-{container_key}::before {{
            content: "";
            position: absolute;
            inset: 18px;
            border: 2px solid rgba(209,255,220,.37);
            pointer-events: none;
            z-index: 0;
        }}

        .mf-pitch-{container_key}::after {{
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            top: 50%;
            border-top: 2px solid rgba(209,255,220,.37);
            pointer-events: none;
            z-index: 0;
        }}

        .mf-pitch-slot {{
            position: absolute;
            transform: translate(-50%, -50%);
            width: 76px;
            height: 76px;
            border-radius: 18px;
            border: 2px solid rgba(32,217,135,.72);
            background: rgba(8,33,49,.94);
            color: #eafff5;
            box-shadow: 0 0 0 3px rgba(32,217,135,.12);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            white-space: normal;
            text-decoration: none;
            font-weight: 900;
            font-size: .68rem;
            line-height: 1.18;
            z-index: 2;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
            overflow: hidden;
        }}

        .mf-pitch-slot:hover {{
            border-color: #20d987;
            transform: translate(-50%, -50%) scale(1.04);
            box-shadow: 0 0 0 5px rgba(32,217,135,.18);
            color: white;
            text-decoration: none;
        }}

        .mf-pitch-slot.disabled {{
            pointer-events: none;
            opacity: .95;
        }}

        .mf-pitch-legend {{
            position: absolute;
            left: 28px;
            top: 26px;
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            max-width: calc(100% - 56px);
            z-index: 5;
            pointer-events: none;
        }}

        .mf-pitch-legend-item {{
            padding: 4px 8px;
            border-radius: 999px;
            background: rgba(8, 33, 49, .58);
            border: 1px solid rgba(173, 255, 199, .22);
            color: rgba(215, 248, 255, .78);
            font-size: .62rem;
            font-weight: 900;
            letter-spacing: .04em;
            line-height: 1;
            backdrop-filter: blur(3px);
        }}

        .mf-pitch-caption {{
            text-align: center;
            color: #8fb0c3;
            margin-top: .55rem;
            font-size: .78rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_pitch_legend(slots: list[dict]) -> str:
    html_parts = ['<div class="mf-pitch-legend">']

    for line in _used_lines(slots):
        html_parts.append(
            f'<span class="mf-pitch-legend-item">{html.escape(_line_label(line))}</span>'
        )

    html_parts.append("</div>")
    return "".join(html_parts)


def render_pitch(
    players: pd.DataFrame,
    formation: str,
    lineup: dict,
    page: str | None = None,
) -> None:
    if formation not in FORMATIONS:
        st.error(f"지원하지 않는 포메이션입니다: {formation}")
        return

    page_key = page or st.session_state.get("current_page", "coach_squad")
    container_key = _safe_key(f"{page_key}_{formation}_pitch")

    slots = FORMATIONS[formation]
    player_lookup = _get_player_lookup(players)

    _render_pitch_css(container_key)

    html_parts = [f'<div class="mf-pitch-{container_key}">']
    html_parts.append(_render_pitch_legend(slots))

    for slot in slots:
        slot_id = str(slot["slot_id"])
        role = str(slot.get("role", slot_id))
        x = float(slot.get("x", 50))
        y = float(slot.get("y", 50))
        player_name = str(lineup.get(slot_id, "") or "")

        label = _build_slot_label(
            slot_id=slot_id,
            role=role,
            player_name=player_name,
            player_lookup=player_lookup,
        )

        label_html = html.escape(label).replace("\n", "<br>")
        href = _slot_href(page_key, slot_id, lineup)

        html_parts.append(
            f'<a class="mf-pitch-slot" href="{href}" target="_self" style="left:{x}%; top:{y}%;">'
            f'{label_html}'
            f'</a>'
        )

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)

    st.markdown(
        """
        <div class="mf-pitch-caption">
            슬롯을 클릭하면 해당 포지션 후보를 선택할 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_payload_pitch(
    slots: list[dict],
    page: str | None = None,
    *,
    interactive: bool = True,
    caption: str = "포지션 슬롯을 클릭하면 해당 위치에 배치할 선수를 선택할 수 있습니다.",
) -> None:
    page_key = page or st.session_state.get("current_page", "coach_squad")
    container_key = _safe_key(f"{page_key}_payload_pitch")

    _render_pitch_css(container_key)

    html_parts = [f'<div class="mf-pitch-{container_key}">']
    html_parts.append(_render_pitch_legend(slots))

    lineup_for_url = {}

    for slot in slots:
        slot_id = str(slot.get("slotId", slot.get("slot_id", "")))
        player = slot.get("player")

        if not player:
            continue

        salary_id = player.get("salaryId")

        if salary_id not in [None, ""]:
            lineup_for_url[slot_id] = int(salary_id)

    for slot in slots:
        slot_id = str(slot.get("slotId", slot.get("slot_id", "")))
        x = float(slot.get("x", 50))
        y = float(slot.get("y", 50))

        label = _payload_slot_label(slot)
        label_html = html.escape(label).replace("\n", "<br>")

        if interactive:
            href = _slot_href(page_key, slot_id, lineup_for_url)
            html_parts.append(
                f'<a class="mf-pitch-slot" href="{href}" target="_self" style="left:{x}%; top:{y}%;">'
                f'{label_html}'
                f'</a>'
            )
        else:
            html_parts.append(
                f'<div class="mf-pitch-slot disabled" style="left:{x}%; top:{y}%;">'
                f'{label_html}'
                f'</div>'
            )

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)

    if caption:
        st.markdown(
            f"""
            <div class="mf-pitch-caption">
                {html.escape(caption)}
            </div>
            """,
            unsafe_allow_html=True,
        )