#!/usr/bin/env python3
"""
User Activity and License Analysis CLI Tool

A comprehensive command-line interface for analyzing user login/logout activity
from log files, providing user activity metrics, license-based usage breakdowns,
comprehensive user listing and sorting, advanced system insights, and data visualization.

Author: AI Assistant
Version: 1.0
"""

import re
import sys
import json
import logging
import argparse
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import os
from pathlib import Path
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_activity_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Represents a parsed log entry"""
    timestamp: datetime
    user_id: str
    event_type: str  # 'LOGIN' or 'LOGOUT'
    license_type: Optional[str] = None
    ip_address: Optional[str] = None
    raw_message: str = ""

@dataclass
class UserSession:
    """Represents a user session"""
    user_id: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    license_type: Optional[str] = None
    is_complete: bool = False

@dataclass
class UserActivity:
    """Represents user activity metrics"""
    user_id: str
    total_login_time_hours: float
    average_session_duration_minutes: float
    number_of_sessions: int
    last_login_timestamp: Optional[datetime] = None
    activity_score: float = 0.0
    license_type: Optional[str] = None

@dataclass
class LicenseUsage:
    """Represents license usage metrics"""
    license_type: str
    total_active_time_hours: float
    number_of_unique_users: int
    average_session_duration_minutes: float
    peak_concurrent_users: int

class LogParser:
    """Handles parsing of log files with robust error handling"""
    
    def __init__(self):
        # Regex patterns for different log formats
        self.patterns = {
            'polarion_licensing': re.compile(
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?User \'([^\']+)\' logged (in|out)(?: with (?:named|concurrent) (\w+))?'
            ),
            'generic_login': re.compile(
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(?:login|logon).*?(\w+)',
                re.IGNORECASE
            ),
            'generic_logout': re.compile(
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(?:logout|logoff).*?(\w+)',
                re.IGNORECASE
            )
        }
        
    def parse_log_file(self, file_path: str) -> List[LogEntry]:
        """Parse log file and extract login/logout events"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        entry = self._parse_line(line.strip(), line_num)
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Error parsing line {line_num}: {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"Log file not found: {file_path}")
            return []
        except PermissionError:
            logger.error(f"Permission denied accessing file: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}")
            return []
            
        logger.info(f"Successfully parsed {len(entries)} log entries from {file_path}")
        return entries
    
    def _parse_line(self, line: str, line_num: int) -> Optional[LogEntry]:
        """Parse a single log line"""
        if not line:
            return None
            
        # Try Polarion licensing pattern first
        match = self.patterns['polarion_licensing'].search(line)
        if match:
            timestamp_str, user_id, action, license_type = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                event_type = 'LOGIN' if action == 'in' else 'LOGOUT'
                return LogEntry(
                    timestamp=timestamp,
                    user_id=user_id,
                    event_type=event_type,
                    license_type=license_type,
                    raw_message=line
                )
            except ValueError as e:
                logger.warning(f"Invalid timestamp format on line {line_num}: {e}")
                return None
        
        # Try generic patterns
        login_match = self.patterns['generic_login'].search(line)
        if login_match:
            timestamp_str, user_id = login_match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                return LogEntry(
                    timestamp=timestamp,
                    user_id=user_id,
                    event_type='LOGIN',
                    raw_message=line
                )
            except ValueError:
                return None
                
        logout_match = self.patterns['generic_logout'].search(line)
        if logout_match:
            timestamp_str, user_id = logout_match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                return LogEntry(
                    timestamp=timestamp,
                    user_id=user_id,
                    event_type='LOGOUT',
                    raw_message=line
                )
            except ValueError:
                return None
                
        return None

class SessionManager:
    """Manages user session reconstruction and analysis"""
    
    def __init__(self, timeout_minutes: int = 30):
        self.timeout_minutes = timeout_minutes
        
    def reconstruct_sessions(self, entries: List[LogEntry]) -> List[UserSession]:
        """Reconstruct user sessions from login/logout events"""
        sessions = []
        
        # Group entries by user
        user_entries = {}
        for entry in entries:
            if entry.user_id not in user_entries:
                user_entries[entry.user_id] = []
            user_entries[entry.user_id].append(entry)
        
        # Process each user's entries
        for user_id, user_entries_list in user_entries.items():
            user_sessions = self._process_user_sessions(user_id, user_entries_list)
            sessions.extend(user_sessions)
            
        logger.info(f"Reconstructed {len(sessions)} sessions for {len(user_entries)} users")
        return sessions
    
    def _process_user_sessions(self, user_id: str, entries: List[LogEntry]) -> List[UserSession]:
        """Process sessions for a single user"""
        sessions = []
        entries.sort(key=lambda x: x.timestamp)
        
        current_login = None
        
        for entry in entries:
            if entry.event_type == 'LOGIN':
                # If there's already a login, create a session with timeout
                if current_login:
                    timeout_logout = current_login.timestamp + timedelta(minutes=self.timeout_minutes)
                    session = UserSession(
                        user_id=user_id,
                        login_time=current_login.timestamp,
                        logout_time=timeout_logout,
                        duration_minutes=(timeout_logout - current_login.timestamp).total_seconds() / 60,
                        license_type=current_login.license_type,
                        is_complete=False
                    )
                    sessions.append(session)
                
                current_login = entry
                
            elif entry.event_type == 'LOGOUT' and current_login:
                # Complete session
                duration = (entry.timestamp - current_login.timestamp).total_seconds() / 60
                session = UserSession(
                    user_id=user_id,
                    login_time=current_login.timestamp,
                    logout_time=entry.timestamp,
                    duration_minutes=duration,
                    license_type=current_login.license_type,
                    is_complete=True
                )
                sessions.append(session)
                current_login = None
        
        # Handle incomplete session at the end
        if current_login:
            # Assume session ends at the last entry timestamp + timeout
            last_timestamp = entries[-1].timestamp
            timeout_logout = last_timestamp + timedelta(minutes=self.timeout_minutes)
            session = UserSession(
                user_id=user_id,
                login_time=current_login.timestamp,
                logout_time=timeout_logout,
                duration_minutes=(timeout_logout - current_login.timestamp).total_seconds() / 60,
                license_type=current_login.license_type,
                is_complete=False
            )
            sessions.append(session)
            
        return sessions

class ActivityAnalyzer:
    """Analyzes user activity and generates metrics"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        
    def analyze_user_activity(self, sessions: List[UserSession]) -> List[UserActivity]:
        """Analyze user activity and generate metrics"""
        user_activities = {}
        
        for session in sessions:
            if session.user_id not in user_activities:
                user_activities[session.user_id] = {
                    'total_time': 0.0,
                    'sessions': [],
                    'last_login': None,
                    'license_type': session.license_type
                }
            
            user_data = user_activities[session.user_id]
            user_data['total_time'] += session.duration_minutes or 0
            user_data['sessions'].append(session)
            
            if not user_data['last_login'] or session.login_time > user_data['last_login']:
                user_data['last_login'] = session.login_time
        
        # Convert to UserActivity objects
        activities = []
        for user_id, data in user_activities.items():
            total_hours = data['total_time'] / 60
            avg_duration = data['total_time'] / len(data['sessions']) if data['sessions'] else 0
            activity_score = self._calculate_activity_score(data)
            
            activity = UserActivity(
                user_id=user_id,
                total_login_time_hours=total_hours,
                average_session_duration_minutes=avg_duration,
                number_of_sessions=len(data['sessions']),
                last_login_timestamp=data['last_login'],
                activity_score=activity_score,
                license_type=data['license_type']
            )
            activities.append(activity)
        
        return activities
    
    def _calculate_activity_score(self, user_data: Dict) -> float:
        """Calculate user activity score (0-100)"""
        # Simple scoring based on total time and session count
        total_hours = user_data['total_time'] / 60
        session_count = len(user_data['sessions'])
        
        # Normalize scores (assuming reasonable ranges)
        time_score = min(total_hours / 40, 1.0) * 50  # Max 40 hours = 50 points
        session_score = min(session_count / 20, 1.0) * 50  # Max 20 sessions = 50 points
        
        return min(time_score + session_score, 100.0)
    
    def analyze_license_usage(self, sessions: List[UserSession]) -> List[LicenseUsage]:
        """Analyze license usage patterns"""
        license_data = {}
        
        for session in sessions:
            license_type = session.license_type or 'Unknown'
            if license_type not in license_data:
                license_data[license_type] = {
                    'total_time': 0.0,
                    'users': set(),
                    'sessions': [],
                    'concurrent_users': {}
                }
            
            data = license_data[license_type]
            data['total_time'] += session.duration_minutes or 0
            data['users'].add(session.user_id)
            data['sessions'].append(session)
            
            # Track concurrent users by hour
            if session.login_time and session.logout_time:
                current = session.login_time.replace(minute=0, second=0, microsecond=0)
                end = session.logout_time.replace(minute=0, second=0, microsecond=0)
                
                while current <= end:
                    hour_key = current.strftime('%Y-%m-%d %H:00')
                    if hour_key not in data['concurrent_users']:
                        data['concurrent_users'][hour_key] = set()
                    data['concurrent_users'][hour_key].add(session.user_id)
                    current += timedelta(hours=1)
        
        # Convert to LicenseUsage objects
        license_usages = []
        for license_type, data in license_data.items():
            avg_duration = data['total_time'] / len(data['sessions']) if data['sessions'] else 0
            peak_concurrent = max(len(users) for users in data['concurrent_users'].values()) if data['concurrent_users'] else 0
            
            usage = LicenseUsage(
                license_type=license_type,
                total_active_time_hours=data['total_time'] / 60,
                number_of_unique_users=len(data['users']),
                average_session_duration_minutes=avg_duration,
                peak_concurrent_users=peak_concurrent
            )
            license_usages.append(usage)
        
        return license_usages

class DataVisualizer:
    """Handles data visualization and chart generation"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set Seaborn style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
    def create_user_activity_charts(self, activities: List[UserActivity]) -> List[str]:
        """Create user activity visualization charts"""
        if not activities:
            return []
            
        df = pd.DataFrame([asdict(activity) for activity in activities])
        df['last_login_timestamp'] = pd.to_datetime(df['last_login_timestamp'])
        
        chart_files = []
        
        # 1. User Activity Score Distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['activity_score'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('User Activity Score Distribution')
        plt.xlabel('Activity Score')
        plt.ylabel('Number of Users')
        plt.grid(True, alpha=0.3)
        
        chart_file = self.output_dir / "user_activity_score_distribution.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(str(chart_file))
        
        # 2. Top Users by Login Time
        top_users = df.nlargest(20, 'total_login_time_hours')
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(top_users)), top_users['total_login_time_hours'])
        plt.yticks(range(len(top_users)), top_users['user_id'])
        plt.xlabel('Total Login Time (Hours)')
        plt.title('Top 20 Users by Total Login Time')
        plt.gca().invert_yaxis()
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{width:.1f}h', ha='left', va='center')
        
        chart_file = self.output_dir / "top_users_by_login_time.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(str(chart_file))
        
        # 3. Session Duration Analysis
        plt.figure(figsize=(10, 6))
        plt.scatter(df['number_of_sessions'], df['average_session_duration_minutes'], 
                   alpha=0.6, s=50)
        plt.xlabel('Number of Sessions')
        plt.ylabel('Average Session Duration (Minutes)')
        plt.title('Session Count vs Average Duration')
        plt.grid(True, alpha=0.3)
        
        chart_file = self.output_dir / "session_analysis.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(str(chart_file))
        
        return chart_files
    
    def create_license_usage_charts(self, license_usages: List[LicenseUsage]) -> List[str]:
        """Create license usage visualization charts"""
        if not license_usages:
            return []
            
        df = pd.DataFrame([asdict(usage) for usage in license_usages])
        
        chart_files = []
        
        # 1. License Usage Comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Total active time by license
        bars1 = ax1.bar(df['license_type'], df['total_active_time_hours'])
        ax1.set_title('Total Active Time by License Type')
        ax1.set_ylabel('Hours')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}h', ha='center', va='bottom')
        
        # Number of unique users by license
        bars2 = ax2.bar(df['license_type'], df['number_of_unique_users'], color='orange')
        ax2.set_title('Number of Unique Users by License Type')
        ax2.set_ylabel('Users')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        chart_file = self.output_dir / "license_usage_comparison.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(str(chart_file))
        
        # 2. Peak Concurrent Users
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['license_type'], df['peak_concurrent_users'], color='lightgreen')
        plt.title('Peak Concurrent Users by License Type')
        plt.ylabel('Peak Concurrent Users')
        plt.xticks(rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        chart_file = self.output_dir / "peak_concurrent_users.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(str(chart_file))
        
        return chart_files

class CLI:
    """Command-line interface for the user activity analyzer"""
    
    def __init__(self):
        self.parser = LogParser()
        self.analyzer = ActivityAnalyzer()
        self.visualizer = DataVisualizer()
        
    def run(self):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description="User Activity and License Analysis CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python user_activity_analyzer.py --log-file "license logs/log4j-licensing-20250805-0022-03.log.2025-08-05-1"
  python user_activity_analyzer.py --log-file "license logs/*.log" --output-format json
  python user_activity_analyzer.py --log-file "license logs/" --top-percentile 0.1 --generate-charts
            """
        )
        
        parser.add_argument(
            '--log-file', '-f',
            required=True,
            help='Path to log file(s). Supports glob patterns and directories.'
        )
        
        parser.add_argument(
            '--output-format', '-o',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format for results (default: table)'
        )
        
        parser.add_argument(
            '--top-percentile', '-p',
            type=float,
            default=0.1,
            help='Top percentile for outlier analysis (default: 0.1)'
        )
        
        parser.add_argument(
            '--generate-charts', '-c',
            action='store_true',
            help='Generate visualization charts'
        )
        
        parser.add_argument(
            '--sort-by',
            choices=['user_id', 'total_login_time', 'activity_score', 'sessions'],
            default='activity_score',
            help='Sort users by metric (default: activity_score)'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of results displayed'
        )
        
        parser.add_argument(
            '--filter-user',
            help='Filter results by user ID (supports partial matches)'
        )
        
        parser.add_argument(
            '--date-range',
            nargs=2,
            metavar=('START_DATE', 'END_DATE'),
            help='Filter by date range (YYYY-MM-DD format)'
        )
        
        args = parser.parse_args()
        
        try:
            self._process_analysis(args)
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            sys.exit(1)
    
    def _process_analysis(self, args):
        """Process the analysis based on command line arguments"""
        print("🔍 User Activity and License Analysis CLI Tool")
        print("=" * 50)
        
        # Find log files
        log_files = self._find_log_files(args.log_file)
        if not log_files:
            print(f"❌ No log files found matching: {args.log_file}")
            return
        
        print(f"📁 Found {len(log_files)} log file(s)")
        
        # Parse log files
        print("📖 Parsing log files...")
        all_entries = []
        for log_file in log_files:
            entries = self.parser.parse_log_file(log_file)
            all_entries.extend(entries)
        
        if not all_entries:
            print("❌ No valid log entries found")
            return
        
        print(f"✅ Parsed {len(all_entries)} log entries")
        
        # Reconstruct sessions
        print("🔄 Reconstructing user sessions...")
        sessions = self.analyzer.session_manager.reconstruct_sessions(all_entries)
        print(f"✅ Reconstructed {len(sessions)} sessions")
        
        # Analyze user activity
        print("📊 Analyzing user activity...")
        activities = self.analyzer.analyze_user_activity(sessions)
        print(f"✅ Analyzed activity for {len(activities)} users")
        
        # Analyze license usage
        print("🔑 Analyzing license usage...")
        license_usages = self.analyzer.analyze_license_usage(sessions)
        print(f"✅ Analyzed usage for {len(license_usages)} license types")
        
        # Apply filters
        activities = self._apply_filters(activities, args)
        
        # Generate charts if requested
        if args.generate_charts:
            print("📈 Generating visualization charts...")
            user_charts = self.visualizer.create_user_activity_charts(activities)
            license_charts = self.visualizer.create_license_usage_charts(license_usages)
            print(f"✅ Generated {len(user_charts) + len(license_charts)} charts in 'charts' directory")
        
        # Display results
        self._display_results(activities, license_usages, args)
        
        # Display outlier analysis
        self._display_outlier_analysis(activities, args.top_percentile)
    
    def _find_log_files(self, pattern: str) -> List[str]:
        """Find log files based on pattern"""
        from glob import glob
        
        if os.path.isdir(pattern):
            # Directory - find all log files
            log_files = []
            for ext in ['*.log', '*.txt']:
                log_files.extend(glob(os.path.join(pattern, ext)))
                log_files.extend(glob(os.path.join(pattern, '**', ext), recursive=True))
            return log_files
        else:
            # File or glob pattern
            return glob(pattern)
    
    def _apply_filters(self, activities: List[UserActivity], args) -> List[UserActivity]:
        """Apply filters to activities"""
        filtered = activities
        
        # Filter by user
        if args.filter_user:
            filtered = [a for a in filtered if args.filter_user.lower() in a.user_id.lower()]
        
        # Filter by date range
        if args.date_range:
            start_date, end_date = args.date_range
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                filtered = [a for a in filtered if a.last_login_timestamp and 
                          start_dt <= a.last_login_timestamp < end_dt]
            except ValueError:
                print("⚠️  Invalid date format. Use YYYY-MM-DD")
        
        # Sort
        reverse = True if args.sort_by in ['total_login_time', 'activity_score', 'sessions'] else False
        if args.sort_by == 'total_login_time':
            filtered.sort(key=lambda x: x.total_login_time_hours, reverse=reverse)
        elif args.sort_by == 'activity_score':
            filtered.sort(key=lambda x: x.activity_score, reverse=reverse)
        elif args.sort_by == 'sessions':
            filtered.sort(key=lambda x: x.number_of_sessions, reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.user_id, reverse=reverse)
        
        # Limit
        if args.limit:
            filtered = filtered[:args.limit]
        
        return filtered
    
    def _display_results(self, activities: List[UserActivity], license_usages: List[LicenseUsage], args):
        """Display analysis results"""
        print("\n" + "=" * 50)
        print("📊 USER ACTIVITY SUMMARY")
        print("=" * 50)
        
        if args.output_format == 'json':
            self._display_json(activities, license_usages)
        elif args.output_format == 'csv':
            self._display_csv(activities, license_usages)
        else:
            self._display_table(activities, license_usages)
        
        print("\n" + "=" * 50)
        print("🔑 LICENSE USAGE SUMMARY")
        print("=" * 50)
        self._display_license_summary(license_usages)
    
    def _display_table(self, activities: List[UserActivity], license_usages: List[LicenseUsage]):
        """Display results in table format"""
        if not activities:
            print("No user activity data to display")
            return
        
        # Prepare data for tabulation
        table_data = []
        for activity in activities:
            table_data.append([
                activity.user_id,
                f"{activity.total_login_time_hours:.1f}",
                f"{activity.average_session_duration_minutes:.1f}",
                activity.number_of_sessions,
                f"{activity.activity_score:.1f}",
                activity.license_type or "Unknown",
                activity.last_login_timestamp.strftime('%Y-%m-%d %H:%M') if activity.last_login_timestamp else "N/A"
            ])
        
        headers = ["User ID", "Total Hours", "Avg Session (min)", "Sessions", "Activity Score", "License", "Last Login"]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid", numalign="right"))
    
    def _display_json(self, activities: List[UserActivity], license_usages: List[LicenseUsage]):
        """Display results in JSON format"""
        output = {
            'user_activities': [asdict(activity) for activity in activities],
            'license_usages': [asdict(usage) for usage in license_usages],
            'summary': {
                'total_users': len(activities),
                'total_license_types': len(license_usages),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        # Convert datetime objects to strings for JSON serialization
        for activity in output['user_activities']:
            if activity['last_login_timestamp']:
                activity['last_login_timestamp'] = activity['last_login_timestamp'].isoformat()
        
        print(json.dumps(output, indent=2))
    
    def _display_csv(self, activities: List[UserActivity], license_usages: List[LicenseUsage]):
        """Display results in CSV format"""
        import csv
        import io
        
        # User activities CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ["User ID", "Total Hours", "Avg Session (min)", "Sessions", "Activity Score", "License", "Last Login"]
        writer.writerow(headers)
        
        for activity in activities:
            writer.writerow([
                activity.user_id,
                f"{activity.total_login_time_hours:.1f}",
                f"{activity.average_session_duration_minutes:.1f}",
                activity.number_of_sessions,
                f"{activity.activity_score:.1f}",
                activity.license_type or "Unknown",
                activity.last_login_timestamp.strftime('%Y-%m-%d %H:%M') if activity.last_login_timestamp else "N/A"
            ])
        
        print("User Activities:")
        print(output.getvalue())
        
        # License usage CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ["License Type", "Total Hours", "Unique Users", "Avg Session (min)", "Peak Concurrent"]
        writer.writerow(headers)
        
        for usage in license_usages:
            writer.writerow([
                usage.license_type,
                f"{usage.total_active_time_hours:.1f}",
                usage.number_of_unique_users,
                f"{usage.average_session_duration_minutes:.1f}",
                usage.peak_concurrent_users
            ])
        
        print("\nLicense Usage:")
        print(output.getvalue())
    
    def _display_license_summary(self, license_usages: List[LicenseUsage]):
        """Display license usage summary"""
        if not license_usages:
            print("No license usage data to display")
            return
        
        table_data = []
        for usage in license_usages:
            table_data.append([
                usage.license_type,
                f"{usage.total_active_time_hours:.1f}",
                usage.number_of_unique_users,
                f"{usage.average_session_duration_minutes:.1f}",
                usage.peak_concurrent_users
            ])
        
        headers = ["License Type", "Total Hours", "Unique Users", "Avg Session (min)", "Peak Concurrent"]
        print(tabulate(table_data, headers=headers, tablefmt="grid", numalign="right"))
    
    def _display_outlier_analysis(self, activities: List[UserActivity], percentile: float):
        """Display outlier analysis (top/bottom percentile)"""
        if not activities:
            return
        
        print("\n" + "=" * 50)
        print(f"🎯 OUTLIER ANALYSIS (Top/Bottom {percentile*100}%)")
        print("=" * 50)
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([asdict(activity) for activity in activities])
        
        # Top percentile users by activity score
        top_threshold = df['activity_score'].quantile(1 - percentile)
        top_users = df[df['activity_score'] >= top_threshold]
        
        print(f"\n🏆 TOP {percentile*100}% USERS BY ACTIVITY SCORE:")
        print(f"Threshold: {top_threshold:.1f}")
        
        top_table_data = []
        for _, row in top_users.head(10).iterrows():
            top_table_data.append([
                row['user_id'],
                f"{row['activity_score']:.1f}",
                f"{row['total_login_time_hours']:.1f}",
                row['number_of_sessions']
            ])
        
        headers = ["User ID", "Activity Score", "Total Hours", "Sessions"]
        print(tabulate(top_table_data, headers=headers, tablefmt="grid", numalign="right"))
        
        # Bottom percentile users
        bottom_threshold = df['activity_score'].quantile(percentile)
        bottom_users = df[df['activity_score'] <= bottom_threshold]
        
        print(f"\n📉 BOTTOM {percentile*100}% USERS BY ACTIVITY SCORE:")
        print(f"Threshold: {bottom_threshold:.1f}")
        
        bottom_table_data = []
        for _, row in bottom_users.head(10).iterrows():
            bottom_table_data.append([
                row['user_id'],
                f"{row['activity_score']:.1f}",
                f"{row['total_login_time_hours']:.1f}",
                row['number_of_sessions']
            ])
        
        print(tabulate(bottom_table_data, headers=headers, tablefmt="grid", numalign="right"))

def main():
    """Main entry point"""
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main() 