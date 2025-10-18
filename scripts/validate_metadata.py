#!/usr/bin/env python3
"""
Script để validate chi tiết chất lượng metadata
Kiểm tra từng field để đảm bảo 100% accuracy
"""

import json
import re
from collections import defaultdict

def validate_document_number(number):
    """Validate document number format"""
    if not number or number == "Không xác định":
        return False, "Missing or undefined"
    
    # Check minimum length
    if len(number) < 5:
        return False, "Too short"
    
    # Check for proper format (number + letters)
    if not re.search(r'\d+.*[A-Z]', number):
        return False, "Invalid format (should have numbers and letters)"
    
    # Check for common patterns
    valid_patterns = [
        r'\d+/\d{4}/[A-Z-]+',  # 01/2024/QĐ-UBND
        r'\d+/[A-Z-]+',        # 689/KH-UBATGTQG
        r'\d+/\d{4}/[A-Z]+\d*', # 36/2024/QH15
    ]
    
    for pattern in valid_patterns:
        if re.match(pattern, number):
            return True, "Valid format"
    
    return False, f"Unusual format: {number}"

def validate_title(title):
    """Title field has been removed from dataset"""
    return True, "Title field removed - not validated"

def validate_issue_date(date):
    """Validate issue date format"""
    if not date or date == "Không xác định":
        return False, "Missing or undefined"
    
    # Check for DD/MM/YYYY format
    if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', date):
        return False, f"Invalid format: {date}"
    
    # Parse and validate date components
    try:
        parts = date.split('/')
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        
        if not (1 <= day <= 31):
            return False, f"Invalid day: {day}"
        if not (1 <= month <= 12):
            return False, f"Invalid month: {month}"
        if not (1990 <= year <= 2025):
            return False, f"Invalid year: {year}"
            
    except (ValueError, IndexError):
        return False, f"Cannot parse date: {date}"
    
    return True, "Valid date"

def validate_agency(agency):
    """Validate issuing agency"""
    if not agency or agency == "Không xác định":
        return False, "Missing or undefined"
    
    # Check minimum length
    if len(agency) < 5:
        return False, "Too short"
    
    # Check for generic/invalid agencies
    invalid_agencies = ["unknown", "n/a", "không rõ", "chưa xác định"]
    if any(invalid.lower() in agency.lower() for invalid in invalid_agencies):
        return False, f"Invalid agency: {agency}"
    
    return True, "Valid agency"

def validate_metadata_quality(file_path):
    """Validate toàn bộ chất lượng metadata"""
    
    print(f"Validating metadata quality: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    total_docs = len(documents)
    
    print(f"Total documents to validate: {total_docs}")
    
    # Validation results
    results = {
        'total_documents': total_docs,
        'field_validation': {
            'number': {'valid': 0, 'invalid': 0, 'issues': []},
            'title': {'valid': 0, 'invalid': 0, 'issues': []},
            'issue_date': {'valid': 0, 'invalid': 0, 'issues': []},
            'agency': {'valid': 0, 'invalid': 0, 'issues': []}
        },
        'perfect_documents': 0,
        'problematic_documents': []
    }
    
    # Validate each document
    for i, doc in enumerate(documents):
        doc_issues = []
        
        # Validate document number
        number = doc.get('number', '')
        is_valid, reason = validate_document_number(number)
        if is_valid:
            results['field_validation']['number']['valid'] += 1
        else:
            results['field_validation']['number']['invalid'] += 1
            results['field_validation']['number']['issues'].append(f"Doc {i+1}: {reason}")
            doc_issues.append(f"number: {reason}")
        
        # Title field has been removed - skip validation
        results['field_validation']['title']['valid'] += 1
        
        # Validate issue date
        issue_date = doc.get('issue_date', '')
        is_valid, reason = validate_issue_date(issue_date)
        if is_valid:
            results['field_validation']['issue_date']['valid'] += 1
        else:
            results['field_validation']['issue_date']['invalid'] += 1
            results['field_validation']['issue_date']['issues'].append(f"Doc {i+1}: {reason}")
            doc_issues.append(f"issue_date: {reason}")
        
        # Validate agency
        agency = doc.get('agency', '')
        is_valid, reason = validate_agency(agency)
        if is_valid:
            results['field_validation']['agency']['valid'] += 1
        else:
            results['field_validation']['agency']['invalid'] += 1
            results['field_validation']['agency']['issues'].append(f"Doc {i+1}: {reason}")
            doc_issues.append(f"agency: {reason}")
        
        # Check if document is perfect
        if not doc_issues:
            results['perfect_documents'] += 1
        else:
            results['problematic_documents'].append({
                'index': i + 1,
                'url': doc.get('url', '')[:80] + '...',
                'issues': doc_issues
            })
    
    return results

def print_validation_report(results):
    """In báo cáo validation chi tiết"""
    
    total = results['total_documents']
    perfect = results['perfect_documents']
    problematic = len(results['problematic_documents'])
    
    print(f"\nMETADATA VALIDATION REPORT")
    print("=" * 60)
    
    print(f"Overall Quality:")
    print(f"   - Total documents: {total}")
    print(f"   - Perfect metadata: {perfect} ({perfect/total*100:.1f}%)")
    print(f"   - Problematic: {problematic} ({problematic/total*100:.1f}%)")
    
    print(f"\nField-by-Field Analysis:")
    for field, stats in results['field_validation'].items():
        valid = stats['valid']
        invalid = stats['invalid']
        accuracy = valid / total * 100 if total > 0 else 0
        
        status = "PASS" if accuracy == 100 else "WARN" if accuracy >= 95 else "FAIL"
        
        # Special handling for title field
        if field == 'title':
            print(f"   [SKIP] {field}: Field removed from dataset")
        else:
            print(f"   [{status}] {field}: {valid}/{total} ({accuracy:.1f}% accurate)")
            
            if invalid > 0:
                print(f"      Issues: {invalid} documents")
    
    print(f"\nQuality Assessment:")
    overall_accuracy = perfect / total * 100 if total > 0 else 0
    
    if overall_accuracy == 100:
        print(f"   PERFECT: 100% metadata accuracy!")
    elif overall_accuracy >= 95:
        print(f"   EXCELLENT: {overall_accuracy:.1f}% accuracy")
    elif overall_accuracy >= 90:
        print(f"   GOOD: {overall_accuracy:.1f}% accuracy")
    elif overall_accuracy >= 80:
        print(f"   ACCEPTABLE: {overall_accuracy:.1f}% accuracy")
    else:
        print(f"   POOR: {overall_accuracy:.1f}% accuracy - Cần cải thiện")

def show_sample_issues(results, num_samples=5):
    """Hiển thị sample issues"""
    
    if not results['problematic_documents']:
        print(f"\nNO ISSUES FOUND - All metadata is perfect!")
        return
    
    print(f"\nSample Issues (showing {min(num_samples, len(results['problematic_documents']))} examples):")
    print("-" * 60)
    
    for i, doc in enumerate(results['problematic_documents'][:num_samples]):
        print(f"\n[ISSUE] Document #{doc['index']}:")
        print(f"   URL: {doc['url']}")
        for issue in doc['issues']:
            print(f"   - {issue}")

def main():
    """Main function"""
    
    print("METADATA QUALITY VALIDATOR")
    print("Kiểm tra chi tiết chất lượng metadata của final dataset")
    print("=" * 60)
    
    file_path = "data/raw/final_perfect_dataset.json"
    
    try:
        # Validate metadata
        results = validate_metadata_quality(file_path)
        
        # Print report
        print_validation_report(results)
        
        # Show sample issues
        show_sample_issues(results)
        
        # Final summary
        perfect_pct = results['perfect_documents'] / results['total_documents'] * 100
        print(f"\nFINAL VERDICT:")
        if perfect_pct == 100:
            print(f"   PERFECT METADATA: 100% accuracy!")
            print(f"   Ready for evaluation!")
        else:
            print(f"   Metadata accuracy: {perfect_pct:.1f}%")
            print(f"   {len(results['problematic_documents'])} documents need attention")
        
    except FileNotFoundError:
        print(f"Error: File {file_path} not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()