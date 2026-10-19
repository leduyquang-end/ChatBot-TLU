from __future__ import annotations


def fill_merged_cells(rows: list[list]) -> list[list]:
    """Điền ô trống do gộp ô bằng giá trị ở ô phía trên."""
    if not rows:
        return []
    filled = [list(row) for row in rows]
    for r in range(1, len(filled)):
        for c in range(len(filled[r])):
            if filled[r][c] is None or str(filled[r][c]).strip() == "":
                filled[r][c] = filled[r - 1][c] if c < len(filled[r - 1]) else None
    return filled


def drop_total_and_note_rows(rows: list[list]) -> list[list]:
    """Bỏ dòng tổng cộng, tiêu đề nhóm, chú thích."""
    keywords = ("tổng cộng", "tổng cộng cộng", "total", "ghi chú", "chú thích")
    kept = []
    for row in rows:
        joined = " ".join(str(c or "").lower() for c in row)
        if any(k in joined for k in keywords):
            continue
        if all(c is None or str(c).strip() == "" for c in row):
            continue
        kept.append(row)
    return kept


def rows_to_blocks(
    rows: list[list], *, id_column: int = 0, sheet: str = "", headers: list[str] | None = None
) -> list[dict]:
    """Gộp các dòng cùng mã định danh thành một khối (BR-03)."""
    if not rows:
        return []
    header = headers or [str(c or "") for c in rows[0]]
    data_rows = rows[1:] if headers is None else rows

    blocks: dict[str, list[str]] = {}
    order: list[str] = []
    for row in data_rows:
        key = str(row[id_column] or "").strip() if id_column < len(row) else ""
        if not key:
            continue
        if key not in blocks:
            blocks[key] = []
            order.append(key)
        pairs = []
        for i, cell in enumerate(row):
            name = header[i] if i < len(header) and header[i] else f"cột_{i}"
            if cell is not None and str(cell).strip() != "":
                pairs.append(f"{name}: {cell}")
        blocks[key].append(" | ".join(pairs))

    result = []
    for key in order:
        text = f"Mã định danh: {key}\n" + "\n".join(blocks[key])
        result.append(
            {
                "text": text,
                "metadata": {
                    "sheet": sheet,
                    "columns": ", ".join(header),
                    "block_id": key,
                    "document": sheet,
                },
            }
        )
    return result
