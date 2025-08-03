# ReqIF File Comparator

A comprehensive tool for comparing two ReqIF (Requirements Interchange Format) files and analyzing their differences in structure, content, and metadata.

## Features

- **XML Structure Comparison**: Compare the overall structure and hierarchy of ReqIF files
- **Content Analysis**: Identify differences in element content and attributes
- **Requirements Tracking**: Specifically analyze requirement-related elements
- **Multiple Output Formats**: Generate both text reports and JSON results
- **Detailed Diff Reports**: Get comprehensive analysis of all differences

## Installation

The tool uses only Python standard library modules, so no additional installation is required beyond Python 3.6+.

## Usage

### Command Line Interface

```bash
# Basic comparison
python reqif_comparator.py file1.reqif file2.reqif

# Save results to files
python reqif_comparator.py file1.reqif file2.reqif --output results.json --report report.txt
```

### Python API

```python
from reqif_comparator import ReqIFComparator

# Create comparator
comparator = ReqIFComparator("file1.reqif", "file2.reqif")

# Generate report
report = comparator.generate_diff_report()
print(report)

# Save results
comparator.save_comparison_results("results.json")
```

### Test the Tool

Run the test script to see the tool in action with sample files:

```bash
python test_reqif_comparator.py
```

## Output

The tool provides several types of analysis:

### 1. Structure Comparison
- Tags present in only one file
- Common tags between files
- XPath differences

### 2. Content Comparison
- Element content differences
- Attribute differences
- Missing/extra elements

### 3. Requirements Analysis
- Requirement-specific elements
- Requirement differences
- Common requirements

### 4. Detailed Reports
- Text-based human-readable reports
- JSON format for programmatic access

## Example Output

```
================================================================================
REQIF FILE COMPARISON REPORT
================================================================================
File 1: sample1.reqif
File 2: sample2.reqif

STRUCTURE COMPARISON
----------------------------------------
Tags only in File 1: 0
Tags only in File 2: 0
Common tags: 15

CONTENT COMPARISON
----------------------------------------
Content differences: 2
Attribute differences: 1
Missing elements: 0
Extra elements: 0

REQUIREMENTS COMPARISON
----------------------------------------
Requirements in File 1: 2
Requirements in File 2: 2
Requirements only in File 1: 0
Requirements only in File 2: 1
Common requirements: 1
```

## File Format Support

The tool supports standard ReqIF XML files that follow the OMG ReqIF specification. It can handle:

- ReqIF 1.0 and 1.1 formats
- Various ReqIF tools' output formats
- Custom requirement specifications
- Metadata and attribute comparisons

## Advanced Usage

### Custom Element Analysis

You can extend the tool to focus on specific elements:

```python
# Focus on specific requirement types
req_elements = comparator.find_requirement_elements(comparator.root1)
for req in req_elements:
    print(f"Requirement: {req['tag']} - {req['content']}")
```

### Batch Processing

For comparing multiple files:

```python
import glob
from reqif_comparator import ReqIFComparator

reqif_files = glob.glob("*.reqif")
for i in range(len(reqif_files)):
    for j in range(i+1, len(reqif_files)):
        comparator = ReqIFComparator(reqif_files[i], reqif_files[j])
        report = comparator.generate_diff_report()
        print(f"Comparing {reqif_files[i]} vs {reqif_files[j]}")
        print(report)
```

## Troubleshooting

### Common Issues

1. **XML Parse Errors**: Ensure your ReqIF files are valid XML
2. **File Not Found**: Check file paths and permissions
3. **Memory Issues**: For very large files, consider processing in chunks

### Error Messages

- `Error parsing XML file`: Invalid XML structure
- `File not found`: File path issues
- `Error saving results`: Permission or disk space issues

## Contributing

The tool is designed to be extensible. You can add:

- New comparison algorithms
- Additional output formats
- Custom element analyzers
- Integration with other tools

## License

This tool is provided as-is for educational and development purposes. 