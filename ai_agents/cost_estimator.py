"""
Cost Estimator - Chi phí tuân thủ và áp dụng
Ước lượng các loại chi phí từ văn bản pháp luật
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class CostCategory(Enum):
    """Phân loại chi phí"""
    COMPLIANCE = "compliance"          # Chi phí tuân thủ
    IMPLEMENTATION = "implementation"  # Chi phí triển khai
    OPERATIONAL = "operational"        # Chi phí vận hành
    TRAINING = "training"             # Chi phí đào tạo
    EQUIPMENT = "equipment"           # Chi phí trang thiết bị
    ADMINISTRATIVE = "administrative"  # Chi phí hành chính

@dataclass
class CostEstimate:
    """Cấu trúc ước lượng chi phí"""
    category: CostCategory
    amount: float
    currency: str
    confidence: float
    basis: str
    assumptions: List[str]

class CostEstimator:
    """Engine ước lượng chi phí tuân thủ và áp dụng"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cost_multipliers = self._load_cost_multipliers()
        self.agency_factors = self._load_agency_factors()
        self.complexity_weights = self._load_complexity_weights()
    
    def _load_cost_multipliers(self) -> Dict[str, float]:
        """Load hệ số nhân chi phí theo loại văn bản"""
        return {
            'NĐ': 2.5,    # Nghị định - chi phí cao
            'QĐ': 1.8,    # Quyết định - chi phí trung bình
            'TT': 1.2,    # Thông tư - chi phí thấp
            'CT': 1.0,    # Chỉ thị - chi phí cơ bản
            'TB': 0.5,    # Thông báo - chi phí thấp nhất
            'KH': 1.5,    # Kế hoạch - chi phí trung bình
            'NQ': 2.0,    # Nghị quyết - chi phí cao
            'QH': 3.0,    # Quốc hội - chi phí rất cao
            'default': 1.0
        }
    
    def _load_agency_factors(self) -> Dict[str, float]:
        """Load hệ số theo cơ quan ban hành"""
        return {
            'CP': 3.0,        # Chính phủ
            'TTg': 2.8,       # Thủ tướng
            'BGTVT': 2.2,     # Bộ GTVT
            'BTC': 2.0,       # Bộ Tài chính
            'BCA': 2.5,       # Bộ Công an
            'BXD': 2.1,       # Bộ Xây dựng
            'UBND': 1.5,      # UBND các cấp
            'VPCP': 1.8,      # VP Chính phủ
            'default': 1.0
        }
    
    def _load_complexity_weights(self) -> Dict[str, float]:
        """Load trọng số độ phức tạp"""
        return {
            'high_complexity': ['đầu tư', 'xây dựng', 'hạ tầng', 'công nghệ', 'hệ thống'],
            'medium_complexity': ['quản lý', 'tổ chức', 'điều hành', 'giám sát', 'kiểm tra'],
            'low_complexity': ['thông báo', 'hướng dẫn', 'báo cáo', 'thống kê']
        }
    
    def estimate_compliance_cost(self, document: Dict, economic_impact: Dict) -> CostEstimate:
        """
        Ước lượng chi phí tuân thủ
        
        Args:
            document: Văn bản pháp luật
            economic_impact: Kết quả phân tích kinh tế
            
        Returns:
            CostEstimate: Ước lượng chi phí tuân thủ
        """
        content = document.get('content', '')
        doc_number = document.get('number', '')
        agency = document.get('agency', '')
        
        # Base cost calculation
        base_cost = self._calculate_base_compliance_cost(content)
        
        # Apply multipliers
        doc_type_multiplier = self._get_document_type_multiplier(doc_number)
        agency_multiplier = self._get_agency_multiplier(agency)
        complexity_multiplier = self._get_complexity_multiplier(content)
        
        # Final cost calculation
        total_cost = base_cost * doc_type_multiplier * agency_multiplier * complexity_multiplier
        
        # Generate assumptions
        assumptions = self._generate_compliance_assumptions(document, total_cost)
        
        # Calculate confidence
        confidence = self._calculate_cost_confidence(content, economic_impact)
        
        return CostEstimate(
            category=CostCategory.COMPLIANCE,
            amount=total_cost,
            currency="VND_MILLION",
            confidence=confidence,
            basis=f"Base: {base_cost:.1f}M, DocType: {doc_type_multiplier}x, Agency: {agency_multiplier}x, Complexity: {complexity_multiplier}x",
            assumptions=assumptions
        )
    
    def estimate_implementation_cost(self, document: Dict, economic_impact: Dict) -> CostEstimate:
        """Ước lượng chi phí triển khai"""
        content = document.get('content', '')
        
        # Implementation cost components
        training_cost = self._estimate_training_cost(content)
        equipment_cost = self._estimate_equipment_cost(content)
        administrative_cost = self._estimate_administrative_cost(content)
        operational_cost = self._estimate_operational_cost(content)
        
        total_cost = training_cost + equipment_cost + administrative_cost + operational_cost
        
        # Apply scaling factors
        scale_factor = self._get_implementation_scale_factor(document)
        total_cost *= scale_factor
        
        assumptions = self._generate_implementation_assumptions(document, total_cost)
        confidence = self._calculate_cost_confidence(content, economic_impact)
        
        return CostEstimate(
            category=CostCategory.IMPLEMENTATION,
            amount=total_cost,
            currency="VND_MILLION",
            confidence=confidence,
            basis=f"Training: {training_cost:.1f}M, Equipment: {equipment_cost:.1f}M, Admin: {administrative_cost:.1f}M, Ops: {operational_cost:.1f}M",
            assumptions=assumptions
        )
    
    def estimate_opportunity_cost(self, document: Dict, compliance_cost: float, implementation_cost: float) -> CostEstimate:
        """Ước lượng chi phí cơ hội"""
        content = document.get('content', '')
        
        # Opportunity cost is typically 15-25% of direct costs
        direct_costs = compliance_cost + implementation_cost
        opportunity_rate = self._get_opportunity_cost_rate(content)
        
        opportunity_cost = direct_costs * opportunity_rate
        
        assumptions = [
            f"Chi phí cơ hội = {opportunity_rate*100:.1f}% của chi phí trực tiếp",
            "Giả định tỷ suất sinh lời thay thế 8-12%/năm",
            "Thời gian cơ hội trung bình 2-3 năm"
        ]
        
        confidence = 0.6  # Lower confidence for opportunity costs
        
        return CostEstimate(
            category=CostCategory.OPERATIONAL,
            amount=opportunity_cost,
            currency="VND_MILLION",
            confidence=confidence,
            basis=f"Opportunity rate: {opportunity_rate*100:.1f}% of direct costs ({direct_costs:.1f}M)",
            assumptions=assumptions
        )
    
    def _calculate_base_compliance_cost(self, content: str) -> float:
        """Tính chi phí tuân thủ cơ bản"""
        # Base cost factors
        content_length = len(content)
        word_count = len(content.split())
        
        # Complexity indicators
        complexity_keywords = [
            'hệ thống', 'công nghệ', 'phần mềm', 'thiết bị', 'đào tạo',
            'giám sát', 'kiểm tra', 'báo cáo', 'thủ tục', 'quy trình'
        ]
        
        complexity_score = sum(1 for keyword in complexity_keywords if keyword in content.lower())
        
        # Base cost calculation (triệu VND)
        base_cost = 10.0  # Minimum 10 million VND
        base_cost += (word_count / 1000) * 5.0  # 5M per 1000 words
        base_cost += complexity_score * 15.0    # 15M per complexity indicator
        
        return base_cost
    
    def _estimate_training_cost(self, content: str) -> float:
        """Ước lượng chi phí đào tạo"""
        training_keywords = ['đào tạo', 'tập huấn', 'hướng dẫn', 'bồi dưỡng', 'nâng cao năng lực']
        training_count = sum(1 for keyword in training_keywords if keyword in content.lower())
        
        if training_count == 0:
            return 5.0  # Minimum training cost
        
        # Estimate based on training complexity
        base_training_cost = 20.0  # 20M base
        training_cost = base_training_cost * (1 + training_count * 0.5)
        
        return training_cost
    
    def _estimate_equipment_cost(self, content: str) -> float:
        """Ước lượng chi phí trang thiết bị"""
        equipment_keywords = [
            'thiết bị', 'máy móc', 'công cụ', 'phần mềm', 'hệ thống',
            'mua sắm', 'đầu tư', 'trang bị', 'lắp đặt'
        ]
        
        equipment_count = sum(1 for keyword in equipment_keywords if keyword in content.lower())
        
        if equipment_count == 0:
            return 10.0  # Minimum equipment cost
        
        # High-cost equipment indicators
        high_cost_indicators = ['hệ thống', 'công nghệ', 'phần mềm', 'máy móc']
        high_cost_count = sum(1 for indicator in high_cost_indicators if indicator in content.lower())
        
        base_equipment_cost = 30.0  # 30M base
        equipment_cost = base_equipment_cost * (1 + equipment_count * 0.3)
        
        if high_cost_count > 0:
            equipment_cost *= (1 + high_cost_count * 0.5)
        
        return equipment_cost
    
    def _estimate_administrative_cost(self, content: str) -> float:
        """Ước lượng chi phí hành chính"""
        admin_keywords = [
            'thủ tục', 'giấy tờ', 'hồ sơ', 'báo cáo', 'kiểm tra',
            'giám sát', 'quản lý', 'điều hành', 'tổ chức'
        ]
        
        admin_count = sum(1 for keyword in admin_keywords if keyword in content.lower())
        
        base_admin_cost = 15.0  # 15M base
        admin_cost = base_admin_cost * (1 + admin_count * 0.2)
        
        return admin_cost
    
    def _estimate_operational_cost(self, content: str) -> float:
        """Ước lượng chi phí vận hành"""
        ops_keywords = [
            'vận hành', 'duy trì', 'bảo trì', 'sửa chữa', 'nâng cấp',
            'hoạt động', 'thực hiện', 'triển khai'
        ]
        
        ops_count = sum(1 for keyword in ops_keywords if keyword in content.lower())
        
        base_ops_cost = 25.0  # 25M base
        ops_cost = base_ops_cost * (1 + ops_count * 0.3)
        
        return ops_cost
    
    def _get_document_type_multiplier(self, doc_number: str) -> float:
        """Lấy hệ số nhân theo loại văn bản"""
        for doc_type, multiplier in self.cost_multipliers.items():
            if doc_type in doc_number:
                return multiplier
        return self.cost_multipliers['default']
    
    def _get_agency_multiplier(self, agency: str) -> float:
        """Lấy hệ số nhân theo cơ quan"""
        for agency_code, multiplier in self.agency_factors.items():
            if agency_code in agency:
                return multiplier
        return self.agency_factors['default']
    
    def _get_complexity_multiplier(self, content: str) -> float:
        """Tính hệ số phức tạp"""
        content_lower = content.lower()
        
        high_complexity_count = sum(1 for keyword in self.complexity_weights['high_complexity'] 
                                  if keyword in content_lower)
        medium_complexity_count = sum(1 for keyword in self.complexity_weights['medium_complexity'] 
                                    if keyword in content_lower)
        low_complexity_count = sum(1 for keyword in self.complexity_weights['low_complexity'] 
                                 if keyword in content_lower)
        
        # Calculate weighted complexity score
        complexity_score = (high_complexity_count * 1.5 + 
                          medium_complexity_count * 1.0 + 
                          low_complexity_count * 0.5)
        
        # Convert to multiplier (1.0 to 2.0)
        multiplier = 1.0 + min(complexity_score / 10.0, 1.0)
        
        return multiplier
    
    def _get_implementation_scale_factor(self, document: Dict) -> float:
        """Tính hệ số quy mô triển khai"""
        agency = document.get('agency', '')
        
        # National level agencies have higher scale
        if any(code in agency for code in ['CP', 'TTg']):
            return 3.0
        elif any(code in agency for code in ['BỘ', 'BGTVT', 'BTC', 'BCA']):
            return 2.0
        elif 'UBND' in agency:
            return 1.5
        else:
            return 1.0
    
    def _get_opportunity_cost_rate(self, content: str) -> float:
        """Tính tỷ lệ chi phí cơ hội"""
        # Higher opportunity cost for complex regulations
        complexity_indicators = ['hệ thống', 'công nghệ', 'đầu tư lớn', 'thay đổi lớn']
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in content.lower())
        
        base_rate = 0.15  # 15% base
        additional_rate = complexity_count * 0.05  # 5% per complexity indicator
        
        return min(base_rate + additional_rate, 0.30)  # Max 30%
    
    def _generate_compliance_assumptions(self, document: Dict, total_cost: float) -> List[str]:
        """Tạo giả định cho chi phí tuân thủ"""
        assumptions = [
            "Giả định tỷ lệ lạm phát 3-4%/năm ảnh hưởng đến chi phí",
            "Chi phí nhân công tăng 6-8%/năm theo mức lương tối thiểu",
            "Không tính chi phí cơ hội của thời gian chờ phê duyệt"
        ]
        
        agency = document.get('agency', '')
        if 'UBND' in agency:
            assumptions.append("Giả định ngân sách địa phương có khả năng chi trả")
        
        if total_cost > 100:
            assumptions.append("Chi phí lớn có thể được phân bổ trong 2-3 năm")
        
        return assumptions
    
    def _generate_implementation_assumptions(self, document: Dict, total_cost: float) -> List[str]:
        """Tạo giả định cho chi phí triển khai"""
        assumptions = [
            "Giả định có đủ nhân lực có trình độ để triển khai",
            "Hạ tầng công nghệ hiện tại đáp ứng 70% yêu cầu",
            "Thời gian triển khai 6-12 tháng tùy độ phức tạp"
        ]
        
        content = document.get('content', '')
        if 'công nghệ' in content.lower():
            assumptions.append("Giả định công nghệ được chọn phù hợp và ổn định")
        
        if 'đào tạo' in content.lower():
            assumptions.append("Tỷ lệ nhân viên cần đào tạo lại không quá 30%")
        
        return assumptions
    
    def _calculate_cost_confidence(self, content: str, economic_impact: Dict) -> float:
        """Tính độ tin cậy của ước lượng chi phí"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have explicit cost mentions
        cost_keywords = ['chi phí', 'ngân sách', 'kinh phí', 'đầu tư']
        cost_mentions = sum(1 for keyword in cost_keywords if keyword in content.lower())
        confidence += min(cost_mentions * 0.1, 0.3)
        
        # Increase confidence if economic impact analysis found indicators
        if economic_impact and economic_impact.get('confidence_score', 0) > 0.7:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def estimate_all_costs(self, document: Dict, economic_impact: Dict) -> Dict[str, CostEstimate]:
        """Ước lượng tất cả các loại chi phí"""
        results = {}
        
        # Compliance cost
        compliance_cost = self.estimate_compliance_cost(document, economic_impact)
        results['compliance'] = compliance_cost
        
        # Implementation cost
        implementation_cost = self.estimate_implementation_cost(document, economic_impact)
        results['implementation'] = implementation_cost
        
        # Opportunity cost
        opportunity_cost = self.estimate_opportunity_cost(
            document, compliance_cost.amount, implementation_cost.amount
        )
        results['opportunity'] = opportunity_cost
        
        return results

if __name__ == "__main__":
    # Test cost estimator
    estimator = CostEstimator()
    
    sample_doc = {
        'number': '15/2025/NĐ-CP',
        'agency': 'CHÍNH PHỦ',
        'content': 'Quy định về đầu tư hệ thống công nghệ mới, yêu cầu đào tạo nhân viên và mua sắm thiết bị chuyên dụng để nâng cao hiệu quả quản lý giao thông.'
    }
    
    sample_impact = {'confidence_score': 0.8}
    
    costs = estimator.estimate_all_costs(sample_doc, sample_impact)
    
    for cost_type, estimate in costs.items():
        print(f"\n{cost_type.upper()} COST:")
        print(f"Amount: {estimate.amount:.2f} {estimate.currency}")
        print(f"Confidence: {estimate.confidence:.2f}")
        print(f"Basis: {estimate.basis}")
        print(f"Assumptions: {estimate.assumptions[:2]}")  # Show first 2 assumptions