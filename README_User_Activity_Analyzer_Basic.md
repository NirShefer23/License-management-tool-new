# User Activity and License Analysis CLI Tool (Basic Version)

A comprehensive Python command-line interface for analyzing user login/logout activity from log files, providing detailed insights into user behavior, license utilization, and system performance.

**This basic version uses only pure Python without external dependencies, making it easy to install and run on any system.**

## 🚀 Features

### Core Functionality
- **Robust Log Parsing**: Supports multiple log formats including Polarion licensing logs
- **Session Reconstruction**: Intelligently reconstructs user sessions from login/logout events
- **User Activity Metrics**: Calculates comprehensive user engagement metrics
- **License Usage Analysis**: Provides detailed license utilization breakdowns
- **Advanced Analytics**: Includes outlier detection and percentile analysis

### CLI Features
- **Flexible Input**: Supports single files, glob patterns, and directories
- **Multiple Output Formats**: Table, JSON, CSV, and Summary output options
- **Advanced Filtering**: Filter by user, date range, and metrics
- **Sorting Options**: Sort by various metrics (activity score, login time, sessions)
- **Outlier Analysis**: Configurable percentile analysis for identifying extreme users

## 📋 Requirements

- **Python 3.8 or higher** (no external dependencies required)
- **Pure Python implementation** - no compilation needed

## 🛠️ Installation

1. **Download the script**: `user_activity_analyzer_basic.py`
2. **No installation required** - just run the script directly!

## 📖 Usage

### Basic Usage

```bash
# Analyze a single log file
python user_activity_analyzer_basic.py --log-file "license logs/log4j-licensing-20250805-0022-03.log.2025-08-05-1"

# Analyze multiple log files using glob pattern
python user_activity_analyzer_basic.py --log-file "license logs/*.log"

# Analyze all log files in a directory
python user_activity_analyzer_basic.py --log-file "license logs/"
```

### Advanced Usage

```bash
# Generate summary report
python user_activity_analyzer_basic.py --log-file "license logs/" --output-format summary

# Analyze top 0.1% users with custom sorting
python user_activity_analyzer_basic.py --log-file "license logs/" --top-percentile 0.1 --sort-by total_login_time

# Filter by user and date range
python user_activity_analyzer_basic.py --log-file "license logs/" --filter-user "admin" --date-range "2025-08-01" "2025-08-05"

# Limit results and sort by activity score
python user_activity_analyzer_basic.py --log-file "license logs/" --limit 20 --sort-by activity_score

# Export as JSON for programmatic processing
python user_activity_analyzer_basic.py --log-file "license logs/" --output-format json
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--log-file` | `-f` | Path to log file(s). Supports glob patterns and directories | Required |
| `--output-format` | `-o` | Output format: table, json, csv, summary | table |
| `--top-percentile` | `-p` | Top percentile for outlier analysis (0.0-1.0) | 0.1 |
| `--sort-by` | | Sort by: user_id, total_login_time, activity_score, sessions | activity_score |
| `--limit` | | Limit number of results displayed | No limit |
| `--filter-user` | | Filter by user ID (supports partial matches) | No filter |
| `--date-range` | | Filter by date range (YYYY-MM-DD format) | No filter |

## 📊 Output Formats

### Table Format (Default)
Displays results in a formatted table with columns:
- User ID
- Total Hours
- Average Session Duration (minutes)
- Number of Sessions
- Activity Score
- License Type
- Last Login Timestamp

### JSON Format
Structured JSON output including:
- User activities with all metrics
- License usage statistics
- Analysis summary and timestamp

### CSV Format
Comma-separated values suitable for import into spreadsheet applications.

### Summary Format
Comprehensive text summary including:
- Overall statistics
- Top 10 users by activity score
- License usage breakdown
- Activity distribution analysis

## 🔍 Analysis Features

### User Activity Metrics
- **Total Login Time**: Cumulative hours of user activity
- **Average Session Duration**: Mean session length in minutes
- **Session Count**: Number of individual sessions
- **Activity Score**: Composite score (0-100) based on time and session frequency
- **Last Login**: Most recent login timestamp

### License Usage Analysis
- **Total Active Time**: Cumulative hours per license type
- **Unique Users**: Number of distinct users per license type
- **Average Session Duration**: Mean session length per license type
- **Peak Concurrent Users**: Maximum simultaneous users per license type

### Outlier Analysis (0.1% Analysis)
- **Top Percentile Users**: Most active users based on activity score
- **Bottom Percentile Users**: Least active users for investigation
- **Configurable Thresholds**: Adjustable percentile for outlier detection

## 🛡️ Error Handling

The tool includes robust error handling for:
- **File Access Issues**: Missing files, permission errors
- **Parsing Errors**: Malformed log entries, invalid timestamps
- **Data Processing**: Missing or incomplete session data
- **Memory Management**: Efficient processing of large log files

## 📝 Log Format Support

### Supported Formats
1. **Polarion Licensing Logs**: Primary format with license type information
   ```
   2025-08-05 00:25:45,215 [ajp-nio-127.0.0.1-8889-exec-6] INFO  PolarionLicensing - User 'lidorw' logged in with named REQUIREMENTS
   ```

2. **Generic Login/Logout Logs**: Standard format support
   ```
   2025-08-05 10:30:00 User 'username' logged in
   2025-08-05 11:45:00 User 'username' logged out
   ```

### Extensible Parsing
The tool uses regex patterns that can be easily extended to support additional log formats.

## 🔧 Configuration

### Session Timeout
Default session timeout is 30 minutes. This can be modified in the `SessionManager` class.

### Activity Score Calculation
The activity score is calculated as:
- 50% based on total login time (normalized to 40 hours max)
- 50% based on session count (normalized to 20 sessions max)

## 📁 File Structure

```
user_activity_analyzer_basic.py     # Main CLI application (no dependencies)
README_User_Activity_Analyzer_Basic.md  # This documentation
user_activity_analyzer.log          # Application log file
```

## 🚨 Troubleshooting

### Common Issues

1. **No log entries found**
   - Verify log file path and format
   - Check if log files contain login/logout events
   - Ensure proper file permissions

2. **Memory issues with large files**
   - The tool processes files line-by-line to minimize memory usage
   - For very large files, consider splitting into smaller chunks

3. **Parsing errors**
   - Check log format compatibility
   - Review the log file for malformed entries
   - Consider extending regex patterns for custom formats

### Performance Tips

- Use specific file paths instead of directory scanning for faster processing
- Limit results with `--limit` for large datasets
- Use `--output-format json` for programmatic processing
- Use `--output-format summary` for quick overview

## 📈 Example Output

### Sample Analysis Results

```
🔍 User Activity and License Analysis CLI Tool (Basic)
============================================================

📁 Found 1 log file(s)
📖 Parsing log files...
✅ Parsed 8957 log entries
🔄 Reconstructing user sessions...
✅ Reconstructed 4480 sessions
📊 Analyzing user activity...
✅ Analyzed activity for 325 users
🔑 Analyzing license usage...
✅ Analyzed usage for 4 license types

============================================================
📊 USER ACTIVITY SUMMARY
============================================================

+-----------+-------------+-------------------+----------+-------------+--------------+------------------+
| User ID   | Total Hours | Avg Session (min) | Sessions | Activity Score | License      | Last Login       |
+-----------+-------------+-------------------+----------+-------------+--------------+------------------+
| admin3    | 178.1       | 29.5              | 362      | 100.0          | ALM          | 2025-08-05 17:15 |
| matanlevh | 134.7       | 28.7              | 282      | 100.0          | REQUIREMENTS | 2025-08-05 19:34 |
| eyalt     | 136.5       | 29.8              | 275      | 100.0          | REQUIREMENTS | 2025-08-05 13:07 |
+-----------+-------------+-------------------+----------+-------------+--------------+------------------+

============================================================
🔑 LICENSE USAGE SUMMARY
============================================================

+--------------+-------------+--------------+-------------------+-----------------+
| License Type | Total Hours | Unique Users | Avg Session (min) | Peak Concurrent |
+--------------+-------------+--------------+-------------------+-----------------+
| REQUIREMENTS | 1856.6      | 250          | 29.1              | 121             |
| ALM          | 198.5       | 6            | 29.4              | 6               |
| REVIEWER     | 94.3        | 65           | 24.5              | 22              |
| PRO          | 5.7         | 5            | 28.3              | 4               |
+--------------+-------------+--------------+-------------------+-----------------+
```

## 🔮 Future Enhancements

Potential improvements and extensions:
- **Database Integration**: Persistent storage for historical analysis
- **Real-time Processing**: Streaming analysis for live log monitoring
- **Web Dashboard**: Browser-based interface for interactive analysis
- **Machine Learning**: Advanced anomaly detection and user behavior prediction
- **API Integration**: REST API for programmatic access
- **Additional Log Formats**: Support for more log file types
- **Custom Metrics**: User-defined activity scoring algorithms

## 📄 License

This tool is part of the Polarion License Manager project and follows the same licensing terms.

## 🤝 Contributing

Contributions are welcome! Please consider:
- Adding support for new log formats
- Improving table formatting and output options
- Enhancing performance for large datasets
- Adding new analysis metrics
- Improving error handling and user feedback

## 📞 Support

For issues, questions, or feature requests, please refer to the main project documentation or create an issue in the project repository.

## 🎯 Quick Start

1. **Download the script**: `user_activity_analyzer_basic.py`
2. **Run basic analysis**:
   ```bash
   python user_activity_analyzer_basic.py --log-file "your_log_file.log"
   ```
3. **Get summary report**:
   ```bash
   python user_activity_analyzer_basic.py --log-file "your_log_file.log" --output-format summary
   ```
4. **Export to JSON**:
   ```bash
   python user_activity_analyzer_basic.py --log-file "your_log_file.log" --output-format json > analysis_results.json
   ```

That's it! No installation, no dependencies, just pure Python analysis power. 