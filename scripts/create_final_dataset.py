#!/usr/bin/env python3
"""
CREATE FINAL DATASET - SIMPLIFIED VERSION
========================================

Script để tạo dataset cuối cùng từ raw data với metadata đã được fix
Dataset structure: number, issue_date, agency, url, content, field
Note: Title field đã được xóa khỏi dataset
"""

import json
import re
from datetime import datetime

def extract_date_from_content(content):
    """Extract issue date from document content"""
    if not content:
        return None
    
    # Look for date patterns in Vietnamese legal documents
    date_patterns = [
        r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        r'(\d{1,2})-(\d{1,2})-(\d{4})',
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            try:
                if 'tháng' in pattern:
                    day, month, year = match.groups()
                else:
                    day, month, year = match.groups()
                
                day, month, year = int(day), int(month), int(year)
                
                # Validate date
                if (1 <= day <= 31 and 1 <= month <= 12 and 1990 <= year <= 2025):
                    return f"{day:02d}/{month:02d}/{year}"
            except:
                continue
    
    return None

def extract_agency_from_content(content):
    """Extract issuing agency from document content"""
    if not content:
        return None
    
    # Look for agency patterns
    agency_patterns = [
        r'(BỘ [A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+?)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
        r'(ỦY BAN [A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+?)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
        r'(CHÍNH PHỦ)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
        r'(QUỐC HỘI)(?=\s*[-]{3,}|\s*CỘNG HÒA|\r|\n)',
    ]
    
    for pattern in agency_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            agency = match.group(1).strip()
            agency = re.sub(r'\s+', ' ', agency)
            
            if len(agency) >= 8 and len(agency) <= 60:
                return agency
    
    return None

def extract_document_number(content):
    """Extract document number from content"""
    if not content:
        return None
    
    # Look for document number patterns
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
    
    return None

def create_final_dataset():
    """Create final dataset from source data"""
    
    print("CREATING FINAL DATASET")
    print("=" * 50)
    
    # Load source data
    source_file = "data/raw/all_traffic_documents_debug_fixed.json"
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        print(f"Source file not found: {source_file}")
        return
    
    source_docs = source_data.get('documents', [])
    print(f"Source documents: {len(source_docs)}")
    
    # Process documents
    final_docs = []
    processed_count = 0
    skipped_count = 0
    
    for i, doc in enumerate(source_docs):
        content = doc.get('content', '')
        url = doc.get('url', '')
        
        # Skip documents without content
        if not content or len(content) < 100:
            skipped_count += 1
            continue
        
        # Extract metadata from content
        number = extract_document_number(content) or doc.get('number', 'Không xác định')
        issue_date = extract_date_from_content(content) or doc.get('issue_date', 'Không xác định')
        agency = extract_agency_from_content(content) or doc.get('agency', 'Không xác định')
        field = doc.get('field', 'Giao thông')
        
        # Clean field if it's JSON schema
        if field and len(field) > 100:
            field = "Giao thông"
        
        # Create final document (without title)
        final_doc = {
            'url': url,
            'crawl_time': doc.get('crawl_time', datetime.now().isoformat()),
            'number': number,
            'field': field,
            'issue_date': issue_date,
            'agency': agency,
            'content': content
        }
        
        final_docs.append(final_doc)
        processed_count += 1
        
        if processed_count % 200 == 0:
            print(f"   Processed {processed_count} documents...")
    
    # Create final dataset
    final_dataset = {
        'documents': final_docs,
        'total_documents': len(final_docs),
        'created_at': datetime.now().isoformat(),
        'source_file': source_file,
        'processing_notes': [
            'Title field removed (not required by test)',
            'Metadata extracted from document content',
            'Documents without content skipped',
            'Field values simplified from JSON schema'
        ]
    }
    
    # Save final dataset
    output_file = "data/raw/final_perfect_dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\nFINAL DATASET CREATED:")
    print(f"   Processed: {processed_count} documents")
    print(f"   Skipped: {skipped_count} documents")
    print(f"   Output: {output_file}")
    print(f"   Structure: number, issue_date, agency, url, content, field")
    
    return processed_count

def main():
    """Main function"""
    
    try:
        processed_count = create_final_dataset()
        
        if processed_count > 0:
            print(f"\nRunning validation...")
            import subprocess
            try:
                result = subprocess.run(['python3', 'scripts/validate_metadata.py'], 
                                      capture_output=True, text=True)
                print(result.stdout)
            except:
                print("Could not run validation automatically")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()