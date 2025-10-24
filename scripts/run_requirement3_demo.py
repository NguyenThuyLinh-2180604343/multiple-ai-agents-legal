#!/usr/bin/env python3
"""
Demo Yêu cầu 3: Đánh giá tác động kinh tế giao thông

Chức năng chính:
1. Load dữ liệu văn bản giao thông từ yêu cầu 1 & 2
2. Phân tích tác động kinh tế cho từng văn bản
3. Tạo 3 kịch bản (lạc quan, trung bình, bi quan) với >=3 giả định
4. Tính % độ lệch so với benchmark chuyên gia
5. Tạo báo cáo tổng hợp với khuyến nghị

Metrics theo đề bài:
- % độ lệch dự báo (so với benchmark chuyên gia)
- Số giả định được giải thích rõ (>=3 giả định/kịch bản)
"""

import sys
import os
import json
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from economic_analysis.transport_economic_analyzer import TransportEconomicAnalyzer, EconomicAnalysisResult

# ============================================================================
# CONFIGURATION - Cấu hình demo
# ============================================================================

DEMO_CONFIG = {
    'input_file': 'data/raw/final_perfect_dataset.json',
    'output_file': 'reports/transport_economic_analysis.json',
    'num_documents_to_analyze': 3,  # Số văn bản để demo
    'show_detailed_analysis': True   # Hiển thị phân tích chi tiết
}

# ============================================================================
# DATA LOADING - Load dữ liệu
# ============================================================================

def load_transport_documents() -> List[Dict]:
    """
    Load dữ liệu văn bản giao thông từ yêu cầu 1 & 2
    
    Returns:
        List[Dict]: Danh sách văn bản đã được xử lý
    """
    try:
        with open(DEMO_CONFIG['input_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
        
        print(f"   Loaded {len(documents)} processed documents from {DEMO_CONFIG['input_file'].split('/')[-1]}")
        return documents
    
    except FileNotFoundError:
        print(f"   ERROR: Không tìm thấy file {DEMO_CONFIG['input_file']}")
        return []
    except json.JSONDecodeError:
        print(f"   ERROR: File {DEMO_CONFIG['input_file']} không đúng định dạng JSON")
        return []

def select_demo_documents(documents: List[Dict]) -> List[Dict]:
    """
    Chọn văn bản để demo (ưu tiên văn bản có nội dung giao thông rõ ràng)
    
    Args:
        documents: Danh sách tất cả văn bản
        
    Returns:
        List[Dict]: Danh sách văn bản được chọn để demo
    """
    # Filter văn bản giao thông
    transport_docs = []
    for doc in documents:
        field = doc.get('field', '').lower()
        content = doc.get('content', '').lower()
        
        # Kiểm tra có phải văn bản giao thông không
        if ('giao thông' in field or 'vận tải' in field or 
            'giao thông' in content or 'vận tải' in content):
            transport_docs.append(doc)
    
    print(f"   Tìm thấy {len(transport_docs)} văn bản giao thông")
    
    # Chọn số lượng văn bản theo config
    selected = transport_docs[:DEMO_CONFIG['num_documents_to_analyze']]
    print(f"   Chọn {len(selected)} văn bản để phân tích")
    
    return selected

# ============================================================================
# ANALYSIS EXECUTION - Thực hiện phân tích
# ============================================================================

def analyze_documents(documents: List[Dict], analyzer: TransportEconomicAnalyzer) -> List[EconomicAnalysisResult]:
    """
    Phân tích tác động kinh tế cho danh sách văn bản
    
    Args:
        documents: Danh sách văn bản cần phân tích
        analyzer: Transport Economic Analyzer đã khởi tạo
        
    Returns:
        List[EconomicAnalysisResult]: Kết quả phân tích cho từng văn bản
    """
    results = []
    
    print(f"Bắt đầu phân tích {len(documents)} văn bản giao thông...")
    print("=" * 60)
    
    for i, doc in enumerate(documents, 1):
        try:
            print(f"\n[{i}/{len(documents)}] Phân tích văn bản: {doc.get('number', 'N/A')}")
            
            # Thực hiện phân tích
            result = analyzer.analyze_document(doc)
            results.append(result)
            
            # Hiển thị kết quả tóm tắt
            average_scenario = result.scenarios['average']
            print(f"  Chi phí: {average_scenario.total_cost:.1f}M VND")
            print(f"  Lợi ích: {average_scenario.total_benefit:.1f}M VND/năm")
            print(f"  ROI: {average_scenario.roi_percentage:.1f}%")
            
        except Exception as e:
            print(f"  ERROR: Lỗi khi phân tích văn bản {doc.get('number', 'N/A')}: {str(e)}")
            continue
    
    return results

def print_detailed_analysis(result: EconomicAnalysisResult):
    """
    In phân tích chi tiết cho 1 văn bản (văn bản đầu tiên)
    
    Args:
        result: Kết quả phân tích của văn bản
    """
    print("\n" + "=" * 80)
    print("PHÂN TÍCH CHI TIẾT VĂN BẢN ĐẦU TIÊN:")
    print("=" * 80)
    
    # Sử dụng method có sẵn của analyzer để in chi tiết
    analyzer = TransportEconomicAnalyzer()
    analyzer.print_analysis_result(result)

# ============================================================================
# SUMMARY REPORTING - Báo cáo tổng hợp
# ============================================================================

def print_summary_report(results: List[EconomicAnalysisResult]):
    """
    In báo cáo tổng hợp cho tất cả văn bản đã phân tích
    
    Args:
        results: Danh sách kết quả phân tích
    """
    print("\n" + "=" * 80)
    print("BÁO CÁO TỔNG HỢP PHÂN TÍCH TÁC ĐỘNG KINH TẾ GIAO THÔNG")
    print("=" * 80)
    
    if not results:
        print("Không có kết quả phân tích nào.")
        return
    
    # Tính toán thống kê tổng quan
    total_docs = len(results)
    total_cost = sum(r.scenarios['average'].total_cost for r in results)
    total_benefit = sum(r.scenarios['average'].total_benefit for r in results)
    positive_roi_count = sum(1 for r in results if r.scenarios['average'].roi_percentage > 0)
    
    # Tính độ lệch trung bình so với chuyên gia
    deviations = [r.expert_deviation['overall_deviation'] for r in results if r.expert_deviation]
    avg_deviation = sum(deviations) / len(deviations) if deviations else 0
    
    print(f"\nTHỐNG KÊ TỔNG QUAN:")
    print(f"Số văn bản phân tích: {total_docs}")
    print(f"Tổng chi phí ước tính: {total_cost:.1f} triệu VND")
    print(f"Tổng lợi ích ước tính: {total_benefit:.1f} triệu VND/năm")
    print(f"Lợi ích ròng tổng: {total_benefit - total_cost:.1f} triệu VND")
    print(f"Văn bản có ROI dương: {positive_roi_count}/{total_docs} ({positive_roi_count/total_docs*100:.1f}%)")
    print(f"Độ lệch trung bình so với chuyên gia: {avg_deviation:.1f}%")
    
    # Top 3 văn bản có ROI cao nhất
    sorted_results = sorted(results, key=lambda r: r.scenarios['average'].roi_percentage, reverse=True)
    
    print(f"\nTOP 3 VĂN BẢN CÓ ROI CAO NHẤT:")
    for i, result in enumerate(sorted_results[:3], 1):
        scenario = result.scenarios['average']
        doc_info = result.document_info
        print(f"{i}. {doc_info['number']} - ROI: {scenario.roi_percentage:.1f}%")
        print(f"   Cơ quan: {doc_info['agency']}")
        print(f"   Chi phí: {scenario.total_cost:.1f}M, Lợi ích: {scenario.total_benefit:.1f}M/năm")
    
    # Khuyến nghị chung
    print(f"\nKHUYẾN NGHỊ CHUNG:")
    if positive_roi_count / total_docs >= 0.7:
        print("Tổng thể các quy định giao thông có tác động kinh tế tích cực")
    else:
        print("Cần xem xét lại hiệu quả kinh tế của các quy định")
    
    print("Nên ưu tiên triển khai các quy định có ROI cao")
    print("Cần hỗ trợ doanh nghiệp trong giai đoạn đầu triển khai")

# ============================================================================
# DATA EXPORT - Xuất dữ liệu
# ============================================================================

def save_results_to_file(results: List[EconomicAnalysisResult], output_path: str = None):
    """
    Lưu kết quả phân tích ra file JSON
    
    Args:
        results: Danh sách kết quả phân tích
        output_path: Đường dẫn file output (optional)
    """
    if output_path is None:
        output_path = DEMO_CONFIG['output_file']
    
    # Tạo thư mục nếu chưa có
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Chuyển đổi results thành format JSON-serializable
    export_data = {
        'analysis_date': '2024-01-01',
        'total_documents': len(results),
        'results': []
    }
    
    for result in results:
        # Chuyển đổi từng result thành dict
        result_dict = {
            'document_info': result.document_info,
            'features': {
                'compliance_costs': result.features.compliance_costs,
                'penalties': result.features.penalties,
                'fees': result.features.fees,
                'keywords': result.features.keywords
            },
            'cost_analysis': {
                'total_compliance_cost': result.cost_analysis.total_compliance_cost,
                'total_penalty_risk': result.cost_analysis.total_penalty_risk,
                'total_indirect_cost': result.cost_analysis.total_indirect_cost,
                'total_cost': result.cost_analysis.total_cost
            },
            'benefit_analysis': {
                'direct_benefits': result.benefit_analysis.direct_benefits,
                'indirect_benefits': result.benefit_analysis.indirect_benefits,
                'total_benefits': result.benefit_analysis.total_benefits
            },
            'scenarios': {
                name: {
                    'name': scenario.name,
                    'description': scenario.description,
                    'probability': scenario.probability,
                    'total_cost': scenario.total_cost,
                    'total_benefit': scenario.total_benefit,
                    'net_benefit': scenario.net_benefit,
                    'roi_percentage': scenario.roi_percentage,
                    'payback_months': scenario.payback_months,
                    'assumptions': scenario.assumptions
                }
                for name, scenario in result.scenarios.items()
            },
            'expert_deviation': result.expert_deviation,
            'recommendations': result.recommendations
        }
        
        export_data['results'].append(result_dict)
    
    # Lưu file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nKết quả đã được lưu vào: {output_path}")

# ============================================================================
# MAIN EXECUTION - Thực thi chính
# ============================================================================

def main():
    """
    Hàm chính thực hiện demo yêu cầu 3
    
    Workflow:
    1. Load dữ liệu văn bản giao thông
    2. Khởi tạo analyzer
    3. Chọn văn bản để demo
    4. Thực hiện phân tích
    5. Hiển thị kết quả chi tiết
    6. Tạo báo cáo tổng hợp
    7. Lưu kết quả ra file
    """
    print("DEMO YÊU CẦU 3: PHÂN TÍCH TÁC ĐỘNG KINH TẾ GIAO THÔNG")
    print("Sử dụng dữ liệu thực từ Yêu cầu 1 & 2")
    print("=" * 60)
    
    # Bước 1: Khởi tạo analyzer
    print("1. Khởi tạo analyzer...")
    analyzer = TransportEconomicAnalyzer()
    
    # Bước 2: Load dữ liệu
    print("2. Load dữ liệu giao thông...")
    documents = load_transport_documents()
    if not documents:
        print("   ERROR: Không có dữ liệu để phân tích!")
        return
    
    # Bước 3: Chọn văn bản demo
    print("3. Chọn văn bản mẫu để demo...")
    selected_docs = select_demo_documents(documents)
    if not selected_docs:
        print("   ERROR: Không tìm thấy văn bản giao thông phù hợp!")
        return
    
    # Bước 4: Thực hiện phân tích
    print("4. Thực hiện phân tích...")
    results = analyze_documents(selected_docs, analyzer)
    if not results:
        print("   ERROR: Không có kết quả phân tích nào!")
        return
    
    # Bước 5: Hiển thị phân tích chi tiết (văn bản đầu tiên)
    if DEMO_CONFIG['show_detailed_analysis'] and results:
        print_detailed_analysis(results[0])
    
    # Bước 6: Báo cáo tổng hợp
    print_summary_report(results)
    
    # Bước 7: Lưu kết quả
    print("5. Lưu kết quả...")
    save_results_to_file(results)
    
    # Kết thúc demo
    print("\n" + "=" * 80)
    print("DEMO YÊU CẦU 3 HOÀN THÀNH!")
    print("Đã phân tích tác động kinh tế từ văn bản giao thông thực tế")
    print("Tạo được 3 kịch bản với xác suất và giả định")
    print("Tính được % độ lệch so với benchmark chuyên gia")
    print("Đưa ra khuyến nghị cụ thể cho từng văn bản")
    print("=" * 80)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()