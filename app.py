import streamlit as st
import pandas as pd
import json
import google.generativeai as genai

# --- 1. ページ設定とタイトル ---
st.set_page_config(page_title="会計仕訳一括変換アプリ", page_icon="📑", layout="wide")
st.title("📑 ScanSnap & 手入力 AI会計自動化アプリ")
st.caption("Gemini AIがレシート・請求書(PDF/画像)を解析し、各社インポート用CSVを生成します。")

# --- 2. APIキーの設定 ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("⚠️ Gemini APIキーが設定されていません。Streamlit Cloudの「Secrets」に GEMINI_API_KEY を設定してください。")

# --- 3. ファイルアップロード ---
st.subheader("1. 会計資料のアップロード")
uploaded_file = st.file_uploader("PDFまたは画像ファイルをアップロードしてください", type=["pdf", "png", "jpg", "jpeg"])

# --- 4. Gemini AIによるリアル解析処理 ---
if uploaded_file and API_KEY:
    if st.button("🚀 AIで解析を開始する", type="primary"):
        with st.spinner("Gemini AIがPDF/画像を解析中..."):
            try:
                # アップロードファイルをGemini APIに渡すデータ形式に変換
                bytes_data = uploaded_file.getvalue()
                mime_type = uploaded_file.type
                
                # 最新の Gemini 2.0 Flash モデルを使用
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # プロンプト（抽出フォーマットの指定）
                prompt = """
                提示された領収書、レシート、または請求書(PDF/画像)から以下の情報を読み取り、指定のJSON配列形式のみで出力してください。
                解説文やMarkdownの装飾(```json 等)は一切含めないでください。

                [
                  {
                    "date": "YYYY-MM-DD",
                    "vendor": "支払先名称",
                    "category": "勘定科目 (例: 会議費, 旅費交通費, 消耗品費, 通信費, 雑費等から推測)",
                    "payment_method": "現金 または 預金 または クレジットカード",
                    "amount": 1000
                  }
                ]
                """
                
                # AIへ解析依頼
                response = model.generate_content([
                    {"mime_type": mime_type, "data": bytes_data},
                    prompt
                ])
                
                # クリーニングとJSONパース
                res_text = response.text.strip()
                if res_text.startswith("```json"):
                    res_text = res_text[7:]
                if res_text.startswith("```"):
                    res_text = res_text[3:]
                if res_text.endswith("```"):
                    res_text = res_text[:-3]
                
                extracted_data = json.loads(res_text.strip())
                st.session_state['parsed_data'] = extracted_data
                st.success("解析が完了しました！")
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

# --- 5. 解析結果の表示とCSVダウンロード ---
if 'parsed_data' in st.session_state:
    data = st.session_state['parsed_data']
    df_preview = pd.DataFrame(data)
    
    st.subheader("2. 読み取り結果のプレビュー・確認")
    st.dataframe(df_preview, use_container_width=True)

    # 3社別 CSV出力機能
    st.subheader("3. 会計ソフトを選択して出力")
    col1, col2, col3 = st.columns(3)

    # 【マネーフォワード用】
    with col1:
        mf_rows = []
        for idx, row in enumerate(data):
            mf_rows.append({
                "取引No": idx + 1, "取引日": str(row.get("date","")).replace("-", "/"),
                "借方勘定科目": row.get("category",""), "借方金額(円)": row.get("amount",0),
                "貸方勘定科目": row.get("payment_method","現金"), "貸方金額(円)": row.get("amount",0),
                "摘要": f"{row.get('vendor','')} ({row.get('category','')})"
            })
        df_mf = pd.DataFrame(mf_rows)
        csv_mf = df_mf.to_csv(index=False, encoding="shift_jis", errors="replace").encode("shift_jis", errors="replace")
        st.download_button("🏢 マネーフォワード用CSV", csv_mf, "MF_Import.csv", "text/csv", use_container_width=True)

    # 【freee用】
    with col2:
        freee_rows = []
        for row in data:
            freee_rows.append({
                "収支区分": "支出", "発生日": row.get("date",""), "勘定科目": row.get("category",""),
                "決済状態": "完了", "決済口座": row.get("payment_method","現金"), "金額": row.get("amount",0), "取引先": row.get("vendor","")
            })
        df_freee = pd.DataFrame(freee_rows)
        csv_freee = df_freee.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("🟢 freee用CSV", csv_freee, "freee_Import.csv", "text/csv", use_container_width=True)

    # 【ICS用】
    with col3:
        ics_rows = []
        for idx, row in enumerate(data):
            ics_rows.append({
                "日付": str(row.get("date","")).replace("-", "/"), "相手方ｺｰﾄﾞ": "154",
                "相手方名称": row.get("vendor",""), "摘要": row.get("category",""), "出金": row.get("amount",0)
            })
        df_ics = pd.DataFrame(ics_rows)
        csv_ics = df_ics.to_csv(index=False, encoding="shift_jis", errors="replace").encode("shift_jis", errors="replace")
        st.download_button("🔵 ICS用CSV", csv_ics, "ICS_Import.csv", "text/csv", use_container_width=True)
