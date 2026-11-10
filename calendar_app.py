import calendar
from datetime import date, datetime
import html
import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="蒼大 やることリスト ＆ 成績管理",
    page_icon="📚",
    layout="wide",
)

DATA_FILE = "schedule_data.json"
SCORES_FILE = "scores_data.json"

COLORS = {
    "塾": "#DCEBFA",
    "家庭教師": "#E1F2E5",
    "家庭学習": "#FFF0D6",
    "過去問": "#EDE4F8",
    "埼玉過去問": "#FFE5EC",
    "学校": "#F1F1F1",
}

TEXT_COLORS = {
    "塾": "#245A91",
    "家庭教師": "#287548",
    "家庭学習": "#956117",
    "過去問": "#7045A0",
    "埼玉過去問": "#B8214B",
    "学校": "#555555",
}

DEFAULT_WEEKLY = {
    0: [  # 月曜日（家庭教師内で解き直し）
        ("家庭教師", "18:00〜19:30（合格力テスト 国・算解き直し）"),
        ("家庭学習", "漢字5つ"),
        ("家庭学習", "日能研の宿題・予習"),
    ],
    1: [  # 火曜日
        ("塾", "17:00〜21:00"),
        ("家庭学習", "漢字5つ"),
    ],
    2: [  # 水曜日
        ("塾", "17:00〜19:30"),
        ("家庭学習", "漢字5つ"),
        ("埼玉過去問", "21:00〜 埼玉過去問（算数50分）"),
        ("埼玉過去問", "自己採点"),
    ],
    3: [  # 木曜日
        ("塾", "17:00〜21:00"),
        ("家庭学習", "漢字5つ"),
        ("家庭学習", "地理の関連分野復習（15分）"),
    ],
    4: [  # 金曜日
        ("家庭教師", "18:00〜19:30"),
        ("家庭学習", "漢字5つ"),
        ("家庭学習", "日能研の宿題・予習"),
    ],
    5: [  # 土曜日（午前は埼玉過去問）
        ("塾", "12:40〜19:30"),
        ("家庭学習", "漢字5つ"),
        ("埼玉過去問", "午前：埼玉過去問（国語50分）"),
        ("家庭学習", "午前：理科の復習"),
        ("家庭学習", "21:00〜 社会の復習・暗記（30分）"),
    ],
    6: [  # 日曜日
        ("塾", "8:45〜16:45"),
        ("家庭学習", "漢字5つ"),
        ("家庭学習", "テストの振り返り"),
    ],
}

DEFAULT_SPECIAL = {
    "2026-11-09": [
        ("学校", "振替休日・学校休み"),
        ("埼玉過去問", "午前〜お昼：埼玉過去問（国語・算数セット）"),
        ("家庭教師", "18:00〜19:30（国・算解き直し）"),
        ("家庭学習", "漢字5つ"),
        ("家庭学習", "日能研の宿題・予習"),
    ],

    "2026-11-18": [
        ("学校", "11:40まで"),
        ("埼玉過去問", "午後：埼玉過去問（国語・算数セット）"),
        ("塾", "17:00〜19:30"),
        ("家庭学習", "漢字5つ"),
        ("埼玉過去問", "自己採点"),
    ],
}


def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if "db" not in st.session_state:
    st.session_state.db = load_json(DATA_FILE)

if "scores_db" not in st.session_state:
    st.session_state.scores_db = load_json(SCORES_FILE)
    if "schools" not in st.session_state.scores_db:
        st.session_state.scores_db["schools"] = []
    if "results" not in st.session_state.scores_db:
        st.session_state.scores_db["results"] = []


def get_day_events(target_date):
    date_str = target_date.strftime("%Y-%m-%d")

    # すでにユーザーが個別に編集・チェック保存済みのデータがあればそれを最優先
    if date_str in st.session_state.db:
        return st.session_state.db[date_str]

    events = []
    is_winter_vacation = (target_date.month == 12 and target_date.day >= 23) or (
        target_date.month == 1 and target_date.day <= 7
    )

    if is_winter_vacation:
        events.append({"category": "塾", "content": "冬期講習", "done": False})
    elif date_str in DEFAULT_SPECIAL:
        # 特別予定がある日は、曜日の基本予定を追加せず、特別予定で置換
        for cat, cnt in DEFAULT_SPECIAL[date_str]:
            events.append({"category": cat, "content": cnt, "done": False})
    else:
        weekday = target_date.weekday()
        base_schedule = DEFAULT_WEEKLY.get(weekday, [])
        for cat, cnt in base_schedule:
            events.append({"category": cat, "content": cnt, "done": False})

    return events


st.title("📚 蒼大 やることリスト ＆ 成績管理")
st.caption("2026年11月〜2027年2月 入試直前ダッシュボード")

tab_cal, tab_score = st.tabs(
    ["📅 学習カレンダー", "📊 テスト成績・志望校管理"]
)

# TAB 1: 学習カレンダー
with tab_cal:
    col1, col2 = st.columns(2)

    with col1:
        year = st.selectbox("年", [2026, 2027], index=0, key="cal_year")

    with col2:
        if year == 2026:
            month = st.selectbox("月", [11, 12], index=0, key="cal_month")
        else:
            month = st.selectbox("月", [1, 2], index=0, key="cal_month")

    st.markdown(
        """
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .calendar-table { width: 100%; table-layout: fixed; border-collapse: separate; border-spacing: 5px; }
    .calendar-table th { background-color: #F4F7F5; padding: 10px; border-radius: 8px; color: #3B5546; font-size: 15px; }
    .calendar-table td { vertical-align: top; height: 140px; background-color: #FFFFFF; border: 1px solid #E5EAE6; border-radius: 10px; padding: 7px; }
    .past-day { background-color: #F5F5F5 !important; opacity: 0.55; }
    .day-number { font-weight: bold; font-size: 16px; margin-bottom: 6px; color: #35483B; }
    .event { padding: 4px 5px; margin-bottom: 4px; border-radius: 5px; font-size: 11px; line-height: 1.4; overflow-wrap: anywhere; }
    .event-done { text-decoration: line-through; opacity: 0.6; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
    border_date = date(2026, 11, 6)

    html_calendar = '<table class="calendar-table"><tr>'
    for weekday in weekday_names:
        html_calendar += f"<th>{weekday}</th>"
    html_calendar += "</tr>"

    for week in month_days:
        html_calendar += "<tr>"
        for day in week:
            if day == 0:
                html_calendar += "<td style='background:#F8FAF9;'></td>"
                continue

            cur_date = date(year, month, day)
            is_past = cur_date < border_date
            td_class = " class='past-day'" if is_past else ""

            html_calendar += f"<td{td_class}>"
            html_calendar += f"<div class='day-number'>{day}</div>"

            events = get_day_events(cur_date)

            for ev in events:
                bg = COLORS.get(ev["category"], "#F1F1F1")
                color = TEXT_COLORS.get(ev["category"], "#333333")
                safe_content = html.escape(ev["content"])
                done_class = " event-done" if ev.get("done", False) else ""
                check_mark = "✅ " if ev.get("done", False) else ""

                html_calendar += f'<div class="event{done_class}" style="background-color:{bg};color:{color};"><b>{check_mark}{ev["category"]}</b><br>{safe_content}</div>'

            html_calendar += "</td>"
        html_calendar += "</tr>"
    html_calendar += "</table>"

    st.markdown(html_calendar, unsafe_allow_html=True)

    st.divider()
    st.subheader("📖 1日の学習内容（チェックリスト ＆ 予定編集）")

    default_selected = (
        date(2026, 11, 6)
        if (year == 2026 and month == 11)
        else date(year, month, 1)
    )

    selected_day = st.date_input(
        "日付を選択", value=default_selected, key="selected_date_picker"
    )

    date_key = selected_day.strftime("%Y-%m-%d")
    day_events = get_day_events(selected_day)

    st.markdown(
        f"### {selected_day.month}月{selected_day.day}日（{weekday_names[selected_day.weekday()]}）の予定"
    )

    if not day_events:
        st.info("予定はありません。下の「予定の追加・編集」から登録できます。")
    else:
        done_count = sum(1 for e in day_events if e.get("done", False))
        progress = done_count / len(day_events) if day_events else 0.0
        st.progress(
            progress,
            text=f"達成度: {done_count} / {len(day_events)} 件 完了 ({int(progress*100)}%)",
        )

        updated = False
        for i, ev in enumerate(day_events):
            col_chk, col_txt = st.columns([1, 11])
            with col_chk:
                is_checked = st.checkbox(
                    "", value=ev.get("done", False), key=f"chk_{date_key}_{i}"
                )
                if is_checked != ev.get("done", False):
                    ev["done"] = is_checked
                    updated = True

            with col_txt:
                bg = COLORS.get(ev["category"], "#F1F1F1")
                color = TEXT_COLORS.get(ev["category"], "#333333")
                safe_content = html.escape(ev["content"])
                st.markdown(
                    f'<div style="background-color:{bg};padding:8px 12px;border-radius:8px;color:{color};"><b>[{ev["category"]}]</b> {safe_content}</div>',
                    unsafe_allow_html=True,
                )

        if updated:
            st.session_state.db[date_key] = day_events
            save_json(DATA_FILE, st.session_state.db)
            st.rerun()

    with st.expander("🛠️ この日の予定を追加・編集する"):
        st.markdown("#### 予定の追加")
        new_cat = st.selectbox(
            "カテゴリ", list(COLORS.keys()), key=f"new_cat_{date_key}"
        )
        new_cnt = st.text_input(
            "内容（例: 18:00〜19:30 / 算数過去問）", key=f"new_cnt_{date_key}"
        )

        if st.button("＋ 予定を追加", key=f"btn_add_{date_key}"):
            if new_cnt.strip():
                day_events.append(
                    {"category": new_cat, "content": new_cnt, "done": False}
                )
                st.session_state.db[date_key] = day_events
                save_json(DATA_FILE, st.session_state.db)
                st.success("予定を追加しました！")
                st.rerun()

        if day_events:
            st.divider()
            st.markdown("#### 登録済み予定の削除")
            for i, ev in enumerate(day_events):
                c1, c2 = st.columns([4, 1])
                c1.write(f"・[{ev['category']}] {ev['content']}")
                if c2.button("削除", key=f"del_{date_key}_{i}"):
                    day_events.pop(i)
                    st.session_state.db[date_key] = day_events
                    save_json(DATA_FILE, st.session_state.db)
                    st.rerun()

# TAB 2: 科目別テスト成績・志望校管理
with tab_score:
    st.header("🏆 志望校 ＆ 科目別成績ダッシュボード")

    st.subheader("🎯 志望校一覧（目標R4偏差値）")
    schools = st.session_state.scores_db.get("schools", [])

    if schools:
        cols = st.columns(len(schools) if len(schools) <= 4 else 4)
        for idx, sch in enumerate(schools):
            with cols[idx % 4]:
                st.metric(
                    label=f"{sch['name']} ({sch['date']})",
                    value=f"R4: {sch['r4']}",
                )
    else:
        st.info("志望校を入力してください。")

    with st.expander("➕ 志望校の追加・編集"):
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        s_name = col_s1.text_input("学校名（例: 埼玉栄 / 栄東）")
        s_date = col_s2.text_input("入試日（例: 1/10）")
        s_r4 = col_s3.number_input(
            "目標R4偏差値", min_value=30, max_value=75, value=50
        )

        if st.button("志望校を追加"):
            if s_name.strip():
                st.session_state.scores_db["schools"].append(
                    {"name": s_name, "date": s_date, "r4": s_r4}
                )
                save_json(SCORES_FILE, st.session_state.scores_db)
                st.success(f"{s_name} を追加しました！")
                st.rerun()

        if schools:
            st.write("---")
            st.write("**登録済み志望校の削除**")
            for idx, sch in enumerate(schools):
                cs1, cs2 = st.columns([4, 1])
                cs1.write(f"・{sch['name']} ({sch['date']}) - R4: {sch['r4']}")
                if cs2.button("削除", key=f"del_sch_{idx}"):
                    st.session_state.scores_db["schools"].pop(idx)
                    save_json(SCORES_FILE, st.session_state.scores_db)
                    st.rerun()

    st.divider()

    st.subheader("📈 科目別 偏差値推移グラフ")

    results = st.session_state.scores_db.get("results", [])

    if results:
        df = pd.DataFrame(results)
        df["日付"] = pd.to_datetime(df["date"])
        df = df.sort_values("日付")

        cols_needed = ["dev_kokugo", "dev_sansu", "dev_rika", "dev_shakai", "dev_4ka"]
        for c in cols_needed:
            if c not in df.columns:
                df[c] = df["deviation"] if "deviation" in df.columns else 50.0
            else:
                df[c] = df[c].fillna(df["deviation"] if "deviation" in df.columns else 50.0)

        chart_df = df.set_index("date")[cols_needed]
        chart_df.columns = [
            "国語 偏差値",
            "算数 偏差値",
            "理科 偏差値",
            "社会 偏差値",
            "4科 偏差値",
        ]

        st.line_chart(chart_df)

        st.subheader("📋 テスト結果一覧")
        show_cols = ["date", "type", "name", "score"] + cols_needed
        show_df = df[show_cols].rename(
            columns={
                "date": "日付",
                "type": "種別",
                "name": "テスト名",
                "score": "4科点数",
                "dev_kokugo": "国語",
                "dev_sansu": "算数",
                "dev_rika": "理科",
                "dev_shakai": "社会",
                "dev_4ka": "4科",
            }
        )
        st.dataframe(show_df, use_container_width=True)
    else:
        st.info("まだテスト結果が登録されていません。下記から登録してください。")

    with st.expander("📝 テスト結果を入力する"):
        col_r1, col_r2 = st.columns(2)
        r_type = col_r1.selectbox(
            "テスト種別",
            [
                "育成/合格力テスト",
                "全国公開テスト",
                "過去問",
            ],
        )
        r_date = col_r2.date_input("実施日", value=date.today())
        r_name = st.text_input(
            "テスト名（例: 第1回 合格力実践 / 第2回 公開テスト）"
        )

        r_score = st.number_input(
            "4教科合計点", min_value=0, max_value=500, value=300
        )

        st.write("**科目別 偏差値**")
        c_k, c_s, c_r, c_sy, c_4 = st.columns(5)
        dev_k = c_k.number_input("国語", 20.0, 80.0, 50.0, 0.1, format="%.1f")
        dev_s = c_s.number_input("算数", 20.0, 80.0, 50.0, 0.1, format="%.1f")
        dev_r = c_r.number_input("理科", 20.0, 80.0, 50.0, 0.1, format="%.1f")
        dev_sy = c_sy.number_input("社会", 20.0, 80.0, 50.0, 0.1, format="%.1f")
        dev_4 = c_4.number_input("4科", 20.0, 80.0, 50.0, 0.1, format="%.1f")

        if st.button("テスト結果を保存"):
            if r_name.strip():
                st.session_state.scores_db["results"].append(
                    {
                        "date": r_date.strftime("%Y-%m-%d"),
                        "type": r_type,
                        "name": r_name,
                        "score": r_score,
                        "dev_kokugo": dev_k,
                        "dev_sansu": dev_s,
                        "dev_rika": dev_r,
                        "dev_shakai": dev_sy,
                        "dev_4ka": dev_4,
                    }
                )
                save_json(SCORES_FILE, st.session_state.scores_db)
                st.success("成績を保存しました！")
                st.rerun()

        if results:
            st.write("---")
            st.write("**登録済みテスト結果の削除**")
            for idx, res in enumerate(results):
                cr1, cr2 = st.columns([4, 1])
                cr1.write(
                    f"・[{res['date']}] {res['name']} - 4科:{res.get('dev_4ka', 50)} (国:{res.get('dev_kokugo', 50)} 算:{res.get('dev_sansu', 50)} 理:{res.get('dev_rika', 50)} 社:{res.get('dev_shakai', 50)})"
                )
                if cr2.button("削除", key=f"del_res_{idx}"):
                    st.session_state.scores_db["results"].pop(idx)
                    save_json(SCORES_FILE, st.session_state.scores_db)
                    st.rerun()
