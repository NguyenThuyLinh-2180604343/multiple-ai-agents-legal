# preprocess/normalizer.py
import re
import unicodedata

def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    # chuẩn hóa xuống dòng: tối đa 2 dòng trống liên tiếp
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()
