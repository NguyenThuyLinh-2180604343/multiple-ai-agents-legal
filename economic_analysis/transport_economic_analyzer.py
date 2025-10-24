#!/usr/bin/env python3
"""
Transport Economic Analyzer - Yêu cầu 3: Đánh giá tác động kinh tế

Chức năng chính:
1. Ước lượng chi phí tuân thủ, chi phí áp dụng, lợi ích
2. Xây dựng 3 kịch bản (lạc quan, trung bình, bi quan)
3. Tính % độ lệch dự báo so với benchmark chuyên gia
4. Đảm bảo >=3 giả định/kịch bản

Metrics theo đề bài:
- % độ lệch dự báo (so với benchmark chuyên gia)
- Số giả định được giải thích rõ (>=3 giả định/kịch bản)
"""

import json
import re
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# DATA STRUCTURES - Cấu trúc dữ liệu chính
# ============================================================================

@dataclass
class EconomicFeatures:
    """Features kinh tế được trích xuất từ văn bản"""
    compliance_costs: List[float]      # Chi phí tuân thủ
    penalties: List[float]             # Mức phạt
    fees: List[float]                  # Lệ phí
    benefits: List[float]              # Lợi ích
    keywords: List[str]                # Từ khóa tìm được
    document_info: Dict[str, str]      # Thông tin văn bản

@dataclass
class CostAnalysis:
    """Kết quả phân tích chi phí"""
    total_compliance_cost: float       # Tổng chi phí tuân thủ
    total_penalty_risk: float          # Tổng rủi ro phạt
    total_indirect_cost: float         # Tổng chi phí gián tiếp
    total_cost: float                  # Tổng chi phí
    cost_breakdown: Dict[str, any]     # Chi tiết phân tích

@dataclass
class BenefitAnalysis:
    """Kết quả phân tích lợi ích"""
    direct_benefits: float             # Lợi ích trực tiếp
    indirect_benefits: float           # Lợi ích gián tiếp
    total_benefits: float              # Tổng lợi ích
    benefit_breakdown: Dict[str, any]  # Chi tiết phân tích

@dataclass
class Scenario:
    """Một kịch bản phân tích (lạc quan/trung bình/bi quan)"""
    name: str                          # Tên kịch bản
    description: str                   # Mô tả
    probability: float                 # Xác suất (0-1)
    total_cost: float                  # Tổng chi phí
    total_benefit: float               # Tổng lợi ích
    net_benefit: float                 # Lợi ích ròng
    roi_percentage: float              # ROI %
    payback_months: int                # Thời gian hoàn vốn (tháng)
    assumptions: List[str]             # Giả định (>=3)

@dataclass
class EconomicAnalysisResult:
    """Kết quả phân tích tổng thể"""
    document_info: Dict[str, str]      # Thông tin văn bản
    features: EconomicFeatures         # Features trích xuất
    cost_analysis: CostAnalysis        # Phân tích chi phí
    benefit_analysis: BenefitAnalysis  # Phân tích lợi ích
    scenarios: Dict[str, Scenario]     # 3 kịch bản
    recommendations: List[str]         # Khuyến nghị
    expert_deviation: Dict[str, any]   # % độ lệch so với chuyên gia

# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class TransportEconomicAnalyzer:
    """
    Analyzer chính cho yêu cầu 3: Đánh giá tác động kinh tế giao thông
    
    Workflow:
    1. Load keywords và patterns
    2. Extract features từ văn bản
    3. Analyze costs và benefits
    4. Generate 3 scenarios với assumptions
    5. Calculate deviation từ expert benchmark
    """
    
    def __init__(self):
        """Khởi tạo analyzer với keywords và benchmarks"""
        self.transport_keywords = self._load_transport_keywords()
        self.cost_patterns = self._load_cost_patterns()
        self.benchmarks = self._load_benchmarks()
    
    # ------------------------------------------------------------------------
    # CONFIGURATION LOADING - Load cấu hình và từ khóa
    # ------------------------------------------------------------------------
    
    def _load_transport_keywords(self) -> Dict[str, List[str]]:
        """Load từ khóa giao thông để phân loại"""
        return {
            'cost_keywords': [
                'chi phí', 'phí', 'lệ phí', 'kinh phí', 'ngân sách',
                'đầu tư', 'mua sắm', 'trang thiết bị', 'đào tạo',
                'kiểm định', 'đăng ký', 'bảo hiểm', 'bảo dưỡng'
            ],
            'penalty_keywords': [
                'phạt', 'vi phạm', 'xử phạt', 'tiền phạt', 'phạt nguội',
                'tước bằng', 'tạm giữ', 'thu hồi'
            ],
            'benefit_keywords': [
                'an toàn', 'giảm tai nạn', 'hiệu quả', 'tiết kiệm',
                'cải thiện', 'nâng cao', 'tối ưu', 'chất lượng'
            ],
            'transport_keywords': [
                'giao thông', 'vận tải', 'đường bộ', 'xe cộ', 'lái xe',
                'phương tiện', 'ô tô', 'xe máy', 'xe tải', 'xe khách'
            ]
        }
    
    def _load_cost_patterns(self) -> List[str]:
        """Load regex patterns để tìm số tiền trong văn bản"""
        return [
            r'(\d+(?:\.\d+)?)\s*(?:triệu|tr)\s*(?:đồng|vnđ|vnd)?',
            r'(\d+(?:\.\d+)?)\s*(?:tỷ|tỉ)\s*(?:đồng|vnđ|vnd)?',
            r'(\d+(?:,\d{3})*)\s*(?:đồng|vnđ|vnd)',
            r'từ\s*(\d+)\s*(?:đến|-)\s*(\d+)\s*(?:triệu|tr|tỷ|tỉ)',
            r'(\d+)\s*-\s*(\d+)\s*(?:triệu|tr)',
        ]
    
    def _load_benchmarks(self) -> Dict:
        """Load benchmarks giao thông từ file unified hoặc fallback"""
        benchmarks = {}
        
        # Load transport benchmarks (nguồn chính thức duy nhất)
        try:
            with open('benchmarks/transport_benchmarks.json', 'r', encoding='utf-8') as f:
                benchmarks.update(json.load(f))
        except FileNotFoundError:
            pass
        
        # Fallback benchmarks nếu không có file
        if not benchmarks:
            benchmarks = {
                'transport_compliance_costs': {
                    'vehicle_inspection': {'cost_range': {'average': 2.0}},
                    'driver_training': {'cost_range': {'average': 8.0}},
                    'safety_equipment': {'cost_range': {'average': 5.0}},
                    'reporting_compliance': {'cost_range': {'average': 3.0}}
                },
                'transport_penalties': {
                    'speed_violation': {'penalty_range': {'average': 5.0}},
                    'alcohol_violation': {'penalty_range': {'average': 15.0}},
                    'overload_violation': {'penalty_range': {'average': 10.0}}
                },
                'transport_benefits': {
                    'accident_reduction': {'benefit_range': {'average': 50.0}},
                    'insurance_savings': {'benefit_range': {'average': 10.0}},
                    'operational_efficiency': {'benefit_range': {'average': 25.0}}
                }
            }
        
        return benchmarks
    
    # ------------------------------------------------------------------------
    # FEATURE EXTRACTION - Trích xuất features từ văn bản
    # ------------------------------------------------------------------------
    
    def extract_economic_features(self, document: Dict) -> EconomicFeatures:
        """
        Trích xuất features kinh tế từ văn bản giao thông
        
        Args:
            document: Dict chứa thông tin văn bản (number, agency, content, etc.)
            
        Returns:
            EconomicFeatures: Features đã trích xuất
        """
        content = document.get('content', '')
        
        # Khởi tạo lists để chứa kết quả
        compliance_costs = []
        penalties = []
        fees = []
        benefits = []
        keywords = []
        
        # Tìm số tiền trong văn bản bằng regex patterns
        for pattern in self.cost_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Lấy context xung quanh số tiền để phân loại
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end].lower()
                
                try:
                    # Trích xuất số tiền
                    if len(match.groups()) >= 2:  # Range pattern (từ X đến Y)
                        amount1 = float(match.group(1))
                        amount2 = float(match.group(2))
                        amount = (amount1 + amount2) / 2  # Lấy trung bình
                    else:
                        amount = float(match.group(1).replace(',', ''))
                    
                    # Chuyển đổi đơn vị về triệu VND
                    if 'tỷ' in match.group(0) or 'tỉ' in match.group(0):
                        amount *= 1000  # Tỷ -> triệu
                    
                    # Phân loại dựa trên context
                    if any(keyword in context for keyword in self.transport_keywords['penalty_keywords']):
                        penalties.append(amount)
                    elif any(keyword in context for keyword in self.transport_keywords['benefit_keywords']):
                        benefits.append(amount)
                    elif 'phí' in context:
                        fees.append(amount)
                    else:
                        compliance_costs.append(amount)
                        
                except (ValueError, IndexError):
                    continue
        
        # Trích xuất keywords
        for category, keyword_list in self.transport_keywords.items():
            for keyword in keyword_list:
                if keyword in content.lower():
                    keywords.append(keyword)
        
        # Loại bỏ keywords trùng lặp
        keywords = list(set(keywords))
        
        return EconomicFeatures(
            compliance_costs=compliance_costs,
            penalties=penalties,
            fees=fees,
            benefits=benefits,
            keywords=keywords,
            document_info={
                'number': document.get('number', ''),
                'agency': document.get('agency', ''),
                'field': document.get('field', ''),
                'content': document.get('content', '')
            }
        )
    
    # ------------------------------------------------------------------------
    # COST & BENEFIT ANALYSIS - Phân tích chi phí và lợi ích
    # ------------------------------------------------------------------------
    
    def analyze_costs(self, features: EconomicFeatures) -> CostAnalysis:
        """
        Phân tích chi phí từ features - ưu tiên dữ liệu thực tế từ văn bản
        
        Args:
            features: EconomicFeatures đã trích xuất
            
        Returns:
            CostAnalysis: Kết quả phân tích chi phí
        """
        
        # 1. COMPLIANCE COSTS - Chi phí tuân thủ
        if features.compliance_costs:
            # Có dữ liệu thực tế từ văn bản
            total_compliance = sum(features.compliance_costs)
            cost_source = "content_based"
        else:
            # Fallback về benchmark
            benchmarks = self.benchmarks['transport_compliance_costs']
            compliance_costs = [
                benchmarks['vehicle_inspection']['cost_range']['average'],
                benchmarks['driver_training']['cost_range']['average'],
                benchmarks['safety_equipment']['cost_range']['average']
            ]
            total_compliance = sum(compliance_costs)
            cost_source = "benchmark_fallback"
        
        # 2. PENALTY COSTS - Rủi ro phạt
        if features.penalties:
            penalties = features.penalties
            total_penalty_risk = sum(penalties) * 0.15  # 15% xác suất vi phạm
        else:
            # Fallback về benchmark
            benchmarks = self.benchmarks['transport_penalties']
            penalties = [
                benchmarks['speed_violation']['penalty_range']['average'],
                benchmarks['alcohol_violation']['penalty_range']['average']
            ]
            total_penalty_risk = sum(penalties) * 0.15
        
        # 3. FEES - Lệ phí
        total_fees = sum(features.fees) if features.fees else 0
        
        # 4. INDIRECT COSTS - Chi phí gián tiếp (25% của chi phí trực tiếp)
        total_indirect = (total_compliance + total_fees) * 0.25
        
        # 5. TOTAL COST
        total_cost = total_compliance + total_penalty_risk + total_fees + total_indirect
        
        return CostAnalysis(
            total_compliance_cost=total_compliance,
            total_penalty_risk=total_penalty_risk,
            total_indirect_cost=total_indirect,
            total_cost=total_cost,
            cost_breakdown={
                'compliance_items': features.compliance_costs,
                'penalty_items': penalties,
                'fee_items': features.fees,
                'cost_source': cost_source,
                'total_fees': total_fees,
                'indirect_percentage': 25,
                'violation_probability': 15
            }
        )
    
    def analyze_benefits(self, features: EconomicFeatures) -> BenefitAnalysis:
        """
        Phân tích lợi ích dựa trên nội dung văn bản
        
        Args:
            features: EconomicFeatures đã trích xuất
            
        Returns:
            BenefitAnalysis: Kết quả phân tích lợi ích
        """
        
        content = features.document_info.get('content', '').lower()
        benchmarks = self.benchmarks['transport_benefits']
        
        # Tính hệ số lợi ích dựa trên nội dung
        benefit_multiplier = self._calculate_benefit_multiplier(content, features)
        
        # Base benefits từ benchmarks
        base_accident_reduction = benchmarks['accident_reduction']['benefit_range']['average']
        base_insurance_savings = benchmarks['insurance_savings']['benefit_range']['average']
        base_operational_efficiency = benchmarks['operational_efficiency']['benefit_range']['average']
        
        # Tính lợi ích thực tế
        accident_reduction = base_accident_reduction * benefit_multiplier
        insurance_savings = base_insurance_savings * benefit_multiplier
        operational_efficiency = base_operational_efficiency * benefit_multiplier
        
        direct_benefits = accident_reduction + insurance_savings
        indirect_benefits = operational_efficiency
        total_benefits = direct_benefits + indirect_benefits
        
        return BenefitAnalysis(
            direct_benefits=direct_benefits,
            indirect_benefits=indirect_benefits,
            total_benefits=total_benefits,
            benefit_breakdown={
                'accident_reduction': accident_reduction,
                'insurance_savings': insurance_savings,
                'operational_efficiency': operational_efficiency,
                'benefit_multiplier': benefit_multiplier,
                'content_based': True
            }
        )
    
    def _calculate_benefit_multiplier(self, content: str, features: EconomicFeatures) -> float:
        """
        Tính hệ số lợi ích dựa trên nội dung văn bản
        
        Args:
            content: Nội dung văn bản
            features: Features đã trích xuất
            
        Returns:
            float: Hệ số lợi ích (0.3 - 4.0)
        """
        multiplier = 1.0
        
        # High-impact keywords
        high_impact_keywords = [
            'giảm tai nạn', 'an toàn giao thông', 'nâng cao hiệu quả',
            'cải thiện chất lượng', 'tiết kiệm chi phí', 'tối ưu hóa'
        ]
        
        impact_count = sum(1 for keyword in high_impact_keywords if keyword in content)
        multiplier += impact_count * 0.15
        
        # Scope indicators
        scope_keywords = ['toàn quốc', 'tỉnh', 'doanh nghiệp', 'người dân']
        scope_count = sum(1 for keyword in scope_keywords if keyword in content)
        multiplier += scope_count * 0.08
        
        # Quantitative indicators
        quantitative_patterns = [r'(\d+(?:\.\d+)?)\s*%', r'giảm\s*(\d+)', r'tăng\s*(\d+)']
        quantitative_count = 0
        for pattern in quantitative_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            quantitative_count += len(matches)
        
        if quantitative_count > 0:
            multiplier += min(quantitative_count * 0.1, 0.5)
        
        # Giới hạn multiplier trong khoảng hợp lý
        return min(max(multiplier, 0.3), 4.0)
    
    # ------------------------------------------------------------------------
    # SCENARIO GENERATION - Tạo 3 kịch bản
    # ------------------------------------------------------------------------
    
    def generate_scenarios(self, cost_analysis: CostAnalysis, 
                          benefit_analysis: BenefitAnalysis) -> Dict[str, Scenario]:
        """
        Tạo 3 kịch bản phân tích: lạc quan, trung bình, bi quan
        Mỗi kịch bản có >=3 giả định theo yêu cầu đề bài
        
        Args:
            cost_analysis: Kết quả phân tích chi phí
            benefit_analysis: Kết quả phân tích lợi ích
            
        Returns:
            Dict[str, Scenario]: 3 kịch bản với key là tên kịch bản
        """
        
        base_cost = cost_analysis.total_cost
        base_benefit = benefit_analysis.total_benefits
        
        scenarios = {}
        
        # KỊCH BẢN LẠC QUAN (30% xác suất)
        opt_cost = base_cost * 0.8      # Chi phí giảm 20%
        opt_benefit = base_benefit * 1.3 # Lợi ích tăng 30%
        scenarios['optimistic'] = Scenario(
            name='Lạc quan',
            description='Thực hiện hiệu quả, chi phí thấp, lợi ích cao',
            probability=0.3,
            total_cost=opt_cost,
            total_benefit=opt_benefit,
            net_benefit=opt_benefit - opt_cost,
            roi_percentage=((opt_benefit - opt_cost) / opt_cost * 100) if opt_cost > 0 else 0,
            payback_months=int(opt_cost / (opt_benefit / 12)) if opt_benefit > 0 else 999,
            assumptions=[
                'Doanh nghiệp hợp tác tích cực trong triển khai',
                'Không có chi phí phát sinh ngoài dự kiến',
                'Hiệu quả an toàn đạt cao hơn mục tiêu'
            ]
        )
        
        # KỊCH BẢN TRUNG BÌNH (50% xác suất)
        scenarios['average'] = Scenario(
            name='Trung bình',
            description='Thực hiện theo kế hoạch, chi phí và lợi ích như dự tính',
            probability=0.5,
            total_cost=base_cost,
            total_benefit=base_benefit,
            net_benefit=base_benefit - base_cost,
            roi_percentage=((base_benefit - base_cost) / base_cost * 100) if base_cost > 0 else 0,
            payback_months=int(base_cost / (base_benefit / 12)) if base_benefit > 0 else 999,
            assumptions=[
                'Thực hiện đúng theo kế hoạch đã đề ra',
                'Chi phí và lợi ích như dự tính ban đầu',
                'Tỷ lệ tuân thủ đạt mức trung bình ngành'
            ]
        )
        
        # KỊCH BẢN BI QUAN (20% xác suất)
        pess_cost = base_cost * 1.4      # Chi phí tăng 40%
        pess_benefit = base_benefit * 0.7 # Lợi ích giảm 30%
        scenarios['pessimistic'] = Scenario(
            name='Bi quan',
            description='Gặp khó khăn triển khai, chi phí cao, lợi ích thấp',
            probability=0.2,
            total_cost=pess_cost,
            total_benefit=pess_benefit,
            net_benefit=pess_benefit - pess_cost,
            roi_percentage=((pess_benefit - pess_cost) / pess_cost * 100) if pess_cost > 0 else 0,
            payback_months=int(pess_cost / (pess_benefit / 12)) if pess_benefit > 0 else 999,
            assumptions=[
                'Gặp khó khăn trong quá trình triển khai',
                'Chi phí phát sinh cao hơn dự kiến',
                'Tỷ lệ tuân thủ thấp hơn mong đợi'
            ]
        )
        
        return scenarios
    
    # ------------------------------------------------------------------------
    # EXPERT DEVIATION CALCULATION - Tính % độ lệch so với chuyên gia
    # ------------------------------------------------------------------------
    
    def calculate_deviation_from_expert_benchmark(self, scenarios: Dict[str, Scenario]) -> Dict[str, any]:
        """
        Tính % độ lệch dự báo so với benchmark chuyên gia
        Đây là 1 trong 2 metrics chính của yêu cầu 3
        
        Args:
            scenarios: 3 kịch bản đã tạo
            
        Returns:
            Dict: Thông tin về độ lệch so với chuyên gia
        """
        
        # Expert benchmark values từ file unified
        expert_benchmark = {
            'average_cost': 65.0,      # 65M VND chi phí trung bình
            'average_benefit': 180.0,  # 180M VND lợi ích trung bình
            'average_roi': 175.0       # 175% ROI trung bình
        }
        
        # Load từ benchmarks nếu có expert data
        if 'expert_benchmarks' in self.benchmarks:
            expert_data = self.benchmarks['expert_benchmarks']['vehicle_inspection_regulation']['expert_scenarios']['average']
            expert_benchmark = {
                'average_cost': expert_data['cost_estimate'],
                'average_benefit': expert_data['benefit_estimate'],
                'average_roi': expert_data['roi_estimate']
            }
        
        # Lấy kịch bản trung bình để so sánh
        average_scenario = scenarios['average']
        
        # Tính % độ lệch
        cost_deviation = abs(average_scenario.total_cost - expert_benchmark['average_cost']) / expert_benchmark['average_cost'] * 100
        benefit_deviation = abs(average_scenario.total_benefit - expert_benchmark['average_benefit']) / expert_benchmark['average_benefit'] * 100
        roi_deviation = abs(average_scenario.roi_percentage - expert_benchmark['average_roi']) / expert_benchmark['average_roi'] * 100
        
        # Tính độ lệch tổng thể
        overall_deviation = (cost_deviation + benefit_deviation + roi_deviation) / 3
        
        # Xác định trạng thái validation
        if overall_deviation <= 25.0:
            validation_status = "ACCEPTABLE"
        elif overall_deviation <= 50.0:
            validation_status = "REVIEW_NEEDED"
        else:
            validation_status = "REVIEW_NEEDED"
        
        return {
            'expert_benchmark': expert_benchmark,
            'predicted_values': {
                'cost': average_scenario.total_cost,
                'benefit': average_scenario.total_benefit,
                'roi': average_scenario.roi_percentage
            },
            'cost_deviation': cost_deviation,
            'benefit_deviation': benefit_deviation,
            'roi_deviation': roi_deviation,
            'overall_deviation': overall_deviation,
            'validation_status': validation_status,
            'scenario_details': {
                scenario_name: {
                    'cost_deviation': abs(scenario.total_cost - expert_benchmark['average_cost']) / expert_benchmark['average_cost'] * 100,
                    'benefit_deviation': abs(scenario.total_benefit - expert_benchmark['average_benefit']) / expert_benchmark['average_benefit'] * 100,
                    'roi_deviation': abs(scenario.roi_percentage - expert_benchmark['average_roi']) / expert_benchmark['average_roi'] * 100
                }
                for scenario_name, scenario in scenarios.items()
            }
        }
    
    # ------------------------------------------------------------------------
    # RECOMMENDATIONS - Tạo khuyến nghị
    # ------------------------------------------------------------------------
    
    def generate_recommendations(self, scenarios: Dict[str, Scenario]) -> List[str]:
        """
        Tạo khuyến nghị dựa trên kết quả phân tích 3 kịch bản
        
        Args:
            scenarios: 3 kịch bản đã tạo
            
        Returns:
            List[str]: Danh sách khuyến nghị
        """
        
        recommendations = []
        average = scenarios['average']
        
        # Đánh giá khả thi kinh tế
        if average.net_benefit > 0:
            recommendations.append(
                f"Quy định có tác động kinh tế tích cực với ROI {average.roi_percentage:.1f}%"
            )
        else:
            recommendations.append(
                f"Quy định có chi phí cao hơn lợi ích trong ngắn hạn (ROI {average.roi_percentage:.1f}%)"
            )
        
        # Khuyến nghị triển khai
        if average.payback_months <= 12:
            recommendations.append("Thời gian hoàn vốn ngắn, nên triển khai sớm")
        elif average.payback_months <= 36:
            recommendations.append("Cần lập kế hoạch tài chính dài hạn cho triển khai")
        else:
            recommendations.append("Cần xem xét lại hiệu quả kinh tế trước khi triển khai")
        
        # Quản lý rủi ro
        pessimistic = scenarios['pessimistic']
        if pessimistic.net_benefit < -average.total_cost * 0.5:
            recommendations.append("Cần có kế hoạch dự phòng cho kịch bản bi quan")
        
        return recommendations
    
    # ------------------------------------------------------------------------
    # MAIN ANALYSIS METHOD - Phương thức phân tích chính
    # ------------------------------------------------------------------------
    
    def analyze_document(self, document: Dict) -> EconomicAnalysisResult:
        """
        Phân tích toàn diện một văn bản giao thông theo yêu cầu 3
        
        Workflow:
        1. Extract economic features từ văn bản
        2. Analyze costs và benefits
        3. Generate 3 scenarios với >=3 assumptions mỗi scenario
        4. Calculate % deviation từ expert benchmark
        5. Generate recommendations
        
        Args:
            document: Dict chứa thông tin văn bản
            
        Returns:
            EconomicAnalysisResult: Kết quả phân tích đầy đủ
        """
        
        # Bước 1: Trích xuất features
        features = self.extract_economic_features(document)
        
        # Bước 2: Phân tích chi phí và lợi ích
        cost_analysis = self.analyze_costs(features)
        benefit_analysis = self.analyze_benefits(features)
        
        # Bước 3: Tạo 3 kịch bản với giả định
        scenarios = self.generate_scenarios(cost_analysis, benefit_analysis)
        
        # Bước 4: Tính % độ lệch so với chuyên gia
        expert_deviation = self.calculate_deviation_from_expert_benchmark(scenarios)
        
        # Bước 5: Tạo khuyến nghị
        recommendations = self.generate_recommendations(scenarios)
        
        return EconomicAnalysisResult(
            document_info=features.document_info,
            features=features,
            cost_analysis=cost_analysis,
            benefit_analysis=benefit_analysis,
            scenarios=scenarios,
            recommendations=recommendations,
            expert_deviation=expert_deviation
        )
    
    # ------------------------------------------------------------------------
    # OUTPUT METHODS - Phương thức xuất kết quả
    # ------------------------------------------------------------------------
    
    def print_analysis_result(self, result: EconomicAnalysisResult):
        """In kết quả phân tích ra console với format dễ đọc"""
        
        print("=" * 80)
        print("PHÂN TÍCH TÁC ĐỘNG KINH TẾ - LĨNH VỰC GIAO THÔNG")
        print("=" * 80)
        
        # Thông tin văn bản
        doc = result.document_info
        print(f"\nVĂN BẢN PHÂN TÍCH:")
        print(f"Số hiệu: {doc.get('number', 'N/A')}")
        print(f"Cơ quan: {doc.get('agency', 'N/A')}")
        print(f"Lĩnh vực: {doc.get('field', 'N/A')}")
        print(f"Tiêu đề: ...")
        
        # Features trích xuất
        features = result.features
        print(f"\nDỮ LIỆU TRÍCH XUẤT:")
        print(f"Chi phí tuân thủ: {len(features.compliance_costs)} mục")
        print(f"Mức phạt: {len(features.penalties)} mục")
        print(f"Phí dịch vụ: {len(features.fees)} mục")
        print(f"Từ khóa tìm được: {len(features.keywords)} từ")
        
        # Phân tích chi phí
        cost = result.cost_analysis
        print(f"\nPHÂN TÍCH CHI PHÍ:")
        print(f"Chi phí tuân thủ: {cost.total_compliance_cost:.1f} triệu VND")
        print(f"Rủi ro phạt: {cost.total_penalty_risk:.1f} triệu VND")
        print(f"Chi phí gián tiếp: {cost.total_indirect_cost:.1f} triệu VND")
        print(f"TỔNG CHI PHÍ: {cost.total_cost:.1f} triệu VND")
        
        # Phân tích lợi ích
        benefit = result.benefit_analysis
        print(f"\nPHÂN TÍCH LỢI ÍCH:")
        print(f"Lợi ích trực tiếp: {benefit.direct_benefits:.1f} triệu VND/năm")
        print(f"Lợi ích gián tiếp: {benefit.indirect_benefits:.1f} triệu VND/năm")
        print(f"TỔNG LỢI ÍCH: {benefit.total_benefits:.1f} triệu VND/năm")
        
        # 3 kịch bản
        print(f"\n3 KỊCH BẢN PHÂN TÍCH:")
        print("-" * 80)
        
        for name, scenario in result.scenarios.items():
            print(f"\n{scenario.name.upper()} ({scenario.probability*100:.0f}% khả năng):")
            print(f"  Mô tả: {scenario.description}")
            print(f"  Chi phí: {scenario.total_cost:.1f} triệu VND")
            print(f"  Lợi ích: {scenario.total_benefit:.1f} triệu VND/năm")
            print(f"  Lợi ích ròng: {scenario.net_benefit:.1f} triệu VND")
            print(f"  ROI: {scenario.roi_percentage:.1f}%")
            print(f"  Hoàn vốn: {scenario.payback_months} tháng")
            print(f"  Giả định:")
            for i, assumption in enumerate(scenario.assumptions, 1):
                print(f"    - {assumption}")
        
        # So sánh với chuyên gia
        if result.expert_deviation:
            print(f"\nSO SÁNH VỚI BENCHMARK CHUYÊN GIA:")
            deviation = result.expert_deviation
            print(f"Độ lệch chi phí: {deviation['cost_deviation']:.1f}%")
            print(f"Độ lệch lợi ích: {deviation['benefit_deviation']:.1f}%")
            print(f"Độ lệch ROI: {deviation['roi_deviation']:.1f}%")
            print(f"Độ lệch tổng thể: {deviation['overall_deviation']:.1f}%")
            print(f"Trạng thái validation: {deviation['validation_status']}")
            
            # Chi tiết theo kịch bản
            print(f"\nChi tiết theo kịch bản:")
            for scenario_name, details in deviation['scenario_details'].items():
                print(f"  {scenario_name.upper()}:")
                print(f"    Chi phí: {details['cost_deviation']:.1f}% lệch")
                print(f"    Lợi ích: {details['benefit_deviation']:.1f}% lệch") 
                print(f"    ROI: {details['roi_deviation']:.1f}% lệch")
        
        # Khuyến nghị
        print(f"\nKHUYẾN NGHỊ:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")
        
        print("=" * 80)

# ============================================================================
# EXAMPLE USAGE - Ví dụ sử dụng
# ============================================================================

if __name__ == "__main__":
    """
    Test analyzer với dữ liệu thực từ final_perfect_dataset.json
    """
    
    # Load dữ liệu thực
    try:
        with open('data/raw/final_perfect_dataset.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
        
        # Tìm văn bản có nội dung kinh tế
        test_doc = None
        for doc in documents:
            content = doc.get('content', '').lower()
            if any(keyword in content for keyword in ['triệu đồng', 'tỷ đồng', 'chi phí', 'phạt tiền', 'lệ phí']):
                test_doc = doc
                break
        
        if not test_doc:
            test_doc = documents[0] if documents else None
            
        print(f"Testing với văn bản thực: {test_doc.get('number', 'N/A')}")
        
    except FileNotFoundError:
        print("Không tìm thấy dữ liệu thực. Sử dụng sample data.")
        # Fallback sample document
        test_doc = {
            'number': 'TEST/2024',
            'agency': 'Bộ Giao thông Vận tải',
            'field': 'Giao thông',
            'content': '''
            Điều 1. Quy định kiểm định xe
            1. Xe ô tô phải kiểm định định kỳ với chi phí 2 triệu đồng/lần
            2. Lái xe phải đào tạo bổ sung với chi phí 8 triệu đồng
            3. Vi phạm sẽ bị phạt từ 5-15 triệu đồng
            4. Quy định nhằm nâng cao an toàn giao thông
            '''
        }
    
    # Chạy phân tích
    analyzer = TransportEconomicAnalyzer()
    result = analyzer.analyze_document(test_doc)
    analyzer.print_analysis_result(result)