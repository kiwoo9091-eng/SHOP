"""마트 장보기 리스트 — Streamlit 화면 (진입점).

Streamlit은 조작할 때마다 이 스크립트를 처음부터 다시 실행한다.
그래서 동작은 콜백(on_click / on_change)에서 처리하고, 위젯 key에는 아이템 id를 넣는다.
데이터 처리는 shoplist/ 패키지에 있고, 이 파일은 화면만 담당한다.
"""
from __future__ import annotations

import hmac
import html
import re
from datetime import datetime

import streamlit as st

from shoplist import csv_io, db, models

st.set_page_config(page_title="장보기 리스트", page_icon="🛒", layout="centered")

S = st.session_state
ADD_DEFAULTS = {"add_name": "", "add_qty": 1, "add_price": None, "add_memo": ""}

# 분류별 스티커 색
CATEGORY_COLORS = {
    "veg": "#B8F2A4", "meat": "#FFB3B3", "dairy": "#CFE8FF", "food": "#FFE08A",
    "snack": "#FFC9E9", "home": "#D9CCFF", "etc": "#E6E6E6",
}

# ───────── 만화 스타일 CSS ─────────
_CATEGORY_CSS = "\n".join(
    f'[class*="st-key-card_{key}_"] {{ --cat: {color}; }}' for key, color in CATEGORY_COLORS.items()
)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Black+Han+Sans&display=swap');

:root { --ink: #1E1E1E; --paper: #FFF8E7; --sun: #FFD93D; --coral: #FF6B6B; --sky: #6BCBFF; }

/* 바탕: 크림색 종이 + 만화 망점 */
.stApp {
  background-color: var(--paper);
  background-image: radial-gradient(rgba(30,30,30,.09) 1.3px, transparent 1.4px);
  background-size: 18px 18px;
}
.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp li, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricLabel"], .stApp [data-baseweb="select"] * {
  font-family: 'Jua', system-ui, sans-serif !important;
}
.block-container { padding-top: 3.4rem; padding-bottom: 4rem; max-width: 720px; }
header[data-testid="stHeader"] { background: transparent; }

/* 제목 말풍선 */
.hero { position: relative; background: #fff; border: 3.5px solid var(--ink); border-radius: 26px;
        box-shadow: 6px 6px 0 var(--ink); padding: 18px 22px 16px; margin: 0 0 22px; }
.hero::after { content: ""; position: absolute; left: 46px; bottom: -22px; width: 26px; height: 26px;
               background: #fff; border-right: 3.5px solid var(--ink); border-bottom: 3.5px solid var(--ink);
               transform: skewY(-35deg) rotate(45deg); }
.hero h1 { font-family: 'Black Han Sans', 'Jua', sans-serif !important; font-size: 2.15rem; margin: 0;
           line-height: 1.3; color: var(--ink); letter-spacing: .5px; padding: 0 56px 0 0; word-break: keep-all; }
@media (max-width: 480px) {
  .hero h1 { font-size: 1.65rem; padding-right: 40px; }
  .hero .mascot { font-size: 2.4rem; top: -20px; }
  [data-testid="stMetric"] { padding: 6px 12px; }
  [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
}
.hero h1 .pop { display: inline-block; background: var(--sun); padding: 0 10px; border: 3px solid var(--ink);
                border-radius: 12px; transform: rotate(-3deg); box-shadow: 3px 3px 0 var(--ink); }
.hero p { margin: 8px 0 0; color: #555; font-size: 1.02rem; }
.hero .mascot { position: absolute; right: 16px; top: -26px; font-size: 3rem; transform: rotate(12deg);
                filter: drop-shadow(3px 3px 0 rgba(0,0,0,.25)); }

/* 요약 패널 */
[data-testid="stMetric"] { background: #fff; border: 3px solid var(--ink); border-radius: 18px;
                           box-shadow: 4px 4px 0 var(--ink); padding: 10px 14px; }
[data-testid="stMetricLabel"] p { font-size: .95rem !important; color: #555; }
[data-testid="stMetricValue"] { font-size: 1.7rem !important; color: var(--ink); }
.st-key-m_todo [data-testid="stMetric"] { background: #FFF1B8; }
.st-key-m_done [data-testid="stMetric"] { background: #D8F7C9; }
.st-key-m_money [data-testid="stMetric"] { background: #FFDDE0; }
[data-testid="stProgress"] [role="progressbar"] { border: 3px solid var(--ink); border-radius: 999px;
                                                 background: #fff; overflow: hidden; }
[data-testid="stProgress"] [role="progressbar"] > div { height: 14px !important; background: transparent !important; }
[data-testid="stProgress"] [role="progressbar"] > div > div { background: repeating-linear-gradient(
    -45deg, var(--coral) 0 10px, #ff8a8a 10px 20px) !important; height: 14px !important; }

/* 펼치기 상자, 폼 */
[data-testid="stExpander"] details { background: #fff; border: 3px solid var(--ink) !important;
                                     border-radius: 18px !important; box-shadow: 5px 5px 0 var(--ink); }
[data-testid="stExpander"] summary p { font-size: 1.15rem !important; }
.stApp input, .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] {
  border-radius: 12px !important; }
.stApp [data-baseweb="input"], .stApp [data-baseweb="select"] > div {
  border: 2.5px solid var(--ink) !important; background: #fff !important; }

/* 버튼: 두꺼운 테두리 + 꾹 눌리는 그림자 */
.stApp button[kind] { border: 3px solid var(--ink) !important; border-radius: 14px !important;
                      box-shadow: 3px 3px 0 var(--ink); transition: transform .06s, box-shadow .06s; }
.stApp button[kind]:active:not(:disabled) { transform: translate(3px, 3px); box-shadow: 0 0 0 var(--ink); }
.stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"] {
  background: var(--coral) !important; color: #fff !important; }
.stApp button[kind]:disabled { box-shadow: none; opacity: .45; }
[data-testid="stButtonGroup"] button { box-shadow: 2px 2px 0 var(--ink) !important; margin: 2px 4px 4px 0; }
[data-testid="stButtonGroup"] button[kind$="Active"] { background: var(--sun) !important; color: var(--ink) !important; }

/* 아이템 카드 */
""" + _CATEGORY_CSS + """
[class*="st-key-card_"] { background: #fff; border: 3px solid var(--ink) !important; border-radius: 18px !important;
                          box-shadow: 5px 5px 0 var(--ink); padding: 10px 12px !important; }
[class*="st-key-card_"]:has(.item.done) { background: #F1F1F1; box-shadow: 2px 2px 0 var(--ink); }
.item { min-width: 0; position: relative; }
.item .title { font-size: 1.18rem; line-height: 1.35; overflow-wrap: anywhere; word-break: keep-all; color: var(--ink); }
.item .meta { color: #555; font-size: .95rem; margin-top: 4px; }
.item .meta .qty { display: inline-block; background: var(--sun); border: 2px solid var(--ink); border-radius: 8px;
                   padding: 0 7px; margin-right: 4px; color: var(--ink); }
.item .meta .unit { color: #888; font-size: .85rem; }
.item .memo { display: inline-block; margin-top: 6px; background: #FFFBEA; border: 2px dashed #bbb; border-radius: 10px;
              padding: 1px 9px; color: #666; font-size: .9rem; overflow-wrap: anywhere; }
.sticker { display: inline-block; margin-right: 6px; padding: 1px 9px; background: var(--cat, #eee);
           border: 2px solid var(--ink); border-radius: 999px; font-size: .82rem; transform: rotate(-3deg);
           white-space: nowrap; vertical-align: 2px; box-shadow: 2px 2px 0 var(--ink); }
.item.done .name { text-decoration: line-through; text-decoration-thickness: 3px; text-decoration-color: var(--coral); color: #999; }
.item.done .meta, .item.done .sticker { opacity: .55; }
.stamp { position: absolute; right: 0; top: -2px; font-size: .85rem; color: var(--coral); border: 2.5px solid var(--coral);
         border-radius: 8px; padding: 0 6px; transform: rotate(8deg); background: #fff; }

/* 카드 안 줄: 휴대폰에서도 체크박스·내용·버튼을 한 줄로 */
[class*="st-key-row_"] { flex-wrap: nowrap !important; }
[class*="st-key-row_"] > div:nth-child(2) { flex: 1 1 auto; min-width: 0; }
[class*="st-key-row_"] [data-testid="stCheckbox"] label { min-height: 44px; min-width: 34px; align-items: center; }
[class*="st-key-row_"] [data-testid="stCheckbox"] label > span:first-child {
  transform: scale(1.35); border: 2.5px solid var(--ink) !important; border-radius: 6px !important; }
[class*="st-key-row_"] button[kind] { min-height: 42px; min-width: 42px; padding: 0 .45rem; box-shadow: 2px 2px 0 var(--ink); }

/* 빈 화면 */
.empty { text-align: center; background: #fff; border: 3px dashed var(--ink); border-radius: 22px;
         padding: 26px 12px 22px; color: #555; font-size: 1.1rem; margin: 6px 0 14px; }
.empty .big { font-size: 3rem; display: block; margin-bottom: 6px; animation: bob 1.6s ease-in-out infinite; }
@keyframes bob { 50% { transform: translateY(-6px) rotate(-6deg); } }
@media (prefers-reduced-motion: reduce) { .empty .big { animation: none; } }

/* 확인 창 */
div[role="dialog"] { border: 3.5px solid var(--ink) !important; border-radius: 22px !important; box-shadow: 7px 7px 0 var(--ink) !important; }

.section { font-size: 1.25rem; margin: 18px 0 6px; color: var(--ink); }
.section .hl { background: linear-gradient(transparent 55%, var(--sun) 55%); padding: 0 3px; }
</style>
"""


# ───────── 공통 ─────────
def esc(text) -> str:
    """HTML에 넣을 사용자 입력 이스케이프."""
    return html.escape(str(text or ""), quote=True)


_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|~<>:$])")


def md(text) -> str:
    """마크다운(st.toast, st.warning 등)에 넣을 사용자 입력 이스케이프."""
    return _MD_SPECIAL.sub(r"\\\1", str(text or ""))


def flash(message: str, icon: str = "✅") -> None:
    """다음 화면에서 보여 줄 알림. (콜백 안에서는 바로 toast를 띄울 수 없어서 모아 둠)"""
    S.setdefault("flash", []).append((message, icon))


def open_dialog(kind: str, item_id: int | None = None) -> None:
    S.dialog = (kind, item_id)
    S.dialog_nonce = S.get("dialog_nonce", 0) + 1


def section(title: str) -> None:
    st.markdown(f'<div class="section"><span class="hl">{title}</span></div>', unsafe_allow_html=True)


# ───────── 비밀번호 (배포 시 Secrets에 APP_PASSWORD가 있을 때만) ─────────
def app_password() -> str | None:
    try:
        return st.secrets.get("APP_PASSWORD")
    except Exception:  # secrets.toml이 없는 로컬 실행
        return None


def require_password() -> bool:
    password = app_password()
    if not password or S.get("auth_ok"):
        return True
    render_hero()
    with st.form("login"):
        typed = st.text_input("비밀번호", type="password")
        if st.form_submit_button("들어가기", type="primary", width="stretch"):
            if hmac.compare_digest(typed.encode(), str(password).encode()):
                S.auth_ok = True
                st.rerun()
            st.error("비밀번호가 맞지 않아요.")
    return False


def render_hero() -> None:
    st.markdown(
        '<div class="hero"><span class="mascot">🛒</span>'
        '<h1>오늘의 <span class="pop">장보기</span> 리스트!</h1>'
        '<p>살 것을 적어 두고, 장바구니에 담으면 체크! ✔</p></div>',
        unsafe_allow_html=True,
    )


# ───────── 추가 ─────────
def reset_add_form() -> None:
    for key, value in ADD_DEFAULTS.items():
        S[key] = value
    S.add_errors = []


def on_add() -> None:
    values, errors = models.validate_item(S.add_name, S.add_category, S.add_qty, S.add_price, S.add_memo)
    S.add_errors = errors
    if errors:
        return
    dup = models.find_duplicate(db.list_items(), values["name"])
    if dup:
        S.pending_add = {"values": values, "dup_id": dup["id"], "dup_name": dup["name"], "dup_qty": dup["quantity"]}
        return
    db.add_item(**values)
    flash(f"‘{md(values['name'])}’ 담았어요!", models.CATEGORY_ICONS[values["category"]])
    reset_add_form()


def on_dup_merge() -> None:
    p = S.pop("pending_add", None)
    if not p:
        return
    qty = min(models.QTY_MAX, p["dup_qty"] + p["values"]["quantity"])
    if db.update_item(p["dup_id"], quantity=qty):
        flash(f"‘{md(p['dup_name'])}’ 수량을 {qty}개로 늘렸어요", "➕")
    else:  # 그 사이에 지워졌으면 새로 추가
        db.add_item(**p["values"])
        flash(f"‘{md(p['values']['name'])}’ 담았어요!")
    reset_add_form()


def on_dup_separate() -> None:
    p = S.pop("pending_add", None)
    if p:
        db.add_item(**p["values"])
        flash(f"‘{md(p['values']['name'])}’ 따로 담았어요!")
        reset_add_form()


def on_dup_cancel() -> None:
    S.pop("pending_add", None)


def render_add(expanded: bool) -> None:
    for key, value in ADD_DEFAULTS.items():
        S.setdefault(key, value)
    with st.expander("✏️ 살 것 적기", expanded=expanded):
        with st.form("add_form", border=False, enter_to_submit=True):
            st.text_input("이름", key="add_name", max_chars=models.NAME_MAX, placeholder="예: 우유, 대파, 키친타올")
            st.pills("분류", list(models.CATEGORIES), format_func=models.label, default="etc",
                     required=True, key="add_category")
            c1, c2 = st.columns(2)
            c1.number_input("수량", min_value=models.QTY_MIN, max_value=models.QTY_MAX, step=1, key="add_qty")
            c2.number_input("1개 가격 (원)", min_value=0, max_value=models.PRICE_MAX, step=100,
                            key="add_price", placeholder="모르면 비워 두세요")
            st.text_input("메모", key="add_memo", max_chars=models.MEMO_MAX, placeholder="예: 1+1이면 2개, 유통기한 확인")
            st.form_submit_button("🛒 리스트에 담기", type="primary", width="stretch", on_click=on_add)

        for err in S.get("add_errors", []):
            st.error(err, icon="⚠️")

        p = S.get("pending_add")
        if p:
            st.warning(f"‘{md(p['dup_name'])}’은(는) 이미 리스트에 있어요 (지금 {p['dup_qty']}개). 수량을 늘릴까요?", icon="🔁")
            c1, c2, c3 = st.columns(3)
            c1.button(f"수량 늘리기 (+{p['values']['quantity']})", type="primary", width="stretch", on_click=on_dup_merge)
            c2.button("따로 담기", width="stretch", on_click=on_dup_separate)
            c3.button("취소", width="stretch", on_click=on_dup_cancel)


# ───────── 요약 ─────────
def render_summary(items: list[dict]) -> None:
    s = models.summarize(items)
    c1, c2, c3 = st.columns(3)
    with c1.container(key="m_todo"):
        st.metric("📝 살 것", f"{s['todo']}개")
    with c2.container(key="m_done"):
        st.metric("✅ 담은 것", f"{s['done']} / {s['total']}")
    with c3.container(key="m_money"):
        st.metric("💰 남은 금액", models.format_won(s["remaining_amount"]))
    pct = round(s["progress"] * 100)
    cheer = "다 샀다! 🎉" if s["total"] and s["done"] == s["total"] else ("거의 다 왔어요! 💪" if pct >= 70 else "")
    st.progress(s["progress"], text=f"장보기 진행률 {pct}% {cheer}")
    if s["unpriced_todo"]:
        st.caption(f"가격 미정 {s['unpriced_todo']}개는 금액에 포함되지 않았어요.")


# ───────── 목록 ─────────
def on_toggle(item_id: int) -> None:
    checked = S[f"item_{item_id}_check"]
    if db.set_checked(item_id, checked):
        item = db.get_item(item_id)
        flash(f"‘{md(item['name'])}’ {'장바구니에 쏙!' if checked else '다시 살 것으로'}", "🛒" if checked else "↩️")


def card_html(it: dict) -> str:
    cat = it["category"]
    if it.get("price") is None:
        amount = "가격 미정"
    else:
        amount = models.format_won(models.item_total(it))
        if it["quantity"] > 1:
            amount += f' <span class="unit">({models.format_won(it["price"])} × {it["quantity"]})</span>'
    memo = f'<div class="memo">📝 {esc(it["memo"])}</div>' if it.get("memo") else ""
    stamp = '<span class="stamp">담았다!</span>' if it["checked"] else ""
    cls = "item done" if it["checked"] else "item"
    # 빈 줄 없이 <div>로 시작해야 마크다운으로 해석되지 않음
    return (f'<div class="{cls}">{stamp}<div class="title">'
            f'<span class="sticker">{models.CATEGORY_ICONS[cat]} {models.CATEGORIES[cat]}</span>'
            f'<span class="name">{esc(it["name"])}</span></div>'
            f'<div class="meta"><span class="qty">×{it["quantity"]}</span> {amount}</div>{memo}</div>')


def render_item(it: dict) -> None:
    iid = it["id"]
    check_key = f"item_{iid}_check"
    S[check_key] = it["checked"]  # 위젯을 만들기 전에 DB 값과 맞춤
    with st.container(key=f"card_{it['category']}_{iid}"):
        with st.container(horizontal=True, vertical_alignment="center", gap="small", key=f"row_{iid}"):
            st.checkbox(f"{it['name']} 구매 완료", key=check_key, on_change=on_toggle, args=(iid,),
                        label_visibility="collapsed", width="content")
            st.markdown(card_html(it), unsafe_allow_html=True, width="stretch")
            st.button("✏️", key=f"item_{iid}_edit", help="수정", on_click=open_dialog, args=("edit", iid))
            st.button("🗑️", key=f"item_{iid}_del", help="삭제", on_click=open_dialog, args=("delete", iid))


def render_list(items: list[dict]) -> None:
    section("🧾 내 장보기 목록")
    if not items:
        st.markdown('<div class="empty"><span class="big">🛒</span>장바구니가 텅 비었어요!<br>'
                    '위에서 살 것을 적어 보세요.</div>', unsafe_allow_html=True)
        return
    cat = st.pills("코너", ["all", *models.CATEGORIES],
                   format_func=lambda k: "🏪 전체" if k == "all" else models.label(k),
                   default="all", required=True, key="f_cat")
    c1, c2 = st.columns([1, 1])
    with c1:
        status = st.segmented_control("상태", list(models.STATUS_FILTERS), format_func=models.STATUS_FILTERS.get,
                                      default="all", required=True, key="f_status")
    with c2:
        sort = st.selectbox("정렬", list(models.SORT_MODES), format_func=models.SORT_MODES.get, key="f_sort")

    visible = models.sort_items(models.filter_items(items, cat, status), sort)
    if not visible:
        st.info("조건에 맞는 아이템이 없어요.", icon="🔍")
        return
    st.caption(f"{len(visible)}개 표시 중")
    for it in visible:
        render_item(it)


# ───────── 백업 ─────────
def uploader_key() -> str:
    return f"uploader_{S.get('upload_nonce', 0)}"


def finish_import(count: int, errors: list, replaced: bool) -> None:
    S.import_report = {"count": count, "errors": errors, "replaced": replaced}
    S.upload_nonce = S.get("upload_nonce", 0) + 1  # 업로드 칸 비우기
    flash(f"{count}개를 불러왔어요" + (" (기존 리스트를 바꿨어요)" if replaced else ""), "📤")


def on_import() -> None:
    file = S.get(uploader_key())
    if file is None:
        return
    items, errors = csv_io.import_csv(file.getvalue())
    if not items:
        S.import_report = {"count": 0, "errors": errors or [(0, "불러올 아이템이 없어요.")], "replaced": False}
        return
    if S.import_mode == "replace":
        S.pending_import = {"items": items, "errors": errors}
        open_dialog("replace")
    else:
        db.add_many(items)
        finish_import(len(items), errors, replaced=False)


def render_backup(items: list[dict]) -> None:
    with st.expander("💾 백업 · 복원 (CSV)"):
        st.caption("⚠️ 배포된 앱은 서버가 다시 시작되면 데이터가 지워질 수 있어요. 가끔 CSV로 백업해 두세요.")
        st.download_button(
            "📥 CSV로 내보내기", data=csv_io.export_csv(items),
            file_name=f"shoplist_{datetime.now():%Y%m%d}.csv", mime="text/csv",
            disabled=not items, width="stretch", on_click="ignore",
        )
        st.divider()
        st.file_uploader("CSV 불러오기", type=["csv"], key=uploader_key(),
                         help="머리글: 이름, 분류, 수량, 가격, 메모, 구매 완료")
        st.radio("불러오는 방법", ["append", "replace"], horizontal=True, key="import_mode",
                 format_func={"append": "기존 리스트에 추가", "replace": "기존 리스트를 바꾸기"}.get)
        st.button("📤 불러오기", width="stretch", on_click=on_import, disabled=S.get(uploader_key()) is None)

        report = S.get("import_report")
        if report:
            if report["count"]:
                st.success(f"{report['count']}개를 불러왔어요.", icon="✅")
            if report["errors"]:
                lines = "\n".join(f"- {'파일' if n == 0 else f'{n}번째 줄'}: {md(msg)}" for n, msg in report["errors"][:20])
                more = f"\n- … 외 {len(report['errors']) - 20}개" if len(report["errors"]) > 20 else ""
                st.warning(f"건너뛴 줄이 {len(report['errors'])}개 있어요.\n\n{lines}{more}", icon="⚠️")


# ───────── 확인 창 ─────────
def dialog_key(name: str) -> str:
    return f"dlg_{S.get('dialog_nonce', 0)}_{name}"


@st.dialog("✏️ 아이템 고치기")
def edit_dialog(item_id: int) -> None:
    it = db.get_item(item_id)
    if not it:
        st.warning("이미 삭제된 아이템이에요.")
        return
    k = dialog_key
    name = st.text_input("이름", it["name"], max_chars=models.NAME_MAX, key=k("name"))
    category = st.pills("분류", list(models.CATEGORIES), format_func=models.label,
                        default=it["category"], required=True, key=k("cat"))
    c1, c2 = st.columns(2)
    qty = c1.number_input("수량", min_value=models.QTY_MIN, max_value=models.QTY_MAX,
                          value=it["quantity"], step=1, key=k("qty"))
    price = c2.number_input("1개 가격 (원)", min_value=0, max_value=models.PRICE_MAX, value=it["price"],
                            step=100, key=k("price"), placeholder="모르면 비워 두세요")
    memo = st.text_input("메모", it["memo"], max_chars=models.MEMO_MAX, key=k("memo"))
    checked = st.checkbox("장바구니에 담았어요 (구매 완료)", value=it["checked"], key=k("checked"))

    c1, c2 = st.columns(2)
    if c1.button("저장", type="primary", width="stretch", key=k("save")):
        values, errors = models.validate_item(name, category, qty, price, memo)
        if errors:
            for err in errors:
                st.error(err, icon="⚠️")
            return
        db.update_item(item_id, **values)
        db.set_checked(item_id, checked)
        flash(f"‘{md(values['name'])}’ 고쳤어요", "✏️")
        st.rerun()
    if c2.button("취소", width="stretch", key=k("cancel")):
        st.rerun()


@st.dialog("🗑️ 아이템 삭제")
def delete_dialog(item_id: int) -> None:
    it = db.get_item(item_id)
    if not it:
        st.warning("이미 삭제된 아이템이에요.")
        return
    st.write(f"‘**{md(it['name'])}**’을(를) 리스트에서 뺄까요?")
    c1, c2 = st.columns(2)
    if c1.button("삭제", type="primary", width="stretch", key=dialog_key("yes")):
        db.delete_item(item_id)
        flash(f"‘{md(it['name'])}’ 삭제했어요", "🗑️")
        st.rerun()
    if c2.button("취소", width="stretch", key=dialog_key("no")):
        st.rerun()


@st.dialog("🧹 담은 것 정리하기")
def delete_checked_dialog() -> None:
    n = sum(1 for it in db.list_items() if it["checked"])
    st.write(f"장바구니에 담은 아이템 **{n}개**를 리스트에서 모두 지울까요?")
    c1, c2 = st.columns(2)
    if c1.button("모두 삭제", type="primary", width="stretch", key=dialog_key("yes")):
        removed = db.delete_checked()
        flash(f"담은 것 {removed}개를 정리했어요", "🧹")
        st.rerun()
    if c2.button("취소", width="stretch", key=dialog_key("no")):
        st.rerun()


@st.dialog("📤 리스트 바꾸기")
def replace_dialog() -> None:
    p = S.get("pending_import")
    if not p:
        return
    current = len(db.list_items())
    st.write(f"지금 리스트의 **{current}개**를 모두 지우고, CSV의 **{len(p['items'])}개**로 바꿀까요?")
    c1, c2 = st.columns(2)
    if c1.button("바꾸기", type="primary", width="stretch", key=dialog_key("yes")):
        db.replace_all(p["items"])
        S.pop("pending_import", None)
        finish_import(len(p["items"]), p["errors"], replaced=True)
        st.rerun()
    if c2.button("취소", width="stretch", key=dialog_key("no")):
        S.pop("pending_import", None)
        st.rerun()


def show_dialog() -> None:
    kind, item_id = S.pop("dialog", (None, None))
    if kind == "edit":
        edit_dialog(item_id)
    elif kind == "delete":
        delete_dialog(item_id)
    elif kind == "delete_checked":
        delete_checked_dialog()
    elif kind == "replace":
        replace_dialog()


# ───────── 화면 ─────────
def main() -> None:
    db.init_db()
    st.markdown(CSS, unsafe_allow_html=True)
    if not require_password():
        return

    for message, icon in S.pop("flash", []):
        st.toast(message, icon=icon)

    items = db.list_items()
    render_hero()
    render_summary(items)
    render_add(expanded=not items or bool(S.get("add_errors")) or "pending_add" in S)
    render_list(items)

    done = sum(1 for it in items if it["checked"])
    if items:
        st.button(f"🧹 담은 것 모두 지우기 ({done}개)", width="stretch", disabled=done == 0,
                  on_click=open_dialog, args=("delete_checked",))
    render_backup(items)
    show_dialog()


main()
