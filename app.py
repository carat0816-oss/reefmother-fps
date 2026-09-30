"""リーフマザー討伐 ─ Streamlit で遊ぶための入れ物。

ゲーム本体は static/game.html（Three.js）。Streamlit はそれをページに埋め込んで表示するだけ。
起動:  streamlit run app.py
"""
import socket
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="リーフマザー討伐", page_icon="🦑", layout="wide")

# 余白を詰めて、ゲーム画面をできるだけ大きく見せる
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.2rem; padding-bottom: 0; max-width: 100%;}
      header[data-testid="stHeader"] {background: transparent;}
    </style>
    """,
    unsafe_allow_html=True,
)

ゲームHTML = (Path(__file__).parent / "static" / "game.html").read_text(encoding="utf-8")

# 「別ウィンドウで遊ぶ」の行き先。
# 手元で start_server.bat から起動していればゲーム専用サーバー(8502)、
# それ以外（Streamlit Cloud など）は GitHub Pages に置いた同じゲームを開く。
PAGES_URL = "https://carat0816-oss.github.io/reefmother-fps/"


def ゲーム単体のURL() -> str:
    try:
        with socket.create_connection(("127.0.0.1", 8502), timeout=0.2):
            return "http://localhost:8502/game.html"
    except OSError:
        return PAGES_URL

with st.sidebar:
    st.header("🦑 リーフマザー討伐")
    高さ = st.slider("画面の高さ", 480, 1100, 760, step=20)
    st.markdown(
        """
        **操作**
        - WASD：移動 / Shift：走る / Space：ジャンプ
        - 左クリック：射撃 / 右クリック：構える
        - R：装填 / Q：爆裂矢 / E：補給箱
        - Esc：一時停止

        **攻略のヒント**
        - 光る **眼** は弱点（ダメージ約3倍）
        - 甲板の **赤い円** が出たらすぐ離れる
        - 叩きつけてきた触手を撃ち続けると **切断** できる
        - 紫の **墨弾** は撃ち落とせる
        """
    )
    st.markdown(
        """
        **視点操作の2方式**
        - **カーソル照準**（この画面の標準）：照準がマウスに付いてくる。
          カーソルを画面の端に寄せると、その方向へ振り向く
        - **マウス固定**：普通のFPSと同じ操作。この埋め込み画面では使えないので、
          下のボタンから別ウィンドウで開く
        - F キーで全画面表示
        """
    )
    st.link_button("🖥 別ウィンドウで遊ぶ（マウス固定・推奨）", ゲーム単体のURL(), type="primary", width="stretch")

components.html(ゲームHTML, height=高さ, scrolling=False)
