# scripts/run_preprocess.py
import os, sys, json, pathlib

# cho phép import module trong project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preprocess.normalizer import normalize_text
from preprocess.segmenter import segment
from preprocess.diff_engine import diff_articles

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_FILE = ROOT/"data/raw/final_perfect_dataset.json"
PROCESSED_DIR = ROOT/"data/processed"
DIFF_DIR = ROOT/"data/diffs"

def main():
    if not RAW_FILE.exists():
        print(f"Không tìm thấy {RAW_FILE}. Hãy chạy crawl (Q1) trước.")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)

    # Handle both old format (list) and new format (dict with documents key)
    raw_data = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    if isinstance(raw_data, dict) and "documents" in raw_data:
        raw = raw_data["documents"]
    else:
        raw = raw_data
    docs = []

    # Chuẩn hóa + tách điều/khoản
    processed_ids = set()  # Track processed IDs to avoid duplicates
    
    for i, d in enumerate(raw):
        content = d.get("content", "")
        text = normalize_text(content)
        struct = segment(text)
        
        # Create unique doc_id
        doc_number = d.get("number", "")
        if doc_number:
            base_id = doc_number.replace("/", "_").replace("-", "_").replace(".", "_")
        else:
            # Fallback to URL-based ID
            url = d.get("url", "unknown")
            base_id = url.split("/")[-1].split(".")[0] if "/" in url else f"doc_{i}"
        
        # Ensure uniqueness
        doc_id = base_id
        counter = 1
        while doc_id in processed_ids:
            doc_id = f"{base_id}_{counter}"
            counter += 1
        
        processed_ids.add(doc_id)
        
        out = {"doc_id": doc_id, "meta": d, "structure": struct}
        (PROCESSED_DIR/f"{doc_id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        docs.append(out)

    
    # Diff giữa văn bản gốc và văn bản đã xử lý (chuẩn hóa + tách điều khoản)
    for i, doc in enumerate(docs):
        # Tạo "original" structure từ raw content (chưa tách điều khoản)
        raw_content = raw[i].get("content", "")
        original_structure = {
            "articles": [{
                "section": "Original",
                "title": "Raw Document Content",
                "clauses": [{
                    "no": "1",
                    "text": raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content,
                    "points": []
                }]
            }]
        }
        
        # Diff giữa original và processed
        if doc["structure"].get("articles"):
            diff = {
                "base": f"{doc['doc_id']}_original",
                "revised": f"{doc['doc_id']}_processed",
                "diff": diff_articles(original_structure, doc["structure"]),
            }
            (DIFF_DIR/f"{doc['doc_id']}_original_vs_processed.json").write_text(
                json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    print(f"Yêu cầu 2 hoàn thành!")
    print(f"   Processed documents: {len(docs)}")
    print(f"   Saved to: {PROCESSED_DIR}")
    print(f"   Diff files: {DIFF_DIR}")
    print(f"   Ready for evaluation!")

if __name__ == "__main__":
    main()
