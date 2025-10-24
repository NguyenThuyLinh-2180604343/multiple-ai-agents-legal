"""
Scenario Generator - Tạo 3 kịch bản (lạc quan, trung bình, bi quan)
Mô phỏng các tình huống khác nhau cho phân tích tác động kinh tế
"""

import json
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class ScenarioType(Enum):
    """Loại kịch bản"""
    OPTIMISTIC = "optimistic"    # Lạc quan
    AVERAGE = "average"          # Trung bình
    PESSIMISTIC = "pessimistic"  # Bi quan

@dataclass
class ScenarioParameters:
    """Tham số kịch bản"""
    cost_multiplier: float
    benefit_multiplier: float
    implementation_time_multiplier: float
    success_probability: float
    risk_factor: float
    assumptions: List[str]

@dataclass
class ScenarioResult:
    """Kết quả kịch bản"""
    scenario_type: ScenarioType
    total_cost: float
    total_benefit: float
    net_benefit: float
    roi_percentage: float
    payback_period_months: int
    risk_score: float
    confidence_level: float
    key_assumptions: List[str]
    critical_factors: List[str]

class ScenarioGenerator:
    """Engine tạo kịch bản phân tích kinh tế"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scenario_parameters = self._load_scenario_parameters()
        self.risk_factors = self._load_risk_factors()
        self.external_factors = self._load_external_factors()
    
    def _load_scenario_parameters(self) -> Dict[ScenarioType, ScenarioParameters]:
        """Load tham số cho từng loại kịch bản"""
        return {
            ScenarioType.OPTIMISTIC: ScenarioParameters(
                cost_multiplier=0.8,      # Chi phí giảm 20%
                benefit_multiplier=1.3,   # Lợi ích tăng 30%
                implementation_time_multiplier=0.7,  # Thời gian giảm 30%
                success_probability=0.9,  # 90% thành công
                risk_factor=0.3,         # Rủi ro thấp
                assumptions=[
                    "Điều kiện kinh tế ổn định và thuận lợi",
                    "Không có thay đổi lớn về chính sách",
                    "Nhân lực có trình độ cao và sẵn sàng",
                    "Công nghệ phát triển nhanh hơn dự kiến",
                    "Sự hợp tác tốt từ các bên liên quan"
                ]
            ),
            ScenarioType.AVERAGE: ScenarioParameters(
                cost_multiplier=1.0,      # Chi phí theo dự kiến
                benefit_multiplier=1.0,   # Lợi ích theo dự kiến
                implementation_time_multiplier=1.0,  # Thời gian theo kế hoạch
                success_probability=0.75, # 75% thành công
                risk_factor=0.5,         # Rủi ro trung bình
                assumptions=[
                    "Điều kiện kinh tế bình thường",
                    "Lạm phát trong tầm kiểm soát (3-4%)",
                    "Nhân lực đáp ứng 80% yêu cầu",
                    "Công nghệ phát triển theo xu hướng",
                    "Một số trở ngại nhỏ trong triển khai"
                ]
            ),
            ScenarioType.PESSIMISTIC: ScenarioParameters(
                cost_multiplier=1.4,      # Chi phí tăng 40%
                benefit_multiplier=0.7,   # Lợi ích giảm 30%
                implementation_time_multiplier=1.5,  # Thời gian tăng 50%
                success_probability=0.6,  # 60% thành công
                risk_factor=0.8,         # Rủi ro cao
                assumptions=[
                    "Điều kiện kinh tế bất ổn",
                    "Lạm phát cao (>5%), tỷ giá biến động",
                    "Thiếu nhân lực có trình độ",
                    "Công nghệ chậm phát triển hoặc lỗi thời",
                    "Nhiều trở ngại và phản đối trong triển khai"
                ]
            )
        }
    
    def _load_risk_factors(self) -> Dict[str, List[str]]:
        """Load các yếu tố rủi ro"""
        return {
            'economic': [
                'Lạm phát cao hơn dự kiến',
                'Tỷ giá USD/VND biến động mạnh',
                'Suy thoái kinh tế',
                'Thiếu nguồn vốn đầu tư',
                'Chi phí nguyên liệu tăng cao'
            ],
            'technical': [
                'Công nghệ không đáp ứng yêu cầu',
                'Lỗi hệ thống trong quá trình triển khai',
                'Thiếu chuyên gia kỹ thuật',
                'Hạ tầng công nghệ lạc hậu',
                'Bảo mật thông tin không đảm bảo'
            ],
            'regulatory': [
                'Thay đổi chính sách pháp luật',
                'Quy định mới xung đột với hiện tại',
                'Thủ tục phê duyệt kéo dài',
                'Thiếu hướng dẫn chi tiết',
                'Khó khăn trong giám sát thực thi'
            ],
            'organizational': [
                'Thiếu sự phối hợp giữa các bộ phận',
                'Nhân viên chưa sẵn sàng thay đổi',
                'Thiếu kinh nghiệm quản lý dự án',
                'Xung đột lợi ích giữa các bên',
                'Thiếu cam kết từ lãnh đạo'
            ],
            'external': [
                'Phản ứng tiêu cực từ công chúng',
                'Cạnh tranh từ giải pháp thay thế',
                'Thay đổi nhu cầu thị trường',
                'Tác động từ dịch bệnh/thiên tai',
                'Áp lực từ tổ chức quốc tế'
            ]
        }
    
    def _load_external_factors(self) -> Dict[str, float]:
        """Load các yếu tố bên ngoài ảnh hưởng"""
        return {
            'gdp_growth': 0.065,      # Tăng trưởng GDP 6.5%
            'inflation_rate': 0.035,  # Lạm phát 3.5%
            'interest_rate': 0.08,    # Lãi suất 8%
            'exchange_rate_volatility': 0.05,  # Biến động tỷ giá 5%
            'technology_adoption_rate': 0.15   # Tỷ lệ áp dụng công nghệ 15%
        }
    
    def generate_scenario(self, scenario_type: ScenarioType, 
                         base_costs: Dict[str, float], 
                         base_benefits: Dict[str, float],
                         document: Dict) -> ScenarioResult:
        """
        Tạo kịch bản cụ thể
        
        Args:
            scenario_type: Loại kịch bản
            base_costs: Chi phí cơ bản
            base_benefits: Lợi ích cơ bản
            document: Văn bản pháp luật
            
        Returns:
            ScenarioResult: Kết quả kịch bản
        """
        params = self.scenario_parameters[scenario_type]
        
        # Calculate adjusted costs and benefits
        adjusted_costs = self._adjust_costs(base_costs, params, document)
        adjusted_benefits = self._adjust_benefits(base_benefits, params, document)
        
        # Calculate totals
        total_cost = sum(adjusted_costs.values())
        total_benefit = sum(adjusted_benefits.values())
        net_benefit = total_benefit - total_cost
        
        # Calculate financial metrics
        roi_percentage = (net_benefit / total_cost * 100) if total_cost > 0 else 0
        payback_period = self._calculate_payback_period(total_cost, total_benefit, params)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(scenario_type, document)
        
        # Generate scenario-specific assumptions
        scenario_assumptions = self._generate_scenario_assumptions(scenario_type, document, params)
        
        # Identify critical factors
        critical_factors = self._identify_critical_factors(scenario_type, document)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(scenario_type, document)
        
        return ScenarioResult(
            scenario_type=scenario_type,
            total_cost=total_cost,
            total_benefit=total_benefit,
            net_benefit=net_benefit,
            roi_percentage=roi_percentage,
            payback_period_months=payback_period,
            risk_score=risk_score,
            confidence_level=confidence_level,
            key_assumptions=scenario_assumptions,
            critical_factors=critical_factors
        )
    
    def generate_all_scenarios(self, base_costs: Dict[str, float], 
                              base_benefits: Dict[str, float],
                              document: Dict) -> Dict[ScenarioType, ScenarioResult]:
        """Tạo tất cả 3 kịch bản"""
        scenarios = {}
        
        for scenario_type in ScenarioType:
            scenario_result = self.generate_scenario(scenario_type, base_costs, base_benefits, document)
            scenarios[scenario_type] = scenario_result
            
            self.logger.info(f"Generated {scenario_type.value} scenario: "
                           f"Cost={scenario_result.total_cost:.1f}M, "
                           f"Benefit={scenario_result.total_benefit:.1f}M, "
                           f"ROI={scenario_result.roi_percentage:.1f}%")
        
        return scenarios
    
    def _adjust_costs(self, base_costs: Dict[str, float], 
                     params: ScenarioParameters, 
                     document: Dict) -> Dict[str, float]:
        """Điều chỉnh chi phí theo kịch bản"""
        adjusted_costs = {}
        
        for cost_type, base_amount in base_costs.items():
            # Apply base multiplier
            adjusted_amount = base_amount * params.cost_multiplier
            
            # Apply specific adjustments based on cost type
            if cost_type == 'compliance':
                # Compliance costs are more stable
                variance = 0.1
            elif cost_type == 'implementation':
                # Implementation costs have higher variance
                variance = 0.2
            else:
                variance = 0.15
            
            # Add scenario-specific variance
            if params.cost_multiplier < 1.0:  # Optimistic
                adjustment = random.uniform(-variance, variance/2)
            elif params.cost_multiplier > 1.0:  # Pessimistic
                adjustment = random.uniform(-variance/2, variance)
            else:  # Average
                adjustment = random.uniform(-variance/2, variance/2)
            
            adjusted_amount *= (1 + adjustment)
            adjusted_costs[cost_type] = max(adjusted_amount, 0)
        
        return adjusted_costs
    
    def _adjust_benefits(self, base_benefits: Dict[str, float], 
                        params: ScenarioParameters, 
                        document: Dict) -> Dict[str, float]:
        """Điều chỉnh lợi ích theo kịch bản"""
        adjusted_benefits = {}
        
        for benefit_type, base_amount in base_benefits.items():
            # Apply base multiplier
            adjusted_amount = base_amount * params.benefit_multiplier
            
            # Apply specific adjustments based on benefit type
            if 'financial' in benefit_type:
                # Financial benefits are more predictable
                variance = 0.15
            elif benefit_type in ['safety', 'efficiency']:
                # Operational benefits have medium variance
                variance = 0.2
            else:
                # Social/environmental benefits have high variance
                variance = 0.3
            
            # Add scenario-specific variance
            if params.benefit_multiplier > 1.0:  # Optimistic
                adjustment = random.uniform(-variance/2, variance)
            elif params.benefit_multiplier < 1.0:  # Pessimistic
                adjustment = random.uniform(-variance, variance/2)
            else:  # Average
                adjustment = random.uniform(-variance/2, variance/2)
            
            adjusted_amount *= (1 + adjustment)
            adjusted_benefits[benefit_type] = max(adjusted_amount, 0)
        
        return adjusted_benefits
    
    def _calculate_payback_period(self, total_cost: float, 
                                 total_benefit: float, 
                                 params: ScenarioParameters) -> int:
        """Tính thời gian hoàn vốn (tháng)"""
        if total_benefit <= 0:
            return 999  # Never pays back
        
        # Assume benefits are realized over time
        monthly_benefit = total_benefit / 36  # Spread over 3 years
        
        if monthly_benefit <= 0:
            return 999
        
        payback_months = int(total_cost / monthly_benefit)
        
        # Adjust for scenario parameters
        payback_months = int(payback_months * params.implementation_time_multiplier)
        
        return min(payback_months, 999)
    
    def _calculate_risk_score(self, scenario_type: ScenarioType, document: Dict) -> float:
        """Tính điểm rủi ro (0-1, càng cao càng rủi ro)"""
        base_risk = self.scenario_parameters[scenario_type].risk_factor
        
        # Adjust based on document characteristics
        agency = document.get('agency', '')
        content = document.get('content', '')
        
        # Higher risk for complex implementations
        complexity_indicators = ['hệ thống', 'công nghệ', 'đầu tư lớn', 'thay đổi lớn']
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in content.lower())
        complexity_risk = min(complexity_count * 0.1, 0.3)
        
        # Higher risk for certain agencies
        if any(high_risk_agency in agency for high_risk_agency in ['CP', 'TTg']):
            agency_risk = 0.1
        else:
            agency_risk = 0.0
        
        total_risk = min(base_risk + complexity_risk + agency_risk, 1.0)
        return total_risk
    
    def _generate_scenario_assumptions(self, scenario_type: ScenarioType, 
                                     document: Dict, 
                                     params: ScenarioParameters) -> List[str]:
        """Tạo giả định cụ thể cho kịch bản"""
        base_assumptions = params.assumptions.copy()
        
        # Add document-specific assumptions
        agency = document.get('agency', '')
        content = document.get('content', '')
        
        if scenario_type == ScenarioType.OPTIMISTIC:
            if 'GTVT' in agency:
                base_assumptions.append("Hạ tầng giao thông được nâng cấp đồng bộ")
            if 'công nghệ' in content.lower():
                base_assumptions.append("Công nghệ mới được áp dụng thành công ngay từ đầu")
        
        elif scenario_type == ScenarioType.PESSIMISTIC:
            if 'UBND' in agency:
                base_assumptions.append("Ngân sách địa phương bị cắt giảm do khó khăn kinh tế")
            if 'đào tạo' in content.lower():
                base_assumptions.append("Tỷ lệ nhân viên cần đào tạo lại cao hơn dự kiến")
        
        # Limit to 5 key assumptions
        return base_assumptions[:5]
    
    def _identify_critical_factors(self, scenario_type: ScenarioType, document: Dict) -> List[str]:
        """Xác định các yếu tố quan trọng"""
        critical_factors = []
        
        # Common critical factors
        if scenario_type == ScenarioType.OPTIMISTIC:
            critical_factors = [
                "Sự ủng hộ mạnh mẽ từ lãnh đạo cấp cao",
                "Nguồn ngân sách đầy đủ và ổn định",
                "Nhân lực có trình độ cao sẵn sàng"
            ]
        elif scenario_type == ScenarioType.AVERAGE:
            critical_factors = [
                "Quản lý dự án hiệu quả",
                "Phối hợp tốt giữa các bên liên quan",
                "Giám sát và điều chỉnh kịp thời"
            ]
        else:  # PESSIMISTIC
            critical_factors = [
                "Quản lý rủi ro chặt chẽ",
                "Kế hoạch dự phòng chi tiết",
                "Giao tiếp và thuyết phục các bên"
            ]
        
        # Add document-specific factors
        content = document.get('content', '')
        if 'công nghệ' in content.lower():
            critical_factors.append("Độ tin cậy và ổn định của công nghệ")
        
        if 'đào tạo' in content.lower():
            critical_factors.append("Chất lượng chương trình đào tạo")
        
        return critical_factors[:4]  # Limit to 4 factors
    
    def _calculate_confidence_level(self, scenario_type: ScenarioType, document: Dict) -> float:
        """Tính mức độ tin cậy của kịch bản"""
        base_confidence = {
            ScenarioType.OPTIMISTIC: 0.6,   # Lower confidence for best case
            ScenarioType.AVERAGE: 0.8,      # Higher confidence for realistic case
            ScenarioType.PESSIMISTIC: 0.7   # Medium confidence for worst case
        }
        
        confidence = base_confidence[scenario_type]
        
        # Adjust based on data quality
        content = document.get('content', '')
        if len(content) > 5000:  # More detailed document
            confidence += 0.1
        
        # Adjust based on agency type
        agency = document.get('agency', '')
        if any(reliable_agency in agency for reliable_agency in ['BTC', 'BGTVT']):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def compare_scenarios(self, scenarios: Dict[ScenarioType, ScenarioResult]) -> Dict[str, any]:
        """So sánh các kịch bản"""
        comparison = {
            'cost_range': {
                'min': min(s.total_cost for s in scenarios.values()),
                'max': max(s.total_cost for s in scenarios.values()),
                'variance': max(s.total_cost for s in scenarios.values()) - min(s.total_cost for s in scenarios.values())
            },
            'benefit_range': {
                'min': min(s.total_benefit for s in scenarios.values()),
                'max': max(s.total_benefit for s in scenarios.values()),
                'variance': max(s.total_benefit for s in scenarios.values()) - min(s.total_benefit for s in scenarios.values())
            },
            'roi_range': {
                'min': min(s.roi_percentage for s in scenarios.values()),
                'max': max(s.roi_percentage for s in scenarios.values()),
                'average': sum(s.roi_percentage for s in scenarios.values()) / len(scenarios)
            },
            'risk_assessment': {
                'lowest_risk': min(scenarios.values(), key=lambda x: x.risk_score).scenario_type.value,
                'highest_risk': max(scenarios.values(), key=lambda x: x.risk_score).scenario_type.value,
                'risk_spread': max(s.risk_score for s in scenarios.values()) - min(s.risk_score for s in scenarios.values())
            },
            'recommendation': self._generate_recommendation(scenarios)
        }
        
        return comparison
    
    def _generate_recommendation(self, scenarios: Dict[ScenarioType, ScenarioResult]) -> str:
        """Tạo khuyến nghị dựa trên so sánh kịch bản"""
        avg_scenario = scenarios[ScenarioType.AVERAGE]
        opt_scenario = scenarios[ScenarioType.OPTIMISTIC]
        pes_scenario = scenarios[ScenarioType.PESSIMISTIC]
        
        # Check if all scenarios are positive
        if all(s.net_benefit > 0 for s in scenarios.values()):
            if avg_scenario.roi_percentage > 20:
                return "KHUYẾN NGHỊ: THỰC HIỆN - Tất cả kịch bản đều có lợi, ROI trung bình cao"
            else:
                return "KHUYẾN NGHỊ: CÂN NHẮC THỰC HIỆN - Có lợi nhưng ROI không cao"
        
        # Check if average scenario is positive
        elif avg_scenario.net_benefit > 0:
            if pes_scenario.net_benefit > -avg_scenario.total_cost * 0.2:  # Loss < 20% of cost
                return "KHUYẾN NGHỊ: THỰC HIỆN VỚI QUẢN LÝ RỦI RO - Kịch bản trung bình tích cực"
            else:
                return "KHUYẾN NGHỊ: HOÃN THỰC HIỆN - Rủi ro thua lỗ cao trong kịch bản xấu"
        
        # Only optimistic scenario is positive
        elif opt_scenario.net_benefit > 0:
            return "KHUYẾN NGHỊ: KHÔNG THỰC HIỆN - Chỉ có lợi trong điều kiện lý tưởng"
        
        # All scenarios are negative
        else:
            return "KHUYẾN NGHỊ: KHÔNG THỰC HIỆN - Tất cả kịch bản đều thua lỗ"
    
    def save_scenarios(self, scenarios: Dict[ScenarioType, ScenarioResult], 
                      comparison: Dict, output_path: str):
        """Lưu kết quả kịch bản"""
        output_data = {
            'scenarios': {},
            'comparison': comparison,
            'generated_at': json.dumps({"timestamp": "2025-01-21T10:00:00Z"})
        }
        
        for scenario_type, result in scenarios.items():
            output_data['scenarios'][scenario_type.value] = {
                'total_cost': result.total_cost,
                'total_benefit': result.total_benefit,
                'net_benefit': result.net_benefit,
                'roi_percentage': result.roi_percentage,
                'payback_period_months': result.payback_period_months,
                'risk_score': result.risk_score,
                'confidence_level': result.confidence_level,
                'key_assumptions': result.key_assumptions,
                'critical_factors': result.critical_factors
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved scenario analysis to {output_path}")

if __name__ == "__main__":
    # Test scenario generator
    generator = ScenarioGenerator()
    
    sample_costs = {
        'compliance': 100.0,
        'implementation': 150.0,
        'opportunity': 50.0
    }
    
    sample_benefits = {
        'direct_financial': 200.0,
        'indirect_financial': 80.0,
        'safety': 60.0,
        'efficiency': 40.0
    }
    
    sample_doc = {
        'number': '25/2025/NĐ-CP',
        'agency': 'BỘ GIAO THÔNG VẬN TẢI',
        'content': 'Quy định về đầu tư hệ thống công nghệ quản lý giao thông thông minh, yêu cầu đào tạo nhân viên và nâng cấp hạ tầng.'
    }
    
    scenarios = generator.generate_all_scenarios(sample_costs, sample_benefits, sample_doc)
    comparison = generator.compare_scenarios(scenarios)
    
    print("SCENARIO ANALYSIS RESULTS:")
    print("=" * 50)
    
    for scenario_type, result in scenarios.items():
        print(f"\n{scenario_type.value.upper()} SCENARIO:")
        print(f"  Total Cost: {result.total_cost:.1f} million VND")
        print(f"  Total Benefit: {result.total_benefit:.1f} million VND")
        print(f"  Net Benefit: {result.net_benefit:.1f} million VND")
        print(f"  ROI: {result.roi_percentage:.1f}%")
        print(f"  Payback Period: {result.payback_period_months} months")
        print(f"  Risk Score: {result.risk_score:.2f}")
        print(f"  Confidence: {result.confidence_level:.2f}")
    
    print(f"\nRECOMMENDATION: {comparison['recommendation']}")
    print(f"ROI Range: {comparison['roi_range']['min']:.1f}% - {comparison['roi_range']['max']:.1f}%")