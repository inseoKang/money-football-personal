"""포메이션과 포지션 기준 정의 파일.

프론트에서는 경기장 좌표를 그릴 때 사용하고,
백엔드에서는 추천 라인업과 포지션 적합도 계산에 사용합니다.
"""

FORMATIONS = {
    "4-3-3": [
        {"slot_id": "LW", "role": "LW", "line": "FW", "x": 18, "y": 18},
        {"slot_id": "ST", "role": "ST", "line": "FW", "x": 50, "y": 14},
        {"slot_id": "RW", "role": "RW", "line": "FW", "x": 82, "y": 18},

        {"slot_id": "LCM", "role": "CM", "line": "MF", "x": 32, "y": 46},
        {"slot_id": "CM", "role": "CM", "line": "MF", "x": 50, "y": 52},
        {"slot_id": "RCM", "role": "CM", "line": "MF", "x": 68, "y": 46},

        {"slot_id": "LB", "role": "LB", "line": "DF", "x": 16, "y": 76},
        {"slot_id": "LCB", "role": "CB", "line": "DF", "x": 38, "y": 80},
        {"slot_id": "RCB", "role": "CB", "line": "DF", "x": 62, "y": 80},
        {"slot_id": "RB", "role": "RB", "line": "DF", "x": 84, "y": 76},

        {"slot_id": "GK", "role": "GK", "line": "GK", "x": 50, "y": 90},
    ],

    "4-4-2": [
        {"slot_id": "LST", "role": "ST", "line": "FW", "x": 30, "y": 18},
        {"slot_id": "RST", "role": "ST", "line": "FW", "x": 70, "y": 18},

        {"slot_id": "LM", "role": "LW", "line": "MF", "x": 18, "y": 44},
        {"slot_id": "LCM", "role": "CM", "line": "MF", "x": 40, "y": 44},
        {"slot_id": "RCM", "role": "CM", "line": "MF", "x": 60, "y": 44},
        {"slot_id": "RM", "role": "RW", "line": "MF", "x": 82, "y": 44},

        {"slot_id": "LB", "role": "LB", "line": "DF", "x": 18, "y": 72},
        {"slot_id": "LCB", "role": "CB", "line": "DF", "x": 40, "y": 72},
        {"slot_id": "RCB", "role": "CB", "line": "DF", "x": 60, "y": 72},
        {"slot_id": "RB", "role": "RB", "line": "DF", "x": 82, "y": 72},

        {"slot_id": "GK", "role": "GK", "line": "GK", "x": 50, "y": 88},
    ],

    "3-5-2": [
        {"slot_id": "LST", "role": "ST", "line": "FW", "x": 38, "y": 16},
        {"slot_id": "RST", "role": "ST", "line": "FW", "x": 62, "y": 16},

        {"slot_id": "LM", "role": "LW", "line": "MF", "x": 14, "y": 44},
        {"slot_id": "LCM", "role": "CM", "line": "MF", "x": 34, "y": 44},
        {"slot_id": "DM", "role": "DM", "line": "DM", "x": 50, "y": 56},
        {"slot_id": "RCM", "role": "CM", "line": "MF", "x": 66, "y": 44},
        {"slot_id": "RM", "role": "RW", "line": "MF", "x": 86, "y": 44},

        {"slot_id": "LCB", "role": "CB", "line": "DF", "x": 30, "y": 76},
        {"slot_id": "CB", "role": "CB", "line": "DF", "x": 50, "y": 76},
        {"slot_id": "RCB", "role": "CB", "line": "DF", "x": 70, "y": 76},

        {"slot_id": "GK", "role": "GK", "line": "GK", "x": 50, "y": 90},
    ],

    "4-2-3-1": [
        {"slot_id": "ST", "role": "ST", "line": "FW", "x": 50, "y": 14},

        {"slot_id": "LAM", "role": "LW", "line": "AM", "x": 24, "y": 34},
        {"slot_id": "CAM", "role": "AM", "line": "AM", "x": 50, "y": 34},
        {"slot_id": "RAM", "role": "RW", "line": "AM", "x": 76, "y": 34},

        {"slot_id": "LDM", "role": "DM", "line": "DM", "x": 40, "y": 56},
        {"slot_id": "RDM", "role": "DM", "line": "DM", "x": 60, "y": 56},

        {"slot_id": "LB", "role": "LB", "line": "DF", "x": 16, "y": 76},
        {"slot_id": "LCB", "role": "CB", "line": "DF", "x": 38, "y": 80},
        {"slot_id": "RCB", "role": "CB", "line": "DF", "x": 62, "y": 80},
        {"slot_id": "RB", "role": "RB", "line": "DF", "x": 84, "y": 76},

        {"slot_id": "GK", "role": "GK", "line": "GK", "x": 50, "y": 90},
    ],

    "3-4-3": [
        {"slot_id": "LW", "role": "LW", "line": "FW", "x": 20, "y": 18},
        {"slot_id": "ST", "role": "ST", "line": "FW", "x": 50, "y": 14},
        {"slot_id": "RW", "role": "RW", "line": "FW", "x": 80, "y": 18},

        {"slot_id": "LM", "role": "LW", "line": "MF", "x": 18, "y": 46},
        {"slot_id": "LCM", "role": "CM", "line": "MF", "x": 40, "y": 50},
        {"slot_id": "RCM", "role": "CM", "line": "MF", "x": 60, "y": 50},
        {"slot_id": "RM", "role": "RW", "line": "MF", "x": 82, "y": 46},

        {"slot_id": "LCB", "role": "CB", "line": "DF", "x": 30, "y": 76},
        {"slot_id": "CB", "role": "CB", "line": "DF", "x": 50, "y": 76},
        {"slot_id": "RCB", "role": "CB", "line": "DF", "x": 70, "y": 76},

        {"slot_id": "GK", "role": "GK", "line": "GK", "x": 50, "y": 90},
    ],
}


ROLE_ALIASES = {
    "GK": ["GK"],
    "CB": ["CB", "DF"],
    "LB": ["LB", "RB", "DF"],
    "RB": ["RB", "LB", "DF"],
    "DM": ["DM", "CM", "MF"],
    "CM": ["CM", "DM", "AM", "MF"],
    "AM": ["AM", "CM", "MF"],
    "LW": ["LW", "RW", "FW", "AM"],
    "RW": ["RW", "LW", "FW", "AM"],
    "ST": ["ST", "FW"],
}