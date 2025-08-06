# User Activity and License Analysis CLI Tool

A comprehensive Python command-line interface for analyzing user login/logout activity from log files, providing detailed insights into user behavior, license utilization, and system performance.

## 🚀 Features

### Core Functionality
- **Robust Log Parsing**: Supports multiple log formats including Polarion licensing logs
- **Session Reconstruction**: Intelligently reconstructs user sessions from login/logout events
- **User Activity Metrics**: Calculates comprehensive user engagement metrics
- **License Usage Analysis**: Provides detailed license utilization breakdowns
- **Advanced Analytics**: Includes outlier detection and percentile analysis

### Data Visualization
- **User Activity Charts**: Activity score distribution, top users, session analysis
- **License Usage Charts**: Usage comparison, peak concurrent users
- **High-Quality Output**: Professional charts saved as PNG files

### CLI Features
- **Flexible Input**: Supports single files, glob patterns, and directories
- **Multiple Output Formats**: Table, JSON, and CSV output options
- **Advanced Filtering**: Filter by user, date range, and metrics
- **Sorting Options**: Sort by various metrics (activity score, login time, sessions)
- **Outlier Analysis**: Configurable percentile analysis for identifying extreme users

## 📋 Requirements

- Python 3.8 or higher
- Required packages (see `requirements_analyzer.txt`):
  - pandas==2.1.4
  - matplotlib==3.8.2
  - seaborn==0.13.0
  - tabulate==0.9.0
  - numpy==1.24.3

## 🛠️ Installation

1. **Clone or download the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements_analyzer.txt
   ```

## 📖 Usage

### Basic Usage

```bash
# Analyze a single log file
python user_activity_analyzer.py --log-file "license logs/log4j-licensing-20250805-0022-03.log.2025-08-05-1"

# Analyze multiple log files using glob pattern
python user_activity_analyzer.py --log-file "license logs/*.log"

# Analyze all log files in a directory
python user_activity_analyzer.py --log-file "license logs/"
```

### Advanced Usage

```bash
# Generate charts and save as JSON
python user_activity_analyzer.py --log-file "license logs/" --generate-charts --output-format json

# Analyze top 0.1% users with custom sorting
python user_activity_analyzer.py --log-file "license logs/" --top-percentile 0.1 --sort-by total_login_time

# Filter by user and date range
python user_activity_analyzer.py --log-file "license logs/" --filter-user "admin" --date-range "2025-08-01" "2025-08-05"

# Limit results and sort by activity score
python user_activity_analyzer.py --log-file "license logs/" --limit 20 --sort-by activity_score
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--log-file` | `-f` | Path to log file(s). Supports glob patterns and directories | Required |
| `--output-format` | `-o` | Output format: table, json, csv | table |
| `--top-percentile` | `-p` | Top percentile for outlier analysis (0.0-1.0) | 0.1 |
| `--generate-charts` | `-c` | Generate visualization charts | False |
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

## 📈 Generated Charts

When using `--generate-charts`, the tool creates the following visualizations in the `charts/` directory:

### User Activity Charts
1. **User Activity Score Distribution**: Histogram showing distribution of user activity scores
2. **Top 20 Users by Login Time**: Horizontal bar chart of most active users
3. **Session Analysis**: Scatter plot of session count vs average duration

### License Usage Charts
1. **License Usage Comparison**: Side-by-side comparison of total hours and unique users by license type
2. **Peak Concurrent Users**: Bar chart showing peak concurrent usage by license type

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

### Chart Customization
Charts are generated with professional styling using Seaborn. Colors, sizes, and layouts can be customized in the `DataVisualizer` class.

## 📁 File Structure

```
user_activity_analyzer.py          # Main CLI application
requirements_analyzer.txt          # Python dependencies
README_User_Activity_Analyzer.md   # This documentation
charts/                            # Generated charts (created automatically)
user_activity_analyzer.log         # Application log file
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

3. **Chart generation fails**
   - Ensure matplotlib and seaborn are properly installed
   - Check write permissions for the charts directory
   - Verify sufficient disk space

4. **Parsing errors**
   - Check log format compatibility
   - Review the log file for malformed entries
   - Consider extending regex patterns for custom formats

### Performance Tips

- Use specific file paths instead of directory scanning for faster processing
- Limit results with `--limit` for large datasets
- Use `--output-format json` for programmatic processing
- Generate charts only when needed with `--generate-charts`

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
- Improving visualization options
- Enhancing performance for large datasets
- Adding new analysis metrics
- Improving error handling and user feedback

## 📞 Support

For issues, questions, or feature requests, please refer to the main project documentation or create an issue in the project repository. 