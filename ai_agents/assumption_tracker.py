"""
Assumption Tracker - Track >=3 giả định/kịch bản
Theo dõi và quản lý các giả định trong phân tích kinh tế
"""

import json
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

class AssumptionCategory(Enum):
    """Phân loại giả định"""
    ECONOMIC = "economic"           # Kinh tế vĩ mô
    FINANCIAL = "financial"         # Tài chính
    TECHNICAL = "technical"         # Kỹ thuật
    REGULATORY = "regulatory"       # Pháp lý/quy định
    ORGANIZATIONAL = "organizational"  # Tổ chức
    MARKET = "market"              # Thị trường
    OPERATIONAL = "operational"     # Vận hành

class AssumptionImpact(Enum):
    """Mức độ tác động của giả định"""
    HIGH = "high"       # Tác động cao
    MEDIUM = "medium"   # Tác động trung bình
    LOW = "low"         # Tác động thấp

class AssumptionStatus(Enum):
    """Trạng thái giả định"""
    ACTIVE = "active"           # Đang áp dụng
    VALIDATED = "validated"     # Đã xác thực
    INVALIDATED = "invalidated" # Đã bị bác bỏ
    UNCERTAIN = "uncertain"     # Không chắc chắn

@dataclass
class Assumption:
    """Cấu trúc một giả định"""
    id: str
    description: str
    category: AssumptionCategory
    impact: AssumptionImpact
    confidence: float  # 0-1
    source: str
    rationale: str
    status: AssumptionStatus = AssumptionStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validated_at: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    related_scenarios: List[str] = field(default_factory=list)

@dataclass
class AssumptionSet:
    """Tập hợp giả định cho một phân tích"""
    analysis_id: str
    document_id: str
    scenario_type: str
    assumptions: List[Assumption]
    total_count: int = field(init=False)
    high_impact_count: int = field(init=False)
    average_confidence: float = field(init=False)
    
    def __post_init__(self):
        self.total_count = len(self.assumptions)
        self.high_impact_count = sum(1 for a in self.assumptions if a.impact == AssumptionImpact.HIGH)
        self.average_confidence = sum(a.confidence for a in self.assumptions) / len(self.assumptions) if self.assumptions else 0.0

class AssumptionTracker:
    """Engine theo dõi và quản lý giả định"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.assumption_templates = self._load_assumption_templates()
        self.validation_rules = self._load_validation_rules()
        self.dependency_map = {}
        self.assumption_counter = 0
    
    def _load_assumption_templates(self) -> Dict[str, List[Dict]]:
        """Load template giả định theo danh mục"""
        return {
            'economic': [
                {
                    'description': 'Tỷ lệ lạm phát duy trì ở mức {rate}%/năm',
                    'category': AssumptionCategory.ECONOMIC,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.7,
                    'rationale': 'Dựa trên dự báo của Ngân hàng Nhà nước và IMF'
                },
                {
                    'description': 'Tăng trưởng GDP duy trì ở mức {rate}%/năm',
                    'category': AssumptionCategory.ECONOMIC,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.6,
                    'rationale': 'Dựa trên kế hoạch phát triển kinh tế xã hội'
                },
                {
                    'description': 'Tỷ giá USD/VND biến động trong khoảng ±{range}%',
                    'category': AssumptionCategory.ECONOMIC,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.5,
                    'rationale': 'Dựa trên lịch sử biến động tỷ giá 5 năm qua'
                }
            ],
            'financial': [
                {
                    'description': 'Chi phí nhân công tăng {rate}%/năm',
                    'category': AssumptionCategory.FINANCIAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.8,
                    'rationale': 'Dựa trên xu hướng tăng lương tối thiểu'
                },
                {
                    'description': 'Lãi suất cho vay doanh nghiệp ở mức {rate}%/năm',
                    'category': AssumptionCategory.FINANCIAL,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.7,
                    'rationale': 'Dựa trên chính sách tiền tệ hiện tại'
                },
                {
                    'description': 'Nguồn ngân sách đầy đủ cho toàn bộ dự án',
                    'category': AssumptionCategory.FINANCIAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.6,
                    'rationale': 'Dựa trên cam kết ngân sách được phê duyệt'
                }
            ],
            'technical': [
                {
                    'description': 'Công nghệ được chọn ổn định và phù hợp trong {years} năm',
                    'category': AssumptionCategory.TECHNICAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.7,
                    'rationale': 'Dựa trên đánh giá kỹ thuật và xu hướng công nghệ'
                },
                {
                    'description': 'Hạ tầng hiện tại đáp ứng {percentage}% yêu cầu',
                    'category': AssumptionCategory.TECHNICAL,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.8,
                    'rationale': 'Dựa trên khảo sát hạ tầng hiện tại'
                },
                {
                    'description': 'Có đủ chuyên gia kỹ thuật để triển khai',
                    'category': AssumptionCategory.TECHNICAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.6,
                    'rationale': 'Dựa trên đánh giá nguồn nhân lực hiện có'
                }
            ],
            'regulatory': [
                {
                    'description': 'Không có thay đổi lớn về chính sách trong {years} năm',
                    'category': AssumptionCategory.REGULATORY,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.5,
                    'rationale': 'Dựa trên tính ổn định của khung pháp lý'
                },
                {
                    'description': 'Thủ tục phê duyệt hoàn thành trong {months} tháng',
                    'category': AssumptionCategory.REGULATORY,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.7,
                    'rationale': 'Dựa trên kinh nghiệm các dự án tương tự'
                },
                {
                    'description': 'Các bên liên quan tuân thủ đầy đủ quy định mới',
                    'category': AssumptionCategory.REGULATORY,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.6,
                    'rationale': 'Dựa trên cam kết và năng lực thực thi'
                }
            ],
            'organizational': [
                {
                    'description': 'Nhân viên sẵn sàng thay đổi và học hỏi',
                    'category': AssumptionCategory.ORGANIZATIONAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.6,
                    'rationale': 'Dựa trên khảo sát văn hóa tổ chức'
                },
                {
                    'description': 'Lãnh đạo cam kết hỗ trợ trong suốt quá trình',
                    'category': AssumptionCategory.ORGANIZATIONAL,
                    'impact': AssumptionImpact.HIGH,
                    'confidence': 0.8,
                    'rationale': 'Dựa trên tuyên bố và quyết định chính thức'
                },
                {
                    'description': 'Phối hợp hiệu quả giữa các bộ phận',
                    'category': AssumptionCategory.ORGANIZATIONAL,
                    'impact': AssumptionImpact.MEDIUM,
                    'confidence': 0.5,
                    'rationale': 'Dựa trên kinh nghiệm hợp tác trước đây'
                }
            ]
        }
    
    def _load_validation_rules(self) -> Dict[str, Dict]:
        """Load quy tắc xác thực giả định"""
        return {
            'minimum_assumptions_per_scenario': 3,
            'maximum_assumptions_per_scenario': 8,
            'minimum_high_impact_assumptions': 1,
            'minimum_confidence_threshold': 0.3,
            'required_categories': [
                AssumptionCategory.ECONOMIC,
                AssumptionCategory.FINANCIAL
            ]
        }
    
    def generate_assumptions_for_scenario(self, scenario_type: str, 
                                        document: Dict, 
                                        economic_analysis: Dict) -> AssumptionSet:
        """
        Tạo tập giả định cho một kịch bản
        
        Args:
            scenario_type: Loại kịch bản (optimistic, average, pessimistic)
            document: Văn bản pháp luật
            economic_analysis: Kết quả phân tích kinh tế
            
        Returns:
            AssumptionSet: Tập giả định được tạo
        """
        assumptions = []
        
        # Generate core economic assumptions
        economic_assumptions = self._generate_economic_assumptions(scenario_type, document)
        assumptions.extend(economic_assumptions)
        
        # Generate financial assumptions
        financial_assumptions = self._generate_financial_assumptions(scenario_type, document, economic_analysis)
        assumptions.extend(financial_assumptions)
        
        # Generate technical assumptions if applicable
        if self._requires_technical_assumptions(document):
            technical_assumptions = self._generate_technical_assumptions(scenario_type, document)
            assumptions.extend(technical_assumptions)
        
        # Generate regulatory assumptions
        regulatory_assumptions = self._generate_regulatory_assumptions(scenario_type, document)
        assumptions.extend(regulatory_assumptions)
        
        # Generate organizational assumptions
        organizational_assumptions = self._generate_organizational_assumptions(scenario_type, document)
        assumptions.extend(organizational_assumptions)
        
        # Ensure minimum requirements
        assumptions = self._ensure_minimum_requirements(assumptions, scenario_type)
        
        # Create assumption set
        analysis_id = f"analysis_{document.get('number', 'unknown')}_{scenario_type}"
        assumption_set = AssumptionSet(
            analysis_id=analysis_id,
            document_id=document.get('number', 'unknown'),
            scenario_type=scenario_type,
            assumptions=assumptions
        )
        
        self.logger.info(f"Generated {len(assumptions)} assumptions for {scenario_type} scenario")
        
        return assumption_set
    
    def _generate_economic_assumptions(self, scenario_type: str, document: Dict) -> List[Assumption]:
        """Tạo giả định kinh tế"""
        assumptions = []
        
        # Inflation assumption
        if scenario_type == 'optimistic':
            inflation_rate = 3.0
            confidence = 0.7
        elif scenario_type == 'pessimistic':
            inflation_rate = 6.0
            confidence = 0.6
        else:  # average
            inflation_rate = 4.0
            confidence = 0.8
        
        inflation_assumption = self._create_assumption(
            description=f"Tỷ lệ lạm phát duy trì ở mức {inflation_rate}%/năm",
            category=AssumptionCategory.ECONOMIC,
            impact=AssumptionImpact.HIGH,
            confidence=confidence,
            source="economic_model",
            rationale=f"Dựa trên dự báo lạm phát cho kịch bản {scenario_type}"
        )
        assumptions.append(inflation_assumption)
        
        # GDP growth assumption
        if scenario_type == 'optimistic':
            gdp_growth = 7.0
        elif scenario_type == 'pessimistic':
            gdp_growth = 4.0
        else:
            gdp_growth = 6.0
        
        gdp_assumption = self._create_assumption(
            description=f"Tăng trưởng GDP duy trì ở mức {gdp_growth}%/năm",
            category=AssumptionCategory.ECONOMIC,
            impact=AssumptionImpact.MEDIUM,
            confidence=0.6,
            source="economic_model",
            rationale="Dựa trên kế hoạch phát triển kinh tế xã hội"
        )
        assumptions.append(gdp_assumption)
        
        # Exchange rate assumption
        if scenario_type == 'optimistic':
            exchange_volatility = 3
        elif scenario_type == 'pessimistic':
            exchange_volatility = 8
        else:
            exchange_volatility = 5
        
        exchange_assumption = self._create_assumption(
            description=f"Tỷ giá USD/VND biến động trong khoảng ±{exchange_volatility}%",
            category=AssumptionCategory.ECONOMIC,
            impact=AssumptionImpact.MEDIUM,
            confidence=0.5,
            source="economic_model",
            rationale="Dựa trên lịch sử biến động tỷ giá"
        )
        assumptions.append(exchange_assumption)
        
        return assumptions
    
    def _generate_financial_assumptions(self, scenario_type: str, 
                                      document: Dict, 
                                      economic_analysis: Dict) -> List[Assumption]:
        """Tạo giả định tài chính"""
        assumptions = []
        
        # Labor cost assumption
        if scenario_type == 'optimistic':
            labor_increase = 5
            confidence = 0.8
        elif scenario_type == 'pessimistic':
            labor_increase = 10
            confidence = 0.7
        else:
            labor_increase = 7
            confidence = 0.8
        
        labor_assumption = self._create_assumption(
            description=f"Chi phí nhân công tăng {labor_increase}%/năm",
            category=AssumptionCategory.FINANCIAL,
            impact=AssumptionImpact.HIGH,
            confidence=confidence,
            source="financial_model",
            rationale="Dựa trên xu hướng tăng lương tối thiểu"
        )
        assumptions.append(labor_assumption)
        
        # Budget availability assumption
        agency = document.get('agency', '')
        if 'UBND' in agency:
            budget_confidence = 0.6 if scenario_type == 'pessimistic' else 0.8
        else:
            budget_confidence = 0.7 if scenario_type == 'pessimistic' else 0.9
        
        budget_assumption = self._create_assumption(
            description="Nguồn ngân sách đầy đủ cho toàn bộ dự án",
            category=AssumptionCategory.FINANCIAL,
            impact=AssumptionImpact.HIGH,
            confidence=budget_confidence,
            source="budget_analysis",
            rationale="Dựa trên cam kết ngân sách được phê duyệt"
        )
        assumptions.append(budget_assumption)
        
        # Interest rate assumption
        if scenario_type == 'optimistic':
            interest_rate = 6
        elif scenario_type == 'pessimistic':
            interest_rate = 10
        else:
            interest_rate = 8
        
        interest_assumption = self._create_assumption(
            description=f"Lãi suất cho vay doanh nghiệp ở mức {interest_rate}%/năm",
            category=AssumptionCategory.FINANCIAL,
            impact=AssumptionImpact.MEDIUM,
            confidence=0.7,
            source="financial_model",
            rationale="Dựa trên chính sách tiền tệ hiện tại"
        )
        assumptions.append(interest_assumption)
        
        return assumptions
    
    def _generate_technical_assumptions(self, scenario_type: str, document: Dict) -> List[Assumption]:
        """Tạo giả định kỹ thuật"""
        assumptions = []
        content = document.get('content', '')
        
        if any(tech_keyword in content.lower() for tech_keyword in ['công nghệ', 'hệ thống', 'phần mềm']):
            # Technology stability assumption
            if scenario_type == 'optimistic':
                tech_years = 5
                confidence = 0.8
            elif scenario_type == 'pessimistic':
                tech_years = 2
                confidence = 0.5
            else:
                tech_years = 3
                confidence = 0.7
            
            tech_assumption = self._create_assumption(
                description=f"Công nghệ được chọn ổn định và phù hợp trong {tech_years} năm",
                category=AssumptionCategory.TECHNICAL,
                impact=AssumptionImpact.HIGH,
                confidence=confidence,
                source="technical_analysis",
                rationale="Dựa trên đánh giá kỹ thuật và xu hướng công nghệ"
            )
            assumptions.append(tech_assumption)
            
            # Infrastructure readiness assumption
            if scenario_type == 'optimistic':
                infra_readiness = 80
            elif scenario_type == 'pessimistic':
                infra_readiness = 50
            else:
                infra_readiness = 70
            
            infra_assumption = self._create_assumption(
                description=f"Hạ tầng hiện tại đáp ứng {infra_readiness}% yêu cầu",
                category=AssumptionCategory.TECHNICAL,
                impact=AssumptionImpact.MEDIUM,
                confidence=0.8,
                source="infrastructure_assessment",
                rationale="Dựa trên khảo sát hạ tầng hiện tại"
            )
            assumptions.append(infra_assumption)
        
        return assumptions
    
    def _generate_regulatory_assumptions(self, scenario_type: str, document: Dict) -> List[Assumption]:
        """Tạo giả định pháp lý/quy định"""
        assumptions = []
        
        # Policy stability assumption
        if scenario_type == 'optimistic':
            stability_years = 5
            confidence = 0.7
        elif scenario_type == 'pessimistic':
            stability_years = 2
            confidence = 0.4
        else:
            stability_years = 3
            confidence = 0.6
        
        policy_assumption = self._create_assumption(
            description=f"Không có thay đổi lớn về chính sách trong {stability_years} năm",
            category=AssumptionCategory.REGULATORY,
            impact=AssumptionImpact.HIGH,
            confidence=confidence,
            source="policy_analysis",
            rationale="Dựa trên tính ổn định của khung pháp lý"
        )
        assumptions.append(policy_assumption)
        
        # Approval timeline assumption
        if scenario_type == 'optimistic':
            approval_months = 3
        elif scenario_type == 'pessimistic':
            approval_months = 8
        else:
            approval_months = 6
        
        approval_assumption = self._create_assumption(
            description=f"Thủ tục phê duyệt hoàn thành trong {approval_months} tháng",
            category=AssumptionCategory.REGULATORY,
            impact=AssumptionImpact.MEDIUM,
            confidence=0.7,
            source="regulatory_analysis",
            rationale="Dựa trên kinh nghiệm các dự án tương tự"
        )
        assumptions.append(approval_assumption)
        
        return assumptions
    
    def _generate_organizational_assumptions(self, scenario_type: str, document: Dict) -> List[Assumption]:
        """Tạo giả định tổ chức"""
        assumptions = []
        
        # Staff readiness assumption
        if scenario_type == 'optimistic':
            staff_confidence = 0.8
        elif scenario_type == 'pessimistic':
            staff_confidence = 0.4
        else:
            staff_confidence = 0.6
        
        staff_assumption = self._create_assumption(
            description="Nhân viên sẵn sàng thay đổi và học hỏi",
            category=AssumptionCategory.ORGANIZATIONAL,
            impact=AssumptionImpact.HIGH,
            confidence=staff_confidence,
            source="organizational_assessment",
            rationale="Dựa trên khảo sát văn hóa tổ chức"
        )
        assumptions.append(staff_assumption)
        
        # Leadership support assumption
        leadership_confidence = 0.9 if scenario_type == 'optimistic' else 0.7
        
        leadership_assumption = self._create_assumption(
            description="Lãnh đạo cam kết hỗ trợ trong suốt quá trình",
            category=AssumptionCategory.ORGANIZATIONAL,
            impact=AssumptionImpact.HIGH,
            confidence=leadership_confidence,
            source="leadership_commitment",
            rationale="Dựa trên tuyên bố và quyết định chính thức"
        )
        assumptions.append(leadership_assumption)
        
        return assumptions
    
    def _requires_technical_assumptions(self, document: Dict) -> bool:
        """Kiểm tra có cần giả định kỹ thuật không"""
        content = document.get('content', '').lower()
        tech_keywords = ['công nghệ', 'hệ thống', 'phần mềm', 'thiết bị', 'kỹ thuật']
        return any(keyword in content for keyword in tech_keywords)
    
    def _create_assumption(self, description: str, category: AssumptionCategory,
                          impact: AssumptionImpact, confidence: float,
                          source: str, rationale: str) -> Assumption:
        """Tạo một giả định"""
        self.assumption_counter += 1
        assumption_id = f"ASM_{self.assumption_counter:04d}"
        
        return Assumption(
            id=assumption_id,
            description=description,
            category=category,
            impact=impact,
            confidence=confidence,
            source=source,
            rationale=rationale
        )
    
    def _ensure_minimum_requirements(self, assumptions: List[Assumption], 
                                   scenario_type: str) -> List[Assumption]:
        """Đảm bảo đáp ứng yêu cầu tối thiểu"""
        rules = self.validation_rules
        
        # Ensure minimum number of assumptions
        min_assumptions = rules['minimum_assumptions_per_scenario']
        if len(assumptions) < min_assumptions:
            # Add generic assumptions to meet minimum
            while len(assumptions) < min_assumptions:
                generic_assumption = self._create_assumption(
                    description=f"Điều kiện thực thi thuận lợi cho kịch bản {scenario_type}",
                    category=AssumptionCategory.OPERATIONAL,
                    impact=AssumptionImpact.MEDIUM,
                    confidence=0.6,
                    source="generic_model",
                    rationale="Giả định bổ sung để đáp ứng yêu cầu tối thiểu"
                )
                assumptions.append(generic_assumption)
        
        # Ensure at least one high impact assumption
        high_impact_count = sum(1 for a in assumptions if a.impact == AssumptionImpact.HIGH)
        if high_impact_count < rules['minimum_high_impact_assumptions']:
            # Upgrade the first medium impact assumption to high impact
            for assumption in assumptions:
                if assumption.impact == AssumptionImpact.MEDIUM:
                    assumption.impact = AssumptionImpact.HIGH
                    break
        
        # Limit to maximum number
        max_assumptions = rules['maximum_assumptions_per_scenario']
        if len(assumptions) > max_assumptions:
            # Keep the highest impact and confidence assumptions
            assumptions.sort(key=lambda a: (a.impact.value, a.confidence), reverse=True)
            assumptions = assumptions[:max_assumptions]
        
        return assumptions
    
    def validate_assumption_set(self, assumption_set: AssumptionSet) -> Dict[str, any]:
        """Xác thực tập giả định"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        rules = self.validation_rules
        assumptions = assumption_set.assumptions
        
        # Check minimum number of assumptions
        if len(assumptions) < rules['minimum_assumptions_per_scenario']:
            validation_result['is_valid'] = False
            validation_result['issues'].append(
                f"Insufficient assumptions: {len(assumptions)} < {rules['minimum_assumptions_per_scenario']}"
            )
        
        # Check high impact assumptions
        high_impact_count = sum(1 for a in assumptions if a.impact == AssumptionImpact.HIGH)
        if high_impact_count < rules['minimum_high_impact_assumptions']:
            validation_result['is_valid'] = False
            validation_result['issues'].append(
                f"Insufficient high impact assumptions: {high_impact_count} < {rules['minimum_high_impact_assumptions']}"
            )
        
        # Check confidence levels
        low_confidence_count = sum(1 for a in assumptions if a.confidence < rules['minimum_confidence_threshold'])
        if low_confidence_count > 0:
            validation_result['warnings'].append(
                f"{low_confidence_count} assumptions have low confidence (< {rules['minimum_confidence_threshold']})"
            )
        
        # Check category coverage
        present_categories = set(a.category for a in assumptions)
        required_categories = set(rules['required_categories'])
        missing_categories = required_categories - present_categories
        if missing_categories:
            validation_result['warnings'].append(
                f"Missing required categories: {[c.value for c in missing_categories]}"
            )
        
        # Calculate metrics
        validation_result['metrics'] = {
            'total_assumptions': len(assumptions),
            'high_impact_count': high_impact_count,
            'medium_impact_count': sum(1 for a in assumptions if a.impact == AssumptionImpact.MEDIUM),
            'low_impact_count': sum(1 for a in assumptions if a.impact == AssumptionImpact.LOW),
            'average_confidence': assumption_set.average_confidence,
            'category_distribution': {cat.value: sum(1 for a in assumptions if a.category == cat) 
                                    for cat in AssumptionCategory}
        }
        
        return validation_result
    
    def track_assumption_changes(self, old_set: AssumptionSet, new_set: AssumptionSet) -> Dict[str, any]:
        """Theo dõi thay đổi giả định"""
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'summary': {}
        }
        
        old_assumptions = {a.id: a for a in old_set.assumptions}
        new_assumptions = {a.id: a for a in new_set.assumptions}
        
        # Find added assumptions
        for assumption_id, assumption in new_assumptions.items():
            if assumption_id not in old_assumptions:
                changes['added'].append(assumption.description)
        
        # Find removed assumptions
        for assumption_id, assumption in old_assumptions.items():
            if assumption_id not in new_assumptions:
                changes['removed'].append(assumption.description)
        
        # Find modified assumptions
        for assumption_id in old_assumptions:
            if assumption_id in new_assumptions:
                old_assumption = old_assumptions[assumption_id]
                new_assumption = new_assumptions[assumption_id]
                
                if (old_assumption.confidence != new_assumption.confidence or
                    old_assumption.status != new_assumption.status):
                    changes['modified'].append({
                        'id': assumption_id,
                        'description': new_assumption.description,
                        'old_confidence': old_assumption.confidence,
                        'new_confidence': new_assumption.confidence,
                        'old_status': old_assumption.status.value,
                        'new_status': new_assumption.status.value
                    })
        
        changes['summary'] = {
            'total_changes': len(changes['added']) + len(changes['removed']) + len(changes['modified']),
            'added_count': len(changes['added']),
            'removed_count': len(changes['removed']),
            'modified_count': len(changes['modified'])
        }
        
        return changes
    
    def save_assumption_set(self, assumption_set: AssumptionSet, output_path: str):
        """Lưu tập giả định"""
        output_data = {
            'analysis_id': assumption_set.analysis_id,
            'document_id': assumption_set.document_id,
            'scenario_type': assumption_set.scenario_type,
            'total_count': assumption_set.total_count,
            'high_impact_count': assumption_set.high_impact_count,
            'average_confidence': assumption_set.average_confidence,
            'assumptions': []
        }
        
        for assumption in assumption_set.assumptions:
            output_data['assumptions'].append({
                'id': assumption.id,
                'description': assumption.description,
                'category': assumption.category.value,
                'impact': assumption.impact.value,
                'confidence': assumption.confidence,
                'source': assumption.source,
                'rationale': assumption.rationale,
                'status': assumption.status.value,
                'created_at': assumption.created_at,
                'dependencies': assumption.dependencies,
                'related_scenarios': assumption.related_scenarios
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved assumption set with {len(assumption_set.assumptions)} assumptions to {output_path}")

if __name__ == "__main__":
    # Test assumption tracker
    tracker = AssumptionTracker()
    
    sample_doc = {
        'number': '30/2025/NĐ-CP',
        'agency': 'BỘ GIAO THÔNG VẬN TẢI',
        'content': 'Quy định về đầu tư hệ thống công nghệ thông minh cho quản lý giao thông, yêu cầu đào tạo nhân viên và nâng cấp hạ tầng kỹ thuật.'
    }
    
    sample_economic = {'confidence_score': 0.8}
    
    # Generate assumptions for all scenarios
    for scenario_type in ['optimistic', 'average', 'pessimistic']:
        assumption_set = tracker.generate_assumptions_for_scenario(
            scenario_type, sample_doc, sample_economic
        )
        
        print(f"\n{scenario_type.upper()} SCENARIO ASSUMPTIONS:")
        print(f"Total: {assumption_set.total_count}")
        print(f"High Impact: {assumption_set.high_impact_count}")
        print(f"Average Confidence: {assumption_set.average_confidence:.2f}")
        
        for i, assumption in enumerate(assumption_set.assumptions[:3], 1):
            print(f"{i}. {assumption.description}")
            print(f"   Category: {assumption.category.value}, Impact: {assumption.impact.value}")
            print(f"   Confidence: {assumption.confidence:.2f}")
        
        # Validate assumption set
        validation = tracker.validate_assumption_set(assumption_set)
        print(f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
        if validation['issues']:
            print(f"Issues: {validation['issues']}")
        if validation['warnings']:
            print(f"Warnings: {validation['warnings']}")