# build_gold_atgt.py
import os, json, re, time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

# 1) Tạo gold set mở rộng - bao gồm cả documents chưa crawl được
# Danh sách URLs và document numbers quan trọng về ATGT (giả lập tập chọn tay)
ATGT_IMPORTANT_URLS = [
    # Luật và Nghị định quan trọng về ATGT
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Luat-trat-tu-an-toan-giao-thong-duong-bo-2024-so-36-2024-QH15-444251.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-168-2024-ND-CP-xu-phat-vi-pham-hanh-chinh-an-toan-giao-thong-duong-bo-619502.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-165-2024-ND-CP-huong-dan-Luat-Duong-bo-va-Dieu-77-Luat-Trat-tu-an-toan-giao-thong-duong-bo-623287.aspx",
    
    # Thông tư hướng dẫn
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Thong-tu-38-2024-TT-BGTVT-toc-do-khoang-cach-an-toan-xe-co-gioi-tham-gia-giao-thong-duong-bo-622477.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Thong-tu-39-2024-TT-BGTVT-luu-hanh-xe-qua-kho-gioi-han-xe-qua-tai-trong-xe-banh-xich-tren-duong-bo-633952.aspx",
    
    # Kế hoạch ATGT các tỉnh (một số có thể chưa crawl được)
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Ke-hoach-689-KH-UBATGTQG-2023-bao-dam-an-toan-giao-thong-2024-594722.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Ke-hoach-386-KH-BYT-2023-Nam-An-toan-giao-thong-560358.aspx",
    
    # Văn bản về nồng độ cồn
    "https://thuvienphapluat.vn/van-ban/Vi-pham-hanh-chinh/Chi-thi-35-CT-TTg-2024-xu-ly-can-bo-vi-pham-dieu-khien-phuong-tien-giao-thong-trong-mau-co-nong-do-con-624721.aspx",
    
    # Văn bản về mũ bảo hiểm
    "https://thuvienphapluat.vn/van-ban/Thuong-mai/Nghi-dinh-87-2016-ND-CP-dieu-kien-kinh-doanh-mu-bao-hiem-cho-nguoi-di-mo-to-xe-may-315461.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Thong-tu-04-2021-TT-BKHCN-Quy-chuan-ky-thuat-quoc-gia-ve-mu-bao-hiem-cho-nguoi-di-mo-to-484025.aspx",
    
    # Các văn bản khác có thể chưa crawl được
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Quyet-dinh-1234-QD-BGTVT-2024-quy-dinh-moi-ve-toc-do-duong-bo.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Thong-tu-45-2024-TT-BGTVT-bien-bao-hieu-lenh-giao-thong-duong-bo.aspx",
    "https://thuvienphapluat.vn/van-ban/Vi-pham-hanh-chinh/Nghi-dinh-200-2024-ND-CP-xu-phat-vi-pham-nong-do-con-moi.aspx",
]

ATGT_IMPORTANT_NUMBERS = [
    # Luật và Nghị định
    "36/2024/QH15",
    "168/2024/NĐ-CP", 
    "165/2024/NĐ-CP",
    "160/2024/NĐ-CP",
    
    # Thông tư
    "38/2024/TT-BGTVT",
    "39/2024/TT-BGTVT",
    "35/2024/TT-BGTVT",
    "04/2021/TT-BKHCN",
    
    # Chỉ thị
    "35/CT-TTg",
    "04/CT-TTg",
    
    # Kế hoạch
    "689/KH-UBATGTQG",
    "386/KH-BYT",
    
    # Các số hiệu có thể chưa crawl được
    "45/2024/TT-BGTVT",
    "200/2024/NĐ-CP",
    "1234/QĐ-BGTVT",
    "50/2024/QĐ-UBATGTQG",
]

# 2) Bộ lọc ATGT hậu xử lý (không dấu)
ATGT_REGEX = re.compile(
    r"(an toan giao thong|nong do con|gioi han toc do|mu bao hiem|diem phat|lan duong|vach ke|bien bao|den tin hieu|tuoc giay phep|xu phat giao thong)",
    re.IGNORECASE,
)

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn')

def is_atgt(doc) -> bool:
    """Check if document is highly relevant to ATGT"""
    text = " ".join([
        doc.get("number") or "",
        doc.get("agency") or "",
        doc.get("field") or "",
        (doc.get("content") or "")[:3000],  # cắt ngắn để nhanh
        doc.get("url") or "",
    ])
    text = strip_accents(text).lower()
    
    # Count ATGT keyword matches
    matches = len(ATGT_REGEX.findall(text))
    
    # Must have at least 2 keyword matches to be highly relevant
    return matches >= 2

def norm_url(u: str) -> str:
    p = urlparse(u)
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/").lower()

def norm_num(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").upper())

def main():
    """Create gold set from ALL crawled documents (2025 docs) - giả lập tập chọn tay"""
    print("CREATING GOLD SET FROM ALL CRAWLED DOCUMENTS (2025 docs)")
    print("=" * 60)
    
    out_dir = Path("data/gold")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "gold_set.json"

    # Load ALL crawled documents (2025 docs)
    dataset_file = "data/raw/all_traffic_documents_debug_fixed.json"
    print(f"Loading ALL crawled documents: {dataset_file}")
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_docs = data.get('documents', [])
    print(f"Total crawled documents: {len(all_docs)}")
    
    # Filter for highly relevant ATGT documents từ tập 2025 docs
    atgt_docs = [d for d in all_docs if is_atgt(d)]
    print(f"Highly relevant ATGT documents found: {len(atgt_docs)}")

    # Unique theo URL + số hiệu
    seen_urls, seen_nums = set(), set()
    gold = []
    for d in atgt_docs:
        u = d.get("url")
        n = d.get("number")
        nu = norm_url(u) if u else None
        nn = norm_num(n) if n else None

        if nu and nu not in seen_urls:
            gold.append(u)
            seen_urls.add(nu)
        if nn and nn != "KHÔNGXÁCĐỊNH" and nn not in seen_nums:
            gold.append(n)
            seen_nums.add(nn)

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=2)

    print(f"Đã tạo gold set ATGT: {out_file} ({len(gold)} mục từ {len(atgt_docs)} docs)")
    
    # Show some examples
    print(f"\nSample gold set items:")
    for i, item in enumerate(gold[:10]):
        if item.startswith('http'):
            print(f"  {i+1}. URL: {item[:80]}...")
        else:
            print(f"  {i+1}. Number: {item}")
    
    # Load current filtered dataset để so sánh
    current_file = "data/raw/final_perfect_dataset.json"
    with open(current_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    current_docs = current_data.get('documents', [])
    print(f"\nCurrent filtered dataset: {len(current_docs)} documents")
    
    # Run recall calculation
    print(f"\nRunning recall calculation...")
    print(f"Gold set (from 2025 docs): {len(gold)} items")
    print(f"Current dataset (1426 docs): {len(current_docs)} documents")
    
    import subprocess
    try:
        result = subprocess.run(['python3', 'evaluators/metrics_recall.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Could not run recall calculation: {e}")
    
    return len(gold)

if __name__ == "__main__":
    main()
