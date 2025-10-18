# preprocess/diff_engine.py
import re

def _norm_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _article_id(a: dict) -> str:
    # Hỗ trợ nhiều loại cấu trúc: "article" (Điều), "section", "chapter"
    if "article" in a and a["article"]:
        # Thêm thông tin chapter/section nếu có
        prefix = ""
        if "chapter" in a and a["chapter"]:
            prefix = f"{a['chapter']} - "
        elif "section" in a and a["section"]:
            prefix = f"{a['section']} - "
        return f"{prefix}{a['article']}"
    
    if "chapter" in a and a["chapter"]:
        return a["chapter"]
    
    if "section" in a and a["section"]:
        return f"Section {a['section']}"
    
    return "Unknown"

def _clauses_of(a: dict):
    # Trả về danh sách (no, text) đã chuẩn hoá
    out = []
    clauses = a.get("clauses", []) or []
    auto_no = 1
    for c in clauses:
        no = c.get("no")
        if not no:
            no = str(auto_no)
            auto_no += 1
        text = _norm_text(c.get("text", ""))
        out.append((str(no), text))
    return out

def _kv_index(struct: dict):
    """
    Tạo chỉ số dạng:
      { (article_id, clause_no): text }
    """
    m = {}
    for a in struct.get("articles", []) or []:
        aid = _article_id(a)
        for no, text in _clauses_of(a):
            m[(aid, str(no))] = text
    return m

def diff_articles(base_struct: dict, new_struct: dict):
    """So sánh theo (article/section, clause no) → added / modified / deleted."""
    base = _kv_index(base_struct)
    new  = _kv_index(new_struct)

    out = []

    # Added / Modified
    for k, v in new.items():
        if k not in base:
            out.append({
                "level": "clause",
                "id": f"{k[0]}.{k[1]}",
                "change": "added",
                "to": v
            })
        elif base[k] != v:
            out.append({
                "level": "clause",
                "id": f"{k[0]}.{k[1]}",
                "change": "modified",
                "from": base[k],
                "to": v
            })

    # Deleted
    for k, v in base.items():
        if k not in new:
            out.append({
                "level": "clause",
                "id": f"{k[0]}.{k[1]}",
                "change": "deleted",
                "from": v
            })

    return out
