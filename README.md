# Polarion License Manager

A comprehensive automation tool for managing Polarion user licenses with database integration, license configuration parsing, and safe modification operations.

## Features

### 🔗 Database Integration
- **PostgreSQL Connection**: Connect directly to Polarion database via pgAdmin4 or direct connection
- **User Fetching**: Automatically fetch all active users from `polarion.t_user` table
- **Schema Validation**: Verify database schema and table structure
- **Connection Testing**: Comprehensive connection testing and error reporting

### 📊 License Management
- **Configuration Parsing**: Parse license configuration from text files, CSV, or Excel
- **Named/Concurrent Slots**: Support for both named and concurrent license types
- **Placeholder Filtering**: Automatically ignore placeholder entries (index ≥ 5000)
- **Comment Handling**: Properly handle commented and active license lines

### 👥 User Management
- **Flexible User Loading**: Load users from database or CSV/Excel files
- **Enhanced Mixed Identifiers**: Support for comma or semicolon separated lists with mixed user IDs, full names, and email addresses
- **Multiple Identifiers**: Find users by ID, email, or full name
- **Batch Operations**: Add, remove, or switch licenses for multiple users
- **Duplicate Prevention**: Comprehensive checks for duplicate licenses

### 🛡️ Safety & Validation
- **Change Tracking**: Track all modifications with detailed logging
- **Validation Checks**: Validate changes for potential issues
- **Backup Creation**: Automatic backup of original configuration
- **Confirmation Prompts**: Require confirmation before applying changes

### 📋 Main Menu Options
1. **Query User License Status** - Check license status for specific users
2. **List Inactive Users** - Find users with licenses who are no longer active
3. **Add User(s) to License** - Assign licenses to users
4. **Remove User(s) from License** - Remove license assignments
5. **Switch User License Type** - Change user's license type
6. **Show Current License Summary** - Display current license assignments
7. **Apply Changes and Generate Output** - Apply changes and save results
8. **Database Status and Connection Info** - Check database connectivity
9. **Exit** - Exit with option to save changes

## Installation

### Prerequisites
- Python 3.7 or higher
- PostgreSQL database access (for database features)
- Required Python packages (see requirements.txt)

### Setup
1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python polarion_license_manager.py
   ```

## Usage

### 1. Database Connection Setup
The tool will prompt you to connect to the Polarion database:
- **Host**: Database server address (default: localhost)
- **Port**: Database port (default: 5432)
- **Database**: Database name
- **Username**: Database username
- **Password**: Database password

If database connection fails, you can load users from a CSV/Excel file instead.

### 2. License Configuration Input
You can provide license configuration in several ways:
- **File Path**: Direct path to license configuration file
- **Excel/CSV**: Path to Excel or CSV file with license data
- **Paste**: Manually paste configuration text

### 3. User Management
The tool supports multiple ways to load users:
- **Database**: Fetch from `polarion.t_user` table
- **CSV/Excel File**: Load from user list file
- **Manual Entry**: Enter users manually if needed

### 4. Enhanced Input Format
The tool now supports enhanced input for user identifiers:
- **Mixed Identifiers**: Enter a combination of user IDs, full names, and email addresses
- **Flexible Separators**: Use commas (`,`) or semicolons (`;`) to separate identifiers
- **Automatic Categorization**: The system automatically categorizes each identifier type
- **Batch Processing**: Process multiple users at once with the same license settings

**Example Input Formats:**
```
# Mixed user IDs and emails
bshrager, uhizi, Baruch.Shrager@mobileye.com

# Mixed names and user IDs
Baruch Shrager; Uzi Hizi; nirshe

# Compound format (name + email together)
Baruch Shrager Baruch.Shrager@mobileye.com; David Harbater Dudu.Harbater@mobileye.com

# Complex mixed format
Baruch Shrager Baruch.Shrager@mobileye.com; Uzi Hizi Uzi.Hizi@mobileye.com; nirshe

# Pure email list
user1@test.com, user2@test.com, user3@test.com

# Pure user ID list
john.doe, jane.smith, bob_wilson
```

### 5. License Operations
All license operations include:
- **User Validation**: Ensure users exist before operations
- **Duplicate Checking**: Prevent duplicate license assignments
- **Change Tracking**: Log all modifications
- **Confirmation**: Require user confirmation before applying

## File Formats

### License Configuration Format
```
# ------------------------------- POLARION ALM -------------------------------
# NAMED USERS:
namedALMUser1=user_id
namedALMUser2=another_user
# CONCURRENT USERS:
concurrentALMUser1=concurrent_user

# ------------------------------- POLARION QA -------------------------------
# NAMED USERS:
namedQAUser1=qa_user
# CONCURRENT USERS:
concurrentQAUser1=qa_concurrent_user
```

### User File Format (CSV/Excel)
```csv
user_id,full_name,email
bshrager,Bob Shrager,bob.shrager@company.com
uhizi,User Hizi,user.hizi@company.com
asegal1,Alice Segal,alice.segal@company.com
```

## License Types Supported

- **ALM**: Application Lifecycle Management
- **QA**: Quality Assurance
- **Requirements**: Requirements Management
- **Pro**: Professional
- **Reviewer**: Review Management

## Assignment Types

- **Named**: Dedicated license for specific user
- **Concurrent**: Shared license that can be used by multiple users

## Output Files

The tool generates several output files:
- **Backup Files**: `polarion_license_backup_YYYYMMDD_HHMMSS.txt`
- **Updated Configuration**: `polarion_license_updated_YYYYMMDD_HHMMSS.txt`
- **Change Summary**: `polarion_license_changes_YYYYMMDD_HHMMSS.txt`
- **Log File**: `polarion_license_manager.log`

## Testing

Run the test script to verify functionality:
```bash
python test_polarion_manager.py
```

The test script includes:
- Basic functionality testing
- User loading from files
- License parsing and operations
- Database connection testing (optional)

## Troubleshooting

### Database Connection Issues
1. Verify database credentials
2. Check network connectivity
3. Ensure PostgreSQL is running
4. Verify schema and table existence

### User Not Found Errors
1. Check if users are loaded from database/file
2. Verify user identifiers match exactly
3. Use database status option to check connectivity
4. Try loading users from a file instead

### License Parsing Issues
1. Verify license configuration format
2. Check for proper section headers
3. Ensure user IDs exist in the system
4. Review log file for detailed error messages

## Logging

The tool provides comprehensive logging:
- **File Logging**: All operations logged to `polarion_license_manager.log`
- **Console Output**: Important messages displayed in console
- **Debug Information**: Detailed debugging information available

## Security Considerations

- **Password Handling**: Passwords are not stored or logged
- **Backup Creation**: Original configurations are automatically backed up
- **Validation**: All changes are validated before application
- **Confirmation**: User confirmation required for all modifications

## Support

For issues or questions:
1. Check the log file for detailed error messages
2. Run the test script to verify functionality
3. Review the database status option for connectivity issues
4. Ensure all dependencies are properly installed

## Version History

- **v1.1**: Enhanced input mechanism for mixed user identifiers
  - Added support for comma and semicolon separated lists
  - Automatic categorization of user IDs, full names, and email addresses
  - Enhanced batch processing for multiple users
  - Improved user experience with flexible input formats

- **v1.0**: Initial release with comprehensive license management features
  - Enhanced database connectivity and user management
  - Added file-based user loading as alternative to database
  - Improved error handling and validation
  - Added comprehensive testing and documentation 