#!/usr/bin/env python3
"""
ReqIF File Comparator

This tool compares two ReqIF (Requirements Interchange Format) files and provides
detailed analysis of their differences in structure, content, and metadata.

Features:
- XML structure comparison
- Content differences analysis
- Metadata comparison
- Requirements tracking
- Visual diff output
- Support for .reqifz compressed files
"""

import xml.etree.ElementTree as ET
import difflib
import argparse
import sys
import os
import zipfile
import tempfile
from typing import Dict, List, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class ReqIFElement:
    """Represents a ReqIF element with its attributes and content."""
    tag: str
    attributes: Dict[str, str]
    content: str
    children: List['ReqIFElement']
    xpath: str


class ReqIFComparator:
    """Main class for comparing ReqIF files."""
    
    def __init__(self, file1: str, file2: str):
        self.file1 = file1
        self.file2 = file2
        self.tree1 = None
        self.tree2 = None
        self.root1 = None
        self.root2 = None
        self.temp_files = []  # Track temporary files for cleanup
        
    def extract_reqif_from_zip(self, zip_path: str) -> str:
        """Extract ReqIF XML file from .reqifz archive."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Look for .reqif or .xml files in the archive
                reqif_files = [f for f in zip_ref.namelist() if f.endswith(('.reqif', '.xml'))]
                
                if not reqif_files:
                    raise ValueError(f"No ReqIF XML files found in {zip_path}")
                
                # Use the first ReqIF file found
                reqif_file = reqif_files[0]
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.reqif', delete=False)
                self.temp_files.append(temp_file.name)
                
                # Extract and write to temporary file
                with zip_ref.open(reqif_file) as source:
                    temp_file.write(source.read())
                    temp_file.close()
                
                return temp_file.name
                
        except zipfile.BadZipFile:
            raise ValueError(f"{zip_path} is not a valid ZIP file")
        except Exception as e:
            raise ValueError(f"Error extracting from {zip_path}: {e}")
    
    def get_reqif_file_path(self, file_path: str) -> str:
        """Get the actual ReqIF XML file path, handling both .reqif and .reqifz files."""
        if file_path.lower().endswith('.reqifz'):
            return self.extract_reqif_from_zip(file_path)
        else:
            return file_path
        
    def load_files(self) -> bool:
        """Load and parse both ReqIF files."""
        try:
            # Handle .reqifz files
            reqif_file1 = self.get_reqif_file_path(self.file1)
            reqif_file2 = self.get_reqif_file_path(self.file2)
            
            self.tree1 = ET.parse(reqif_file1)
            self.tree2 = ET.parse(reqif_file2)
            self.root1 = self.tree1.getroot()
            self.root2 = self.tree2.getroot()
            return True
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            return False
        except FileNotFoundError as e:
            print(f"File not found: {e}")
            return False
        except ValueError as e:
            print(f"Error processing file: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass  # Ignore cleanup errors
        self.temp_files.clear()
    
    def extract_elements(self, root: ET.Element, xpath: str = "") -> List[ReqIFElement]:
        """Extract all elements from the XML tree with their attributes and content."""
        elements = []
        
        for child in root:
            current_xpath = f"{xpath}/{child.tag}" if xpath else child.tag
            
            # Get attributes
            attributes = {k: v for k, v in child.attrib.items()}
            
            # Get text content
            content = child.text.strip() if child.text else ""
            
            # Recursively get children
            children = self.extract_elements(child, current_xpath)
            
            element = ReqIFElement(
                tag=child.tag,
                attributes=attributes,
                content=content,
                children=children,
                xpath=current_xpath
            )
            elements.append(element)
            
            # Add children to the list
            elements.extend(children)
        
        return elements
    
    def compare_structure(self) -> Dict[str, Any]:
        """Compare the structure of both ReqIF files."""
        elements1 = self.extract_elements(self.root1)
        elements2 = self.extract_elements(self.root2)
        
        # Get unique tags
        tags1 = {elem.tag for elem in elements1}
        tags2 = {elem.tag for elem in elements2}
        
        # Get unique xpaths
        xpaths1 = {elem.xpath for elem in elements1}
        xpaths2 = {elem.xpath for elem in elements2}
        
        return {
            'tags_only_in_file1': tags1 - tags2,
            'tags_only_in_file2': tags2 - tags1,
            'common_tags': tags1 & tags2,
            'xpaths_only_in_file1': xpaths1 - xpaths2,
            'xpaths_only_in_file2': xpaths2 - xpaths1,
            'common_xpaths': xpaths1 & xpaths2
        }
    
    def compare_content(self) -> Dict[str, Any]:
        """Compare the content of both ReqIF files."""
        elements1 = self.extract_elements(self.root1)
        elements2 = self.extract_elements(self.root2)
        
        # Create dictionaries for easy lookup
        elements1_dict = {elem.xpath: elem for elem in elements1}
        elements2_dict = {elem.xpath: elem for elem in elements2}
        
        differences = {
            'content_differences': [],
            'attribute_differences': [],
            'missing_elements': [],
            'extra_elements': []
        }
        
        # Compare common elements
        common_xpaths = set(elements1_dict.keys()) & set(elements2_dict.keys())
        
        for xpath in common_xpaths:
            elem1 = elements1_dict[xpath]
            elem2 = elements2_dict[xpath]
            
            # Compare content
            if elem1.content != elem2.content:
                differences['content_differences'].append({
                    'xpath': xpath,
                    'file1_content': elem1.content,
                    'file2_content': elem2.content
                })
            
            # Compare attributes
            if elem1.attributes != elem2.attributes:
                differences['attribute_differences'].append({
                    'xpath': xpath,
                    'file1_attributes': elem1.attributes,
                    'file2_attributes': elem2.attributes
                })
        
        # Find missing and extra elements
        differences['missing_elements'] = list(set(elements2_dict.keys()) - set(elements1_dict.keys()))
        differences['extra_elements'] = list(set(elements1_dict.keys()) - set(elements2_dict.keys()))
        
        return differences
    
    def compare_requirements(self) -> Dict[str, Any]:
        """Specifically compare requirements between the two files."""
        # Look for requirement-related elements
        req_elements1 = self.find_requirement_elements(self.root1)
        req_elements2 = self.find_requirement_elements(self.root2)
        
        return {
            'requirements_file1': req_elements1,
            'requirements_file2': req_elements2,
            'requirement_differences': self.compare_requirement_lists(req_elements1, req_elements2)
        }
    
    def find_requirement_elements(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Find all requirement-related elements in the XML tree."""
        requirements = []
        
        # Common ReqIF requirement element names
        req_tags = ['REQ-IF-REQ', 'REQ-IF-REQ-IF', 'SPEC-OBJECT', 'SPECIFICATION', 'REQUIREMENT']
        
        for elem in root.iter():
            if any(req_tag in elem.tag.upper() for req_tag in req_tags):
                req_info = {
                    'tag': elem.tag,
                    'xpath': self.get_xpath(elem),
                    'attributes': elem.attrib,
                    'content': elem.text.strip() if elem.text else "",
                    'children': [child.tag for child in elem]
                }
                requirements.append(req_info)
        
        return requirements
    
    def get_xpath(self, element: ET.Element) -> str:
        """Get the XPath of an element."""
        path_parts = []
        current = element
        
        while current is not None:
            if current.tag:
                path_parts.append(current.tag)
            current = current.getparent() if hasattr(current, 'getparent') else None
        
        return '/' + '/'.join(reversed(path_parts))
    
    def compare_requirement_lists(self, reqs1: List[Dict], reqs2: List[Dict]) -> Dict[str, Any]:
        """Compare two lists of requirements."""
        # Create lookup dictionaries
        reqs1_dict = {req['xpath']: req for req in reqs1}
        reqs2_dict = {req['xpath']: req for req in reqs2}
        
        return {
            'only_in_file1': [req for xpath, req in reqs1_dict.items() if xpath not in reqs2_dict],
            'only_in_file2': [req for xpath, req in reqs2_dict.items() if xpath not in reqs1_dict],
            'common_requirements': [xpath for xpath in reqs1_dict.keys() if xpath in reqs2_dict]
        }
    
    def generate_diff_report(self) -> str:
        """Generate a comprehensive diff report."""
        if not self.load_files():
            return "Failed to load ReqIF files."
        
        report = []
        report.append("=" * 80)
        report.append("REQIF FILE COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"File 1: {self.file1}")
        report.append(f"File 2: {self.file2}")
        report.append("")
        
        # Structure comparison
        structure_diff = self.compare_structure()
        report.append("STRUCTURE COMPARISON")
        report.append("-" * 40)
        report.append(f"Tags only in File 1: {len(structure_diff['tags_only_in_file1'])}")
        for tag in sorted(structure_diff['tags_only_in_file1']):
            report.append(f"  - {tag}")
        
        report.append(f"Tags only in File 2: {len(structure_diff['tags_only_in_file2'])}")
        for tag in sorted(structure_diff['tags_only_in_file2']):
            report.append(f"  - {tag}")
        
        report.append(f"Common tags: {len(structure_diff['common_tags'])}")
        report.append("")
        
        # Content comparison
        content_diff = self.compare_content()
        report.append("CONTENT COMPARISON")
        report.append("-" * 40)
        report.append(f"Content differences: {len(content_diff['content_differences'])}")
        report.append(f"Attribute differences: {len(content_diff['attribute_differences'])}")
        report.append(f"Missing elements: {len(content_diff['missing_elements'])}")
        report.append(f"Extra elements: {len(content_diff['extra_elements'])}")
        report.append("")
        
        # Requirements comparison
        req_diff = self.compare_requirements()
        report.append("REQUIREMENTS COMPARISON")
        report.append("-" * 40)
        report.append(f"Requirements in File 1: {len(req_diff['requirements_file1'])}")
        report.append(f"Requirements in File 2: {len(req_diff['requirements_file2'])}")
        report.append(f"Requirements only in File 1: {len(req_diff['requirement_differences']['only_in_file1'])}")
        report.append(f"Requirements only in File 2: {len(req_diff['requirement_differences']['only_in_file2'])}")
        report.append(f"Common requirements: {len(req_diff['requirement_differences']['common_requirements'])}")
        report.append("")
        
        # Detailed differences
        if content_diff['content_differences']:
            report.append("DETAILED CONTENT DIFFERENCES")
            report.append("-" * 40)
            for i, diff in enumerate(content_diff['content_differences'][:10], 1):  # Limit to first 10
                report.append(f"{i}. XPath: {diff['xpath']}")
                report.append(f"   File 1: {diff['file1_content'][:100]}...")
                report.append(f"   File 2: {diff['file2_content'][:100]}...")
                report.append("")
        
        return "\n".join(report)
    
    def save_comparison_results(self, output_file: str):
        """Save comparison results to a JSON file."""
        if not self.load_files():
            return False
        
        results = {
            'file1': self.file1,
            'file2': self.file2,
            'structure_comparison': self.compare_structure(),
            'content_comparison': self.compare_content(),
            'requirements_comparison': self.compare_requirements()
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False


def main():
    """Main function to run the ReqIF comparator."""
    parser = argparse.ArgumentParser(description='Compare two ReqIF files')
    parser.add_argument('file1', help='First ReqIF file path (.reqif or .reqifz)')
    parser.add_argument('file2', help='Second ReqIF file path (.reqif or .reqifz)')
    parser.add_argument('--output', '-o', help='Output file for JSON results')
    parser.add_argument('--report', '-r', help='Output file for text report')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.file1):
        print(f"Error: File '{args.file1}' not found.")
        sys.exit(1)
    
    if not os.path.exists(args.file2):
        print(f"Error: File '{args.file2}' not found.")
        sys.exit(1)
    
    # Create comparator
    comparator = ReqIFComparator(args.file1, args.file2)
    
    try:
        # Generate and display report
        report = comparator.generate_diff_report()
        print(report)
        
        # Save results if requested
        if args.output:
            if comparator.save_comparison_results(args.output):
                print(f"\nJSON results saved to: {args.output}")
            else:
                print("\nFailed to save JSON results.")
        
        if args.report:
            try:
                with open(args.report, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Text report saved to: {args.report}")
            except Exception as e:
                print(f"Failed to save text report: {e}")
    
    finally:
        # Always cleanup temporary files
        comparator.cleanup_temp_files()


if __name__ == "__main__":
    main() 