#!/usr/bin/env python3
"""
METADATA FIXING SCRIPT - SIMPLIFIED VERSION
==========================================

Script để fix metadata của dataset legal documents:
- Field: Fix JSON schema thành giá trị đơn giản  
- Number: Fix document number không đúng format
- Agency: Fix agency bị sai/chứa thông tin thừa
- Remove: Loại bỏ effective_date không chính xác

Note: Title field đã được xóa khỏi dataset
"""

import json
import re

def extract_field_from_schema(field_value):
    """Fix field value từ JSON schema thành giá trị đơn giản"""
    if not field_value or not isinstance(field_value, str):
        return "Giao thông"
    
    # Nếu đã là giá trị đơn giản, return luôn
    if len(field_value) < 100 and not field_value.startswith('"http://schema.org"'):
        return field_value
    
    # Extract từ JSON schema
    try:
        headline_match = re.search(r'"headline":\s*"([^"]+)"', field_value)
        if headline_match:
            headline = headline_match.group(1)
            
            # Phân loại dựa trên nội dung headline
            if any(keyword in headline.lower() for keyword in ['giao thông', 'vận tải', 'đường bộ', 'an toàn']):
                return "Giao thông"
            elif any(keyword in headline.lower() for keyword in ['xây dựng', 'kiến trúc']):
                return "Xây dựng"
            elif any(keyword in headline.lower() for keyword in ['tài chính', 'ngân sách']):
                return "Tài chính"
            elif any(keyword in headline.lower() for keyword in ['y tế', 'sức khỏe']):
                return "Y tế"
            elif any(keyword in headline.lower() for keyword in ['giáo dục', 'đào tạo']):
                return "Giáo dục"
            else:
                return "Giao thông"
    except:
        pass
    
    return "Giao thông"

def fix_document_number(doc_number, content):
    """Fix document number không đúng format"""
    if not content:
        return doc_number
    
    # Tìm số hiệu đúng trong content
    number_patterns = [
        r'Số:\s*([^\s\r\n]+)',
        r'(\d+/[A-Z\-ĐQD]+)',
        r'(\d+/\d{4}/[A-Z\-ĐQD]+)',
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, content)
        if matches:
            candidate = matches[0].strip()
            # Validate candidate
            if (len(candidate) >= 5 and 
                re.search(r'\d+', candidate) and 
                re.search(r'[A-ZĐ]', candidate)):
                return candidate
    
    # Fix số hiệu hiện tại nếu không tìm thấy trong content
    if doc_number:
        # Fix các format đặc biệt
        special_fixes = {
            r'(\d+)/ĐKVN-VAR': r'\1/ĐKVN-BGTVT',
            r'(\d+)/ĐK': r'\1/QĐ-BGTVT',
        }
        
        for pattern, replacement in special_fixes.items():
            if re.match(pattern, doc_number):
                return re.sub(pattern, replacement, doc_number)
        
        # Fix số hiệu ngắn
        if len(doc_number) < 5:
            if re.match(r'^\d+$', doc_number):
                return f"{doc_number}/QĐ-UBND"
            elif '/' not in doc_number:
                return f"{doc_number}/QĐ"
        
        # Fix thiếu chữ cái
        if not re.search(r'[A-ZĐ]', doc_number):
            if 'QD' not in doc_number.upper():
                return f"{doc_number}/QĐ"
    
    return doc_number

def extract_agency_from_content(content):
    """Extract agency từ nội dung văn bản"""
    if not content:
        return None
    
    # Patterns để tìm agency trong văn bản pháp luật Việt Nam
    agency_patterns = [
        r'((?:BỘ|ỦY BAN|CHÍNH PHỦ|QUỐC HỘI|TÒA ÁN|VIỆN KIỂM SÁT|VĂN PHÒNG)[^\r\n]{5,80}?)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
        r'((?:UBND|UB NHÂN DÂN)[^\r\n]{5,60}?)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
        r'((?:SỞ|CỤC|THANH TRA)[^\r\n]{5,60}?)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
    ]
    
    for pattern in agency_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            agency = match.group(1).strip()
            agency = re.sub(r'\s+', ' ', agency)
            
            if len(agency) >= 8 and len(agency) <= 80:
                return agency
    
    return None

def fix_agency(current_agency, content):
    """Fix agency bằng cách extract từ content và làm sạch"""
    if not content:
        return current_agency
    
    # Thử extract agency từ content
    extracted_agency = extract_agency_from_content(content)
    
    if extracted_agency:
        # Làm sạch extracted agency
        extracted_agency = extracted_agency.strip()
        
        # Loại bỏ các prefix không thuộc tên agency
        prefixes_to_remove = [
            r'^VỀ\s+',
            r'^QUYẾT ĐỊNH\s+',
            r'^THÔNG TƯ\s+',
            r'^NGHỊ ĐỊNH\s+',
        ]
        
        for prefix in prefixes_to_remove:
            extracted_agency = re.sub(prefix, '', extracted_agency, flags=re.IGNORECASE)
        
        # Loại bỏ tên người và title khỏi agency
        person_patterns = [
            r'TRẦN HỒNG HÀ.*',
            r'NGUYỄN.*',
            r'LÊ.*',
            r'PHẠM.*',
            r'VỀ ĐỀ XUẤT.*',
            r'KÉO DÀI THỜI GIAN.*',
        ]
        
        for pattern in person_patterns:
            extracted_agency = re.sub(pattern, '', extracted_agency, flags=re.IGNORECASE)
        
        extracted_agency = extracted_agency.strip()
        
        # Validate extracted agency
        if (len(extracted_agency) >= 8 and 
            len(extracted_agency) <= 60 and
            not re.match(r'^[0-9\s\-/]+$', extracted_agency)):
            return extracted_agency
    
    # Fix agency hiện tại nếu extraction thất bại
    if current_agency:
        # Kiểm tra agency có vấn đề không
        problematic_patterns = [
            r'VỀ\s+',
            r'TRẦN HỒNG HÀ',
            r'ĐỀ XUẤT',
            r'QUYẾT ĐỊNH.*VỀ',
            r'KÉO DÀI THỜI GIAN',
        ]
        
        is_problematic = any(re.search(pattern, current_agency, re.IGNORECASE) 
                           for pattern in problematic_patterns)
        
        # Kiểm tra agency quá dài
        if len(current_agency) > 60:
            is_problematic = True
        
        if is_problematic:
            # Extract chỉ phần agency
            agency_keywords = [
                r'(VĂN PHÒNG CHÍNH PHỦ)',
                r'(BỘ [A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+)',
                r'(ỦY BAN [A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+)',
                r'(CHÍNH PHỦ)',
                r'(QUỐC HỘI)',
            ]
            
            for keyword_pattern in agency_keywords:
                match = re.search(keyword_pattern, current_agency, re.IGNORECASE)
                if match:
                    clean_agency = match.group(1).strip()
                    if len(clean_agency) >= 8:
                        return clean_agency
    
    return current_agency

def fix_all_metadata(file_path):
    """
    MAIN FUNCTION: Fix toàn bộ metadata của dataset
    
    Returns:
        tuple: (field_fixes, number_fixes, agency_fixes, effective_date_removed)
    """
    print(f"FIXING METADATA: {file_path}")
    print("=" * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    total_docs = len(documents)
    
    print(f"Processing {total_docs} documents...")
    
    # Counters
    field_fixed_count = 0
    number_fixed_count = 0
    agency_fixed_count = 0
    effective_date_removed = 0
    
    for i, doc in enumerate(documents):
        # Fix field (JSON schema → simple value)
        current_field = doc.get('field', '')
        if current_field and (len(current_field) > 100 or 'schema.org' in current_field):
            fixed_field = extract_field_from_schema(current_field)
            if fixed_field != current_field:
                doc['field'] = fixed_field
                field_fixed_count += 1
        
        # Fix document number
        current_number = doc.get('number', '')
        content = doc.get('content', '')
        if current_number:
            fixed_number = fix_document_number(current_number, content)
            if fixed_number != current_number:
                doc['number'] = fixed_number
                number_fixed_count += 1
        
        # Fix agency
        current_agency = doc.get('agency', '')
        if current_agency:
            fixed_agency = fix_agency(current_agency, content)
            if fixed_agency != current_agency:
                doc['agency'] = fixed_agency
                agency_fixed_count += 1
        
        # Remove effective_date if exists (không chính xác)
        if 'effective_date' in doc:
            del doc['effective_date']
            effective_date_removed += 1
        
        # Progress
        if (i + 1) % 200 == 0:
            print(f"   Processed {i + 1}/{total_docs} documents...")
    
    # Save fixed data
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Report results
    print(f"\nFIXING RESULTS:")
    print(f"   Field fixes: {field_fixed_count}")
    print(f"   Number fixes: {number_fixed_count}")
    print(f"   Agency fixes: {agency_fixed_count}")
    print(f"   Effective_date removed: {effective_date_removed}")
    print(f"   Total documents: {total_docs}")
    
    return field_fixed_count, number_fixed_count, agency_fixed_count, effective_date_removed

def main():
    """Main function"""
    file_path = "data/raw/final_perfect_dataset.json"
    
    try:
        field_fixes, number_fixes, agency_fixes, effective_date_removed = fix_all_metadata(file_path)
        
        print(f"\nSUCCESS: Fixed metadata for dataset")
        print(f"Dataset structure: number, issue_date, agency, url, content, field")
        
        # Run validation
        print(f"\nRunning validation...")
        import subprocess
        try:
            result = subprocess.run(['python3', 'scripts/validate_metadata.py'], 
                                  capture_output=True, text=True)
            print(result.stdout)
        except:
            print("Could not run validation automatically")
            
    except FileNotFoundError:
        print(f"Error: File {file_path} not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()