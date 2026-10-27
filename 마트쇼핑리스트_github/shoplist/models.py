"""분류 상수, 입력 검증, 금액 계산, 필터·정렬.

Streamlit을 import하지 않는 순수 함수만 둔다. (pytest로 따로 테스트)
"""
from __future__ import annotations

import re
from typing import Any

# 마트 코너 순서 그대로 (코너별 정렬에 사용)
CATEGORIES = {
    "veg": "채소·과일",
    "meat": "정육·수산",
    "dairy": "유제품·계란",
    "food": "가공식품",
    "snack": "과자·음료",
    "home": "생활용품",
    "etc": "기타",
}
CATEGORY_ICONS = {"veg": "🥬", "meat": "🥩", "dairy": "🥛", "food": "🍜", "snack": "🍪", "home": "🧻", "etc": "📦"}
CATEGORY_ORDER = {key: i for i, key in enumerate(CATEGORIES)}
# CSV에서 다르게 적은 분류도 받아 준다
CATEGORY_ALIASES = {
    **{key: key for key in CATEGORIES},
    **{name: key for key, name in CATEGORIES.items()},
    "채소": "veg", "과일": "veg", "야채": "veg",
    "정육": "meat", "수산": "meat", "고기": "meat", "생선": "meat",
    "유제품": "dairy", "계란": "dairy", "우유": "dairy",
    "가공": "food", "식품": "food",
    "과자": "snack", "음료": "snack", "간식": "snack",
    "생활": "home", "세제": "home",
}

NAME_MAX = 50
MEMO_MAX = 200
QTY_MIN, QTY_MAX = 1, 99
PRICE_MAX = 100_000_000

STATUS_FILTERS = {"all": "전체", "todo": "살 것", "done": "산 것"}
SORT_MODES = {"default": "기본 (살 것 먼저 · 최근순)", "category": "코너별", "name": "이름순", "price": "금액 높은순"}

_SPACES = re.compile(r"\s+")


def label(category: str) -> str:
    return f"{CATEGORY_ICONS[category]} {CATEGORIES[category]}"


def _one_line(text: Any) -> str:
    """줄바꿈·탭을 공백 하나로 바꾸고 앞뒤 공백을 지운다."""
    return _SPACES.sub(" ", str(text or "")).strip()


def _to_int(value: Any) -> int | None:
    """빈 값은 None, 정수로 바꿀 수 없으면 ValueError."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("bool")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError("not integer")
    text = str(value).strip().replace(",", "")
    if text == "":
        return None
    return int(text)


def normalize_category(value: Any) -> str | None:
    text = _one_line(value)
    # "🥬 채소·과일"처럼 이모지가 붙어 있어도 받아 줌
    for icon in CATEGORY_ICONS.values():
        text = text.replace(icon, "").strip()
    return CATEGORY_ALIASES.get(text) or CATEGORY_ALIASES.get(text.lower())


def validate_item(name: Any, category: Any, quantity: Any, price: Any, memo: Any) -> tuple[dict, list[str]]:
    """입력값을 정리하고 검증한다. (정리된 값, 오류 메시지 목록)을 돌려준다."""
    errors: list[str] = []

    clean_name = _one_line(name)
    if not clean_name:
        errors.append("이름을 입력해 주세요.")
    elif len(clean_name) > NAME_MAX:
        errors.append(f"이름은 {NAME_MAX}자 이하로 입력해 주세요.")

    clean_category = category if category in CATEGORIES else normalize_category(category)
    if clean_category is None:
        errors.append("분류를 다시 골라 주세요.")

    clean_qty = None
    try:
        clean_qty = _to_int(quantity)
    except (TypeError, ValueError):
        pass
    if clean_qty is None or not QTY_MIN <= clean_qty <= QTY_MAX:
        errors.append(f"수량은 {QTY_MIN}~{QTY_MAX} 사이의 정수로 입력해 주세요.")

    clean_price = None
    try:
        clean_price = _to_int(price)
        if clean_price is not None and not 0 <= clean_price <= PRICE_MAX:
            errors.append("가격은 0원 이상으로 입력해 주세요.")
    except (TypeError, ValueError):
        errors.append("가격은 숫자로 입력해 주세요.")

    clean_memo = _one_line(memo)
    if len(clean_memo) > MEMO_MAX:
        errors.append(f"메모는 {MEMO_MAX}자 이하로 입력해 주세요.")

    values = {
        "name": clean_name,
        "category": clean_category,
        "quantity": clean_qty,
        "price": clean_price,
        "memo": clean_memo,
    }
    return values, errors


def item_total(item: dict) -> int:
    """아이템 금액 = 1개 가격 × 수량 (가격이 없으면 0)."""
    return (item.get("price") or 0) * (item.get("quantity") or 0)


def format_won(amount: int | None) -> str:
    if amount is None:
        return "가격 미정"
    return f"₩ {amount:,}"


def summarize(items: list[dict]) -> dict:
    total = len(items)
    done = sum(1 for it in items if it["checked"])
    todo_items = [it for it in items if not it["checked"]]
    return {
        "total": total,
        "done": done,
        "todo": total - done,
        "progress": done / total if total else 0.0,
        "remaining_amount": sum(item_total(it) for it in todo_items),
        "total_amount": sum(item_total(it) for it in items),
        "unpriced_todo": sum(1 for it in todo_items if it.get("price") is None),
    }


def filter_items(items: list[dict], category: str = "all", status: str = "all") -> list[dict]:
    out = items
    if category in CATEGORIES:
        out = [it for it in out if it["category"] == category]
    if status == "todo":
        out = [it for it in out if not it["checked"]]
    elif status == "done":
        out = [it for it in out if it["checked"]]
    return list(out)


def sort_items(items: list[dict], mode: str = "default") -> list[dict]:
    if mode == "name":
        return sorted(items, key=lambda it: (it["name"].casefold(), it["id"]))
    if mode == "price":
        # 가격 미정은 맨 아래
        return sorted(items, key=lambda it: (it.get("price") is None, -item_total(it), it["id"]))
    if mode == "category":
        # 마트 코너 순서대로, 코너 안에서는 살 것 먼저
        return sorted(items, key=lambda it: (CATEGORY_ORDER.get(it["category"], 99), bool(it["checked"]), it["name"].casefold()))
    # 기본: 살 것 먼저, 그 안에서는 최근에 추가한 것 먼저
    return sorted(items, key=lambda it: (bool(it["checked"]), -it["id"]))


def find_duplicate(items: list[dict], name: str) -> dict | None:
    """이름(대소문자·공백 무시)이 같은, 아직 사지 않은 아이템."""
    key = _one_line(name).casefold()
    for it in items:
        if not it["checked"] and it["name"].casefold() == key:
            return it
    return None
