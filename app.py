"""リーフマザー討伐 ─ Streamlit で遊ぶための入れ物＋射撃分析データの集約。

ゲーム本体は static/game.html（Three.js）。双方向のカスタムコンポーネントとして埋め込み、
- ゲーム → Python：射撃分析モードで「データ提供に同意」した人の1回分のデータを受け取り、保存する（store.py）
- Python → ゲーム：保存済みの全員分のデータを渡し、ゲーム内のデータラボで「みんなのデータ」として分析できるようにする
起動:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from store import clean_run, get_store

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

# static/ フォルダをそのままコンポーネントとして配信する（index.html → game.html）
reef_game = components.declare_component("reef_game", path=str(Path(__file__).parent / "static"))

MAX_SHARED = 600        # ゲームに渡す「みんなのデータ」の最大回数（新しい順）
MAX_PER_SESSION = 40    # 1回の接続で受け付ける最大回数（いたずら対策）

store = get_store()


@st.cache_data(ttl=60, show_spinner=False)
def load_shared() -> list[dict]:
    return store.load(MAX_SHARED)


with st.sidebar:
    st.header("🦑 リーフマザー討伐")
    高さ = st.slider("画面の高さ", 480, 1100, 760, step=20)
    st.markdown(
        """
        **操作**
        - WASD：移動 / Shift：走る / Space：ジャンプ
        - 方向キー：視点（押し続けると速く回る）
        - 左クリック：射撃 / 右クリック：構える
        - R：装填 / Q：爆裂矢 / E：補給箱
        - Esc：一時停止

        **視点操作**
        - この画面では「カーソル照準」（照準がマウスに付いてくる。画面の端で振り向く）
        - タイトルの「別ウィンドウで遊ぶ」から開くと、普通のFPSと同じ「マウス固定」で遊べます。
          射撃分析モードのデータもそのまま送られます
        - F キーで全画面表示

        **射撃分析モード**
        - 30秒・ボスなし。終わると分析レポートが出ます
        - 開始前に「データ提供に同意」すると、その回のデータが集められ、
          データラボの「みんなのデータ」で全員分の分析に使われます
        """
    )
    try:
        n_shared = len(load_shared())
    except Exception as e:  # 保存先に一時的につながらなくてもゲームは遊べるようにする
        n_shared = None
        st.warning(f"データの読み込みに失敗しました：{e}")
    st.caption(f"保存先：{store.label}" + (f" ／ 集まった記録：{n_shared} 回" if n_shared is not None else ""))
    if store.kind == "local":
        st.caption("※ Secrets にスプレッドシートの設定がないため、手元のファイルに保存しています")

try:
    shared = load_shared()
except Exception:
    shared = []

value = reef_game(
    height=高さ,
    shared={"runs": shared, "store": store.kind},
    key="reef",
    default=None,
)

# ゲームから届いた1回分を保存する（同じ回を二重に保存しないよう、保存済みの id を覚えておく）
saved = st.session_state.setdefault("saved_ids", set())
if isinstance(value, dict) and value.get("type") == "run" and value.get("consent") is True:
    run = clean_run(value.get("run"))
    if run and run["id"] not in saved and len(saved) < MAX_PER_SESSION:
        try:
            store.append(run)
            saved.add(run["id"])
            load_shared.clear()
            st.rerun()  # 保存したばかりの回も入った「みんなのデータ」をゲームに渡し直す
        except Exception as e:
            st.toast(f"データの保存に失敗しました：{e}", icon="⚠️")
