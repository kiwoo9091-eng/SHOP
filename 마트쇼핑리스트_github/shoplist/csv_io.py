"""CSV 내보내기 / 불러오기.

- 내보내기: 한글 머리글, UTF-8 BOM (엑셀에서 한글이 깨지지 않게)
- 불러오기: 한글·영문 머리글 모두 받음, UTF-8 / CP949(엑셀 한글 저장) 모두 받음
- 엑셀 수식 주입 방지: =, +, -, @ 로 시작하는 글자는 내보낼 때 앞에 ' 를 붙이고 불러올 때 뗀다
"""
from __future__ import annotations

import csv
import io

from . import models

EXPORT_HEADER = ["이름", "분류", "수량", "가격", "메모", "구매 완료"]
HEADER_MAP = {
    "이름": "name", "name": "name",
    "분류": "category", "종류": "category", "코너": "category", "category": "category",
    "수량": "quantity", "quantity": "quantity",
    "가격": "price", "price": "price",
    "메모": "memo", "memo": "memo",
    "구매 완료": "checked", "구매완료": "checked", "checked": "checked",
}
TRUE_VALUES = {"1", "true", "yes", "y", "o", "예", "완료", "✓", "v"}
FORMULA_START = ("=", "+", "-", "@")
MAX_ROWS = 2000
MAX_BYTES = 1_000_000


def _guard(text: str) -> str:
    return "'" + text if text.startswith(FORMULA_START) else text


def _unguard(text: str) -> str:
    return text[1:] if text.startswith("'") and text[1:2] in FORMULA_START else text


def export_csv(items: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(EXPORT_HEADER)
    for it in items:
        writer.writerow([
            _guard(it["name"]),
            models.CATEGORIES.get(it["category"], it["category"]),
            it["quantity"],
            "" if it.get("price") is None else it["price"],
            _guard(it.get("memo") or ""),
            "O" if it["checked"] else "",
        ])
    return buf.getvalue().encode("utf-8-sig")


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp949"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", data, 0, 1, "지원하지 않는 인코딩")


def import_csv(data: bytes) -> tuple[list[dict], list[tuple[int, str]]]:
    """(올바른 아이템 목록, [(줄 번호, 오류 이유)])를 돌려준다. 줄 번호는 머리글이 1번."""
    if len(data) > MAX_BYTES:
        return [], [(0, "파일이 너무 커요 (최대 1MB).")]
    try:
        text = _decode(data)
    except UnicodeDecodeError:
        return [], [(0, "글자 인코딩을 읽을 수 없어요. UTF-8로 저장해 주세요.")]

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return [], [(0, "빈 파일이에요.")]
    except csv.Error as e:
        return [], [(1, f"CSV 형식 오류: {e}")]
    cols = [HEADER_MAP.get(h.strip().lower(), HEADER_MAP.get(h.strip())) for h in header]
    if "name" not in cols:
        return [], [(1, "머리글에 '이름' 열이 있어야 해요.")]

    items: list[dict] = []
    errors: list[tuple[int, str]] = []
    line_no = 1
    try:
        for row in reader:
            line_no += 1
            if not any(cell.strip() for cell in row):
                continue  # 빈 줄은 건너뜀
            if len(items) + len(errors) >= MAX_ROWS:
                errors.append((line_no, f"최대 {MAX_ROWS}줄까지만 불러올 수 있어요."))
                break
            raw = {c: (row[i] if i < len(row) else "") for i, c in enumerate(cols) if c}
            values, errs = models.validate_item(
                _unguard(raw.get("name", "")),
                raw.get("category", "").strip() or "etc",  # 분류가 비어 있으면 기타
                raw.get("quantity", "") or 1,
                raw.get("price", ""),
                _unguard(raw.get("memo", "")),
            )
            if errs:
                errors.append((line_no, " ".join(errs)))
                continue
            values["checked"] = raw.get("checked", "").strip().lower() in TRUE_VALUES
            items.append(values)
    except csv.Error as e:
        errors.append((line_no, f"CSV 형식 오류: {e}"))
    return items, errors
