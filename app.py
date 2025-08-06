#!/usr/bin/env python3
"""
Mobileye Development Tools Web Interface

A Flask-based web application that provides a user-friendly interface
for executing local Python tools including License Management and ReqIF Comparison.
"""

from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import tempfile
import json
import logging
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import zipfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Tool configurations
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
    },
    'user_activity_analyzer': {
        'script_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\user_activity_analyzer_basic.py",
        'venv_path': r"C:\Users\nirshe\OneDrive - Mobileye\Mobileye Nir\cursor\polarion-license-manager-new\venv\Scripts\python.exe",
        'name': 'User Activity Analyzer'
    }
}

# Store execution history (in production, use a database)
execution_history = []

class ToolExecutor:
    """Handles execution of local Python tools"""
    
    @staticmethod
    def execute_license_management(license_config, user_file=None, action="query", user_identifiers=""):
        """Execute the license management tool"""
        try:
            # Create temporary files
            temp_files = []
            
            # Save license config to temp file
            config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            config_file.write(license_config)
            config_file.close()
            temp_files.append(config_file.name)
            
            # Save user file if provided
            user_file_path = None
            if user_file:
                user_file_path = tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False)
                user_file.save(user_file_path.name)
                user_file_path.close()
                temp_files.append(user_file_path.name)
                user_file_path = user_file_path.name
            
            # Build command
            cmd = [
                TOOLS_CONFIG['license_management']['venv_path'],
                TOOLS_CONFIG['license_management']['script_path']
            ]
            
            # Execute the tool
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(TOOLS_CONFIG['license_management']['script_path'])
            )
            
            # Prepare input for the tool
            input_data = []
            
            # Database connection (n for no)
            input_data.append("n\n")
            
            # Load users from file
            if user_file_path:
                input_data.append("y\n")  # Load from file
                input_data.append(f'"{user_file_path}"\n')
            else:
                input_data.append("n\n")  # Don't load from file
            
            # License configuration
            input_data.append("paste\n")
            input_data.append(license_config + "\n")
            input_data.append("\x1a\n")  # Ctrl+Z to end paste
            
            # Select action
            action_map = {
                "query": "1",
                "inactive": "2", 
                "add": "3",
                "remove": "4",
                "switch": "5",
                "summary": "6",
                "apply": "7",
                "status": "8",
                "exit": "9"
            }
            input_data.append(f"{action_map.get(action, '1')}\n")
            
            # Add user identifiers if needed
            if user_identifiers and action in ["query", "add", "remove"]:
                input_data.append(f"{user_identifiers}\n")
            
            # Exit
            input_data.append("9\n")
            
            # Send input and get output
            input_text = "".join(input_data)
            stdout, stderr = process.communicate(input=input_text)
            
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'output': stdout,
                    'error': stderr if stderr else None
                }
            else:
                return {
                    'success': False,
                    'output': stdout,
                    'error': stderr
                }
                
        except Exception as e:
            logger.error(f"Error executing license management tool: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    @staticmethod
    def execute_reqif_comparison(file1_path, file2_path):
        """Execute the ReqIF comparison tool"""
        try:
            # Build command
            cmd = [
                TOOLS_CONFIG['reqif_comparison']['venv_path'],
                TOOLS_CONFIG['reqif_comparison']['script_path'],
                file1_path,
                file2_path
            ]
            
            # Execute the tool
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(TOOLS_CONFIG['reqif_comparison']['script_path'])
            )
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'output': process.stdout,
                    'error': process.stderr if process.stderr else None
                }
            else:
                return {
                    'success': False,
                    'output': process.stdout,
                    'error': process.stderr
                }
                
        except Exception as e:
            logger.error(f"Error executing ReqIF comparison tool: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    @staticmethod
    def execute_user_activity_analyzer(log_file_path, output_format="table", limit=None, sort_by="activity_score", 
                                     filter_user=None, date_range=None, top_percentile=0.1):
        """Execute the User Activity Analyzer tool"""
        try:
            # Build command
            cmd = [
                TOOLS_CONFIG['user_activity_analyzer']['venv_path'],
                TOOLS_CONFIG['user_activity_analyzer']['script_path'],
                '--log-file', log_file_path,
                '--output-format', output_format,
                '--sort-by', sort_by,
                '--top-percentile', str(top_percentile)
            ]
            
            # Add optional parameters
            if limit:
                cmd.extend(['--limit', str(limit)])
            if filter_user:
                cmd.extend(['--filter-user', filter_user])
            if date_range and len(date_range) == 2:
                cmd.extend(['--date-range', date_range[0], date_range[1]])
            
            # Execute the tool
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(TOOLS_CONFIG['user_activity_analyzer']['script_path'])
            )
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'output': process.stdout,
                    'error': process.stderr if process.stderr else None
                }
            else:
                return {
                    'success': False,
                    'output': process.stdout,
                    'error': process.stderr
                }
                
        except Exception as e:
            logger.error(f"Error executing User Activity Analyzer tool: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

def save_execution_record(tool_name, status, input_params, output_result, duration):
    """Save execution record to history"""
    record = {
        'id': str(uuid.uuid4()),
        'tool_name': tool_name,
        'execution_time': datetime.now().isoformat(),
        'status': status,
        'input_params': input_params,
        'output_result': output_result,
        'duration_seconds': duration
    }
    execution_history.append(record)
    return record

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/license-management')
def license_management():
    """License management tool page"""
    return render_template('license_management.html')

@app.route('/reqif-comparison')
def reqif_comparison():
    """ReqIF comparison tool page"""
    return render_template('reqif_comparison.html')

@app.route('/user-activity-analyzer')
def user_activity_analyzer():
    """User Activity Analyzer tool page"""
    return render_template('user_activity_analyzer.html')

@app.route('/help')
def help_page():
    """Help and support page"""
    return render_template('help.html')

@app.route('/api/execute-license-management', methods=['POST'])
def api_execute_license_management():
    """API endpoint for executing license management tool"""
    try:
        data = request.get_json()
        license_config = data.get('license_config', '')
        action = data.get('action', 'query')
        user_identifiers = data.get('user_identifiers', '')
        
        # Handle file upload if present
        user_file = None
        if 'user_file' in request.files:
            user_file = request.files['user_file']
        
        start_time = datetime.now()
        
        # Execute the tool
        result = ToolExecutor.execute_license_management(
            license_config=license_config,
            user_file=user_file,
            action=action,
            user_identifiers=user_identifiers
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Save execution record
        execution_record = save_execution_record(
            tool_name=TOOLS_CONFIG['license_management']['name'],
            status='completed' if result['success'] else 'failed',
            input_params={
                'action': action,
                'has_license_config': bool(license_config),
                'has_user_file': bool(user_file),
                'user_identifiers': user_identifiers
            },
            output_result=result['output'],
            duration=duration
        )
        
        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'error': result['error'],
            'execution_id': execution_record['id'],
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error in license management API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/execute-reqif-comparison', methods=['POST'])
def api_execute_reqif_comparison():
    """API endpoint for executing ReqIF comparison tool"""
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both files are required'
            }), 400
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        # Validate file types
        if not file1.filename.endswith('.reqifz') or not file2.filename.endswith('.reqifz'):
            return jsonify({
                'success': False,
                'error': 'Both files must be .reqifz format'
            }), 400
        
        # Save files temporarily
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))
        
        file1.save(file1_path)
        file2.save(file2_path)
        
        start_time = datetime.now()
        
        # Execute the tool
        result = ToolExecutor.execute_reqif_comparison(file1_path, file2_path)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Clean up temp files
        try:
            os.unlink(file1_path)
            os.unlink(file2_path)
        except:
            pass
        
        # Save execution record
        execution_record = save_execution_record(
            tool_name=TOOLS_CONFIG['reqif_comparison']['name'],
            status='completed' if result['success'] else 'failed',
            input_params={
                'file1_name': file1.filename,
                'file2_name': file2.filename,
                'file1_size': file1.content_length,
                'file2_size': file2.content_length
            },
            output_result=result['output'],
            duration=duration
        )
        
        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'error': result['error'],
            'execution_id': execution_record['id'],
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error in ReqIF comparison API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/execute-user-activity-analyzer', methods=['POST'])
def api_execute_user_activity_analyzer():
    """API endpoint for executing User Activity Analyzer tool"""
    try:
        data = request.get_json()
        log_file_path = data.get('log_file_path', '')
        output_format = data.get('output_format', 'table')
        limit = data.get('limit')
        sort_by = data.get('sort_by', 'activity_score')
        filter_user = data.get('filter_user')
        date_range = data.get('date_range')
        top_percentile = data.get('top_percentile', 0.1)
        
        if not log_file_path:
            return jsonify({
                'success': False,
                'error': 'Log file path is required'
            }), 400
        
        start_time = datetime.now()
        
        # Execute the tool
        result = ToolExecutor.execute_user_activity_analyzer(
            log_file_path=log_file_path,
            output_format=output_format,
            limit=limit,
            sort_by=sort_by,
            filter_user=filter_user,
            date_range=date_range,
            top_percentile=top_percentile
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Save execution record
        execution_record = save_execution_record(
            tool_name=TOOLS_CONFIG['user_activity_analyzer']['name'],
            status='completed' if result['success'] else 'failed',
            input_params={
                'log_file_path': log_file_path,
                'output_format': output_format,
                'limit': limit,
                'sort_by': sort_by,
                'filter_user': filter_user,
                'date_range': date_range,
                'top_percentile': top_percentile
            },
            output_result=result['output'],
            duration=duration
        )
        
        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'error': result['error'],
            'execution_id': execution_record['id'],
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error in User Activity Analyzer API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/execution-history')
def api_execution_history():
    """API endpoint for getting execution history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        recent_executions = execution_history[-limit:] if len(execution_history) > limit else execution_history
        return jsonify(recent_executions)
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        return jsonify([])

@app.route('/api/tool-stats')
def api_tool_stats():
    """API endpoint for getting tool statistics"""
    try:
        total_executions = len(execution_history)
        successful_executions = len([e for e in execution_history if e['status'] == 'completed'])
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        return jsonify({
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': round(success_rate, 1),
            'available_tools': len(TOOLS_CONFIG)
        })
    except Exception as e:
        logger.error(f"Error getting tool stats: {e}")
        return jsonify({
            'total_executions': 0,
            'successful_executions': 0,
            'success_rate': 0,
            'available_tools': len(TOOLS_CONFIG)
        })

if __name__ == '__main__':
    print("=" * 60)
    print("Mobileye Business IS Development Tools")
    print("=" * 60)
    print(f"Starting server on http://localhost:5000")
    print(f"Available tools: {len(TOOLS_CONFIG)}")
    for tool_id, config in TOOLS_CONFIG.items():
        print(f"  - {config['name']}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
    #zzz
    