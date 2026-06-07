import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="バレーボールスタッツ",
    page_icon="🏐",
    layout="wide"
)

# ───────────────────────────────────────────
# 定数
# ───────────────────────────────────────────
FILE_NAME = "stats.csv"
MATCH_FILE = "matches.csv"
PLAYER_FILE = "players.csv"

SKILLS = ["サーブ", "アタック", "レシーブ", "ブロック"]
GRADES = ["A", "B", "C", "D"]

GRADE_LABELS = {
    "A": "A（得点・Aカット）",
    "B": "B（Bカット）",
    "C": "C（Cカット）",
    "D": "D（ミス）",
}
GRADE_COLORS = {
    "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"
}

# ───────────────────────────────────────────
# データ読み込み・保存
# ───────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        for col in ["試合ID", "試合名", "時間", "選手", "種類", "評価"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(
        columns=["試合ID", "試合名", "時間", "選手", "種類", "評価"]
    )


def save_data(df: pd.DataFrame) -> None:
    df.to_csv(FILE_NAME, index=False, encoding="utf-8-sig")


def load_matches() -> pd.DataFrame:
    if os.path.exists(MATCH_FILE):
        return pd.read_csv(MATCH_FILE)
    return pd.DataFrame(columns=["試合ID", "試合名", "日付"])


def save_matches(df: pd.DataFrame) -> None:
    df.to_csv(MATCH_FILE, index=False, encoding="utf-8-sig")


def load_players() -> pd.DataFrame:
    if os.path.exists(PLAYER_FILE):
        return pd.read_csv(PLAYER_FILE, dtype={"背番号": str})
    return pd.DataFrame(columns=["背番号", "名前", "選手名"])


def save_players(df: pd.DataFrame) -> None:
    df.to_csv(PLAYER_FILE, index=False, encoding="utf-8-sig")


# ───────────────────────────────────────────
# セッション管理
# ───────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_data()

if "matches" not in st.session_state:
    st.session_state.matches = load_matches()

if "players" not in st.session_state:
    st.session_state.players = load_players()

df: pd.DataFrame = st.session_state.df
matches: pd.DataFrame = st.session_state.matches
players: pd.DataFrame = st.session_state.players


def get_player_list():
    if len(players) == 0:
        return []
    return players["選手名"].tolist()


def calc_rates(target_df: pd.DataFrame) -> pd.DataFrame:
    """選手×種類ごとにA率・ミス率・総数を計算"""
    if len(target_df) == 0:
        return pd.DataFrame()
    rows = []
    for player in sorted(target_df["選手"].unique()):
        for skill in SKILLS:
            sub = target_df[
                (target_df["選手"] == player) &
                (target_df["種類"] == skill)
            ]
            total = len(sub)
            if total == 0:
                continue
            a = int((sub["評価"] == "A").sum())
            b = int((sub["評価"] == "B").sum())
            c = int((sub["評価"] == "C").sum())
            d = int((sub["評価"] == "D").sum())
            rows.append({
                "選手": player,
                "種類": skill,
                "総数": total,
                "A": a,
                "B": b,
                "C": c,
                "D": d,
                "A率": round(a / total * 100, 1),
                "ミス率": round(d / total * 100, 1),
            })
    return pd.DataFrame(rows)


# ───────────────────────────────────────────
# タイトル
# ───────────────────────────────────────────
st.title("🏐 バレーボールスタッツ")

# ───────────────────────────────────────────
# サイドバー：選手管理
# ───────────────────────────────────────────
with st.sidebar:
    st.header("👤 選手管理")

    with st.expander("選手を登録する"):
        num = st.text_input(
            "背番号",
            placeholder="例：1",
            key="reg_num"
        )
        name = st.text_input(
            "名前",
            placeholder="例：山田",
            key="reg_name"
        )
        if st.button("登録する", key="btn_add_player"):
            if num and name:
                player_name = f"{num} {name}"
                if player_name in get_player_list():
                    st.warning("すでに登録されています")
                else:
                    new_row = pd.DataFrame([{
                        "背番号": num,
                        "名前": name,
                        "選手名": player_name,
                    }])
                    st.session_state.players = pd.concat(
                        [st.session_state.players, new_row],
                        ignore_index=True
                    )
                    save_players(st.session_state.players)
                    players = st.session_state.players
                    st.success(f"「{player_name}」を登録しました")
                    st.rerun()
            else:
                st.warning("背番号と名前を入力してください")

    with st.expander("選手を削除する"):
        if len(players) > 0:
            del_player = st.selectbox(
                "削除する選手",
                get_player_list(),
                key="del_player"
            )
            if st.button("削除する", key="btn_del_player"):
                st.session_state.players = players[
                    players["選手名"] != del_player
                ]
                save_players(st.session_state.players)
                players = st.session_state.players
                st.success(f"「{del_player}」を削除しました")
                st.rerun()
        else:
            st.info("登録された選手がいません")

    st.divider()
    st.subheader("登録選手一覧")
    if len(players) > 0:
        show = players[["背番号", "名前"]].sort_values("背番号").reset_index(drop=True)
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.info("選手が登録されていません")

# ───────────────────────────────────────────
# 試合管理
# ───────────────────────────────────────────
st.subheader("📅 試合管理")

with st.expander("試合を作成する"):
    new_match = st.text_input(
        "試合名",
        placeholder="例：春高予選 vs ○○高校"
    )
    if st.button("試合を追加"):
        if new_match:
            new_id = (
                int(matches["試合ID"].max()) + 1
                if len(matches) > 0 else 1
            )
            new_row = pd.DataFrame([{
                "試合ID": new_id,
                "試合名": new_match,
                "日付": datetime.now().date()
            }])
            matches = pd.concat(
                [matches, new_row], ignore_index=True
            )
            save_matches(matches)
            st.session_state.matches = matches
            st.success(f"「{new_match}」を追加しました")
            st.rerun()
        else:
            st.warning("試合名を入力してください")

with st.expander("試合を削除する"):
    if len(matches) > 0:
        delete_match = st.selectbox(
            "削除する試合",
            matches["試合名"].tolist(),
            key="delete_match"
        )
        if st.button("試合を削除"):
            matches = matches[matches["試合名"] != delete_match]
            save_matches(matches)
            st.session_state.matches = matches

            st.session_state.df = st.session_state.df[
                st.session_state.df["試合名"] != delete_match
            ]
            save_data(st.session_state.df)
            df = st.session_state.df

            st.success(f"「{delete_match}」を削除しました")
            st.rerun()
    else:
        st.info("登録されている試合がありません")

# ───────────────────────────────────────────
# 入力エリア
# ───────────────────────────────────────────
st.divider()
st.subheader("📝 記録入力")

with st.container(border=True):
    matches = st.session_state.matches
    players = st.session_state.players

    if len(matches) == 0:
        st.warning("先に試合を登録してください")
        st.stop()

    if len(players) == 0:
        st.warning("先に選手を登録してください（左サイドバー）")
        st.stop()

    selected_match = st.selectbox(
        "試合",
        matches["試合名"].tolist()
    )

    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        player = st.selectbox(
            "選手",
            get_player_list(),
            key="input_player"
        )
    with col2:
        skill = st.selectbox("種類", SKILLS, key="input_skill")
    with col3:
        grade = st.selectbox(
            "評価",
            GRADES,
            format_func=lambda g: g,
            key="input_grade"
        )
    with col4:
        st.write("")
        record_btn = st.button(
            "✚ 記録する",
            use_container_width=True,
            type="primary"
        )

    # 評価の説明
    st.caption(
        "　".join([f"{g}：{GRADE_LABELS[g]}" for g in GRADES])
    )

if record_btn:
    selected_match_id = matches.loc[
        matches["試合名"] == selected_match, "試合ID"
    ].iloc[0]

    new_row = pd.DataFrame([{
        "試合ID": selected_match_id,
        "試合名": selected_match,
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "選手": player,
        "種類": skill,
        "評価": grade,
    }])
    st.session_state.df = pd.concat(
        [st.session_state.df, new_row], ignore_index=True
    )
    save_data(st.session_state.df)
    st.success(
        f"{GRADE_COLORS[grade]} {player} / {skill} / 評価{grade} を記録しました"
    )
    df = st.session_state.df

# ───────────────────────────────────────────
# 分析エリア
# ───────────────────────────────────────────
st.divider()
df = st.session_state.df
total_all = len(df)

# 全体メトリクス
count_a = int((df["評価"] == "A").sum()) if total_all > 0 else 0
rate_a = f"{count_a / total_all * 100:.1f}%" if total_all > 0 else "—"
count_d = int((df["評価"] == "D").sum()) if total_all > 0 else 0
rate_d = f"{count_d / total_all * 100:.1f}%" if total_all > 0 else "—"

m1, m2, m3, m4 = st.columns(4)
m1.metric("総記録数", total_all)
m2.metric("A率（全体）", rate_a)
m3.metric("ミス率（全体）", rate_d)
m4.metric("登録選手数", len(players))

st.divider()

# 試合フィルター
if len(matches) > 0:
    filter_options = ["全試合"] + matches["試合名"].tolist()
    selected_analysis_match = st.selectbox(
        "🔍 分析する試合",
        filter_options,
        key="analysis_match"
    )
    if selected_analysis_match == "全試合":
        filtered_df = df.copy()
    else:
        filtered_df = df[df["試合名"] == selected_analysis_match]
else:
    filtered_df = df.copy()

# ───────────────────────────────────────────
# 集計タブ
# ───────────────────────────────────────────
tab_team, tab_ranking, tab_player_tab, tab_log = st.tabs(
    ["📊 チーム集計", "🏆 選手ランキング", "👤 個人成績", "📋 記録ログ"]
)

# ── チーム集計 ────────────────────────────
with tab_team:
    if len(filtered_df) == 0:
        st.info("データがありません")
    else:
        st.subheader("種類ごとのA率・ミス率")
        team_rows = []
        for skill in SKILLS:
            sub = filtered_df[filtered_df["種類"] == skill]
            total = len(sub)
            if total == 0:
                continue
            a = int((sub["評価"] == "A").sum())
            d = int((sub["評価"] == "D").sum())
            team_rows.append({
                "種類": skill,
                "総数": total,
                "A（得点）": a,
                "D（ミス）": d,
                "A率": f"{a/total*100:.1f}%",
                "ミス率": f"{d/total*100:.1f}%",
            })
        if team_rows:
            team_df = pd.DataFrame(team_rows).set_index("種類")
            st.dataframe(team_df, use_container_width=True)

            st.subheader("種類別 評価内訳（棒グラフ）")
            chart_base = (
                filtered_df.groupby(["種類", "評価"])
                .size()
                .unstack("評価", fill_value=0)
                .reindex(columns=GRADES, fill_value=0)
            )
            st.bar_chart(chart_base, use_container_width=True)

        if selected_analysis_match == "全試合" and len(matches) > 1:
            st.subheader("試合ごとの比較")
            match_rows = []
            for _, m in matches.iterrows():
                mdf = df[df["試合名"] == m["試合名"]]
                total = len(mdf)
                if total == 0:
                    continue
                a = int((mdf["評価"] == "A").sum())
                d = int((mdf["評価"] == "D").sum())
                match_rows.append({
                    "試合名": m["試合名"],
                    "日付": m["日付"],
                    "総数": total,
                    "A率": f"{a/total*100:.1f}%",
                    "ミス率": f"{d/total*100:.1f}%",
                })
            if match_rows:
                st.dataframe(
                    pd.DataFrame(match_rows).set_index("試合名"),
                    use_container_width=True
                )

# ── 選手ランキング ─────────────────────────
with tab_ranking:
    if len(filtered_df) == 0:
        st.info("データがありません")
    else:
        rate_df = calc_rates(filtered_df)
        if len(rate_df) == 0:
            st.info("データがありません")
        else:
            rank_skill = st.selectbox(
                "種類で絞り込む",
                ["全種類"] + SKILLS,
                key="rank_skill"
            )

            if rank_skill == "全種類":
                # 選手ごとに集計
                rank_rows = []
                for player_name in sorted(filtered_df["選手"].unique()):
                    sub = filtered_df[filtered_df["選手"] == player_name]
                    total = len(sub)
                    a = int((sub["評価"] == "A").sum())
                    d = int((sub["評価"] == "D").sum())
                    rank_rows.append({
                        "選手": player_name,
                        "総数": total,
                        "A": a,
                        "D": d,
                        "A率": round(a / total * 100, 1),
                        "ミス率": round(d / total * 100, 1),
                    })
                rank_result = (
                    pd.DataFrame(rank_rows)
                    .sort_values("A率", ascending=False)
                    .reset_index(drop=True)
                )
                rank_result.index += 1
            else:
                rank_result = (
                    rate_df[rate_df["種類"] == rank_skill]
                    [["選手", "総数", "A", "D", "A率", "ミス率"]]
                    .sort_values("A率", ascending=False)
                    .reset_index(drop=True)
                )
                rank_result.index += 1

            st.dataframe(rank_result, use_container_width=True)

# ── 個人成績 ──────────────────────────────
with tab_player_tab:
    if len(filtered_df) == 0:
        st.info("データがありません")
    else:
        players_recorded = sorted(filtered_df["選手"].unique())
        selected_player = st.selectbox(
            "選手を選択",
            players_recorded,
            key="player_filter"
        )
        player_df = filtered_df[filtered_df["選手"] == selected_player]

        # 個人メトリクス
        p_total = len(player_df)
        p_a = int((player_df["評価"] == "A").sum())
        p_d = int((player_df["評価"] == "D").sum())
        pm1, pm2, pm3 = st.columns(3)
        pm1.metric("総数", p_total)
        pm2.metric("A率", f"{p_a/p_total*100:.1f}%" if p_total > 0 else "—")
        pm3.metric("ミス率", f"{p_d/p_total*100:.1f}%" if p_total > 0 else "—")

        st.subheader("種類別 詳細")
        result = (
            player_df.groupby(["種類", "評価"])
            .size()
            .unstack("評価", fill_value=0)
            .reindex(index=SKILLS, columns=GRADES, fill_value=0)
        )
        # A率・ミス率を追加
        result["A率"] = (
            result["A"] / result.sum(axis=1) * 100
        ).round(1).astype(str) + "%"
        result["ミス率"] = (
            result["D"] / result.sum(axis=1) * 100
        ).round(1).astype(str) + "%"
        st.dataframe(result, use_container_width=True)

        st.subheader("評価内訳（グラフ）")
        chart_data = (
            player_df.groupby(["種類", "評価"])
            .size()
            .unstack("評価", fill_value=0)
            .reindex(index=SKILLS, columns=GRADES, fill_value=0)
        )
        st.bar_chart(chart_data, use_container_width=True)

# ── 記録ログ ──────────────────────────────
with tab_log:
    if len(filtered_df) == 0:
        st.info("データがありません")
    else:
        log_df = filtered_df.iloc[::-1].reset_index(drop=True)
        st.dataframe(log_df, use_container_width=True, height=400)

        csv = filtered_df.to_csv(
            index=False, encoding="utf-8-sig"
        ).encode("utf-8-sig")
        st.download_button(
            label="⬇ CSVをダウンロード",
            data=csv,
            file_name=f"volleyball_stats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
