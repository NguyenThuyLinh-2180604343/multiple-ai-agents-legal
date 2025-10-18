# preprocess/segmenter.py
import re
from typing import List, Dict, Any, Optional

# IMPROVED REGEX PATTERNS FOR VIETNAMESE LEGAL DOCUMENTS

# Điều patterns - handle multi-line titles
ART_LAW = re.compile(
    r"(Điều\s+(\d+[a-zA-Z]?))\s*[\.\:\-]?\s*(.*?)(?=\s*Điều\s+\d+|$)", 
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

# Chapter patterns - comprehensive for all Vietnamese legal structures
CHAPTER = re.compile(
    r"(?:^|\n)\s*((?:Chương|CHƯƠNG|Phần|PHẦN|Mục|MỤC|Tiết|TIẾT)\s+(?:[IVXLCDM]+|\d+))\s*[\.\:\-]?\s*([^\r\n]*?)(?=\n|$)", 
    re.IGNORECASE | re.MULTILINE
)

# Clause patterns - numbered items with better boundary detection
CLAUSE = re.compile(
    r"(?:^|\n)\s*(\d+)\s*[\.\)]\s+([^\n]*?)(?=(?:\n\s*\d+\s*[\.\)]|\n\s*[a-z]\s*\)|\n\s*(?:Điều|Chương|Phần|Mục|Tiết)|\Z))", 
    re.MULTILINE | re.DOTALL
)

# Point patterns - lettered items (a), b), c)
POINT = re.compile(
    r"(?:^|\n)\s*([a-z])\s*\)\s+([^\n]*?)(?=(?:\n\s*[a-z]\s*\)|\n\s*\d+\s*[\.\)]|\n\s*(?:Điều|Chương|Phần|Mục|Tiết)|\Z))", 
    re.MULTILINE | re.DOTALL
)

# Sub-point patterns - dash items (-)
SUBPOINT = re.compile(
    r"(?:^|\n)\s*(-)\s+([^\n]*?)(?=(?:\n\s*-|\n\s*[a-z]\s*\)|\n\s*\d+\s*[\.\)]|\Z))", 
    re.MULTILINE | re.DOTALL
)

# Roman numeral patterns for sections
ROMAN = re.compile(
    r"(?:^|\n)\s*([IVXLCDM]+)\s*\.\s*([^\r\n]*?)(?=\n|$)", 
    re.IGNORECASE | re.MULTILINE
)

# Document type detection patterns
DOC_TYPE_PATTERNS = {
    'law': re.compile(r'LUẬT|LAW', re.IGNORECASE),
    'decree': re.compile(r'NGHỊ\s*ĐỊNH|DECREE', re.IGNORECASE), 
    'circular': re.compile(r'THÔNG\s*TƯ|CIRCULAR', re.IGNORECASE),
    'decision': re.compile(r'QUYẾT\s*ĐỊNH|DECISION', re.IGNORECASE),
    'directive': re.compile(r'CHỈ\s*THỊ|DIRECTIVE', re.IGNORECASE),
    'instruction': re.compile(r'HƯỚNG\s*DẪN|INSTRUCTION', re.IGNORECASE)
}

def segment(doc_text: str, doc_meta: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Enhanced segmentation for Vietnamese legal documents with document type detection
    
    Args:
        doc_text: Raw document text
        doc_meta: Optional metadata containing document info
        
    Returns:
        Dictionary with segmented articles and validation info
    """
    
    if not doc_text:
        return {"articles": [], "validation": {"status": "empty", "issues": ["Empty document"]}}
    
    # Clean and normalize text
    text = _normalize_text(doc_text)
    original_length = len(text)
    
    # Detect document type for specialized processing
    doc_type = _detect_document_type(text, doc_meta)
    
    # Apply type-specific segmentation
    if doc_type == 'law':
        result = _segment_law_document(text)
    elif doc_type == 'decree':
        result = _segment_decree_document(text)
    elif doc_type == 'circular':
        result = _segment_circular_document(text)
    else:
        result = _segment_generic_document(text)
    
    # Add validation information
    validation = _validate_segmentation(text, result, original_length)
    result["validation"] = validation
    result["document_type"] = doc_type
    
    return result

def _normalize_text(text: str) -> str:
    """Normalize text for better processing"""
    text = text.strip()
    # Normalize line breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    # Remove excessive whitespace but preserve structure
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    # Normalize spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text

def _detect_document_type(text: str, doc_meta: Optional[Dict] = None) -> str:
    """Detect document type based on content and metadata"""
    
    # Check metadata first if available
    if doc_meta:
        title = doc_meta.get('title', '').upper()
        number = doc_meta.get('number', '').upper()
        
        for doc_type, pattern in DOC_TYPE_PATTERNS.items():
            if pattern.search(title) or pattern.search(number):
                return doc_type
    
    # Check content patterns
    text_upper = text[:1000].upper()  # Check first 1000 chars
    
    for doc_type, pattern in DOC_TYPE_PATTERNS.items():
        if pattern.search(text_upper):
            return doc_type
    
    return 'generic'

def _segment_law_document(text: str) -> Dict[str, Any]:
    """Specialized segmentation for Law documents"""
    
    # Try Điều segmentation first (most common in laws)
    dieu_matches = list(ART_LAW.finditer(text))
    if len(dieu_matches) >= 2:
        articles = _segment_by_dieu(text, dieu_matches)
        return {"articles": articles, "strategy_used": "dieu"}
    
    # If no Điều found, try chapters
    chapter_matches = list(CHAPTER.finditer(text))
    if chapter_matches:
        articles = []
        # Process by chapters first
        for i, chapter_match in enumerate(chapter_matches):
            chapter_num = chapter_match.group(1)
            chapter_title = chapter_match.group(2).strip()
            
            # Get chapter content
            start_pos = chapter_match.end()
            end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
            chapter_content = text[start_pos:end_pos].strip()
            
            # Look for articles within chapter
            dieu_matches = list(ART_LAW.finditer(chapter_content))
            if dieu_matches:
                chapter_articles = _segment_by_dieu(chapter_content, dieu_matches)
                for article in chapter_articles:
                    article["chapter"] = chapter_num
                    article["chapter_title"] = chapter_title
                articles.extend(chapter_articles)
            else:
                # Chapter without articles - treat as single unit
                clauses = _parse_clauses_advanced(chapter_content)
                articles.append({
                    "chapter": chapter_num,
                    "title": chapter_title,
                    "clauses": clauses
                })
    else:
        # No chapters, look for articles directly
        dieu_matches = list(ART_LAW.finditer(text))
        if dieu_matches:
            articles = _segment_by_dieu(text, dieu_matches)
        else:
            articles = _segment_fallback_advanced(text)
    
    return {"articles": articles}

def _segment_decree_document(text: str) -> Dict[str, Any]:
    """Specialized segmentation for Decree documents"""
    articles = []
    
    # Decrees typically have: Điều -> Khoản -> Điểm
    dieu_matches = list(ART_LAW.finditer(text))
    
    if len(dieu_matches) >= 1:
        articles = _segment_by_dieu(text, dieu_matches)
    else:
        # Look for chapters or sections
        chapter_matches = list(CHAPTER.finditer(text))
        if chapter_matches:
            articles = _segment_by_chapters_advanced(text, chapter_matches)
        else:
            articles = _segment_fallback_advanced(text)
    
    return {"articles": articles}

def _segment_circular_document(text: str) -> Dict[str, Any]:
    """Specialized segmentation for Circular documents"""
    articles = []
    
    # Circulars often have: Phần/Mục -> Điều -> Khoản
    chapter_matches = list(CHAPTER.finditer(text))
    
    if chapter_matches:
        articles = _segment_by_chapters_advanced(text, chapter_matches)
    else:
        # Look for numbered sections or articles
        dieu_matches = list(ART_LAW.finditer(text))
        if dieu_matches:
            articles = _segment_by_dieu(text, dieu_matches)
        else:
            # Try Roman numerals or numbered sections
            roman_matches = list(ROMAN.finditer(text))
            if len(roman_matches) >= 2:
                articles = _segment_by_roman_advanced(text, roman_matches)
            else:
                articles = _segment_fallback_advanced(text)
    
    return {"articles": articles}

def _segment_generic_document(text: str) -> Dict[str, Any]:
    """Generic segmentation for unknown document types"""
    articles = []
    
    # Try Điều segmentation first
    dieu_matches = list(ART_LAW.finditer(text))
    if len(dieu_matches) >= 2:
        articles = _segment_by_dieu(text, dieu_matches)
        return {"articles": articles, "strategy_used": "dieu"}
    
    # Try all other strategies
    strategies = [
        ("chapters", lambda: _try_segment_by_chapters(text)),
        ("sections", lambda: _try_segment_by_sections(text)),
        ("roman", lambda: _try_segment_by_roman(text)),
        ("fallback", lambda: _segment_fallback_advanced(text))
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            result = strategy_func()
            if result and len(result) > 0:
                return {"articles": result, "strategy_used": strategy_name}
        except Exception as e:
            continue
    
    # Ultimate fallback
    return {"articles": _segment_fallback_advanced(text), "strategy_used": "ultimate_fallback"}

def _segment_by_dieu(text: str, matches) -> List[Dict[str, Any]]:
    """Segment by Điều (Law articles) with improved parsing"""
    articles = []
    
    for i, match in enumerate(matches):
        article_num = f"Điều {match.group(2)}"  # Updated to use group(2) for number
        article_title = match.group(3).strip()  # Updated to use group(3) for title
        
        # Get content between this Điều and next Điều
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        content = text[start_pos:end_pos].strip()
        
        # Parse clauses within this article using advanced parsing
        clauses = _parse_clauses_advanced(content)
        
        # If no clauses found, treat entire content as one clause
        if not clauses and content:
            clauses = [{
                "no": "1",
                "text": content,
                "points": []
            }]
        
        articles.append({
            "article": article_num,
            "title": article_title,
            "clauses": clauses
        })
    
    return articles

def _segment_by_roman(text: str, matches):
    """Segment by Roman numerals (Sections)"""
    articles = []
    
    for i, match in enumerate(matches):
        section_num = match.group(1)
        section_title = match.group(2).strip()
        
        # Get content between this section and next section
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        content = text[start_pos:end_pos].strip()
        
        # Parse clauses within this section
        clauses = _parse_clauses(content)
        
        articles.append({
            "section": section_num,
            "title": section_title,
            "clauses": clauses
        })
    
    return articles

def _segment_by_chapters_advanced(text: str, matches) -> List[Dict[str, Any]]:
    """Advanced segmentation by Chapters with better structure handling"""
    articles = []
    
    for i, match in enumerate(matches):
        chapter_num = match.group(1)
        chapter_title = match.group(2).strip()
        
        # Get content between this chapter and next chapter
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start_pos:end_pos].strip()
        
        # Look for Điều within this chapter first
        dieu_in_chapter = list(ART_LAW.finditer(content))
        if len(dieu_in_chapter) >= 1:
            chapter_articles = _segment_by_dieu(content, dieu_in_chapter)
            # Add chapter info to each article
            for article in chapter_articles:
                article["chapter"] = chapter_num
                article["chapter_title"] = chapter_title
            articles.extend(chapter_articles)
        else:
            # Parse as clauses with advanced parsing
            clauses = _parse_clauses_advanced(content)
            if not clauses and content:
                clauses = [{
                    "no": "1",
                    "text": content,
                    "points": []
                }]
            
            articles.append({
                "chapter": chapter_num,
                "title": chapter_title,
                "clauses": clauses
            })
    
    return articles

def _segment_by_roman_advanced(text: str, matches) -> List[Dict[str, Any]]:
    """Advanced segmentation by Roman numerals"""
    articles = []
    
    for i, match in enumerate(matches):
        section_num = match.group(1)
        section_title = match.group(2).strip()
        
        # Get content between this section and next section
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start_pos:end_pos].strip()
        
        # Parse clauses within this section
        clauses = _parse_clauses_advanced(content)
        if not clauses and content:
            clauses = [{
                "no": "1",
                "text": content,
                "points": []
            }]
        
        articles.append({
            "section": section_num,
            "title": section_title,
            "clauses": clauses
        })
    
    return articles

def _parse_clauses_advanced(content: str) -> List[Dict[str, Any]]:
    """Advanced clause parsing with better structure detection"""
    if not content:
        return []
    
    clauses = []
    
    # Strategy 1: Use improved regex for numbered clauses
    clause_matches = list(CLAUSE.finditer(content))
    if clause_matches:
        for match in clause_matches:
            clause_num = match.group(1)
            clause_text = match.group(2).strip()
            
            # Parse points and sub-points within this clause
            points = _parse_points_advanced(clause_text)
            
            clauses.append({
                "no": clause_num,
                "text": clause_text,
                "points": points
            })
        return clauses
    
    # Strategy 2: Line-by-line parsing with better logic
    lines = content.split('\n')
    current_clause = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts with number (more flexible pattern)
        clause_match = re.match(r'^(\d+)\s*[\.\)]\s+(.+)', line)
        if clause_match:
            # Save previous clause
            if current_clause:
                current_clause["points"] = _parse_points_advanced(current_clause["text"])
                clauses.append(current_clause)
            
            # Start new clause
            clause_num = clause_match.group(1)
            clause_text = clause_match.group(2)
            
            current_clause = {
                "no": clause_num,
                "text": clause_text,
                "points": []
            }
        else:
            # Continue current clause or start new one
            if current_clause:
                current_clause["text"] += " " + line
            else:
                # No numbered clauses, treat as single clause
                current_clause = {
                    "no": "1",
                    "text": line,
                    "points": []
                }
    
    # Add last clause
    if current_clause:
        current_clause["points"] = _parse_points_advanced(current_clause["text"])
        clauses.append(current_clause)
    
    # If no clauses found, create one with all content
    if not clauses and content:
        clauses.append({
            "no": "1",
            "text": content,
            "points": []
        })
    
    return clauses

def _parse_points_advanced(content: str) -> List[Dict[str, Any]]:
    """Advanced point parsing with sub-points support"""
    points = []
    
    # Parse lettered points (a), b), c)
    point_matches = list(POINT.finditer(content))
    for match in point_matches:
        letter = match.group(1)
        text = match.group(2).strip()
        
        # Parse sub-points (dash items) within this point
        sub_points = []
        subpoint_matches = list(SUBPOINT.finditer(text))
        for sub_match in subpoint_matches:
            sub_points.append({
                "marker": sub_match.group(1),
                "text": sub_match.group(2).strip()
            })
        
        points.append({
            "letter": letter,
            "text": text,
            "sub_points": sub_points
        })
    
    return points

def _validate_segmentation(original_text: str, result: Dict[str, Any], original_length: int) -> Dict[str, Any]:
    """Validate segmentation quality and completeness"""
    validation = {
        "status": "success",
        "issues": [],
        "stats": {}
    }
    
    articles = result.get("articles", [])
    
    # Calculate content preservation
    total_segmented_length = 0
    total_clauses = 0
    total_points = 0
    
    for article in articles:
        clauses = article.get("clauses", [])
        total_clauses += len(clauses)
        
        for clause in clauses:
            clause_text = clause.get("text", "")
            total_segmented_length += len(clause_text)
            
            points = clause.get("points", [])
            total_points += len(points)
    
    # Content preservation ratio
    preservation_ratio = total_segmented_length / original_length if original_length > 0 else 0
    
    validation["stats"] = {
        "original_length": original_length,
        "segmented_length": total_segmented_length,
        "preservation_ratio": preservation_ratio,
        "total_articles": len(articles),
        "total_clauses": total_clauses,
        "total_points": total_points
    }
    
    # Check for issues
    if preservation_ratio < 0.7:
        validation["issues"].append(f"Low content preservation: {preservation_ratio:.2%}")
        validation["status"] = "warning"
    
    if preservation_ratio > 1.3:
        validation["issues"].append(f"Content duplication detected: {preservation_ratio:.2%}")
        validation["status"] = "warning"
    
    if len(articles) == 0:
        validation["issues"].append("No articles found")
        validation["status"] = "error"
    
    # Check for overly long clauses (potential segmentation failure)
    for article in articles:
        for clause in article.get("clauses", []):
            clause_text = clause.get("text", "")
            if len(clause_text) > 2000:
                validation["issues"].append(f"Very long clause detected ({len(clause_text)} chars)")
                validation["status"] = "warning"
    
    return validation

# Helper functions for trying different segmentation strategies
def _try_segment_by_dieu(text: str) -> List[Dict[str, Any]]:
    """Try segmentation by Điều"""
    dieu_matches = list(ART_LAW.finditer(text))
    if len(dieu_matches) >= 1:
        return _segment_by_dieu(text, dieu_matches)
    return []

def _try_segment_by_chapters(text: str) -> List[Dict[str, Any]]:
    """Try segmentation by chapters"""
    chapter_matches = list(CHAPTER.finditer(text))
    if chapter_matches:
        return _segment_by_chapters_advanced(text, chapter_matches)
    return []

def _try_segment_by_sections(text: str) -> List[Dict[str, Any]]:
    """Try segmentation by sections"""
    # This would be implemented similar to chapters
    return []

def _try_segment_by_roman(text: str) -> List[Dict[str, Any]]:
    """Try segmentation by Roman numerals"""
    roman_matches = list(ROMAN.finditer(text))
    if len(roman_matches) >= 2:
        return _segment_by_roman_advanced(text, roman_matches)
    return []

# Remove old _parse_points function as it's replaced by _parse_points_advanced

def _segment_fallback_advanced(text: str) -> List[Dict[str, Any]]:
    """Advanced fallback segmentation with better structure detection"""
    
    # Try to find any structure patterns
    lines = text.split('\n')
    structured_lines = []
    
    # Enhanced header detection patterns
    header_patterns = [
        r'^[IVXLCDM]+\.\s+.+',  # Roman numerals
        r'^\d+\.\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ].+',  # Numbered headers
        r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]{10,}$',  # All caps lines
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        is_header = False
        
        # Check header patterns
        for pattern in header_patterns:
            if re.match(pattern, line):
                is_header = True
                break
        
        # Check for common Vietnamese legal keywords
        if not is_header and len(line) < 100:
            keywords = ['MỤC TIÊU', 'YÊU CẦU', 'NHIỆM VỤ', 'QUY ĐỊNH', 'NGUYÊN TẮC', 
                       'PHẠM VI', 'ĐỐI TƯỢNG', 'GIẢI THÍCH', 'THI HÀNH']
            if any(keyword in line.upper() for keyword in keywords):
                is_header = True
        
        structured_lines.append({
            "type": "header" if is_header else "content",
            "text": line
        })
    
    # Group content by headers with better logic
    articles = []
    current_article = None
    
    for item in structured_lines:
        if item["type"] == "header":
            # Save previous article
            if current_article and current_article["clauses"]:
                articles.append(current_article)
            
            # Start new article
            current_article = {
                "section": f"Section_{len(articles) + 1}",
                "title": item["text"],
                "clauses": []
            }
        else:
            # Ensure we have an article to add content to
            if not current_article:
                current_article = {
                    "section": "General",
                    "title": "Document Content",
                    "clauses": []
                }
            
            # Try to parse as numbered clause first
            clause_match = re.match(r'^(\d+)\s*[\.\)]\s+(.+)', item["text"])
            if clause_match:
                # This is a numbered clause
                clause_num = clause_match.group(1)
                clause_text = clause_match.group(2)
                
                current_article["clauses"].append({
                    "no": clause_num,
                    "text": clause_text,
                    "points": []
                })
            else:
                # Add to existing clause or create new one
                if current_article["clauses"]:
                    current_article["clauses"][-1]["text"] += " " + item["text"]
                else:
                    current_article["clauses"].append({
                        "no": "1",
                        "text": item["text"],
                        "points": []
                    })
    
    # Add final article
    if current_article and current_article["clauses"]:
        articles.append(current_article)
    
    # Ultimate fallback - single article with all content
    if not articles:
        articles = [{
            "section": "Document",
            "title": "Full Content",
            "clauses": [{
                "no": "1",
                "text": text,
                "points": []
            }]
        }]
    
    return articles

def check_all_segmentation():
    """Kiểm tra toàn bộ segmentation results"""
    import os
    from collections import defaultdict
    
    print("KIỂM TRA TOÀN BỘ SEGMENTATION RESULTS")
    print("=" * 60)
    
    processed_files = [f for f in os.listdir('data/processed/') if f.endswith('.json')]
    print(f"Total processed files: {len(processed_files)}")
    
    # Statistics
    strategies = defaultdict(int)
    article_counts = defaultdict(int)
    
    # Structure types
    has_dieu_count = 0
    has_section_count = 0
    has_chapter_count = 0
    
    # Samples
    sample_dieu = []
    sample_section = []
    sample_chapter = []
    
    errors = []
    
    for i, filename in enumerate(processed_files):
        try:
            import json
            with open(f'data/processed/{filename}', 'r', encoding='utf-8') as f:
                doc = json.load(f)
            
            structure = doc.get('structure', {})
            strategy = structure.get('strategy_used', 'unknown')
            articles = structure.get('articles', [])
            
            strategies[strategy] += 1
            article_counts[len(articles)] += 1
            
            # Check for Điều structure
            has_dieu = False
            has_section = False
            has_chapter = False
            
            for article in articles:
                # Check for Điều
                if 'article' in article and 'Điều' in str(article.get('article', '')):
                    has_dieu = True
                    if len(sample_dieu) < 5:
                        sample_dieu.append({
                            'file': filename,
                            'article': article.get('article'),
                            'title': article.get('title', '')[:50] + '...'
                        })
                
                # Check for Section_
                if 'section' in article and str(article.get('section', '')).startswith('Section_'):
                    has_section = True
                    if len(sample_section) < 5:
                        sample_section.append({
                            'file': filename,
                            'section': article.get('section'),
                            'title': article.get('title', '')[:50] + '...'
                        })
                
                # Check for Chapter
                if 'chapter' in article:
                    has_chapter = True
                    if len(sample_chapter) < 5:
                        sample_chapter.append({
                            'file': filename,
                            'chapter': article.get('chapter'),
                            'title': article.get('title', '')[:50] + '...'
                        })
            
            if has_dieu:
                has_dieu_count += 1
            if has_section:
                has_section_count += 1
            if has_chapter:
                has_chapter_count += 1
            
            # Progress
            if (i + 1) % 200 == 0:
                print(f"   Processed {i + 1}/{len(processed_files)} files...")
                
        except Exception as e:
            errors.append((filename, str(e)))
    
    # Print results
    print(f"\nKET QUA KIEM TRA:")
    print(f"Files processed: {len(processed_files)}")
    print(f"Files co loi: {len(errors)}")
    
    print(f"\nSTRATEGIES SU DUNG:")
    for strategy, count in sorted(strategies.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(processed_files) * 100
        print(f"  {strategy}: {count} files ({percentage:.1f}%)")
    
    print(f"\nCAU TRUC PHAT HIEN:")
    print(f"  Files co Dieu: {has_dieu_count} ({has_dieu_count/len(processed_files)*100:.1f}%)")
    print(f"  Files co Section_: {has_section_count} ({has_section_count/len(processed_files)*100:.1f}%)")
    print(f"  Files co Chapter: {has_chapter_count} ({has_chapter_count/len(processed_files)*100:.1f}%)")
    
    print(f"\nPHAN BO SO ARTICLES:")
    for count, files in sorted(article_counts.items())[:10]:
        print(f"  {count} articles: {files} files")
    
    if sample_dieu:
        print(f"\nSAMPLE DIEU STRUCTURE:")
        for sample in sample_dieu:
            print(f"  {sample['file']}: {sample['article']} - {sample['title']}")
    
    if sample_section:
        print(f"\nSAMPLE SECTION STRUCTURE:")
        for sample in sample_section:
            print(f"  {sample['file']}: {sample['section']} - {sample['title']}")
    
    if sample_chapter:
        print(f"\nSAMPLE CHAPTER STRUCTURE:")
        for sample in sample_chapter:
            print(f"  {sample['file']}: {sample['chapter']} - {sample['title']}")
    
    if errors:
        print(f"\nLOI:")
        for filename, error in errors[:5]:
            print(f"  {filename}: {error}")
    
    # Summary
    print(f"\nTOM TAT:")
    success_rate = (len(processed_files) - len(errors)) / len(processed_files) * 100
    dieu_rate = has_dieu_count / len(processed_files) * 100
    
    print(f"  Processing success: {success_rate:.1f}%")
    print(f"  Dieu detection rate: {dieu_rate:.1f}%")
    
    if dieu_rate >= 30:
        print(f"  GOOD: Nhieu van ban duoc tach dung cau truc Dieu")
    elif dieu_rate >= 10:
        print(f"  FAIR: Mot so van ban duoc tach dung cau truc Dieu")
    else:
        print(f"  POOR: It van ban duoc tach dung cau truc Dieu")

if __name__ == "__main__":
    # Test segmentation on sample text
    sample_text = """
    Điều 1. Phạm vi điều chỉnh
    Thông tư này quy định về...
    
    Điều 2. Đối tượng áp dụng
    Thông tư này áp dụng cho...
    """
    
    result = segment(sample_text)
    print("Sample segmentation result:")
    print(f"Articles: {len(result.get('articles', []))}")
    for i, article in enumerate(result.get('articles', [])):
        if 'article' in article:
            print(f"  {i+1}. {article.get('article')}: {article.get('title', '')}")