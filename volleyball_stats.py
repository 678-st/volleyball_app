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
FILE_NAME    = "stats.csv"
MATCH_FILE   = "matches.csv"
PLAYER_FILE  = "players.csv"

SKILLS = ["サーブ", "アタック", "レシーブ", "ブロック"]
GRADES = ["A", "B", "C", "D"]
GRADE_LABELS = {
    "A": "A（得点・Aカット）",
    "B": "B（Bカット）",
    "C": "C（Cカット）",
    "D": "D（ミス）",
}
GRADE_COLORS = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}

MATCH_TYPES   = ["練習試合", "公式戦"]
TOURNAMENTS   = ["高体連", "高専大会"]

# 現在の年度を自動計算（4月始まり）
def current_nendo() -> int:
    now = datetime.now()
    return now.year if now.month >= 4 else now.year - 1

NENDO_OPTIONS = [f"R{(y - 2018)}" for y in range(current_nendo() - 3, current_nendo() + 2)]
NENDO_DEFAULT = f"R{current_nendo() - 2018}"

# ───────────────────────────────────────────
# データ読み込み・保存
# ───────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        for col in ["試合ID", "試合名", "種別", "大会", "年度", "時間", "選手", "種類", "評価"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["試合ID", "試合名", "種別", "大会", "年度", "時間", "選手", "種類", "評価"])


def save_data(df: pd.DataFrame) -> None:
    df.to_csv(FILE_NAME, index=False, encoding="utf-8-sig")


def load_matches() -> pd.DataFrame:
    if os.path.exists(MATCH_FILE):
        df = pd.read_csv(MATCH_FILE)
        for col in ["試合ID", "試合名", "種別", "大会", "年度", "日付"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["試合ID", "試合名", "種別", "大会", "年度", "日付"])


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
if "df"      not in st.session_state: st.session_state.df      = load_data()
if "matches" not in st.session_state: st.session_state.matches = load_matches()
if "players" not in st.session_state: st.session_state.players = load_players()

df      = st.session_state.df
matches = st.session_state.matches
players = st.session_state.players


def get_player_list():
    return players["選手名"].tolist() if len(players) > 0 else []


def calc_rates(target_df: pd.DataFrame) -> pd.DataFrame:
    if len(target_df) == 0:
        return pd.DataFrame()
    rows = []
    for player in sorted(target_df["選手"].unique()):
        for skill in SKILLS:
            sub = target_df[(target_df["選手"] == player) & (target_df["種類"] == skill)]
            total = len(sub)
            if total == 0:
                continue
            a = int((sub["評価"] == "A").sum())
            d = int((sub["評価"] == "D").sum())
            rows.append({
                "選手": player, "種類": skill, "総数": total,
                "A": a, "B": int((sub["評価"] == "B").sum()),
                "C": int((sub["評価"] == "C").sum()), "D": d,
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
        num  = st.text_input("背番号", placeholder="例：1",  key="reg_num")
        name = st.text_input("名前",   placeholder="例：山田", key="reg_name")
        if st.button("登録する", key="btn_add_player"):
            if num and name:
                pname = f"{num} {name}"
                if pname in get_player_list():
                    st.warning("すでに登録されています")
                else:
                    new_row = pd.DataFrame([{"背番号": num, "名前": name, "選手名": pname}])
                    st.session_state.players = pd.concat(
                        [st.session_state.players, new_row], ignore_index=True)
                    save_players(st.session_state.players)
                    st.success(f"「{pname}」を登録しました")
                    st.rerun()
            else:
                st.warning("背番号と名前を入力してください")

    with st.expander("選手を削除する"):
        if len(players) > 0:
            del_player = st.selectbox("削除する選手", get_player_list(), key="del_player")
            if st.button("削除する", key="btn_del_player"):
                st.session_state.players = players[players["選手名"] != del_player]
                save_players(st.session_state.players)
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
st.subheader("試合管理")

with st.expander("試合を作成する"):
    c1, c2, c3 = st.columns(3)
    with c1:
        new_type = st.selectbox("種別", MATCH_TYPES, key="new_type")
    with c2:
        # 練習試合のときは大会選択不要
        if new_type == "公式戦":
            new_tourn = st.selectbox("大会", TOURNAMENTS, key="new_tourn")
        else:
            new_tourn = "—"
            st.selectbox("大会", ["—"], disabled=True, key="new_tourn_dis")
    with c3:
        new_nendo = st.selectbox(
            "年度", NENDO_OPTIONS,
            index=NENDO_OPTIONS.index(NENDO_DEFAULT),
            key="new_nendo"
        )
    new_match = st.text_input("試合名", placeholder="例：Rn-関東高専大会-vs○○高専")
    if st.button("試合を追加"):
        if new_match:
            new_id = int(matches["試合ID"].max()) + 1 if len(matches) > 0 else 1
            new_row = pd.DataFrame([{
                "試合ID": new_id,
                "試合名": new_match,
                "種別":   new_type,
                "大会":   new_tourn,
                "年度":   new_nendo,
                "日付":   datetime.now().date(),
            }])
            matches = pd.concat([matches, new_row], ignore_index=True)
            save_matches(matches)
            st.session_state.matches = matches
            st.success(f"「{new_nendo} / {new_type} / {new_tourn} / {new_match}」を追加しました")
            st.rerun()
        else:
            st.warning("試合名を入力してください")

with st.expander("試合を削除する"):
    if len(matches) > 0:
        match_labels = (
            matches["年度"] + " | " + matches["種別"] + " | " +
            matches["大会"] + " | " + matches["試合名"]
        )
        del_idx = st.selectbox("削除する試合", match_labels.tolist(), key="delete_match")
        if st.button("試合を削除"):
            del_name = matches.loc[match_labels == del_idx, "試合名"].iloc[0]
            matches = matches[match_labels != del_idx]
            save_matches(matches)
            st.session_state.matches = matches
            st.session_state.df = st.session_state.df[
                st.session_state.df["試合名"] != del_name]
            save_data(st.session_state.df)
            df = st.session_state.df
            st.success(f"「{del_name}」を削除しました")
            st.rerun()
    else:
        st.info("登録されている試合がありません")

# 試合一覧表示
if len(matches) > 0:
    with st.expander("試合一覧を見る"):
        show_matches = matches[["年度", "種別", "大会", "試合名", "日付"]].sort_values(
            ["年度", "種別", "大会"], ascending=[False, True, True]
        ).reset_index(drop=True)
        st.dataframe(show_matches, use_container_width=True, hide_index=True)

# ───────────────────────────────────────────
# 入力エリア
# ───────────────────────────────────────────
st.divider()
st.subheader("記録入力")

with st.container(border=True):
    matches = st.session_state.matches
    players = st.session_state.players

    if len(matches) == 0:
        st.warning("先に試合を登録してください")
        st.stop()
    if len(players) == 0:
        st.warning("先に選手を登録してください（左サイドバー）")
        st.stop()

    # 試合をドリルダウンで選ぶ
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        input_type = st.selectbox("種別", ["すべて"] + MATCH_TYPES, key="input_type")
    with ic2:
        if input_type == "公式戦":
            tourn_opts = ["すべて"] + TOURNAMENTS
        elif input_type == "練習試合":
            tourn_opts = ["—"]
        else:
            tourn_opts = ["すべて"] + TOURNAMENTS + ["—"]
        input_tourn = st.selectbox("大会", tourn_opts, key="input_tourn")
    with ic3:
        input_nendo = st.selectbox("年度", ["すべて"] + NENDO_OPTIONS, key="input_nendo")

    # フィルタリングして試合を絞り込む
    match_filtered = matches.copy()
    if input_type  != "すべて": match_filtered = match_filtered[match_filtered["種別"] == input_type]
    if input_tourn != "すべて": match_filtered = match_filtered[match_filtered["大会"] == input_tourn]
    if input_nendo != "すべて": match_filtered = match_filtered[match_filtered["年度"] == input_nendo]

    if len(match_filtered) == 0:
        st.warning("条件に合う試合がありません。試合を先に登録してください。")
        st.stop()

    match_labels_input = (
        match_filtered["年度"] + " | " + match_filtered["種別"] + " | " +
        match_filtered["大会"] + " | " + match_filtered["試合名"]
    )
    selected_match_label = st.selectbox("試合", match_labels_input.tolist(), key="input_match")
    selected_match_row = match_filtered.loc[match_labels_input == selected_match_label].iloc[0]

    rc1, rc2, rc3, rc4 = st.columns([2, 2, 1, 1])
    with rc1:
        player = st.selectbox("選手", get_player_list(), key="input_player")
    with rc2:
        skill = st.selectbox("種類", SKILLS, key="input_skill")
    with rc3:
        grade = st.selectbox("評価", GRADES, key="input_grade")
    with rc4:
        st.write("")
        record_btn = st.button("✚ 記録する", use_container_width=True, type="primary")

    st.caption("　".join([f"{g}：{GRADE_LABELS[g]}" for g in GRADES]))

if record_btn:
    new_row = pd.DataFrame([{
        "試合ID": selected_match_row["試合ID"],
        "試合名": selected_match_row["試合名"],
        "種別":   selected_match_row["種別"],
        "大会":   selected_match_row["大会"],
        "年度":   selected_match_row["年度"],
        "時間":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "選手":   player,
        "種類":   skill,
        "評価":   grade,
    }])
    st.session_state.df = pd.concat(
        [st.session_state.df, new_row], ignore_index=True)
    save_data(st.session_state.df)
    st.success(f"{GRADE_COLORS[grade]} {player} / {skill} / 評価{grade} を記録しました")
    df = st.session_state.df

# ───────────────────────────────────────────
# 分析エリア
# ───────────────────────────────────────────
st.divider()
df = st.session_state.df
total_all = len(df)

count_a = int((df["評価"] == "A").sum()) if total_all > 0 else 0
count_d = int((df["評価"] == "D").sum()) if total_all > 0 else 0
rate_a  = f"{count_a / total_all * 100:.1f}%" if total_all > 0 else "—"
rate_d  = f"{count_d / total_all * 100:.1f}%" if total_all > 0 else "—"

m1, m2, m3, m4 = st.columns(4)
m1.metric("総記録数",    total_all)
m2.metric("A率（全体）", rate_a)
m3.metric("ミス率（全体）", rate_d)
m4.metric("登録選手数",  len(players))

# ── ドリルダウン絞り込み ──────────────────
st.divider()
st.subheader("🔍 分析する試合を絞り込む")

fa1, fa2, fa3 = st.columns(3)
with fa1:
    f_type = st.selectbox("① 種別", ["すべて"] + MATCH_TYPES, key="f_type")
with fa2:
    if f_type == "練習試合":
        f_tourn_opts = ["—"]
    elif f_type == "公式戦":
        f_tourn_opts = ["すべて"] + TOURNAMENTS
    else:
        f_tourn_opts = ["すべて"] + TOURNAMENTS + ["—"]
    f_tourn = st.selectbox("② 大会", f_tourn_opts, key="f_tourn")
with fa3:
    f_nendo = st.selectbox("③ 年度", ["すべて"] + NENDO_OPTIONS, key="f_nendo")

filtered_df = df.copy()
if f_type  != "すべて": filtered_df = filtered_df[filtered_df["種別"] == f_type]
if f_tourn != "すべて": filtered_df = filtered_df[filtered_df["大会"] == f_tourn]
if f_nendo != "すべて": filtered_df = filtered_df[filtered_df["年度"] == f_nendo]

# 絞り込み結果のサマリー表示
hit_matches = filtered_df["試合名"].nunique() if len(filtered_df) > 0 else 0
st.caption(f"対象：{len(filtered_df)} 件の記録 ／ {hit_matches} 試合")

# さらに試合単位で絞る（任意）
if hit_matches > 1 and len(filtered_df) > 0:
    match_opts = ["すべて"] + sorted(filtered_df["試合名"].unique().tolist())
    f_match = st.selectbox("試合（任意）", match_opts, key="f_match")
    if f_match != "すべて":
        filtered_df = filtered_df[filtered_df["試合名"] == f_match]

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
                "種類": skill, "総数": total,
                "A（得点）": a, "D（ミス）": d,
                "A率": f"{a/total*100:.1f}%",
                "ミス率": f"{d/total*100:.1f}%",
            })
        if team_rows:
            st.dataframe(
                pd.DataFrame(team_rows).set_index("種類"),
                use_container_width=True
            )
            st.subheader("種類別 評価内訳")
            chart_base = (
                filtered_df.groupby(["種類", "評価"])
                .size().unstack("評価", fill_value=0)
                .reindex(columns=GRADES, fill_value=0)
            )
            st.bar_chart(chart_base, use_container_width=True)

        # 試合ごとの比較（複数試合が対象のとき）
        if filtered_df["試合名"].nunique() > 1:
            st.subheader("試合ごとの比較")
            match_rows = []
            for mname in filtered_df["試合名"].unique():
                mdf = filtered_df[filtered_df["試合名"] == mname]
                total = len(mdf)
                a = int((mdf["評価"] == "A").sum())
                d = int((mdf["評価"] == "D").sum())
                row = matches[matches["試合名"] == mname].iloc[0]
                match_rows.append({
                    "年度": row["年度"], "種別": row["種別"],
                    "大会": row["大会"], "試合名": mname,
                    "総数": total,
                    "A率": f"{a/total*100:.1f}%",
                    "ミス率": f"{d/total*100:.1f}%",
                })
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
        rank_skill = st.selectbox(
            "種類で絞り込む", ["全種類"] + SKILLS, key="rank_skill")

        if rank_skill == "全種類":
            rank_rows = []
            for pname in sorted(filtered_df["選手"].unique()):
                sub = filtered_df[filtered_df["選手"] == pname]
                total = len(sub)
                a = int((sub["評価"] == "A").sum())
                d = int((sub["評価"] == "D").sum())
                rank_rows.append({
                    "選手": pname, "総数": total, "A": a, "D": d,
                    "A率": round(a / total * 100, 1),
                    "ミス率": round(d / total * 100, 1),
                })
            rank_result = (
                pd.DataFrame(rank_rows)
                .sort_values("A率", ascending=False)
                .reset_index(drop=True)
            )
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
        selected_player = st.selectbox(
            "選手を選択",
            sorted(filtered_df["選手"].unique()),
            key="player_filter"
        )
        player_df = filtered_df[filtered_df["選手"] == selected_player]

        p_total = len(player_df)
        p_a = int((player_df["評価"] == "A").sum())
        p_d = int((player_df["評価"] == "D").sum())
        pm1, pm2, pm3 = st.columns(3)
        pm1.metric("総数", p_total)
        pm2.metric("A率",   f"{p_a/p_total*100:.1f}%" if p_total > 0 else "—")
        pm3.metric("ミス率", f"{p_d/p_total*100:.1f}%" if p_total > 0 else "—")

        st.subheader("種類別 詳細")
        result = (
            player_df.groupby(["種類", "評価"]).size()
            .unstack("評価", fill_value=0)
            .reindex(index=SKILLS, columns=GRADES, fill_value=0)
        )
        row_totals = result[GRADES].sum(axis=1)
        result["A率"]   = (result["A"] / row_totals * 100).round(1).astype(str) + "%"
        result["ミス率"] = (result["D"] / row_totals * 100).round(1).astype(str) + "%"
        st.dataframe(result, use_container_width=True)

        st.subheader("評価内訳（グラフ）")
        chart_data = (
            player_df.groupby(["種類", "評価"]).size()
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

        csv = filtered_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇ CSVをダウンロード",
            data=csv,
            file_name=f"volleyball_stats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
