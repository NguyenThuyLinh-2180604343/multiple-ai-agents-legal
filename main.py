# main.py
import sys
import os
import json
import re
from urllib.parse import urlparse

# Cho phép import module nội bộ
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from crawler.thuvien_crawler import ThuvienCrawlerAgent


# -----------------------------
# Utils chuẩn hóa để khử trùng lặp
# -----------------------------
def norm_url(u: str) -> str:
    p = urlparse(u or "")
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/").lower()

def norm_num(s: str) -> str:
    # Chuẩn hoá số hiệu tăng khả năng trùng (NĐ-CP ~ ND-CP; bỏ khoảng trắng/ký tự lạ)
    s = (s or "").upper().replace("Đ", "D")
    return re.sub(r"[^A-Z0-9/\-]", "", s)


# -----------------------------
# Danh sách keyword cho PREDICT SET
# (gồm keyword rộng + 1 vài keyword ATGT liên quan)
# -----------------------------
PREDICT_QUERIES = [
    "giao thông",
    "an toàn giao thông",
    "luật giao thông",
    "nghị định giao thông",
    "phương tiện giao thông",
    "đường bộ"
]


def crawl_all_traffic_documents():
    """Crawl TẤT CẢ văn bản về giao thông từ thuvienphapluat.vn"""
    print("=== CRAWL TẤT CẢ VĂN BẢN GIAO THÔNG ===")
    print("Crawl không giới hạn số trang, mỗi trang 20 văn bản")
    print("-" * 60)

    Config.ensure_directories()
    crawler = ThuvienCrawlerAgent()

    # Sử dụng method crawl tất cả trang
    results = crawler.crawl_giao_thong_all_pages(
        docs_per_page=20,
        max_docs=None  # Không giới hạn
    )

    # Lưu kết quả
    output_file = os.path.join(Config.RAW_DATA_DIR, "all_traffic_documents.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Lưu CSV
    csv_file = os.path.join(Config.RAW_DATA_DIR, "all_traffic_documents.csv")
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("STT,Tiêu đề,Số hiệu,Lĩnh vực,Ngày ban hành,Cơ quan,URL\n")
        for i, doc in enumerate(results['documents'], 1):
            title = doc.get('title', '').replace('"', '""')
            number = doc.get('number', '').replace('"', '""')
            field = doc.get('field', '').replace('"', '""')
            date = doc.get('issue_date', '').replace('"', '""')
            agency = doc.get('agency', '').replace('"', '""')
            url = doc.get('url', '')
            f.write(f'{i},"{title}","{number}","{field}","{date}","{agency}","{url}"\n')

    print(f"\n=== KẾT QUẢ CRAWL TẤT CẢ ===")
    print(f"Tổng văn bản: {results['total_crawled']}")
    print(f"Tổng trang: {results.get('pages_crawled', 0)}")
    print(f"Từ khóa sử dụng: {len(results.get('keywords_used', []))}")
    print(f"JSON: {output_file}")
    print(f"CSV: {csv_file}")

    return results


def crawl_limited_traffic_documents(max_docs=100):
    """Crawl văn bản giao thông với giới hạn — dùng HYBRID + khử trùng lặp"""
    print("=== CRAWL VĂN BẢN GIAO THÔNG (HYBRID) ===")
    print(f"Crawl tối đa {max_docs} văn bản về giao thông")
    print("-" * 60)

    Config.ensure_directories()
    crawler = ThuvienCrawlerAgent()

    combined_docs = []
    seen_urls, seen_nums = set(), set()

    # Chia đều hạn mức cho mỗi keyword
    per_query = max(1, max_docs // len(PREDICT_QUERIES))

    for i, kw in enumerate(PREDICT_QUERIES, 1):
        if len(combined_docs) >= max_docs:
            break

        print(f"[{i}/{len(PREDICT_QUERIES)}] HYBRID crawling từ khóa: '{kw}'")

        # Ước lượng: 20 văn bản/trang
        pages_per_query = max(1, per_query // 20)

        res = crawler.process(
            search_params={
                "keyword": kw,
                "max_pages": pages_per_query,
                "docs_per_page": 20,
                "max_docs": per_query,
                "mode": "hybrid",   # ← DÙNG HYBRID Ở ĐÂY
                "headless": True,
            }
        )

        docs = res.get("documents", [])
        # Khử trùng lặp theo URL & Số hiệu
        for d in docs:
            if len(combined_docs) >= max_docs:
                break

            keep = False

            u = d.get("url")
            if u:
                nu = norm_url(u)
                if nu and nu not in seen_urls:
                    seen_urls.add(nu)
                    keep = True

            n = d.get("number")
            if n:
                nn = norm_num(n)
                if nn and nn != "KHÔNGXÁCĐỊNH" and nn not in seen_nums:
                    seen_nums.add(nn)
                    keep = True

            if keep:
                combined_docs.append(d)

    # Gói kết quả tổng hợp theo đúng schema
    results = {
        "documents": combined_docs,
        "total_crawled": len(combined_docs),
        "pages_crawled": None,
        "docs_per_page": 20,
        "crawl_method": "hybrid",
        "keywords_used": PREDICT_QUERIES,
    }

    # Lưu kết quả
    output_file = os.path.join(Config.RAW_DATA_DIR, "crawled_documents.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== KẾT QUẢ HYBRID CRAWL (GIỚI HẠN) ===")
    print(f"Keywords: {len(PREDICT_QUERIES)}")
    print(f"Văn bản unique: {len(combined_docs)}")
    print(f"Phương pháp: HYBRID")
    print(f"Saved: {output_file}")

    return results


def main():
    print("=== BÀI TEST AI ENGINEER - MULTIPLE AI AGENTS CHO LEGAL ===")
    print("YÊU CẦU 1: Thu thập dữ liệu từ thuvienphapluat.vn")
    print("Metadata cần lấy: số hiệu, lĩnh vực, ngày ban hành, hiệu lực")
    print("-" * 60)
    print()
    print("CHỌN CHỨC NĂNG:")
    print("1. Crawl TẤT CẢ văn bản giao thông (không giới hạn)")
    print("2. Crawl giới hạn văn bản giao thông (100 văn bản)")
    print("3. Crawl nhanh để test (20 văn bản)")
    print("-" * 60)

    try:
        choice = input("Nhập lựa chọn (1/2/3): ").strip()

        if choice == "1":
            print("\nCẢNH BÁO: Crawl tất cả có thể mất vài giờ!")
            confirm = input("Bạn có chắc chắn? (y/n): ").lower()
            if confirm in ['y', 'yes']:
                crawl_all_traffic_documents()
            else:
                print("Đã hủy!")

        elif choice == "2":
            crawl_limited_traffic_documents(max_docs=100)

        elif choice == "3":
            crawl_limited_traffic_documents(max_docs=20)

        else:
            print("Lựa chọn không hợp lệ! Chạy crawl mặc định...")
            crawl_limited_traffic_documents(max_docs=50)

    except KeyboardInterrupt:
        print("\nĐã dừng bởi người dùng!")
    except Exception as e:
        print(f"\nLỗi: {e}")

    print("\nGợi ý: chạy 'python evaluators/metrics_recall.py' để tính % Recall so với gold ATGT.")


if __name__ == "__main__":
    main()
