"""
Benefit Calculator - Tính toán lợi ích
Ước lượng lợi ích trực tiếp và gián tiếp từ văn bản pháp luật
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class BenefitCategory(Enum):
    """Phân loại lợi ích"""
    DIRECT_FINANCIAL = "direct_financial"      # Lợi ích tài chính trực tiếp
    INDIRECT_FINANCIAL = "indirect_financial"  # Lợi ích tài chính gián tiếp
    SAFETY = "safety"                         # Lợi ích an toàn
    EFFICIENCY = "efficiency"                 # Lợi ích hiệu quả
    QUALITY = "quality"                       # Lợi ích chất lượng
    ENVIRONMENTAL = "environmental"           # Lợi ích môi trường
    SOCIAL = "social"                        # Lợi ích xã hội

@dataclass
class BenefitEstimate:
    """Cấu trúc ước lượng lợi ích"""
    category: BenefitCategory
    amount: float
    currency: str
    confidence: float
    timeframe: str
    basis: str
    assumptions: List[str]
    quantifiable: bool

class BenefitCalculator:
    """Engine tính toán lợi ích từ văn bản pháp luật"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.benefit_keywords = self._load_benefit_keywords()
        self.quantification_patterns = self._load_quantification_patterns()
        self.benefit_multipliers = self._load_benefit_multipliers()
    
    def _load_benefit_keywords(self) -> Dict[str, List[str]]:
        """Load từ khóa lợi ích theo danh mục"""
        return {
            'financial': [
                'tiết kiệm', 'giảm chi phí', 'tăng doanh thu', 'lợi nhuận',
                'hiệu quả kinh tế', 'giá trị gia tăng', 'sinh lời', 'đầu tư hiệu quả'
            ],
            'safety': [
                'an toàn', 'giảm tai nạn', 'bảo vệ', 'phòng ngừa',
                'giảm rủi ro', 'đảm bảo an toàn', 'tránh thiệt hại', 'bảo đảm'
            ],
            'efficiency': [
                'hiệu quả', 'nâng cao năng suất', 'tối ưu hóa', 'cải thiện',
                'rút ngắn thời gian', 'đơn giản hóa', 'tự động hóa', 'tinh gọn'
            ],
            'quality': [
                'chất lượng', 'nâng cao chất lượng', 'cải thiện chất lượng',
                'đảm bảo chất lượng', 'tiêu chuẩn', 'chất lượng cao'
            ],
            'environmental': [
                'môi trường', 'xanh', 'sạch', 'giảm ô nhiễm',
                'bảo vệ môi trường', 'thân thiện môi trường', 'bền vững'
            ],
            'social': [
                'xã hội', 'cộng đồng', 'dân sinh', 'phúc lợi',
                'lợi ích xã hội', 'phát triển xã hội', 'cải thiện đời sống'
            ]
        }
    
    def _load_quantification_patterns(self) -> List[str]:
        """Load patterns để nhận diện số liệu lợi ích"""
        return [
            r'tiết kiệm.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'giảm.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'tăng.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'cải thiện.*?(\d+(?:\.\d+)?)\s*(?:%)',
            r'nâng cao.*?(\d+(?:\.\d+)?)\s*(?:%)',
            r'hiệu quả.*?(\d+(?:\.\d+)?)\s*(?:%)',
            r'giảm thiểu.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)'
        ]
    
    def _load_benefit_multipliers(self) -> Dict[str, float]:
        """Load hệ số nhân lợi ích theo ngành"""
        return {
            'GTVT': 1.8,      # Giao thông vận tải - tác động lớn
            'YTE': 2.2,       # Y tế - lợi ích xã hội cao
            'GDDT': 2.0,      # Giáo dục - lợi ích dài hạn
            'TNMT': 1.9,      # Tài nguyên môi trường
            'KHCN': 1.7,      # Khoa học công nghệ
            'BCA': 1.6,       # Công an - an ninh trật tự
            'BTC': 1.4,       # Tài chính
            'BXD': 1.5,       # Xây dựng
            'default': 1.0
        }
    
    def calculate_direct_financial_benefit(self, document: Dict, economic_impact: Dict) -> BenefitEstimate:
        """
        Tính lợi ích tài chính trực tiếp
        
        Args:
            document: Văn bản pháp luật
            economic_impact: Kết quả phân tích kinh tế
            
        Returns:
            BenefitEstimate: Ước lượng lợi ích tài chính trực tiếp
        """
        content = document.get('content', '')
        
        # Extract quantified benefits from text
        quantified_benefits = self._extract_quantified_benefits(content)
        
        # Calculate base financial benefit
        base_benefit = 0.0
        for benefit_text, amount in quantified_benefits:
            if any(keyword in benefit_text.lower() for keyword in self.benefit_keywords['financial']):
                base_benefit += amount
        
        # If no explicit benefits found, estimate based on content analysis
        if base_benefit == 0:
            base_benefit = self._estimate_implicit_financial_benefit(content, document)
        
        # Apply sector multiplier
        sector_multiplier = self._get_sector_multiplier(document.get('agency', ''))
        total_benefit = base_benefit * sector_multiplier
        
        # Generate assumptions
        assumptions = self._generate_financial_assumptions(document, total_benefit)
        
        # Calculate confidence
        confidence = self._calculate_benefit_confidence(content, quantified_benefits)
        
        return BenefitEstimate(
            category=BenefitCategory.DIRECT_FINANCIAL,
            amount=total_benefit,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="1-3 years",
            basis=f"Base: {base_benefit:.1f}M, Sector multiplier: {sector_multiplier}x",
            assumptions=assumptions,
            quantifiable=len(quantified_benefits) > 0
        )
    
    def calculate_indirect_financial_benefit(self, document: Dict, direct_benefit: float) -> BenefitEstimate:
        """Tính lợi ích tài chính gián tiếp"""
        content = document.get('content', '')
        
        # Indirect benefits are typically 40-80% of direct benefits
        indirect_multiplier = self._get_indirect_benefit_multiplier(content)
        indirect_benefit = direct_benefit * indirect_multiplier
        
        # Additional indirect benefits from efficiency gains
        efficiency_benefit = self._estimate_efficiency_benefit(content)
        total_indirect = indirect_benefit + efficiency_benefit
        
        assumptions = [
            f"Lợi ích gián tiếp = {indirect_multiplier*100:.0f}% lợi ích trực tiếp",
            "Hiệu ứng lan tỏa trong 2-5 năm",
            "Không tính lợi ích từ cải thiện hình ảnh tổ chức"
        ]
        
        confidence = 0.6  # Lower confidence for indirect benefits
        
        return BenefitEstimate(
            category=BenefitCategory.INDIRECT_FINANCIAL,
            amount=total_indirect,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="2-5 years",
            basis=f"Indirect multiplier: {indirect_multiplier*100:.0f}%, Efficiency: {efficiency_benefit:.1f}M",
            assumptions=assumptions,
            quantifiable=False
        )
    
    def calculate_safety_benefit(self, document: Dict) -> BenefitEstimate:
        """Tính lợi ích an toàn"""
        content = document.get('content', '')
        
        # Count safety-related keywords
        safety_score = sum(1 for keyword in self.benefit_keywords['safety'] 
                          if keyword in content.lower())
        
        if safety_score == 0:
            return BenefitEstimate(
                category=BenefitCategory.SAFETY,
                amount=0.0,
                currency="VND_MILLION",
                confidence=0.0,
                timeframe="N/A",
                basis="No safety benefits identified",
                assumptions=[],
                quantifiable=False
            )
        
        # Estimate safety benefit value
        # Base on avoided accident costs, insurance savings, etc.
        base_safety_value = 50.0  # 50M base value per safety indicator
        safety_benefit = safety_score * base_safety_value
        
        # Higher multiplier for transportation and construction
        agency = document.get('agency', '')
        if any(sector in agency for sector in ['GTVT', 'BXD', 'BCA']):
            safety_benefit *= 2.0
        
        assumptions = [
            "Giá trị tránh được tai nạn: 200-500 triệu/vụ",
            "Giảm chi phí bảo hiểm và bồi thường",
            "Tăng năng suất do môi trường làm việc an toàn hơn"
        ]
        
        confidence = 0.7
        
        return BenefitEstimate(
            category=BenefitCategory.SAFETY,
            amount=safety_benefit,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="Immediate-5 years",
            basis=f"Safety score: {safety_score}, Base value: {base_safety_value}M per indicator",
            assumptions=assumptions,
            quantifiable=True
        )
    
    def calculate_efficiency_benefit(self, document: Dict) -> BenefitEstimate:
        """Tính lợi ích hiệu quả"""
        content = document.get('content', '')
        
        # Efficiency indicators
        efficiency_keywords = self.benefit_keywords['efficiency']
        efficiency_score = sum(1 for keyword in efficiency_keywords if keyword in content.lower())
        
        # Time-saving indicators
        time_saving_patterns = [
            r'rút ngắn.*?(\d+)\s*(?:ngày|giờ|phút)',
            r'giảm.*?(\d+)\s*(?:ngày|giờ|phút)',
            r'tiết kiệm.*?(\d+)\s*(?:ngày|giờ|phút)'
        ]
        
        time_savings = []
        for pattern in time_saving_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    time_value = float(match.group(1))
                    time_savings.append(time_value)
                except (ValueError, IndexError):
                    continue
        
        # Calculate efficiency benefit
        base_efficiency = efficiency_score * 30.0  # 30M per efficiency indicator
        
        # Add time-saving value
        if time_savings:
            avg_time_saving = sum(time_savings) / len(time_savings)
            # Assume 1 day saved = 2M VND value
            time_value = avg_time_saving * 2.0
            base_efficiency += time_value
        
        # Process improvement multiplier
        if any(keyword in content.lower() for keyword in ['tự động hóa', 'số hóa', 'công nghệ']):
            base_efficiency *= 1.5
        
        assumptions = [
            "Giá trị 1 ngày tiết kiệm = 2 triệu VND",
            "Hiệu quả tăng 10-20% sau 6 tháng triển khai",
            "Không tính lợi ích từ cải thiện tinh thần nhân viên"
        ]
        
        confidence = 0.75
        
        return BenefitEstimate(
            category=BenefitCategory.EFFICIENCY,
            amount=base_efficiency,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="6 months - 3 years",
            basis=f"Efficiency score: {efficiency_score}, Time savings: {len(time_savings)} indicators",
            assumptions=assumptions,
            quantifiable=len(time_savings) > 0
        )
    
    def calculate_quality_benefit(self, document: Dict) -> BenefitEstimate:
        """Tính lợi ích chất lượng"""
        content = document.get('content', '')
        
        quality_score = sum(1 for keyword in self.benefit_keywords['quality'] 
                           if keyword in content.lower())
        
        if quality_score == 0:
            return BenefitEstimate(
                category=BenefitCategory.QUALITY,
                amount=0.0,
                currency="VND_MILLION",
                confidence=0.0,
                timeframe="N/A",
                basis="No quality benefits identified",
                assumptions=[],
                quantifiable=False
            )
        
        # Quality improvement value
        base_quality_value = 25.0  # 25M per quality indicator
        quality_benefit = quality_score * base_quality_value
        
        # Standards and certification multiplier
        if any(keyword in content.lower() for keyword in ['tiêu chuẩn', 'chứng nhận', 'ISO']):
            quality_benefit *= 1.3
        
        assumptions = [
            "Cải thiện chất lượng dẫn đến tăng giá trị sản phẩm/dịch vụ",
            "Giảm chi phí xử lý khiếu nại và bảo hành",
            "Tăng độ tin cậy và uy tín thương hiệu"
        ]
        
        confidence = 0.65
        
        return BenefitEstimate(
            category=BenefitCategory.QUALITY,
            amount=quality_benefit,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="1-3 years",
            basis=f"Quality score: {quality_score}, Base value: {base_quality_value}M per indicator",
            assumptions=assumptions,
            quantifiable=False
        )
    
    def calculate_environmental_benefit(self, document: Dict) -> BenefitEstimate:
        """Tính lợi ích môi trường"""
        content = document.get('content', '')
        
        env_score = sum(1 for keyword in self.benefit_keywords['environmental'] 
                       if keyword in content.lower())
        
        if env_score == 0:
            return BenefitEstimate(
                category=BenefitCategory.ENVIRONMENTAL,
                amount=0.0,
                currency="VND_MILLION",
                confidence=0.0,
                timeframe="N/A",
                basis="No environmental benefits identified",
                assumptions=[],
                quantifiable=False
            )
        
        # Environmental benefit value (harder to quantify)
        base_env_value = 20.0  # 20M per environmental indicator
        env_benefit = env_score * base_env_value
        
        # Carbon reduction multiplier
        if any(keyword in content.lower() for keyword in ['carbon', 'khí thải', 'giảm ô nhiễm']):
            env_benefit *= 1.5
        
        assumptions = [
            "Giá trị tránh được ô nhiễm môi trường",
            "Tiết kiệm chi phí xử lý chất thải",
            "Lợi ích dài hạn cho thế hệ tương lai (không định lượng)"
        ]
        
        confidence = 0.5  # Lower confidence due to difficulty in quantification
        
        return BenefitEstimate(
            category=BenefitCategory.ENVIRONMENTAL,
            amount=env_benefit,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="Long-term (5-20 years)",
            basis=f"Environmental score: {env_score}, Base value: {base_env_value}M per indicator",
            assumptions=assumptions,
            quantifiable=False
        )
    
    def calculate_social_benefit(self, document: Dict) -> BenefitEstimate:
        """Tính lợi ích xã hội"""
        content = document.get('content', '')
        
        social_score = sum(1 for keyword in self.benefit_keywords['social'] 
                          if keyword in content.lower())
        
        if social_score == 0:
            return BenefitEstimate(
                category=BenefitCategory.SOCIAL,
                amount=0.0,
                currency="VND_MILLION",
                confidence=0.0,
                timeframe="N/A",
                basis="No social benefits identified",
                assumptions=[],
                quantifiable=False
            )
        
        # Social benefit value
        base_social_value = 15.0  # 15M per social indicator
        social_benefit = social_score * base_social_value
        
        # Public service multiplier
        agency = document.get('agency', '')
        if any(sector in agency for sector in ['YTE', 'GDDT', 'LDTBXH']):
            social_benefit *= 2.0
        
        assumptions = [
            "Cải thiện chất lượng cuộc sống người dân",
            "Tăng sự hài lòng của công chúng",
            "Giảm chi phí xã hội từ các vấn đề được giải quyết"
        ]
        
        confidence = 0.4  # Lowest confidence due to difficulty in quantification
        
        return BenefitEstimate(
            category=BenefitCategory.SOCIAL,
            amount=social_benefit,
            currency="VND_MILLION",
            confidence=confidence,
            timeframe="Long-term (3-10 years)",
            basis=f"Social score: {social_score}, Base value: {base_social_value}M per indicator",
            assumptions=assumptions,
            quantifiable=False
        )
    
    def _extract_quantified_benefits(self, content: str) -> List[Tuple[str, float]]:
        """Trích xuất lợi ích có định lượng từ văn bản"""
        quantified_benefits = []
        
        for pattern in self.quantification_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.group(1))
                    benefit_text = match.group(0)
                    quantified_benefits.append((benefit_text, amount))
                except (ValueError, IndexError):
                    continue
        
        return quantified_benefits
    
    def _estimate_implicit_financial_benefit(self, content: str, document: Dict) -> float:
        """Ước lượng lợi ích tài chính ngầm định"""
        # Count financial benefit keywords
        financial_score = sum(1 for keyword in self.benefit_keywords['financial'] 
                             if keyword in content.lower())
        
        if financial_score == 0:
            return 0.0
        
        # Base benefit per keyword
        base_benefit = financial_score * 40.0  # 40M per financial keyword
        
        # Adjust based on document type
        doc_number = document.get('number', '')
        if any(doc_type in doc_number for doc_type in ['NĐ', 'QĐ']):
            base_benefit *= 1.5  # Higher impact documents
        
        return base_benefit
    
    def _get_sector_multiplier(self, agency: str) -> float:
        """Lấy hệ số nhân theo ngành"""
        for sector, multiplier in self.benefit_multipliers.items():
            if sector in agency:
                return multiplier
        return self.benefit_multipliers['default']
    
    def _get_indirect_benefit_multiplier(self, content: str) -> float:
        """Tính hệ số lợi ích gián tiếp"""
        # Base multiplier
        multiplier = 0.5  # 50% of direct benefits
        
        # Increase for systemic changes
        if any(keyword in content.lower() for keyword in ['hệ thống', 'toàn diện', 'đồng bộ']):
            multiplier += 0.2
        
        # Increase for technology-related benefits
        if any(keyword in content.lower() for keyword in ['công nghệ', 'số hóa', 'tự động']):
            multiplier += 0.15
        
        return min(multiplier, 0.8)  # Max 80%
    
    def _estimate_efficiency_benefit(self, content: str) -> float:
        """Ước lượng lợi ích từ cải thiện hiệu quả"""
        efficiency_indicators = [
            'tự động hóa', 'số hóa', 'đơn giản hóa', 'tinh gọn',
            'tối ưu', 'cải tiến quy trình'
        ]
        
        efficiency_count = sum(1 for indicator in efficiency_indicators 
                              if indicator in content.lower())
        
        return efficiency_count * 35.0  # 35M per efficiency improvement
    
    def _generate_financial_assumptions(self, document: Dict, total_benefit: float) -> List[str]:
        """Tạo giả định cho lợi ích tài chính"""
        assumptions = [
            "Lợi ích được tính theo giá trị hiện tại (NPV)",
            "Tỷ lệ chiết khấu 8%/năm cho dòng tiền tương lai",
            "Không tính lợi ích từ tăng giá tài sản"
        ]
        
        if total_benefit > 100:
            assumptions.append("Lợi ích lớn có thể mất 2-3 năm để thực hiện đầy đủ")
        
        agency = document.get('agency', '')
        if 'GTVT' in agency:
            assumptions.append("Lợi ích giao thông tính cả tiết kiệm thời gian di chuyển")
        
        return assumptions
    
    def _calculate_benefit_confidence(self, content: str, quantified_benefits: List) -> float:
        """Tính độ tin cậy của ước lượng lợi ích"""
        confidence = 0.4  # Base confidence
        
        # Increase if we have quantified benefits
        if quantified_benefits:
            confidence += min(len(quantified_benefits) * 0.15, 0.4)
        
        # Increase for explicit benefit mentions
        benefit_keywords_all = []
        for category in self.benefit_keywords.values():
            benefit_keywords_all.extend(category)
        
        benefit_mentions = sum(1 for keyword in benefit_keywords_all 
                              if keyword in content.lower())
        confidence += min(benefit_mentions * 0.05, 0.3)
        
        return min(confidence, 1.0)
    
    def calculate_all_benefits(self, document: Dict, economic_impact: Dict) -> Dict[str, BenefitEstimate]:
        """Tính tất cả các loại lợi ích"""
        results = {}
        
        # Direct financial benefit
        direct_financial = self.calculate_direct_financial_benefit(document, economic_impact)
        results['direct_financial'] = direct_financial
        
        # Indirect financial benefit
        indirect_financial = self.calculate_indirect_financial_benefit(document, direct_financial.amount)
        results['indirect_financial'] = indirect_financial
        
        # Safety benefit
        safety = self.calculate_safety_benefit(document)
        results['safety'] = safety
        
        # Efficiency benefit
        efficiency = self.calculate_efficiency_benefit(document)
        results['efficiency'] = efficiency
        
        # Quality benefit
        quality = self.calculate_quality_benefit(document)
        results['quality'] = quality
        
        # Environmental benefit
        environmental = self.calculate_environmental_benefit(document)
        results['environmental'] = environmental
        
        # Social benefit
        social = self.calculate_social_benefit(document)
        results['social'] = social
        
        return results

if __name__ == "__main__":
    # Test benefit calculator
    calculator = BenefitCalculator()
    
    sample_doc = {
        'number': '20/2025/NĐ-CP',
        'agency': 'BỘ GIAO THÔNG VẬN TẢI',
        'content': 'Quy định nhằm nâng cao an toàn giao thông, tiết kiệm 15% chi phí vận hành, cải thiện chất lượng dịch vụ và giảm 30% thời gian xử lý thủ tục.'
    }
    
    sample_impact = {'confidence_score': 0.8}
    
    benefits = calculator.calculate_all_benefits(sample_doc, sample_impact)
    
    total_quantifiable = 0
    total_non_quantifiable = 0
    
    for benefit_type, estimate in benefits.items():
        if estimate.amount > 0:
            print(f"\n{benefit_type.upper()} BENEFIT:")
            print(f"Amount: {estimate.amount:.2f} {estimate.currency}")
            print(f"Confidence: {estimate.confidence:.2f}")
            print(f"Timeframe: {estimate.timeframe}")
            print(f"Quantifiable: {estimate.quantifiable}")
            
            if estimate.quantifiable:
                total_quantifiable += estimate.amount
            else:
                total_non_quantifiable += estimate.amount
    
    print(f"\nTOTAL SUMMARY:")
    print(f"Quantifiable benefits: {total_quantifiable:.2f} VND_MILLION")
    print(f"Non-quantifiable benefits: {total_non_quantifiable:.2f} VND_MILLION")
    print(f"Total estimated benefits: {total_quantifiable + total_non_quantifiable:.2f} VND_MILLION")