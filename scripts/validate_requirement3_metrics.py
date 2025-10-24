#!/usr/bin/env python3
"""
Validate Yêu cầu 3 Metrics - Kiểm tra đầy đủ các metrics theo đề bài

Chức năng chính:
1. Standard Validation: Kiểm tra các metrics cơ bản theo yêu cầu đề bài
2. Deep Validation: Phân tích chi tiết nội dung thực tế từ văn bản
3. Comprehensive Report: Tổng hợp cả 2 loại validation trong 1 báo cáo

Metrics theo đề bài yêu cầu 3:
- % độ lệch dự báo (so với benchmark chuyên gia)
- Số giả định được giải thích rõ (>=3 giả định/kịch bản)

Validation bổ sung:
- Ước lượng chi phí tuân thủ, chi phí áp dụng, lợi ích
- 3 kịch bản (lạc quan, trung bình, bi quan)
- Phân tích nội dung thực tế vs ước tính
"""

import sys
import os
import json
import re
import argparse
from typing import Dict, List
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from economic_analysis.transport_economic_analyzer import TransportEconomicAnalyzer

# ============================================================================
# CONFIGURATION - Cấu hình validation
# ============================================================================

VALIDATION_CONFIG = {
    'input_file': 'data/raw/final_perfect_dataset.json',
    'output_file': 'reports/requirement3_validation.json',
    'deep_validation_documents': 5,  # Số văn bản để deep validation
    'acceptable_deviation_threshold': 25.0,  # % độ lệch chấp nhận được
    'minimum_assumptions_per_scenario': 3    # Số giả định tối thiểu/kịch bản
}

# ===========================================================================
# CONTENT EXTRACTION UTILITIES - Tiện ích trích xuất nội dung
# ============================================================================

def extract_actual_costs_from_content(content: str) -> Dict:
    """
    Trích xuất chi phí thực tế từ nội dung văn bản
    Sử dụng regex patterns để tìm số tiền và phân loại theo context
    
    Args:
        content: Nội dung văn bản cần phân tích
        
    Returns:
        Dict: Chứa chi phí, phạt, lệ phí đã phân loại
    """
    # Patterns để tìm số tiền trong văn bản
    cost_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:triệu|tr)\s*(?:đồng|vnđ|vnd)?',
        r'(\d+(?:\.\d+)?)\s*(?:tỷ|ty)\s*(?:đồng|vnđ|vnd)?',
        r'(\d+(?:,\d+)*)\s*(?:đồng|vnđ|vnd)',
        r'từ\s*(\d+(?:\.\d+)?)\s*(?:đến|-)?\s*(\d+(?:\.\d+)?)\s*(?:triệu|tr|tỷ|ty)',
        r'phạt\s*(\d+(?:\.\d+)?)\s*(?:triệu|tr|tỷ|ty)',
        r'chi\s*phí\s*(\d+(?:\.\d+)?)\s*(?:triệu|tr|tỷ|ty)',
        r'lệ\s*phí\s*(\d+(?:\.\d+)?)\s*(?:triệu|tr|tỷ|ty)'
    ]
    
    found_costs = []
    found_penalties = []
    found_fees = []
    
    content_lower = content.lower()
    
    for pattern in cost_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        
        for match in matches:
            # Lấy context xung quanh số tiền để phân loại
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end].lower()
            
            try:
                # Trích xuất số tiền
                if len(match.groups()) >= 2:  # Range pattern
                    amount1 = float(match.group(1).replace(',', ''))
                    amount2 = float(match.group(2).replace(',', ''))
                    amount = (amount1 + amount2) / 2  # Lấy trung bình
                else:
                    amount = float(match.group(1).replace(',', ''))
                
                # Chuyển đổi đơn vị về triệu VND
                if 'tỷ' in match.group(0) or 'ty' in match.group(0):
                    amount *= 1000  # Tỷ -> triệu
                
                # Phân loại dựa trên context
                if any(keyword in context for keyword in ['phạt', 'vi phạm', 'xử phạt']):
                    found_penalties.append({
                        'amount': amount,
                        'context': context.strip(),
                        'match': match.group(0)
                    })
                elif any(keyword in context for keyword in ['lệ phí', 'phí', 'thu phí']):
                    found_fees.append({
                        'amount': amount,
                        'context': context.strip(),
                        'match': match.group(0)
                    })
                elif any(keyword in context for keyword in ['chi phí', 'kinh phí', 'đầu tư', 'mua sắm']):
                    found_costs.append({
                        'amount': amount,
                        'context': context.strip(),
                        'match': match.group(0)
                    })
                else:
                    # Mặc định là chi phí nếu không rõ
                    found_costs.append({
                        'amount': amount,
                        'context': context.strip(),
                        'match': match.group(0)
                    })
                    
            except (ValueError, IndexError):
                continue
    
    return {
        'costs': found_costs,
        'penalties': found_penalties,
        'fees': found_fees,
        'total_costs': sum(item['amount'] for item in found_costs),
        'total_penalties': sum(item['amount'] for item in found_penalties),
        'total_fees': sum(item['amount'] for item in found_fees)
    }

def extract_actual_benefits_from_content(content: str) -> Dict:
    """
    Trích xuất lợi ích thực tế từ nội dung văn bản
    Tìm kiếm các từ khóa và chỉ số định lượng về lợi ích
    
    Args:
        content: Nội dung văn bản cần phân tích
        
    Returns:
        Dict: Thông tin về lợi ích tìm được trong nội dung
    """
    # Từ khóa lợi ích theo danh mục
    benefit_keywords = {
        'safety': ['an toàn', 'giảm tai nạn', 'bảo đảm an toàn', 'phòng chống tai nạn'],
        'efficiency': ['hiệu quả', 'nâng cao', 'cải thiện', 'tối ưu', 'tiết kiệm'],
        'economic': ['kinh tế', 'tiết kiệm chi phí', 'giảm chi phí', 'lợi ích'],
        'quality': ['chất lượng', 'dịch vụ', 'quản lý', 'điều hành']
    }
    
    found_benefits = {
        'safety_mentions': 0,
        'efficiency_mentions': 0,
        'economic_mentions': 0,
        'quality_mentions': 0,
        'quantitative_targets': [],
        'benefit_descriptions': []
    }
    
    content_lower = content.lower()
    
    # Đếm số lần xuất hiện của từ khóa lợi ích
    for category, keywords in benefit_keywords.items():
        count = sum(1 for keyword in keywords if keyword in content_lower)
        found_benefits[f'{category}_mentions'] = count
    
    # Tìm các chỉ tiêu định lượng (%)
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*%|(\d+(?:\.\d+)?)\s*phần\s*trăm'
    percentage_matches = re.findall(percentage_pattern, content_lower)
    
    for match in percentage_matches:
        value = float(match[0] if match[0] else match[1])
        found_benefits['quantitative_targets'].append(value)
    
    # Trích xuất câu mô tả lợi ích
    benefit_sentences = []
    sentences = content.split('.')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keywords in benefit_keywords.values() for keyword in keywords):
            benefit_sentences.append(sentence.strip())
    
    found_benefits['benefit_descriptions'] = benefit_sentences[:5]  # Lấy 5 câu đầu
    
    return found_benefits

# ============================================================================
# STANDARD VALIDATION - Validation cơ bản theo đề bài
# ============================================================================

def validate_cost_estimation(result) -> Dict:
    """
    Validate ước lượng chi phí tuân thủ và áp dụng
    Kiểm tra xem analyzer có tạo được ước lượng chi phí không
    
    Args:
        result: Kết quả phân tích từ analyzer
        
    Returns:
        Dict: Kết quả validation chi phí
    """
    validation = {
        'compliance_cost_estimated': False,
        'application_cost_estimated': False,
        'benefit_estimated': False,
        'details': {}
    }
    
    # Kiểm tra phân tích chi phí
    if result.cost_analysis:
        cost = result.cost_analysis
        if cost.total_compliance_cost > 0:
            validation['compliance_cost_estimated'] = True
            validation['details']['compliance_cost'] = cost.total_compliance_cost
        
        if cost.total_cost > 0:
            validation['application_cost_estimated'] = True
            validation['details']['total_application_cost'] = cost.total_cost
    
    # Kiểm tra phân tích lợi ích
    if result.benefit_analysis and result.benefit_analysis.total_benefits > 0:
        validation['benefit_estimated'] = True
        validation['details']['total_benefits'] = result.benefit_analysis.total_benefits
    
    return validation

def validate_scenarios(result) -> Dict:
    """
    Validate 3 kịch bản (lạc quan, trung bình, bi quan)
    Kiểm tra xem có đủ 3 kịch bản với xác suất không
    
    Args:
        result: Kết quả phân tích từ analyzer
        
    Returns:
        Dict: Kết quả validation kịch bản
    """
    validation = {
        'has_three_scenarios': False,
        'has_optimistic': False,
        'has_average': False, 
        'has_pessimistic': False,
        'scenarios_have_probabilities': False,
        'details': {}
    }
    
    if result.scenarios and len(result.scenarios) >= 3:
        validation['has_three_scenarios'] = True
        scenario_names = list(result.scenarios.keys())
        validation['details']['scenario_count'] = len(result.scenarios)
        validation['details']['scenario_names'] = scenario_names
        
        # Kiểm tra các loại kịch bản bắt buộc
        for name, scenario in result.scenarios.items():
            if 'optimistic' in name.lower() or 'lạc quan' in scenario.name.lower():
                validation['has_optimistic'] = True
            elif 'average' in name.lower() or 'trung bình' in scenario.name.lower():
                validation['has_average'] = True
            elif 'pessimistic' in name.lower() or 'bi quan' in scenario.name.lower():
                validation['has_pessimistic'] = True
            
            # Kiểm tra xác suất
            if hasattr(scenario, 'probability') and scenario.probability > 0:
                validation['scenarios_have_probabilities'] = True
    
    return validation

def validate_assumptions(result) -> Dict:
    """
    Validate >= 3 giả định/kịch bản (metrics chính của đề bài)
    
    Args:
        result: Kết quả phân tích từ analyzer
        
    Returns:
        Dict: Kết quả validation giả định
    """
    validation = {
        'meets_assumption_requirement': True,
        'assumption_details': {},
        'total_assumptions': 0
    }
    
    if result.scenarios:
        for name, scenario in result.scenarios.items():
            assumption_count = len(scenario.assumptions) if hasattr(scenario, 'assumptions') else 0
            validation['assumption_details'][name] = {
                'count': assumption_count,
                'assumptions': scenario.assumptions if hasattr(scenario, 'assumptions') else [],
                'meets_requirement': assumption_count >= VALIDATION_CONFIG['minimum_assumptions_per_scenario']
            }
            validation['total_assumptions'] += assumption_count
            
            # Nếu bất kỳ kịch bản nào không đủ 3 giả định thì fail
            if assumption_count < VALIDATION_CONFIG['minimum_assumptions_per_scenario']:
                validation['meets_assumption_requirement'] = False
    
    return validation

def validate_expert_deviation(result) -> Dict:
    """
    Validate % độ lệch dự báo so với benchmark chuyên gia (metrics chính của đề bài)
    
    Args:
        result: Kết quả phân tích từ analyzer
        
    Returns:
        Dict: Kết quả validation độ lệch
    """
    validation = {
        'has_expert_comparison': False,
        'deviation_calculated': False,
        'acceptable_deviation': False,
        'details': {}
    }
    
    if result.expert_deviation:
        validation['has_expert_comparison'] = True
        overall_dev = result.expert_deviation.get('overall_deviation', 0)
        
        if overall_dev > 0:
            validation['deviation_calculated'] = True
            validation['details']['overall_deviation'] = overall_dev
            validation['details']['cost_deviation'] = result.expert_deviation.get('cost_deviation', 0)
            validation['details']['benefit_deviation'] = result.expert_deviation.get('benefit_deviation', 0)
            validation['details']['roi_deviation'] = result.expert_deviation.get('roi_deviation', 0)
            
            # Kiểm tra độ lệch có chấp nhận được không
            if overall_dev <= VALIDATION_CONFIG['acceptable_deviation_threshold']:
                validation['acceptable_deviation'] = True
            
            validation['details']['validation_status'] = result.expert_deviation.get('validation_status', 'N/A')
    
    return validation

# ============================================================================
# DEEP VALIDATION - Validation chi tiết nội dung
# ============================================================================

def deep_validate_document(doc: Dict, analyzer: TransportEconomicAnalyzer) -> Dict:
    """
    Kiểm tra chi tiết một văn bản - so sánh thực tế vs ước tính
    
    Args:
        doc: Thông tin văn bản
        analyzer: Analyzer đã khởi tạo
        
    Returns:
        Dict: Kết quả deep validation
    """
    print(f"\nDEEP VALIDATION: {doc.get('number', 'N/A')}")
    print(f"Cơ quan: {doc.get('agency', 'N/A')}")
    print("-" * 60)
    
    # 1. Trích xuất dữ liệu thực tế từ nội dung
    actual_costs = extract_actual_costs_from_content(doc.get('content', ''))
    actual_benefits = extract_actual_benefits_from_content(doc.get('content', ''))
    
    # 2. Lấy kết quả ước tính từ analyzer
    result = analyzer.analyze_document(doc)
    
    # 3. So sánh thực tế vs ước tính
    validation_result = {
        'document': {
            'number': doc.get('number', 'N/A'),
            'agency': doc.get('agency', 'N/A')
        },
        'actual_data': {
            'costs_found': actual_costs,
            'benefits_found': actual_benefits
        },
        'estimated_data': {
            'total_cost': result.cost_analysis.total_cost,
            'compliance_cost': result.cost_analysis.total_compliance_cost,
            'penalty_risk': result.cost_analysis.total_penalty_risk,
            'total_benefits': result.benefit_analysis.total_benefits,
            'direct_benefits': result.benefit_analysis.direct_benefits,
            'indirect_benefits': result.benefit_analysis.indirect_benefits
        },
        'validation': {}
    }
    
    # 4. In kết quả chi tiết
    print(f"ACTUAL DATA FOUND:")
    print(f"  Chi phí: {len(actual_costs['costs'])} mục, Tổng: {actual_costs['total_costs']:.1f}M")
    print(f"  Phạt: {len(actual_costs['penalties'])} mục, Tổng: {actual_costs['total_penalties']:.1f}M")
    print(f"  Lệ phí: {len(actual_costs['fees'])} mục, Tổng: {actual_costs['total_fees']:.1f}M")
    
    print(f"ANALYZER ESTIMATES:")
    print(f"  Tổng chi phí ước tính: {result.cost_analysis.total_cost:.1f}M VND")
    print(f"  Tổng lợi ích ước tính: {result.benefit_analysis.total_benefits:.1f}M VND")
    
    # 5. Đánh giá độ chính xác
    total_actual_costs = actual_costs['total_costs'] + actual_costs['total_penalties'] + actual_costs['total_fees']
    if total_actual_costs > 0:
        cost_accuracy = abs(result.cost_analysis.total_cost - total_actual_costs) / total_actual_costs * 100
        print(f"ACCURACY: Độ lệch chi phí {cost_accuracy:.1f}%")
        validation_result['validation']['cost_accuracy'] = cost_accuracy
        validation_result['validation']['cost_based_on_content'] = True
    else:
        print(f"ACCURACY: Không tìm thấy chi phí thực tế, sử dụng benchmark")
        validation_result['validation']['cost_based_on_content'] = False
    
    # Đánh giá lợi ích
    total_benefit_indicators = sum([
        actual_benefits['safety_mentions'],
        actual_benefits['efficiency_mentions'], 
        actual_benefits['economic_mentions'],
        actual_benefits['quality_mentions']
    ])
    
    print(f"BENEFIT INDICATORS: {total_benefit_indicators} mentions")
    validation_result['validation']['benefit_indicators'] = total_benefit_indicators
    validation_result['validation']['benefit_based_on_content'] = total_benefit_indicators > 0
    
    return validation_result

# =======================================================================
# MAIN VALIDATION FUNCTIONS - Hàm validation chính
# ============================================================================

def run_comprehensive_validation():
    """
    Chạy validation toàn diện cho Yêu cầu 3
    Kiểm tra tất cả metrics theo đề bài
    
    Returns:
        Tuple: (validation_report, success_status)
    """
    print("VALIDATION YÊU CẦU 3: ĐÁNH GIÁ TÁC ĐỘNG KINH TẾ")
    print("=" * 60)
    
    # Khởi tạo analyzer
    analyzer = TransportEconomicAnalyzer()
    
    # Load dữ liệu thực
    try:
        with open(VALIDATION_CONFIG['input_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
        
        print(f"Loaded {len(documents)} documents from {VALIDATION_CONFIG['input_file'].split('/')[-1]}")
        
        # Tìm văn bản có nội dung kinh tế để test
        test_doc = None
        for doc in documents:
            content = doc.get('content', '').lower()
            if any(keyword in content for keyword in ['triệu đồng', 'tỷ đồng', 'chi phí', 'phạt tiền', 'lệ phí', 'phạt từ', 'mức phạt']):
                test_doc = doc
                break
        
        if not test_doc:
            # Fallback về văn bản đầu tiên nếu không tìm thấy
            test_doc = documents[0] if documents else None
            
        if not test_doc:
            raise FileNotFoundError("No documents found")
            
        print(f"Using document: {test_doc.get('number', 'N/A')} - {test_doc.get('agency', 'N/A')}")
        
    except FileNotFoundError:
        print("Không tìm thấy dữ liệu thực. Sử dụng sample data.")
        # Fallback sample document
        test_doc = {
            'number': 'VALIDATION_TEST',
            'agency': 'Test Agency',
            'field': 'Giao thông',
            'content': '''
            Điều 1. Quy định kiểm định xe
            1. Xe ô tô phải kiểm định định kỳ với chi phí 2.5 triệu đồng/lần
            2. Lái xe phải đào tạo bổ sung với chi phí 8 triệu đồng
            3. Vi phạm sẽ bị phạt từ 5-15 triệu đồng
            4. Quy định nhằm nâng cao an toàn giao thông, giảm tai nạn
            '''
        }
    
    # Phân tích văn bản
    result = analyzer.analyze_document(test_doc)
    
    # Chạy các validation
    print("\n1. VALIDATION ƯỚC LƯỢNG CHI PHÍ & LỢI ÍCH:")
    cost_validation = validate_cost_estimation(result)
    print(f"   Chi phí tuân thủ: {'PASS' if cost_validation['compliance_cost_estimated'] else 'FAIL'}")
    print(f"   Chi phí áp dụng: {'PASS' if cost_validation['application_cost_estimated'] else 'FAIL'}")
    print(f"   Lợi ích: {'PASS' if cost_validation['benefit_estimated'] else 'FAIL'}")
    
    print("\n2. VALIDATION 3 KỊCH BẢN:")
    scenario_validation = validate_scenarios(result)
    print(f"   Có 3 kịch bản: {'PASS' if scenario_validation['has_three_scenarios'] else 'FAIL'}")
    print(f"   Có kịch bản lạc quan: {'PASS' if scenario_validation['has_optimistic'] else 'FAIL'}")
    print(f"   Có kịch bản trung bình: {'PASS' if scenario_validation['has_average'] else 'FAIL'}")
    print(f"   Có kịch bản bi quan: {'PASS' if scenario_validation['has_pessimistic'] else 'FAIL'}")
    print(f"   Có xác suất: {'PASS' if scenario_validation['scenarios_have_probabilities'] else 'FAIL'}")
    
    print("\n3. VALIDATION GIẢ ĐỊNH (>=3/kịch bản) - METRICS CHÍNH:")
    assumption_validation = validate_assumptions(result)
    print(f"   Đạt yêu cầu >=3 giả định/kịch bản: {'PASS' if assumption_validation['meets_assumption_requirement'] else 'FAIL'}")
    print(f"   Tổng số giả định: {assumption_validation['total_assumptions']}")
    for scenario_name, details in assumption_validation['assumption_details'].items():
        print(f"   {scenario_name}: {details['count']} giả định {'PASS' if details['meets_requirement'] else 'FAIL'}")
    
    print("\n4. VALIDATION % ĐỘ LỆCH SO VỚI CHUYÊN GIA - METRICS CHÍNH:")
    deviation_validation = validate_expert_deviation(result)
    print(f"   Có so sánh với chuyên gia: {'PASS' if deviation_validation['has_expert_comparison'] else 'FAIL'}")
    print(f"   Tính được % độ lệch: {'PASS' if deviation_validation['deviation_calculated'] else 'FAIL'}")
    print(f"   Độ lệch chấp nhận được (<=25%): {'PASS' if deviation_validation['acceptable_deviation'] else 'FAIL'}")
    
    if deviation_validation['details']:
        details = deviation_validation['details']
        print(f"   Độ lệch tổng thể: {details.get('overall_deviation', 0):.1f}%")
        print(f"   Trạng thái: {details.get('validation_status', 'N/A')}")
    
    # Tổng kết
    print("\n" + "=" * 60)
    print("TỔNG KẾT VALIDATION:")
    
    # Đếm số checks pass
    checks = [
        cost_validation['compliance_cost_estimated'],
        cost_validation['application_cost_estimated'], 
        cost_validation['benefit_estimated'],
        scenario_validation['has_three_scenarios'],
        scenario_validation['has_optimistic'],
        scenario_validation['has_average'],
        scenario_validation['has_pessimistic'],
        scenario_validation['scenarios_have_probabilities'],
        assumption_validation['meets_assumption_requirement'],
        deviation_validation['has_expert_comparison'],
        deviation_validation['deviation_calculated']
    ]
    
    total_checks = len(checks)
    passed_checks = sum(checks)
    completion_rate = (passed_checks / total_checks) * 100
    
    print(f"Số checks passed: {passed_checks}/{total_checks}")
    print(f"Tỷ lệ hoàn thành: {completion_rate:.1f}%")
    
    if completion_rate >= 90:
        print("YÊU CẦU 3 HOÀN THÀNH XUẤT SẮC!")
    elif completion_rate >= 80:
        print("YÊU CẦU 3 HOÀN THÀNH TỐT!")
    elif completion_rate >= 70:
        print("YÊU CẦU 3 CẦN CẢI THIỆN!")
    else:
        print("YÊU CẦU 3 CHƯA ĐẠT YÊU CẦU!")
    
    # Tạo báo cáo validation
    validation_report = {
        'timestamp': datetime.now().isoformat(),
        'standard_validation': {
            'cost_estimation': cost_validation,
            'scenarios': scenario_validation,
            'assumptions': assumption_validation,
            'expert_deviation': deviation_validation,
            'overall_completion_rate': completion_rate,
            'total_checks': total_checks,
            'passed_checks': passed_checks
        }
    }
    
    print(f"\nBáo cáo standard validation đã tạo")
    
    return validation_report, completion_rate >= 80

def run_deep_validation():
    """
    Chạy deep validation cho nhiều văn bản
    Phân tích chi tiết nội dung thực tế vs ước tính
    
    Returns:
        Dict: Tổng hợp kết quả deep validation
    """
    print("DEEP VALIDATION YÊU CẦU 3: KIỂM TRA TÍNH CHÍNH XÁC")
    print("=" * 60)
    
    # Load dữ liệu
    try:
        with open(VALIDATION_CONFIG['input_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
    except FileNotFoundError:
        print("Không tìm thấy dữ liệu!")
        return {}
    
    # Tìm văn bản có nội dung kinh tế
    economic_docs = []
    for doc in documents:
        content = doc.get('content', '').lower()
        if any(keyword in content for keyword in ['triệu đồng', 'tỷ đồng', 'chi phí', 'phạt tiền', 'lệ phí']):
            economic_docs.append(doc)
            if len(economic_docs) >= VALIDATION_CONFIG['deep_validation_documents']:
                break
    
    print(f"Tìm thấy {len(economic_docs)} văn bản có nội dung kinh tế để kiểm tra")
    
    # Khởi tạo analyzer
    analyzer = TransportEconomicAnalyzer()
    
    # Validate từng văn bản
    validation_results = []
    for i, doc in enumerate(economic_docs, 1):
        print(f"\n[{i}/{len(economic_docs)}] Validating document...")
        result = deep_validate_document(doc, analyzer)
        validation_results.append(result)
    
    # Tổng hợp kết quả
    print(f"\n" + "=" * 60)
    print("SUMMARY DEEP VALIDATION RESULTS:")
    print("=" * 60)
    
    cost_based_count = sum(1 for r in validation_results if r['validation'].get('cost_based_on_content', False))
    benefit_based_count = sum(1 for r in validation_results if r['validation'].get('benefit_based_on_content', False))
    
    print(f"Văn bản có chi phí thực tế trong nội dung: {cost_based_count}/{len(validation_results)}")
    print(f"Văn bản có chỉ số lợi ích trong nội dung: {benefit_based_count}/{len(validation_results)}")
    
    # Tính độ chính xác trung bình
    cost_accuracies = [r['validation']['cost_accuracy'] for r in validation_results if 'cost_accuracy' in r['validation']]
    avg_cost_accuracy = sum(cost_accuracies) / len(cost_accuracies) if cost_accuracies else 0
    
    if cost_accuracies:
        print(f"Độ chính xác chi phí trung bình: {avg_cost_accuracy:.1f}%")
    
    # Tạo tổng hợp deep validation
    deep_validation_summary = {
        'total_documents_analyzed': len(validation_results),
        'documents_with_actual_costs': cost_based_count,
        'documents_with_benefit_indicators': benefit_based_count,
        'average_cost_accuracy': avg_cost_accuracy,
        'detailed_results': validation_results
    }
    
    print(f"\nBáo cáo deep validation hoàn thành")
    
    return deep_validation_summary

# ============================================================================
# MAIN EXECUTION - Thực thi chính
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate Requirement 3 Metrics')
    parser.add_argument('--standard-only', action='store_true', help='Run only standard validation')
    parser.add_argument('--deep-only', action='store_true', help='Run only deep validation')
    args = parser.parse_args()
    
    if args.standard_only:
        print("Running STANDARD VALIDATION ONLY...")
        standard_report, success = run_comprehensive_validation()
        sys.exit(0 if success else 1)
    elif args.deep_only:
        print("Running DEEP VALIDATION ONLY...")
        deep_report = run_deep_validation()
        # Lưu deep-only report
        os.makedirs('reports', exist_ok=True)
        with open(VALIDATION_CONFIG['output_file'], 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'validation_type': 'deep_only',
                'deep_validation': deep_report
            }, f, indent=2, ensure_ascii=False)
        print("Báo cáo deep validation đã lưu: " + VALIDATION_CONFIG['output_file'])
    else:
        print("COMPREHENSIVE VALIDATION YÊU CẦU 3")
        print("Chạy cả Standard + Deep validation trong 1 lần")
        print("=" * 80)
        
        # 1. Chạy standard validation trước
        print("\nPHASE 1: STANDARD VALIDATION")
        print("-" * 50)
        standard_report, success = run_comprehensive_validation()
        
        # 2. Chạy deep validation
        print(f"\nPHASE 2: DEEP VALIDATION")
        print("-" * 50)
        deep_report = run_deep_validation()
        
        # 3. Gộp báo cáo thành 1 file
        combined_report = {
            'timestamp': standard_report['timestamp'],
            'validation_type': 'comprehensive',
            'standard_validation': standard_report['standard_validation'],
            'deep_validation': deep_report,
            'summary': {
                'standard_completion_rate': standard_report['standard_validation']['overall_completion_rate'],
                'deep_documents_analyzed': deep_report['total_documents_analyzed'],
                'deep_accuracy_rate': deep_report['average_cost_accuracy'],
                'overall_status': 'PASSED' if success and deep_report['average_cost_accuracy'] > 0 else 'REVIEW_NEEDED'
            }
        }
        
        # Lưu báo cáo tổng hợp
        os.makedirs('reports', exist_ok=True)
        with open(VALIDATION_CONFIG['output_file'], 'w', encoding='utf-8') as f:
            json.dump(combined_report, f, indent=2, ensure_ascii=False)
        
        # 4. Tổng kết cuối
        print(f"\n" + "=" * 80)
        print("COMPREHENSIVE VALIDATION COMPLETED!")
        print("=" * 80)
        print("Standard validation: Kiểm tra metrics theo yêu cầu đề bài")
        print("Deep validation: Phân tích chi tiết nội dung thực tế")
        print(f"Standard completion: {standard_report['standard_validation']['overall_completion_rate']:.1f}%")
        print(f"Deep documents analyzed: {deep_report['total_documents_analyzed']}")
        print(f"Deep accuracy: {deep_report['average_cost_accuracy']:.1f}%")
        print("\nBáo cáo tổng hợp đã lưu: " + VALIDATION_CONFIG['output_file'])
        
        sys.exit(0 if success else 1)