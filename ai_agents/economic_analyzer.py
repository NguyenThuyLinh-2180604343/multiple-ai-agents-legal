"""
Core Economic Analysis Logic
Phân tích tác động kinh tế từ văn bản pháp luật
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

@dataclass
class EconomicImpact:
    """Cấu trúc dữ liệu tác động kinh tế"""
    document_id: str
    compliance_cost: float
    implementation_cost: float
    opportunity_cost: float
    direct_benefit: float
    indirect_benefit: float
    confidence_score: float
    economic_keywords: List[str]
    assumptions: List[str]

class EconomicAnalyzer:
    """Core engine phân tích tác động kinh tế"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.economic_keywords = self._load_economic_keywords()
        self.cost_patterns = self._load_cost_patterns()
        self.benefit_patterns = self._load_benefit_patterns()
    
    def _load_economic_keywords(self) -> Dict[str, List[str]]:
        """Load từ khóa kinh tế tiếng Việt"""
        return {
            'cost': [
                'chi phí', 'phí', 'lệ phí', 'thuế', 'tiền phạt', 'phạt tiền',
                'đầu tư', 'ngân sách', 'kinh phí', 'tài chính', 'tiền bạc',
                'mua sắm', 'trang thiết bị', 'nhân lực', 'đào tạo'
            ],
            'benefit': [
                'lợi ích', 'hiệu quả', 'tiết kiệm', 'tăng trưởng', 'phát triển',
                'cải thiện', 'nâng cao', 'tối ưu', 'giảm thiểu', 'an toàn',
                'chất lượng', 'năng suất', 'doanh thu', 'lợi nhuận'
            ],
            'compliance': [
                'tuân thủ', 'chấp hành', 'thực hiện', 'áp dụng', 'triển khai',
                'ban hành', 'quy định', 'nghị định', 'thông tư', 'hướng dẫn'
            ]
        }
    
    def _load_cost_patterns(self) -> List[str]:
        """Patterns để nhận diện chi phí"""
        return [
            r'chi phí.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng)',
            r'phí.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng)',
            r'ngân sách.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng)',
            r'đầu tư.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng)',
            r'kinh phí.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng)'
        ]
    
    def _load_benefit_patterns(self) -> List[str]:
        """Patterns để nhận diện lợi ích"""
        return [
            r'tiết kiệm.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'giảm.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'tăng.*?(\d+(?:\.\d+)?)\s*(?:triệu|tỷ|nghìn|đồng|%)',
            r'cải thiện.*?(\d+(?:\.\d+)?)\s*(?:%)',
            r'nâng cao.*?(\d+(?:\.\d+)?)\s*(?:%)'
        ]
    
    def analyze_document(self, document: Dict) -> EconomicImpact:
        """
        Phân tích tác động kinh tế của một văn bản
        
        Args:
            document: Document từ processed data
            
        Returns:
            EconomicImpact: Kết quả phân tích
        """
        content = document.get('content', '')
        doc_id = document.get('number', 'unknown')
        
        # Extract economic features
        economic_keywords = self._extract_economic_keywords(content)
        cost_indicators = self._extract_cost_indicators(content)
        benefit_indicators = self._extract_benefit_indicators(content)
        
        # Calculate impacts
        compliance_cost = self._estimate_compliance_cost(content, cost_indicators)
        implementation_cost = self._estimate_implementation_cost(content, cost_indicators)
        opportunity_cost = self._estimate_opportunity_cost(content)
        direct_benefit = self._estimate_direct_benefit(content, benefit_indicators)
        indirect_benefit = self._estimate_indirect_benefit(content, benefit_indicators)
        
        # Generate assumptions
        assumptions = self._generate_assumptions(document, economic_keywords)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            economic_keywords, cost_indicators, benefit_indicators
        )
        
        return EconomicImpact(
            document_id=doc_id,
            compliance_cost=compliance_cost,
            implementation_cost=implementation_cost,
            opportunity_cost=opportunity_cost,
            direct_benefit=direct_benefit,
            indirect_benefit=indirect_benefit,
            confidence_score=confidence_score,
            economic_keywords=economic_keywords,
            assumptions=assumptions
        )
    
    def _extract_economic_keywords(self, content: str) -> List[str]:
        """Trích xuất từ khóa kinh tế từ văn bản"""
        found_keywords = []
        content_lower = content.lower()
        
        for category, keywords in self.economic_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    found_keywords.append(f"{category}:{keyword}")
        
        return found_keywords
    
    def _extract_cost_indicators(self, content: str) -> List[Tuple[str, float]]:
        """Trích xuất chỉ số chi phí từ văn bản"""
        cost_indicators = []
        
        for pattern in self.cost_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.group(1))
                    cost_indicators.append((match.group(0), amount))
                except (ValueError, IndexError):
                    continue
        
        return cost_indicators
    
    def _extract_benefit_indicators(self, content: str) -> List[Tuple[str, float]]:
        """Trích xuất chỉ số lợi ích từ văn bản"""
        benefit_indicators = []
        
        for pattern in self.benefit_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.group(1))
                    benefit_indicators.append((match.group(0), amount))
                except (ValueError, IndexError):
                    continue
        
        return benefit_indicators
    
    def _estimate_compliance_cost(self, content: str, cost_indicators: List) -> float:
        """Ước lượng chi phí tuân thủ"""
        base_cost = 0.0
        
        # Heuristic based on document complexity
        content_length = len(content)
        complexity_factor = min(content_length / 10000, 2.0)  # Max 2x multiplier
        
        # Base cost from extracted indicators
        for _, amount in cost_indicators:
            base_cost += amount * 0.3  # 30% of mentioned costs
        
        # Default minimum cost if no indicators found
        if base_cost == 0:
            base_cost = 50.0 * complexity_factor  # 50 triệu VND base
        
        return base_cost * complexity_factor
    
    def _estimate_implementation_cost(self, content: str, cost_indicators: List) -> float:
        """Ước lượng chi phí triển khai"""
        base_cost = 0.0
        
        # Implementation keywords
        impl_keywords = ['triển khai', 'thực hiện', 'áp dụng', 'ban hành']
        impl_count = sum(1 for keyword in impl_keywords if keyword in content.lower())
        
        # Base cost from indicators
        for _, amount in cost_indicators:
            base_cost += amount * 0.5  # 50% of mentioned costs
        
        # Factor based on implementation complexity
        impl_factor = 1.0 + (impl_count * 0.2)
        
        if base_cost == 0:
            base_cost = 100.0 * impl_factor  # 100 triệu VND base
        
        return base_cost * impl_factor
    
    def _estimate_opportunity_cost(self, content: str) -> float:
        """Ước lượng chi phí cơ hội"""
        # Simple heuristic: 20% of compliance + implementation
        return 0.0  # Will be calculated in cost_estimator.py
    
    def _estimate_direct_benefit(self, content: str, benefit_indicators: List) -> float:
        """Ước lượng lợi ích trực tiếp"""
        total_benefit = 0.0
        
        for _, amount in benefit_indicators:
            total_benefit += amount
        
        # If no explicit benefits, estimate based on content
        if total_benefit == 0:
            benefit_keywords = ['an toàn', 'hiệu quả', 'chất lượng', 'tiết kiệm']
            benefit_count = sum(1 for keyword in benefit_keywords if keyword in content.lower())
            total_benefit = benefit_count * 25.0  # 25 triệu per benefit keyword
        
        return total_benefit
    
    def _estimate_indirect_benefit(self, content: str, benefit_indicators: List) -> float:
        """Ước lượng lợi ích gián tiếp"""
        # Indirect benefits are typically 30-50% of direct benefits
        direct_benefit = self._estimate_direct_benefit(content, benefit_indicators)
        return direct_benefit * 0.4
    
    def _generate_assumptions(self, document: Dict, economic_keywords: List[str]) -> List[str]:
        """Tạo danh sách giả định cho phân tích"""
        assumptions = []
        
        # Base assumptions
        assumptions.append("Giả định tỷ giá USD/VND ổn định trong 12 tháng")
        assumptions.append("Giả định lạm phát 3-4% theo dự báo NHNN")
        assumptions.append("Giả định không có thay đổi lớn về chính sách thuế")
        
        # Document-specific assumptions
        agency = document.get('agency', '')
        if 'UBND' in agency:
            assumptions.append("Giả định ngân sách địa phương đủ để triển khai")
        
        if 'BGTVT' in agency:
            assumptions.append("Giả định hạ tầng giao thông hiện tại đáp ứng yêu cầu")
        
        if any('chi phí' in kw for kw in economic_keywords):
            assumptions.append("Giả định chi phí nhân công tăng 5-7%/năm")
        
        return assumptions[:5]  # Limit to 5 assumptions
    
    def _calculate_confidence_score(self, keywords: List[str], 
                                  cost_indicators: List, 
                                  benefit_indicators: List) -> float:
        """Tính điểm tin cậy của phân tích"""
        score = 0.0
        
        # Keywords contribute 40%
        keyword_score = min(len(keywords) / 10.0, 1.0) * 0.4
        
        # Cost indicators contribute 30%
        cost_score = min(len(cost_indicators) / 5.0, 1.0) * 0.3
        
        # Benefit indicators contribute 30%
        benefit_score = min(len(benefit_indicators) / 5.0, 1.0) * 0.3
        
        score = keyword_score + cost_score + benefit_score
        
        return min(score, 1.0)
    
    def analyze_batch(self, documents: List[Dict]) -> List[EconomicImpact]:
        """Phân tích batch documents"""
        results = []
        
        for doc in documents:
            try:
                impact = self.analyze_document(doc)
                results.append(impact)
                self.logger.info(f"Analyzed document {impact.document_id}")
            except Exception as e:
                self.logger.error(f"Error analyzing document: {e}")
                continue
        
        return results
    
    def save_results(self, results: List[EconomicImpact], output_path: str):
        """Lưu kết quả phân tích"""
        output_data = []
        
        for result in results:
            output_data.append({
                'document_id': result.document_id,
                'compliance_cost': result.compliance_cost,
                'implementation_cost': result.implementation_cost,
                'opportunity_cost': result.opportunity_cost,
                'direct_benefit': result.direct_benefit,
                'indirect_benefit': result.indirect_benefit,
                'confidence_score': result.confidence_score,
                'economic_keywords': result.economic_keywords,
                'assumptions': result.assumptions
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(results)} economic analysis results to {output_path}")

if __name__ == "__main__":
    # Test với sample data
    analyzer = EconomicAnalyzer()
    
    sample_doc = {
        'number': 'TEST_001',
        'content': 'Quy định về chi phí đầu tư 100 tỷ đồng để nâng cao chất lượng an toàn giao thông, tiết kiệm 20% chi phí vận hành.',
        'agency': 'BỘ GIAO THÔNG VẬN TẢI'
    }
    
    result = analyzer.analyze_document(sample_doc)
    print(f"Document: {result.document_id}")
    print(f"Compliance Cost: {result.compliance_cost:.2f} triệu VND")
    print(f"Implementation Cost: {result.implementation_cost:.2f} triệu VND")
    print(f"Direct Benefit: {result.direct_benefit:.2f} triệu VND")
    print(f"Confidence Score: {result.confidence_score:.2f}")
    print(f"Assumptions: {result.assumptions}")