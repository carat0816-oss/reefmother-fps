"""射撃分析モードのプレイデータを保存・読み込みする。

- Streamlit の Secrets に Google のサービスアカウントとスプレッドシートの URL があれば、Googleスプレッドシートに保存する
- なければ、手元の data/runs.jsonl に保存する（ローカルでの動作確認用。Streamlit Community Cloud ではアプリの再起動で消える）

スプレッドシートは1回＝1行。集計しやすい列（スコア・命中率・操作の指標など）と、
1発ごと・敵1体ごとの細かいデータを JSON にまとめた列（data_json）を持つ。
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import streamlit as st

# ゲーム側（game.html の OPS / OUTS）と同じ並び
OPS = ["aimSpd", "preAim", "settle", "revRate", "mouseSpd", "walk", "adsRatio", "gapMean", "gapCV", "nearDist", "react", "track"]
OUTS = ["acc", "hs", "kills", "taken", "ttk"]
HEADER = ["run_id", "received_at", "player", "played_at", "aim_mode", "completed", "score", *OUTS, *OPS, "n_shots", "version", "data_json"]

MAX_NAME = 16
MAX_SHOTS = 300
MAX_FOES = 120
CELL_LIMIT = 45000  # スプレッドシートの1セルの上限（5万文字）より少し余裕を持たせる


def _num(v):
    """数値ならそのまま（NaN/無限大は None）、それ以外は None。"""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)) and math.isfinite(v):
        return v
    return None


def clean_run(run: dict) -> dict | None:
    """ブラウザから届いたデータを検査して、保存してよい形にそろえる。おかしければ None。"""
    if not isinstance(run, dict):
        return None
    rid = str(run.get("id", ""))[:40]
    player = str(run.get("player", "")).strip()[:MAX_NAME] or "ゲスト"
    shots = run.get("shots")
    if not rid or not isinstance(shots, list) or len(shots) > MAX_SHOTS:
        return None
    ops = run.get("ops") if isinstance(run.get("ops"), dict) else {}
    outs = run.get("outs") if isinstance(run.get("outs"), dict) else {}
    foes = run.get("foes") if isinstance(run.get("foes"), list) else []
    parts = run.get("parts") if isinstance(run.get("parts"), list) else []
    return {
        "id": rid,
        "player": player,
        "at": _num(run.get("at")) or int(time.time() * 1000),
        "aim": "lock" if run.get("aim") == "lock" else "cursor",
        "clear": bool(run.get("clear")),
        "T": _num(run.get("T")),
        "score": _num(run.get("score")) or 0,
        "ops": {k: _num(ops.get(k)) for k in OPS},
        "outs": {k: _num(outs.get(k)) for k in ["score", *OUTS]},
        "parts": [[str(p[0])[:20], _num(p[1])] for p in parts[:8] if isinstance(p, list) and len(p) == 2],
        "shots": [[_num(v) for v in s[:12]] for s in shots if isinstance(s, list)],
        "foes": [[_num(v) for v in f[:6]] for f in foes[:MAX_FOES] if isinstance(f, list)],
        "v": _num(run.get("v")) or 1,
    }


def _to_row(run: dict) -> list:
    detail = {"T": run["T"], "parts": run["parts"], "shots": run["shots"], "foes": run["foes"]}
    data = json.dumps(detail, ensure_ascii=False, separators=(",", ":"))
    if len(data) > CELL_LIMIT:  # 長すぎたら敵1体ごとのデータを諦める
        detail["foes"] = []
        data = json.dumps(detail, ensure_ascii=False, separators=(",", ":"))
    played = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(run["at"] / 1000))
    received = time.strftime("%Y-%m-%d %H:%M:%S")
    blank = lambda v: "" if v is None else v  # noqa: E731
    return [run["id"], received, run["player"], played, run["aim"], int(run["clear"]), run["score"],
            *[blank(run["outs"].get(k)) for k in OUTS], *[blank(run["ops"].get(k)) for k in OPS],
            len(run["shots"]), run["v"], data]


def _from_row(row: dict) -> dict | None:
    """スプレッドシートの1行 → ゲームのデータラボが読める形。"""
    try:
        detail = json.loads(row.get("data_json") or "{}")
        f = lambda k: _num(float(row[k])) if str(row.get(k, "")).strip() != "" else None  # noqa: E731
        at = time.mktime(time.strptime(str(row["played_at"]), "%Y-%m-%d %H:%M:%S")) * 1000
        score = f("score") or 0
        return {
            "id": str(row["run_id"]), "player": str(row["player"]), "at": at, "aim": row.get("aim_mode") or "cursor",
            "clear": str(row.get("completed")) == "1", "T": detail.get("T"), "score": score,
            "ops": {k: f(k) for k in OPS}, "outs": {"score": score, **{k: f(k) for k in OUTS}},
            "parts": detail.get("parts") or [], "shots": detail.get("shots") or [], "foes": detail.get("foes") or [],
        }
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return None


class SheetStore:
    kind = "sheet"
    label = "Googleスプレッドシート"

    def __init__(self, info: dict, url: str):
        import gspread  # Secrets があるときだけ使う

        gc = gspread.service_account_from_dict(info)
        book = gc.open_by_url(url)
        try:
            self.ws = book.worksheet("runs")
        except gspread.WorksheetNotFound:
            self.ws = book.add_worksheet("runs", rows=1000, cols=len(HEADER))
        if self.ws.row_values(1) != HEADER:
            self.ws.update([HEADER], "A1")

    def append(self, run: dict) -> None:
        self.ws.append_row(_to_row(run), value_input_option="RAW")

    def load(self, limit: int) -> list[dict]:
        rows = self.ws.get_all_records(expected_headers=HEADER, value_render_option="UNFORMATTED_VALUE")
        runs = [r for r in (_from_row(x) for x in rows[-limit:]) if r]
        return runs


class LocalStore:
    kind = "local"
    label = "ローカルファイル（data/runs.jsonl）"

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, run: dict) -> None:
        # スプレッドシートと同じ行の形で保存しておく（読み込みの処理を共通にするため）
        row = dict(zip(HEADER, _to_row(run)))
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load(self, limit: int) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        rows = []
        for ln in lines:
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
        return [r for r in (_from_row(x) for x in rows) if r]


_NO_SECRETS = (KeyError, FileNotFoundError, getattr(st.errors, "StreamlitSecretNotFoundError", FileNotFoundError))


@st.cache_resource
def get_store():
    try:
        info = dict(st.secrets["gcp_service_account"])
        url = st.secrets["sheet_url"]
    except _NO_SECRETS:
        return LocalStore(Path(__file__).parent / "data" / "runs.jsonl")
    return SheetStore(info, url)
