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
 
PLAYERS = [
    "1 山田", "2 佐藤", "3 鈴木",
    "4 高橋", "5 伊藤", "6 渡辺",
]
SKILLS = ["サーブ", "アタック", "レシーブ", "ブロック"]
GRADES = ["A", "B", "C", "D"]
 
GRADE_COLORS = {
    "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"
}
 
# ───────────────────────────────────────────
# データ読み込み（キャッシュ対策：セッション管理）
# ───────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # カラムが足りない場合は補完
        for col in ["時間", "選手", "種類", "評価"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["時間", "選手", "種類", "評価"])
 
 
def save_data(df: pd.DataFrame) -> None:
    df.to_csv(FILE_NAME, index=False, encoding="utf-8-sig")
 
 
# セッション内にデータを保持し、ページ再読み込みでも最新を反映
if "df" not in st.session_state:
    st.session_state.df = load_data()
 
df: pd.DataFrame = st.session_state.df
 
# ───────────────────────────────────────────
# タイトル
# ───────────────────────────────────────────
st.title("🏐 バレーボールスタッツ")
 
# ───────────────────────────────────────────
# 入力エリア
# ───────────────────────────────────────────
with st.container(border=True):
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        player = st.selectbox("選手", PLAYERS, key="input_player")
    with col2:
        skill = st.selectbox("種類", SKILLS, key="input_skill")
    with col3:
        grade = st.selectbox("評価", GRADES, key="input_grade")
    with col4:
        st.write("")  # ラベル分の余白
        record_btn = st.button("✚ 記録する", use_container_width=True, type="primary")
 
if record_btn:
    new_row = pd.DataFrame([{
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "選手": player,
        "種類": skill,
        "評価": grade,
    }])
    st.session_state.df = pd.concat(
        [st.session_state.df, new_row], ignore_index=True
    )
    save_data(st.session_state.df)
    st.success(f"{GRADE_COLORS[grade]} {player} / {skill} / {grade} を記録しました")
    df = st.session_state.df  # ローカル変数も更新
 
# ───────────────────────────────────────────
# メトリクス
# ───────────────────────────────────────────
st.divider()
 
total = len(df)
count_a = int((df["評価"] == "A").sum()) if total > 0 else 0
rate_a = f"{count_a / total * 100:.1f}%" if total > 0 else "—"
player_count = df["選手"].nunique() if total > 0 else 0
 
m1, m2, m3, m4 = st.columns(4)
m1.metric("総記録数", total)
m2.metric("A 評価数", count_a)
m3.metric("A 評価率", rate_a)
m4.metric("登録選手数", player_count)
 
# ───────────────────────────────────────────
# 集計タブ
# ───────────────────────────────────────────
st.divider()
 
tab_summary, tab_player, tab_log = st.tabs(["📊 全体集計", "👤 個人成績", "📋 記録ログ"])
 
# ── 全体集計 ──────────────────────────────
with tab_summary:
    if total == 0:
        st.info("まだデータがありません")
    else:
        summary = (
            df.groupby(["選手", "種類", "評価"])
            .size()
            .unstack("評価", fill_value=0)
            .reindex(columns=GRADES, fill_value=0)  # 未記録のグレード列も必ず表示
        )
        st.dataframe(summary, use_container_width=True)
 
# ── 個人成績 ──────────────────────────────
with tab_player:
    if total == 0:
        st.info("まだデータがありません")
    else:
        players_recorded = sorted(df["選手"].unique())
        selected_player = st.selectbox(
            "選手を選択",
            players_recorded,
            key="player_filter",
        )
        player_df = df[df["選手"] == selected_player]
 
        result = (
            player_df.groupby(["種類", "評価"])
            .size()
            .unstack("評価", fill_value=0)
            .reindex(index=SKILLS, columns=GRADES, fill_value=0)  # 全種類・全評価を表示
        )
        st.dataframe(result, use_container_width=True)
 
        # 棒グラフ（種類ごとの評価内訳）
        chart_data = result.reset_index().melt(
            id_vars="種類", var_name="評価", value_name="回数"
        )
        st.bar_chart(
            chart_data.pivot(index="種類", columns="評価", values="回数"),
            use_container_width=True,
        )
 
# ── 記録ログ ──────────────────────────────
with tab_log:
    if total == 0:
        st.info("まだデータがありません")
    else:
        log_df = df.iloc[::-1].reset_index(drop=True)  # 新しい順
        st.dataframe(log_df, use_container_width=True, height=400)
 
        # CSVダウンロード
        csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇ CSVをダウンロード",
            data=csv,
            file_name=f"volleyball_stats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
