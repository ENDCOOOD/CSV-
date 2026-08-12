import streamlit as st
import pandas as pd
import json
import google.generativeai as genai

# --- 1. ページ設定とタイトル ---
st.set_page_config(page_title="会計仕訳一括変換アプリ", page_icon="📑", layout="wide")
st.title("📑 ScanSnap & 手入力 AI会計自動化アプリ")
st.caption("Gemini AIがレシート・請求書を解析し、各社インポート用CSVを生成します。")

# --- 2. APIキーの設定 ---
# クラウド環境では secrets.toml から安全に読み込みます
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("⚠️ Gemini APIキーが設定されていません。")

# --- 3. ファイルアップロード（ScanSnap / 手動） ---
st.subheader("1. 会計資料のアップロード")
uploaded_file = st.file_uploader("PDFまたは画像ファイルをアップロードしてください", type=["pdf", "png", "jpg", "jpeg"])

# --- 4. 解析処理とプレビュー表示 ---
if uploaded_file and API_KEY:
    if st.button("🚀 AIで解析を開始する", type="primary"):
        with st.spinner("Geminiがデータを読み取り中..."):
            # ※本来はここでGemini APIを呼び出して画像/PDFを読み込ませます
            # ここでは解析されたデータとして処理をデモ実行します
            extracted_data = [
                {"date": "2026-08-10", "vendor": "スターバックスコーヒー 港区店", "category": "会議費", "payment_method": "現金", "amount": 1650},
                {"date": "2026-08-12", "vendor": "日本タクシー", "category": "旅費交通費", "payment_method": "現金", "amount": 3200}
            ]
            st.session_state['parsed_data'] = extracted_data
            st.success("解析が完了しました！")

if 'parsed_data' in st.session_state:
    data = st.session_state['parsed_data']
    df_preview = pd.DataFrame(data)
    
    st.subheader("2. 読み取り結果のプレビュー・確認")
    st.dataframe(df_preview, use_container_width=True)

    # --- 5. 3社別 CSV出力機能 ---
    st.subheader("3. 会計ソフトを選択して出力")
    col1, col2, col3 = st.columns(3)

    # 【マネーフォワード用】
    with col1:
        mf_rows = []
        for idx, row in enumerate(data):
            mf_rows.append({
                "取引No": idx + 1, "取引日": row["date"].replace("-", "/"),
                "借方勘定科目": row["category"], "借方金額(円)": row["amount"],
                "貸方勘定科目": row["payment_method"], "貸方金額(円)": row["amount"],
                "摘要": f"{row['vendor']} ({row['category']})"
            })
        df_mf = pd.DataFrame(mf_rows)
        csv_mf = df_mf.to_csv(index=False, encoding="shift_jis").encode("shift_jis", errors="replace")
        st.download_button("🏢 マネーフォワード用CSV", csv_mf, "MF_Import.csv", "text/csv", use_container_width=True)

    # 【freee用】
    with col2:
        freee_rows = []
        for row in data:
            freee_rows.append({
                "収支区分": "支出", "発生日": row["date"], "勘定科目": row["category"],
                "決済状態": "完了", "決済口座": row["payment_method"], "金額": row["amount"], "取引先": row["vendor"]
            })
        df_freee = pd.DataFrame(freee_rows)
        csv_freee = df_freee.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("🟢 freee用CSV", csv_freee, "freee_Import.csv", "text/csv", use_container_width=True)

    # 【ICS用】
    with col3:
        ics_rows = []
        for idx, row in enumerate(data):
            ics_rows.append({
                "日付": row["date"].replace("-", "/"), "相手方ｺｰﾄﾞ": "154",
                "相手方名称": row["vendor"], "摘要": row["category"], "出金": row["amount"]
            })
        df_ics = pd.DataFrame(ics_rows)
        csv_ics = df_ics.to_csv(index=False, encoding="shift_jis").encode("shift_jis", errors="replace")
        st.download_button("🔵 ICS用CSV", csv_ics, "ICS_Import.csv", "text/csv", use_container_width=True)
