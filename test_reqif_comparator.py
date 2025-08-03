#!/usr/bin/env python3
"""
Test script for ReqIF Comparator

This script demonstrates how to use the ReqIF comparator with example files,
including support for .reqifz compressed files.
"""

import os
import tempfile
import zipfile
from reqif_comparator import ReqIFComparator


def create_sample_reqif_files():
    """Create sample ReqIF files for testing."""
    
    # Sample ReqIF file 1
    reqif1_content = '''<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
    <THE-HEADER>
        <REQ-IF-TOOL-ID>Sample Tool 1</REQ-IF-TOOL-ID>
        <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
        <SOURCE-TOOL-ID>Test Generator</SOURCE-TOOL-ID>
        <TITLE>Sample Requirements Document 1</TITLE>
    </THE-HEADER>
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPECIFICATIONS>
                <SPECIFICATION IDENTIFIER="REQ-001" LAST-CHANGE="2024-01-01T10:00:00Z">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System shall provide user authentication">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="REQ-DESC"/>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                    </VALUES>
                </SPECIFICATION>
                <SPECIFICATION IDENTIFIER="REQ-002" LAST-CHANGE="2024-01-01T11:00:00Z">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System shall support password reset">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="REQ-DESC"/>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                    </VALUES>
                </SPECIFICATION>
            </SPECIFICATIONS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>'''
    
    # Sample ReqIF file 2 (with some differences)
    reqif2_content = '''<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
    <THE-HEADER>
        <REQ-IF-TOOL-ID>Sample Tool 2</REQ-IF-TOOL-ID>
        <REQ-IF-VERSION>1.1</REQ-IF-VERSION>
        <SOURCE-TOOL-ID>Test Generator</SOURCE-TOOL-ID>
        <TITLE>Sample Requirements Document 2</TITLE>
    </THE-HEADER>
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPECIFICATIONS>
                <SPECIFICATION IDENTIFIER="REQ-001" LAST-CHANGE="2024-01-01T10:00:00Z">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System shall provide enhanced user authentication">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="REQ-DESC"/>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                    </VALUES>
                </SPECIFICATION>
                <SPECIFICATION IDENTIFIER="REQ-003" LAST-CHANGE="2024-01-01T12:00:00Z">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System shall support multi-factor authentication">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="REQ-DESC"/>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                    </VALUES>
                </SPECIFICATION>
            </SPECIFICATIONS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.reqif', delete=False, encoding='utf-8') as f1:
        f1.write(reqif1_content)
        file1_path = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.reqif', delete=False, encoding='utf-8') as f2:
        f2.write(reqif2_content)
        file2_path = f2.name
    
    return file1_path, file2_path


def create_sample_reqifz_files():
    """Create sample .reqifz compressed files for testing."""
    
    # Create regular ReqIF files first
    file1_path, file2_path = create_sample_reqif_files()
    
    # Create .reqifz files
    reqifz1_path = file1_path.replace('.reqif', '.reqifz')
    reqifz2_path = file2_path.replace('.reqif', '.reqifz')
    
    # Create ZIP archives
    with zipfile.ZipFile(reqifz1_path, 'w', zipfile.ZIP_DEFLATED) as zip1:
        zip1.write(file1_path, os.path.basename(file1_path))
    
    with zipfile.ZipFile(reqifz2_path, 'w', zipfile.ZIP_DEFLATED) as zip2:
        zip2.write(file2_path, os.path.basename(file2_path))
    
    # Clean up the original .reqif files
    os.unlink(file1_path)
    os.unlink(file2_path)
    
    return reqifz1_path, reqifz2_path


def test_reqif_comparator():
    """Test the ReqIF comparator with sample files."""
    print("Testing with regular .reqif files...")
    print("=" * 50)
    
    # Test with regular .reqif files
    file1, file2 = create_sample_reqif_files()
    
    print(f"Sample file 1: {file1}")
    print(f"Sample file 2: {file2}")
    print()
    
    # Create comparator
    comparator = ReqIFComparator(file1, file2)
    
    # Generate and display report
    print("Generating comparison report...")
    report = comparator.generate_diff_report()
    print(report)
    
    # Clean up
    comparator.cleanup_temp_files()
    try:
        os.unlink(file1)
        os.unlink(file2)
    except Exception as e:
        print(f"Warning: Could not clean up temporary files: {e}")
    
    print("\n" + "=" * 50)
    print("Testing with .reqifz compressed files...")
    print("=" * 50)
    
    # Test with .reqifz files
    reqifz1, reqifz2 = create_sample_reqifz_files()
    
    print(f"Sample .reqifz file 1: {reqifz1}")
    print(f"Sample .reqifz file 2: {reqifz2}")
    print()
    
    # Create comparator for .reqifz files
    comparator_z = ReqIFComparator(reqifz1, reqifz2)
    
    # Generate and display report
    print("Generating comparison report for .reqifz files...")
    report_z = comparator_z.generate_diff_report()
    print(report_z)
    
    # Clean up
    comparator_z.cleanup_temp_files()
    try:
        os.unlink(reqifz1)
        os.unlink(reqifz2)
        print("\nTemporary files cleaned up.")
    except Exception as e:
        print(f"Warning: Could not clean up temporary files: {e}")


if __name__ == "__main__":
    test_reqif_comparator() 