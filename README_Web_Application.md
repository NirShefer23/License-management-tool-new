# Mobileye Development Tools Web Application

A beautiful, user-friendly web interface for executing local Python tools including License Management Automation and ReqIF Comparison tools.

## 🚀 Features

- **Modern Web Interface**: Clean, responsive design with Mobileye branding
- **Tool Integration**: Seamlessly executes your existing Python scripts
- **User-Friendly**: Simple forms and clear instructions for non-technical users
- **Real-time Feedback**: Progress indicators and status updates
- **Execution History**: Track and monitor tool usage
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## 📋 Prerequisites

- Python 3.7 or higher
- Your existing Python tools:
  - `polarion_license_manager.py`
  - `reqif_comparator.py`
- Virtual environment (recommended)

## 🛠️ Installation

### 1. Install Flask Dependencies

```bash
# Install Flask and required packages
pip install -r requirements_web.txt
```

### 2. Verify Tool Paths

Ensure the tool paths in `app.py` match your actual file locations:

```python
TOOLS_CONFIG = {
    'license_management': {
        'script_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\polarion_license_manager.py",
        'venv_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\venv\Scripts\python.exe",
        'name': 'License Management Automation'
    },
    'reqif_comparison': {
        'script_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\reqif_comparator.py",
        'venv_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\venv\Scripts\python.exe",
        'name': 'ReqIF Comparison Tool'
    }
}
```

### 3. Start the Web Server

```bash
# Run the Flask application
python app.py
```

The web application will start on `http://localhost:5000`

## 🎯 How to Use

### Dashboard
- **Overview**: View available tools and recent activity
- **Statistics**: See execution counts and success rates
- **Quick Access**: Launch tools directly from the dashboard

### License Management Tool
1. **Select Action**: Choose from Query, Add, Remove, or Bulk operations
2. **Paste Configuration**: Copy and paste your license configuration data
3. **Upload Files**: Optionally upload user data files (CSV/Excel)
4. **Enter Users**: For user operations, specify email addresses
5. **Execute**: Click the execute button to run the automation
6. **View Results**: See the output in a formatted, readable display

### ReqIF Comparison Tool
1. **Upload Files**: Select two .reqifz files to compare
2. **Start Comparison**: Click "Compare Files" to begin analysis
3. **Monitor Progress**: Watch the progress bar during processing
4. **Review Results**: View detailed comparison report with statistics
5. **Export**: Download results for documentation

### Help & Support
- **Quick Start Guide**: Step-by-step instructions for each tool
- **FAQ**: Common questions and answers
- **Contact Information**: Support email addresses for different issues

## 🏗️ Architecture

### File Structure
```
mobileye-tools-web/
├── app.py                          # Main Flask application
├── requirements_web.txt            # Python dependencies
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with navigation
│   ├── dashboard.html              # Main dashboard page
│   ├── license_management.html     # License management interface
│   ├── reqif_comparison.html       # ReqIF comparison interface
│   └── help.html                   # Help and support page
└── README_Web_Application.md       # This file
```

### Key Components

#### Flask Application (`app.py`)
- **Routes**: Define web pages and API endpoints
- **Tool Executor**: Handles execution of local Python scripts
- **File Handling**: Manages file uploads and temporary storage
- **Execution History**: Tracks tool usage and results

#### Templates
- **Base Template**: Common layout, navigation, and styling
- **Tool Pages**: Dedicated interfaces for each tool
- **Responsive Design**: Works on all device sizes
- **Interactive Elements**: Real-time feedback and progress indicators

#### API Endpoints
- `/api/execute-license-management`: Execute license management tool
- `/api/execute-reqif-comparison`: Execute ReqIF comparison tool
- `/api/execution-history`: Get recent execution history
- `/api/tool-stats`: Get tool usage statistics

## 🎨 Design Features

### Mobileye Branding
- **Color Scheme**: Blue gradients matching Mobileye brand
- **Typography**: Clean, professional fonts
- **Icons**: Consistent iconography throughout
- **Layout**: Modern card-based design

### User Experience
- **Intuitive Navigation**: Clear menu structure
- **Visual Feedback**: Loading states and progress indicators
- **Error Handling**: Friendly error messages
- **Responsive Design**: Optimized for all screen sizes

### Accessibility
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Friendly**: Proper ARIA labels
- **High Contrast**: Readable text and colors
- **Mobile Optimized**: Touch-friendly interface

## 🔧 Configuration

### Customizing Tool Paths
Edit the `TOOLS_CONFIG` in `app.py` to match your file locations:

```python
TOOLS_CONFIG = {
    'license_management': {
        'script_path': 'path/to/your/polarion_license_manager.py',
        'venv_path': 'path/to/your/venv/python.exe',
        'name': 'License Management Automation'
    },
    # ... other tools
}
```

### Adding New Tools
1. Add tool configuration to `TOOLS_CONFIG`
2. Create execution method in `ToolExecutor` class
3. Add API endpoint in Flask app
4. Create HTML template for the tool interface
5. Update navigation in `base.html`

### Styling Customization
- **Colors**: Modify CSS variables in `base.html`
- **Layout**: Adjust Tailwind CSS classes
- **Branding**: Update logos and company information

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
For production use, consider:
- **WSGI Server**: Use Gunicorn or uWSGI
- **Reverse Proxy**: Nginx or Apache
- **SSL Certificate**: HTTPS for security
- **Database**: Store execution history in a database
- **Authentication**: Add user login system

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements_web.txt .
RUN pip install -r requirements_web.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🔒 Security Considerations

- **File Uploads**: Validates file types and sizes
- **Temporary Files**: Automatically cleans up uploaded files
- **Input Validation**: Sanitizes user inputs
- **Error Handling**: Prevents information leakage
- **Local Execution**: Tools run on local machine only

## 📊 Monitoring and Logging

### Execution History
- Tracks all tool executions
- Records success/failure status
- Stores input parameters and output
- Calculates execution duration

### Logging
- Application logs in console
- Error tracking and debugging
- Performance monitoring

## 🆘 Troubleshooting

### Common Issues

**Tool Not Found**
- Verify file paths in `TOOLS_CONFIG`
- Check virtual environment activation
- Ensure Python scripts are executable

**File Upload Errors**
- Check file size limits (100MB default)
- Verify file format (.reqifz for ReqIF, CSV/Excel for license management)
- Ensure proper file permissions

**Execution Failures**
- Check console logs for error messages
- Verify tool dependencies are installed
- Test tools manually in terminal first

### Getting Help
1. Check the Help & Support page in the web application
2. Review console logs for error details
3. Contact technical support with error information
4. Verify tool configuration and paths

## 🔄 Updates and Maintenance

### Adding New Features
1. **New Tools**: Follow the tool integration pattern
2. **UI Improvements**: Modify templates and CSS
3. **API Enhancements**: Add new endpoints as needed
4. **Security Updates**: Keep dependencies updated

### Regular Maintenance
- Update Flask and dependencies
- Monitor execution logs
- Clean up temporary files
- Backup configuration and data

## 📞 Support

For technical support or questions:
- **Technical Issues**: tech-support@mobileye.com
- **License Management**: license-admin@mobileye.com
- **General Help**: help-desk@mobileye.com

## 📄 License

This web application is part of the Mobileye Development Tools suite and is intended for internal use within Mobileye.

---

**Built with ❤️ for the Mobileye Development Team** 