#!/usr/bin/env python3
"""
Enhanced Recall Calculator - Kết hợp features từ file cũ và mới
Tính Recall theo tiêu chí: 'Recall % văn bản liên quan (so với tập chọn tay)'
"""

import json, os, re
from urllib.parse import urlparse
from datetime import datetime

# File paths - có thể config
CRAWLED_JSON = "data/raw/final_perfect_dataset.json"  # Updated to use final dataset
GROUND_JSON  = "data/gold/gold_set.json"
OUTPUT_REPORT = "reports/recall_analysis.json"

def norm_url(u: str) -> str:
    """Normalize URL for comparison - enhanced version"""
    if not u:
        return ""
    p = urlparse(u.lower())
    # Remove www and trailing slash
    netloc = re.sub(r'^www\.', '', p.netloc)
    return f"{p.scheme}://{netloc}{p.path}".rstrip("/")

def norm_num(s: str) -> str:
    """Normalize document number for comparison"""
    return re.sub(r"\s+", "", (s or "").upper())

def load_crawled():
    """Load crawled documents - enhanced to handle multiple formats"""
    print(f"Loading crawled data: {CRAWLED_JSON}")
    
    with open(CRAWLED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, dict) and 'documents' in data:
        docs = data['documents']
        total_docs = data.get('metadata', {}).get('total_documents', len(docs))
        print(f"Loaded {len(docs)} documents (metadata says {total_docs})")
    elif isinstance(data, list):
        docs = data
        total_docs = len(docs)
        print(f"Loaded {total_docs} documents")
    else:
        raise ValueError("Unsupported JSON format")
    
    # Extract URLs and numbers
    crawled_urls = {norm_url(d["url"]) for d in docs if d.get("url")}
    crawled_nums = {norm_num(d.get("number") or d.get("document_number", "")) for d in docs if d.get("number") or d.get("document_number")}
    
    print(f"   URLs: {len(crawled_urls)}")
    print(f"   Numbers: {len(crawled_nums)}")
    
    return crawled_urls, crawled_nums, total_docs

def load_gold():
    """Load gold standard dataset - enhanced with better logging"""
    print(f"Loading gold standard: {GROUND_JSON}")
    
    if not os.path.exists(GROUND_JSON):
        print(f"Error: Không tìm thấy {GROUND_JSON}. Bạn có thể dùng groundtruth crawler thay thế.")
        return set(), set()
    
    with open(GROUND_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)   # mảng URL hoặc số hiệu
    
    gold_urls, gold_nums = set(), set()
    for x in items:
        if str(x).startswith("http"):
            gold_urls.add(norm_url(x))
        else:
            gold_nums.add(norm_num(x))
    
    print(f"Gold standard loaded:")
    print(f"   URLs: {len(gold_urls)}")
    print(f"   Numbers: {len(gold_nums)}")
    print(f"   Total items: {len(items)}")
    
    return gold_urls, gold_nums

def calculate_detailed_metrics(got_urls, got_nums, gold_urls, gold_nums):
    """Calculate detailed metrics including recall, precision, F1"""
    
    print(f"\nCalculating detailed metrics...")
    
    # URL-based matching
    url_matches = got_urls & gold_urls
    url_recall = len(url_matches) / len(gold_urls) if gold_urls else 0
    url_precision = len(url_matches) / len(got_urls) if got_urls else 0
    
    # Number-based matching  
    num_matches = got_nums & gold_nums
    num_recall = len(num_matches) / len(gold_nums) if gold_nums else 0
    num_precision = len(num_matches) / len(got_nums) if got_nums else 0
    
    # Union-based matching (original logic) - tránh đếm trùng
    gold_union = gold_urls | {f"NUM:{n}" for n in gold_nums}
    hit_union = (got_urls & gold_urls) | {f"NUM:{n}" for n in (got_nums & gold_nums)}
    
    overall_recall = len(hit_union) / len(gold_union) if gold_union else 0
    
    # Calculate precision for overall
    got_union = got_urls | {f"NUM:{n}" for n in got_nums}
    overall_precision = len(hit_union) / len(got_union) if got_union else 0
    
    # F1 scores
    url_f1 = 2 * (url_precision * url_recall) / (url_precision + url_recall) if (url_precision + url_recall) > 0 else 0
    num_f1 = 2 * (num_precision * num_recall) / (num_precision + num_recall) if (num_precision + num_recall) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    return {
        'url_metrics': {
            'recall': url_recall,
            'precision': url_precision,
            'f1_score': url_f1,
            'matches': len(url_matches),
            'gold_total': len(gold_urls),
            'crawled_total': len(got_urls)
        },
        'number_metrics': {
            'recall': num_recall,
            'precision': num_precision,
            'f1_score': num_f1,
            'matches': len(num_matches),
            'gold_total': len(gold_nums),
            'crawled_total': len(got_nums)
        },
        'overall_metrics': {
            'recall': overall_recall,
            'precision': overall_precision,
            'f1_score': overall_f1,
            'matches': len(hit_union),
            'gold_total': len(gold_union),
            'crawled_total': len(got_union)
        },
        'detailed_matches': {
            'url_matches': list(url_matches),
            'number_matches': list(num_matches)
        }
    }

def recall_score(got_urls, got_nums, gold_urls, gold_nums):
    """Original recall function - kept for backward compatibility"""
    # union-key để tránh đếm trùng giữa URL và số hiệu
    gold_union = gold_urls | {f"NUM:{n}" for n in gold_nums}
    hit_union  = (got_urls & gold_urls) | {f"NUM:{n}" for n in (got_nums & gold_nums)}
    return (len(hit_union) / len(gold_union)) if gold_union else 0.0, len(hit_union), len(gold_union)

def print_detailed_results(metrics, total_docs):
    """Print comprehensive results"""
    
    print(f"\nCOMPREHENSIVE RECALL ANALYSIS")
    print("=" * 70)
    
    # Overall metrics (main result for evaluation)
    overall = metrics['overall_metrics']
    print(f"OVERALL PERFORMANCE (Union-based):")
    print(f"   Recall: {overall['recall']:.3f} ({overall['recall']*100:.1f}%)")
    print(f"   Precision: {overall['precision']:.3f} ({overall['precision']*100:.1f}%)")
    print(f"   F1-Score: {overall['f1_score']:.3f} ({overall['f1_score']*100:.1f}%)")
    print(f"   Matches: {overall['matches']}/{overall['gold_total']} documents")
    
    # URL-based metrics
    url = metrics['url_metrics']
    print(f"\nURL-BASED MATCHING:")
    print(f"   Recall: {url['recall']:.3f} ({url['recall']*100:.1f}%)")
    print(f"   Precision: {url['precision']:.3f} ({url['precision']*100:.1f}%)")
    print(f"   Matches: {url['matches']}/{url['gold_total']} URLs")
    
    # Number-based metrics
    num = metrics['number_metrics']
    print(f"\nNUMBER-BASED MATCHING:")
    print(f"   Recall: {num['recall']:.3f} ({num['recall']*100:.1f}%)")
    print(f"   Precision: {num['precision']:.3f} ({num['precision']*100:.1f}%)")
    print(f"   Matches: {num['matches']}/{num['gold_total']} numbers")
    
    # Quality assessment
    print(f"\nQUALITY ASSESSMENT:")
    recall_pct = overall['recall'] * 100
    if recall_pct >= 90:
        print(f"   EXCELLENT: Recall >= 90% - Hệ thống thu thập rất tốt!")
    elif recall_pct >= 80:
        print(f"   GOOD: Recall >= 80% - Hệ thống thu thập tốt")
    elif recall_pct >= 70:
        print(f"   ACCEPTABLE: Recall >= 70% - Hệ thống thu thập chấp nhận được")
    elif recall_pct >= 60:
        print(f"   FAIR: Recall >= 60% - Cần cải thiện hệ thống")
    else:
        print(f"   POOR: Recall < 60% - Cần cải thiện đáng kể")
    
    print(f"\nDATASET INFO:")
    print(f"   Total crawled documents: {total_docs}")
    print(f"   Gold standard size: {overall['gold_total']}")
    print(f"   Coverage rate: {overall['matches']}/{overall['gold_total']} ({overall['recall']*100:.1f}%)")

def save_detailed_report(metrics, total_docs):
    """Save comprehensive report to JSON"""
    
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    
    report = {
        'metadata': {
            'calculation_type': 'Enhanced Recall Analysis',
            'description': 'Recall % văn bản liên quan (so với tập chọn tay)',
            'formula': 'Recall = Matched Documents / Total Gold Documents',
            'generated_at': datetime.now().isoformat(),
            'crawled_file': CRAWLED_JSON,
            'gold_file': GROUND_JSON,
            'total_crawled_documents': total_docs
        },
        'metrics': metrics,
        'summary': {
            'main_recall': f"{metrics['overall_metrics']['recall']*100:.1f}%",
            'quality_level': 'Excellent' if metrics['overall_metrics']['recall'] >= 0.9 else 
                           'Good' if metrics['overall_metrics']['recall'] >= 0.8 else
                           'Acceptable' if metrics['overall_metrics']['recall'] >= 0.7 else
                           'Fair' if metrics['overall_metrics']['recall'] >= 0.6 else 'Poor',
            'matches': f"{metrics['overall_metrics']['matches']}/{metrics['overall_metrics']['gold_total']}"
        }
    }
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed report saved to: {OUTPUT_REPORT}")

def main():
    """Enhanced main function with comprehensive analysis"""
    
    print("ENHANCED RECALL CALCULATOR")
    print("Tính Recall theo tiêu chí: 'Recall % văn bản liên quan (so với tập chọn tay)'")
    print("=" * 70)
    
    try:
        # Load data
        got_u, got_n, total_docs = load_crawled()
        gold_u, gold_n = load_gold()
        
        # Calculate metrics
        metrics = calculate_detailed_metrics(got_u, got_n, gold_u, gold_n)
        
        # Print results
        print_detailed_results(metrics, total_docs)
        
        # Save report
        save_detailed_report(metrics, total_docs)
        
        # Legacy output for backward compatibility
        recall, hit, total = recall_score(got_u, got_n, gold_u, gold_n)
        print(f"\nLEGACY FORMAT (for compatibility):")
        print(f"   hits/total: {hit}/{total}")
        print(f"   recall    : {recall:.2%}")
        
        print(f"\nEVALUATION SUMMARY:")
        print(f"   Main Recall: {metrics['overall_metrics']['recall']*100:.1f}%")
        print(f"   Quality: {metrics['overall_metrics']['recall']*100:.1f}% coverage rate")
        print(f"   Ready for submission!")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
