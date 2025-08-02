#!/usr/bin/env python3
"""
Polarion License Management Automation Tool

A comprehensive tool for managing Polarion user licenses with database integration,
license configuration parsing, and safe modification operations.

Author: AI Assistant
Version: 1.0
"""
#test branch2

import re
import sys
import json
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import getpass
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('polarion_license_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """Represents a Polarion user"""
    user_id: str
    full_name: str
    email: str

@dataclass
class LicenseEntry:
    """Represents a license assignment"""
    license_type: str  # ALM, QA, Requirements, Pro, Reviewer
    assignment_type: str  # Named, Concurrent
    index: int
    user_id: str
    line_number: int
    is_active: bool = True

@dataclass
class LicenseChange:
    """Represents a license modification"""
    user_id: str
    user_name: str
    action: str  # 'add', 'remove', 'switch'
    old_license: Optional[str] = None
    new_license: Optional[str] = None
    line_added: Optional[str] = None
    line_removed: Optional[str] = None

class PolarionLicenseManager:
    """Main class for managing Polarion licenses"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.license_entries: List[LicenseEntry] = []
        self.license_config_text: str = ""
        self.changes: List[LicenseChange] = []
        self.db_connection = None
        
        # License categories and their patterns
        self.license_categories = {
            'ALM': 'ALM',
            'QA': 'QA', 
            'Requirements': 'Requirements',
            'Pro': 'Pro',
            'Reviewer': 'Reviewer'
        }
        
        self.assignment_types = ['Named', 'Concurrent']
        
    def connect_to_database(self, host: str, port: int, database: str, username: str, password: str) -> bool:
        """Connect to Polarion PostgreSQL database"""
        try:
            self.db_connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10
            )
            
            # Test the connection
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"Successfully connected to PostgreSQL: {version[0]}")
                
                # Test if polarion schema exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.schemata 
                        WHERE schema_name = 'polarion'
                    );
                """)
                schema_exists = cursor.fetchone()[0]
                
                if not schema_exists:
                    logger.error("Polarion schema not found in database")
                    return False
                
                # Test if t_user table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'polarion' 
                        AND table_name = 't_user'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    logger.error("t_user table not found in polarion schema")
                    return False
                
                logger.info("Database schema validation successful")
                return True
                
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            return False
    
    def test_database_connection(self) -> Dict[str, any]:
        """Test database connection and return detailed status"""
        if not self.db_connection:
            return {
                'connected': False,
                'error': 'No database connection established'
            }
        
        try:
            with self.db_connection.cursor() as cursor:
                # Test basic connection
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                
                # Check schema
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.schemata 
                        WHERE schema_name = 'polarion'
                    );
                """)
                schema_exists = cursor.fetchone()[0]
                
                # Check table
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'polarion' 
                        AND table_name = 't_user'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                # Get table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'polarion' 
                    AND table_name = 't_user'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                # Count users
                cursor.execute("SELECT COUNT(*) FROM polarion.t_user;")
                user_count = cursor.fetchone()[0]
                
                return {
                    'connected': True,
                    'version': version[0],
                    'schema_exists': schema_exists,
                    'table_exists': table_exists,
                    'columns': columns,
                    'user_count': user_count
                }
                
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def get_database_status(self) -> str:
        """Get a formatted string with database status information"""
        status = self.test_database_connection()
        
        if not status['connected']:
            return f"Database Status: DISCONNECTED\nError: {status['error']}"
        
        result = [
            "Database Status: CONNECTED",
            f"PostgreSQL Version: {status['version']}",
            f"Polarion Schema: {'✓' if status['schema_exists'] else '✗'}",
            f"t_user Table: {'✓' if status['table_exists'] else '✗'}",
            f"Total Users in Database: {status['user_count']}",
            f"Users Loaded in Memory: {len(self.users)}"
        ]
        
        if status['columns']:
            result.append("Table Structure:")
            for col in status['columns']:
                result.append(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        return '\n'.join(result)
    
    def fetch_active_users(self) -> bool:
        """Fetch all active users from Polarion database"""
        if not self.db_connection:
            logger.error("No database connection available")
            return False
            
        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # First, let's see what columns are available
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'polarion' 
                    AND table_name = 't_user'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                logger.info(f"Available columns in t_user: {[col['column_name'] for col in columns]}")
                
                # Try different possible column combinations
                possible_queries = [
                    # Standard expected columns
                    """
                    SELECT user_id, full_name, email 
                    FROM polarion.t_user 
                    WHERE user_id IS NOT NULL
                    ORDER BY user_id
                    """,
                    # Alternative column names
                    """
                    SELECT username as user_id, display_name as full_name, email_address as email
                    FROM polarion.t_user 
                    WHERE username IS NOT NULL
                    ORDER BY username
                    """,
                    # Minimal query with just user_id
                    """
                    SELECT user_id, user_id as full_name, user_id as email
                    FROM polarion.t_user 
                    WHERE user_id IS NOT NULL
                    ORDER BY user_id
                    """,
                    # Try with different column names
                    """
                    SELECT id as user_id, name as full_name, email
                    FROM polarion.t_user 
                    WHERE id IS NOT NULL
                    ORDER BY id
                    """
                ]
                
                users_data = None
                successful_query = None
                
                for i, query in enumerate(possible_queries):
                    try:
                        cursor.execute(query)
                        users_data = cursor.fetchall()
                        successful_query = i
                        logger.info(f"Query {i+1} successful, found {len(users_data)} users")
                        break
                    except Exception as e:
                        logger.warning(f"Query {i+1} failed: {e}")
                        continue
                
                if users_data is None:
                    logger.error("All database queries failed")
                    return False
                
                self.users.clear()
                
                for row in users_data:
                    user = User(
                        user_id=str(row['user_id']),
                        full_name=str(row['full_name']) if row['full_name'] else '',
                        email=str(row['email']) if row['email'] else ''
                    )
                    self.users[user.user_id.lower()] = user
                
                logger.info(f"Successfully fetched {len(self.users)} active users from database")
                
                # Log first few users for debugging
                if self.users:
                    sample_users = list(self.users.values())[:5]
                    logger.info(f"Sample users: {[(u.user_id, u.full_name, u.email) for u in sample_users]}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error fetching users from database: {e}")
            return False
    
    def load_users_from_file(self, file_path: str) -> bool:
        """Load users from CSV or Excel file as an alternative to database"""
        try:
            # Automatically detect file type and read
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
                file_type = "CSV"
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
                file_type = "Excel"
            else:
                # Try to read as CSV first, then Excel
                try:
                    df = pd.read_csv(file_path)
                    file_type = "CSV"
                except:
                    df = pd.read_excel(file_path)
                    file_type = "Excel"
            
            logger.info(f"Loading users from {file_type} file: {file_path}")
            logger.info(f"Found {len(df)} rows in the file")
            logger.info(f"Available columns: {list(df.columns)}")
            
            # Clear existing users
            self.users.clear()
            
            # Enhanced column mapping for various file formats
            user_id_col = None
            name_col = None
            email_col = None
            
            # First, try to map specific known column patterns
            for col in df.columns:
                col_lower = col.lower()
                
                # User ID/username columns
                if any(pattern in col_lower for pattern in ['user_id', 'username', 'user', 'login', 'uri']):
                    user_id_col = col
                # Name columns
                elif any(pattern in col_lower for pattern in ['full_name', 'display_name', 'name', 'fullname']):
                    name_col = col
                # Email columns
                elif 'email' in col_lower:
                    email_col = col
            
            # Special handling for common column patterns
            if 'c_pk' in df.columns and 'c_uri' in df.columns:
                # This looks like a Polarion export format
                # But we need to find which column actually contains usernames
                # Let's check if c_uri contains alphanumeric values (usernames) or just numbers
                sample_c_uri = df['c_uri'].head(10).astype(str)
                has_letters_in_c_uri = any(any(c.isalpha() for c in str(val)) for val in sample_c_uri)
                
                if has_letters_in_c_uri:
                    # c_uri contains usernames
                    user_id_col = 'c_uri'
                    name_col = 'c_uri'
                    logger.info("Detected Polarion export format with usernames in c_uri")
                else:
                    # c_uri contains numbers, look for another column with usernames
                    logger.info("c_uri contains numbers, looking for username column...")
                    # First, check for c_id which commonly contains usernames in Polarion exports
                    if 'c_id' in df.columns:
                        sample_c_id = df['c_id'].head(10).astype(str)
                        has_letters_in_c_id = any(any(c.isalpha() for c in str(val)) for val in sample_c_id)
                        if has_letters_in_c_id:
                            user_id_col = 'c_id'
                            logger.info("Found username column: c_id")
                    
                    # If c_id doesn't work, check other columns
                    if not user_id_col:
                        for col in df.columns:
                            if col != 'c_pk' and col != 'c_uri' and col != 'c_id':
                                sample_values = df[col].head(10).astype(str)
                                has_letters = any(any(c.isalpha() for c in str(val)) for val in sample_values)
                                if has_letters:
                                    user_id_col = col
                                    logger.info(f"Found username column: {col}")
                                    break
                    
                    if not user_id_col:
                        # Fallback to c_uri even if it's numeric
                        user_id_col = 'c_uri'
                        logger.info("No username column found, using c_uri as fallback")
                
                # Set name column - prefer c_name if available, otherwise use user_id_col
                if 'c_name' in df.columns:
                    name_col = 'c_name'
                    logger.info("Using c_name for full names")
                else:
                    name_col = user_id_col
                
                if 'c_email' in df.columns:
                    email_col = 'c_email'
            else:
                # Fallback: use first few columns if specific mapping failed
                if not user_id_col and len(df.columns) > 0:
                    user_id_col = df.columns[0]
                if not name_col and len(df.columns) > 1:
                    name_col = df.columns[1]
                if not email_col and len(df.columns) > 2:
                    email_col = df.columns[2]
            
            logger.info(f"Using columns: user_id={user_id_col}, name={name_col}, email={email_col}")
            
            # Process each row
            for index, row in df.iterrows():
                # Debug: Log the raw values being read
                if index < 3:  # Log first 3 rows for debugging
                    logger.info(f"Row {index}: user_id_col='{user_id_col}' value='{row[user_id_col] if user_id_col else 'None'}', name_col='{name_col}' value='{row[name_col] if name_col else 'None'}', email_col='{email_col}' value='{row[email_col] if email_col else 'None'}'")
                
                user_id = str(row[user_id_col]) if user_id_col and pd.notna(row[user_id_col]) else f"user_{index}"
                full_name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else user_id
                email = str(row[email_col]) if email_col and pd.notna(row[email_col]) else ""
                
                # Clean up the data
                user_id = user_id.strip()
                full_name = full_name.strip()
                email = email.strip()
                
                user = User(
                    user_id=user_id,
                    full_name=full_name,
                    email=email
                )
                self.users[user.user_id.lower()] = user
            
            logger.info(f"Successfully loaded {len(self.users)} users from file")
            
            # Log first few users for debugging
            if self.users:
                sample_users = list(self.users.values())[:5]
                logger.info(f"Sample users: {[(u.user_id, u.full_name, u.email) for u in sample_users]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading users from file: {e}")
            return False
    
    def parse_license_configuration(self, config_text: str) -> bool:
        """Parse the license configuration text"""
        self.license_config_text = config_text
        self.license_entries.clear()
        
        lines = config_text.split('\n')
        current_category = None
        current_assignment_type = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for section headers
            if line.startswith('# ------------------------------- POLARION'):
                for category in self.license_categories:
                    if category in line:
                        current_category = category
                        break
                continue
                
            # Check for assignment type headers
            if line.startswith('# NAMED USERS:'):
                current_assignment_type = 'Named'
                continue
            elif line.startswith('# CONCURRENT USERS:'):
                current_assignment_type = 'Concurrent'
                continue
                
            # Parse license assignment lines
            if '=' in line:
                # Check if line is commented out
                is_active = not line.startswith('#')
                if not is_active:
                    line = line[1:].strip()  # Remove comment symbol
                
                # Parse the assignment
                match = re.match(r'(\w+User)(\d+)=(.+)', line)
                if match:
                    prefix, index_str, user_id = match.groups()
                    index = int(index_str)

                    # Skip empty user assignments
                    if not user_id.strip():
                        continue
                    
                    # Determine license category and assignment type from the prefix
                    # Examples: concurrentProUser, namedALMUser, etc.
                    license_category = None
                    assignment_type = None
                    
                    # Check for assignment type first
                    if prefix.lower().startswith('concurrent'):
                        assignment_type = 'Concurrent'
                        # Extract license category from the rest
                        category_part = prefix[10:]  # Remove 'concurrent'
                    elif prefix.lower().startswith('named'):
                        assignment_type = 'Named'
                        # Extract license category from the rest
                        category_part = prefix[5:]  # Remove 'named'
                    else:
                        # Try to infer from the prefix
                        for category in self.license_categories:
                            if category.lower() in prefix.lower():
                                license_category = category
                                break
                        
                        # Default to Concurrent if we can't determine
                        assignment_type = 'Concurrent'
                    
                    # If we haven't determined the license category yet, try to extract it
                    if not license_category:
                        if 'category_part' in locals():
                            # Remove 'User' suffix and capitalize
                            category_part = category_part.replace('User', '')
                            for category in self.license_categories:
                                if category.lower() == category_part.lower():
                                    license_category = category
                                    break
                    
                    # If still no category, try to infer from the prefix
                    if not license_category:
                        for category in self.license_categories:
                            if category.lower() in prefix.lower():
                                license_category = category
                                break
                    
                    # Use current_category/assignment_type only if we couldn't determine from the line itself
                    if not license_category and current_category:
                        license_category = current_category
                    if not assignment_type and current_assignment_type:
                        assignment_type = current_assignment_type
                    
                    # If we still can't determine, skip this entry
                    if not license_category or not assignment_type:
                        logger.warning(f"Could not determine license category or assignment type for line: {line}")
                        continue
                    
                    license_entry = LicenseEntry(
                        license_type=license_category,
                        assignment_type=assignment_type,
                        index=index,
                        user_id=user_id.strip(),
                        line_number=line_num,
                        is_active=is_active
                    )
                    self.license_entries.append(license_entry)
        
        logger.info(f"Parsed {len([e for e in self.license_entries if e.is_active])} active license entries")
        return True
    
    def build_combined_user_license_table(self) -> Dict[str, List[LicenseEntry]]:
        """Build combined table of users and their licenses"""
        user_licenses: Dict[str, List[LicenseEntry]] = {}
        
        # Initialize with all users
        for user_id, user in self.users.items():
            user_licenses[user_id] = []
        
        # Add license assignments
        for entry in self.license_entries:
            if entry.is_active:
                user_id_lower = entry.user_id.lower()
                if user_id_lower in user_licenses:
                    user_licenses[user_id_lower].append(entry)
                else:
                    # User not in active database (stale license)
                    user_licenses[entry.user_id] = [entry]
        
        return user_licenses
    
    def find_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Find user by various identifiers (email, name, user_id)"""
        identifier = identifier.strip().lower()
        
        # Direct user_id match
        if identifier in self.users:
            return self.users[identifier]
        
        # Email match
        for user in self.users.values():
            if user.email.lower() == identifier:
                return user
        
        # Full name match (case insensitive)
        for user in self.users.values():
            if user.full_name.lower() == identifier:
                return user
        
        # Partial name match
        matching_users = []
        for user in self.users.values():
            if identifier in user.full_name.lower() or identifier in user.user_id.lower():
                matching_users.append(user)
        
        if len(matching_users) == 1:
            return matching_users[0]
        elif len(matching_users) > 1:
            logger.warning(f"Multiple users found for '{identifier}': {[u.user_id for u in matching_users]}")
            return None
        
        # If no match found, provide detailed debugging information
        logger.info(f"User '{identifier}' not found.")
        if self.users:
            # Show sample of available user identifiers for debugging
            sample_users = list(self.users.values())[:10]
            available_ids = [f"'{u.user_id}'" for u in sample_users]
            available_names = [f"'{u.full_name}'" for u in sample_users if u.full_name]
            available_emails = [f"'{u.email}'" for u in sample_users if u.email]
            
            debug_info = []
            if available_ids:
                debug_info.append(f"user_ids: {', '.join(available_ids)}")
            if available_names:
                debug_info.append(f"names: {', '.join(available_names)}")
            if available_emails:
                debug_info.append(f"emails: {', '.join(available_emails)}")
            
            logger.info(f"Available identifiers (first 10): {'; '.join(debug_info)}")
        else:
            logger.info("No users loaded in memory")
        
        return None
    
    def query_user_licenses(self, identifiers: List[str]) -> List[Dict]:
        """Query license status for specific users with detailed statistics"""
        results = []
        user_licenses = self.build_combined_user_license_table()
        
        # Calculate overall license statistics
        overall_stats = {}
        for entry in self.license_entries:
            if entry.is_active:
                license_key = f"{entry.assignment_type}{entry.license_type}"
                overall_stats[license_key] = overall_stats.get(license_key, 0) + 1
        
        # Calculate aggregate statistics for queried users only
        queried_users_stats = {}
        queried_users_found = []
        
        for identifier in identifiers:
            user = self.find_user_by_identifier(identifier)
            if user:
                queried_users_found.append(user)
                user_entries = user_licenses.get(user.user_id.lower(), [])
                for entry in user_entries:
                    if entry.is_active:
                        license_key = f"{entry.assignment_type}{entry.license_type}"
                        queried_users_stats[license_key] = queried_users_stats.get(license_key, 0) + 1
        
        # Debug: Log the calculated statistics
        logger.info(f"Overall stats: {overall_stats}")
        logger.info(f"Queried users stats: {queried_users_stats}")
        logger.info(f"Queried users found: {[u.user_id for u in queried_users_found]}")
        
        for identifier in identifiers:
            user = self.find_user_by_identifier(identifier)
            
            if not user:
                results.append({
                    'identifier': identifier,
                    'status': 'not_found',
                    'message': f"User '{identifier}' not found in Polarion system"
                })
                continue
            
            user_entries = user_licenses.get(user.user_id.lower(), [])
            
            if not user_entries:
                results.append({
                    'identifier': identifier,
                    'user': user,
                    'status': 'no_license',
                    'message': f"{user.full_name} - {user.email} - No license assigned"
                })
            else:
                # Build detailed user information with license assignments
                user_license_info = []
                
                for entry in user_entries:
                    if entry.is_active:
                        # Format: concurrentProUser1=dins
                        license_line = f"{entry.assignment_type.lower()}{entry.license_type}User{entry.index}={entry.user_id}"
                        user_license_info.append(license_line)
                
                # Build the detailed message
                if user_license_info:
                    detailed_info = f"{user.full_name} - {user.email} - {', '.join(user_license_info)}"
                    
                    # Add aggregate statistics for queried users only
                    queried_stats_lines = []
                    for license_type, count in queried_users_stats.items():
                        queried_stats_lines.append(f"{license_type} - {count}")
                    
                    # Add overall statistics
                    overall_lines = []
                    for license_type, count in overall_stats.items():
                        overall_lines.append(f"{license_type} - {count}")
                    
                    results.append({
                        'identifier': identifier,
                        'user': user,
                        'status': 'has_license',
                        'licenses': user_license_info,
                        'overall_stats': overall_stats,
                        'queried_users_stats': queried_users_stats,
                        'message': detailed_info,
                        'user_stats_message': '\n'.join(queried_stats_lines),
                        'overall_stats_message': '\n'.join(overall_lines)
                    })
                else:
                    results.append({
                        'identifier': identifier,
                        'user': user,
                        'status': 'no_active_license',
                        'message': f"{user.full_name} - {user.email} - No active license assigned"
                    })
        
        return results
    
    def find_inactive_users_with_licenses(self) -> List[LicenseEntry]:
        """Find users with licenses who are not in the active user database"""
        inactive_entries = []
        
        for entry in self.license_entries:
            if entry.is_active:
                user_id_lower = entry.user_id.lower()
                if user_id_lower not in self.users:
                    inactive_entries.append(entry)
        
        return inactive_entries
    
    def find_available_slot(self, license_type: str, assignment_type: str) -> int:
        """Find the next available slot for a license type"""
        existing_indices = [
            entry.index for entry in self.license_entries
            if entry.license_type == license_type 
            and entry.assignment_type == assignment_type
            and entry.is_active
        ]
        
        if not existing_indices:
            return 1
        
        return max(existing_indices) + 1
    
    def add_user_license(self, user: User, license_type: str, assignment_type: str) -> bool:
        """Add a license for a user"""
        # Check if user already has a license
        user_licenses = self.build_combined_user_license_table()
        existing_licenses = user_licenses.get(user.user_id.lower(), [])
        
        if existing_licenses:
            logger.warning(f"User {user.user_id} already has licenses: {[f'{e.assignment_type} {e.license_type}' for e in existing_licenses]}")
            return False
        
        # Find available slot
        new_index = self.find_available_slot(license_type, assignment_type)
        
        # Create new license entry
        new_entry = LicenseEntry(
            license_type=license_type,
            assignment_type=assignment_type,
            index=new_index,
            user_id=user.user_id,
            line_number=0,  # Will be set when updating text
            is_active=True
        )
        
        self.license_entries.append(new_entry)
        
        # Record change
        change = LicenseChange(
            user_id=user.user_id,
            user_name=user.full_name,
            action='add',
            new_license=f"{assignment_type} {license_type}",
            line_added=f"{assignment_type.lower()}{license_type}User{new_index}={user.user_id}"
        )
        self.changes.append(change)
        
        logger.info(f"Added {assignment_type} {license_type} license for {user.user_id}")
        return True
    
    def remove_user_license(self, user_id: str, license_type: str, assignment_type: str) -> bool:
        """Remove a license for a user"""
        # Find the license entry to remove
        entry_to_remove = None
        for entry in self.license_entries:
            if (entry.user_id.lower() == user_id.lower() and 
                entry.license_type == license_type and 
                entry.assignment_type == assignment_type and 
                entry.is_active):
                entry_to_remove = entry
                break
        
        if not entry_to_remove:
            logger.warning(f"No active {assignment_type} {license_type} license found for user {user_id}")
            return False
        
        # Mark as inactive
        entry_to_remove.is_active = False
        
        # Record change
        user_name = self.users.get(user_id.lower(), User(user_id, user_id, '')).full_name
        change = LicenseChange(
            user_id=user_id,
            user_name=user_name,
            action='remove',
            old_license=f"{assignment_type} {license_type}",
            line_removed=f"{assignment_type.lower()}{license_type}User{entry_to_remove.index}={user_id}"
        )
        self.changes.append(change)
        
        logger.info(f"Removed {assignment_type} {license_type} license for {user_id}")
        return True
    
    def switch_user_license(self, user: User, old_license_type: str, old_assignment_type: str, 
                           new_license_type: str, new_assignment_type: str) -> bool:
        """Switch a user's license from one type to another"""
        # Remove old license
        if not self.remove_user_license(user.user_id, old_license_type, old_assignment_type):
            return False
        
        # Add new license
        if not self.add_user_license(user, new_license_type, new_assignment_type):
            return False
        
        # Update the change record to reflect it's a switch
        if self.changes:
            self.changes[-2].action = 'switch'  # The remove action
            self.changes[-1].action = 'switch'  # The add action
        
        logger.info(f"Switched {user.user_id} from {old_assignment_type} {old_license_type} to {new_assignment_type} {new_license_type}")
        return True
    
    def update_license_config_text(self) -> str:
        """Generate updated license configuration text"""
        lines = self.license_config_text.split('\n')
        updated_lines = lines.copy()
        
        # Sort license entries by category, assignment type, and index
        sorted_entries = sorted(
            self.license_entries,
            key=lambda x: (x.license_type, x.assignment_type, x.index)
        )
        
        # Group entries by category and assignment type
        grouped_entries = {}
        for entry in sorted_entries:
            key = (entry.license_type, entry.assignment_type)
            if key not in grouped_entries:
                grouped_entries[key] = []
            grouped_entries[key].append(entry)
        
        # Rebuild the configuration text
        new_lines = []
        current_category = None
        current_assignment_type = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Keep section headers
            if line_stripped.startswith('# ------------------------------- POLARION'):
                new_lines.append(line)
                for category in self.license_categories:
                    if category in line:
                        current_category = category
                        break
                continue
            
            # Keep assignment type headers
            if line_stripped.startswith('# NAMED USERS:'):
                new_lines.append(line)
                current_assignment_type = 'Named'
                continue
            elif line_stripped.startswith('# CONCURRENT USERS:'):
                new_lines.append(line)
                current_assignment_type = 'Concurrent'
                continue
            
            # Skip old license assignment lines (we'll add them back properly)
            if current_category and current_assignment_type and '=' in line_stripped:
                if re.match(r'(\w+User)(\d+)=(.+)', line_stripped.lstrip('#')):
                    continue
            
            # Keep other lines (comments, empty lines, etc.)
            new_lines.append(line)
        
        # Add license entries in proper order
        for (category, assignment_type), entries in grouped_entries.items():
            # Find the section for this category and assignment type
            section_start = -1
            section_end = -1
            
            for i, line in enumerate(new_lines):
                if f"POLARION {category}" in line:
                    section_start = i
                elif section_start != -1 and line.startswith('# -------------------------------'):
                    section_end = i
                    break
            
            if section_start != -1:
                # Find the assignment type subsection
                subsection_start = -1
                for i in range(section_start, len(new_lines)):
                    if f"# {assignment_type.upper()} USERS:" in new_lines[i]:
                        subsection_start = i + 1
                        break
                
                if subsection_start != -1:
                    # Insert license entries
                    for entry in entries:
                        if entry.is_active:
                            license_line = f"{assignment_type.lower()}{category}User{entry.index}={entry.user_id}"
                        else:
                            license_line = f"# {assignment_type.lower()}{category}User{entry.index}={entry.user_id} (removed)"
                        
                        new_lines.insert(subsection_start, license_line)
                        subsection_start += 1
        
        return '\n'.join(new_lines)
    
    def generate_change_summary(self) -> str:
        """Generate a summary of all changes made"""
        if not self.changes:
            return "No changes were made."
        
        summary = ["\n=== LICENSE CHANGES SUMMARY ===\n"]
        
        added_users = [c for c in self.changes if c.action == 'add']
        removed_users = [c for c in self.changes if c.action == 'remove']
        switched_users = [c for c in self.changes if c.action == 'switch']
        
        if added_users:
            summary.append("ADDED USERS:")
            for change in added_users:
                summary.append(f"  + {change.user_name} ({change.user_id}) - {change.new_license}")
                summary.append(f"    Line added: {change.line_added}")
            summary.append("")
        
        if removed_users:
            summary.append("REMOVED USERS:")
            for change in removed_users:
                summary.append(f"  - {change.user_name} ({change.user_id}) - {change.old_license}")
                summary.append(f"    Line removed: {change.line_removed}")
            summary.append("")
        
        if switched_users:
            summary.append("SWITCHED USERS:")
            # Group switch changes
            switch_groups = {}
            for change in switched_users:
                if change.user_id not in switch_groups:
                    switch_groups[change.user_id] = {'old': None, 'new': None}
                if change.old_license:
                    switch_groups[change.user_id]['old'] = change.old_license
                if change.new_license:
                    switch_groups[change.user_id]['new'] = change.new_license
            
            for user_id, licenses in switch_groups.items():
                user_name = next((c.user_name for c in switched_users if c.user_id == user_id), user_id)
                summary.append(f"  ~ {user_name} ({user_id}) - {licenses['old']} → {licenses['new']}")
            summary.append("")
        
        summary.append(f"Total changes: {len(self.changes)}")
        return '\n'.join(summary)
    
    def validate_changes(self) -> List[str]:
        """Validate proposed changes for potential issues"""
        errors = []
        
        # Check for duplicate active licenses per user
        user_licenses = self.build_combined_user_license_table()
        for user_id, entries in user_licenses.items():
            active_entries = [e for e in entries if e.is_active]
            if len(active_entries) > 1:
                errors.append(f"User {user_id} has multiple active licenses: {[f'{e.assignment_type} {e.license_type}' for e in active_entries]}")
        
        # Check for invalid license assignments
        for entry in self.license_entries:
            if entry.is_active and entry.user_id.lower() not in self.users:
                errors.append(f"Active license for non-existent user: {entry.user_id}")
        
        return errors
    
    def read_excel_or_csv_file(self, file_path: str) -> str:
        """Automatically detect and read Excel or CSV file and convert to license configuration format"""
        try:
            # Automatically detect file type and read
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
                file_type = "CSV"
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
                file_type = "Excel"
            else:
                # Try to read as CSV first, then Excel
                try:
                    df = pd.read_csv(file_path)
                    file_type = "CSV"
                except:
                    df = pd.read_excel(file_path)
                    file_type = "Excel"
            
            print(f"Successfully detected and read {file_type} file: {file_path} sharon")
            print(f"Found {len(df)} rows in the file")
            
            # Convert DataFrame to license configuration text
            config_lines = []
            
            # Add header
            config_lines.append("# ------------------------------- POLARION LICENSE CONFIGURATION -------------------------------")
            config_lines.append(f"# Generated from {file_type} file: {file_path}")
            config_lines.append("")
            
            # Process each row
            for index, row in df.iterrows():
                # Try different possible column names (case-insensitive)
                license_type = str(row.get('License_Type', row.get('license_type', row.get('LicenseType', ''))))
                assignment_type = str(row.get('Assignment_Type', row.get('assignment_type', row.get('AssignmentType', ''))))
                user_id = str(row.get('User_ID', row.get('user_id', row.get('UserID', ''))))
                license_index = str(row.get('Index', row.get('index', '')))
                
                if license_type and assignment_type and user_id:
                    # Format: concurrentALMUser1=user_id
                    config_line = f"{assignment_type.lower()}{license_type}User{license_index}={user_id}"
                    config_lines.append(config_line)
            
            return '\n'.join(config_lines)
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise
    
    def backup_original_config(self) -> str:
        """Create a backup of the original configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"polarion_license_backup_{timestamp}.txt"
        
        try:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.write(self.license_config_text)
            logger.info(f"Backup created: {backup_filename}")
            return backup_filename
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return ""
    
    def parse_mixed_identifiers(self, input_text: str) -> Dict[str, List[str]]:
        """
        Parse mixed identifiers input and categorize them into user_ids, full_names, and emails.
        
        Args:
            input_text: String containing mixed identifiers separated by comma or semicolon
            
        Returns:
            Dictionary with keys 'user_ids', 'full_names', 'emails' containing categorized lists
        """
        # First, normalize separators to commas, then split
        normalized_input = input_text.replace(';', ',')
        
        # Split by comma and clean up identifiers (remove whitespace and empty strings)
        identifiers = [id.strip() for id in normalized_input.split(',') if id.strip()]
        
        # Categorize identifiers
        user_ids = []
        full_names = []
        emails = []
        
        for identifier in identifiers:
            # Check if it's a compound identifier (contains both name and email)
            if ' ' in identifier and '@' in identifier:
                # Try to extract name and email from compound identifier
                parts = identifier.split()
                potential_emails = [part for part in parts if '@' in part and '.' in part]
                potential_names = [part for part in parts if '@' not in part]
                
                if potential_emails and potential_names:
                    # Add the email
                    emails.extend(potential_emails)
                    # Add the name (join remaining parts)
                    name = ' '.join(potential_names)
                    if name.strip():
                        full_names.append(name.strip())
                else:
                    # If we can't clearly separate, treat as email if it contains @
                    if '@' in identifier and '.' in identifier:
                        emails.append(identifier)
                    else:
                        full_names.append(identifier)
            # Check if it's a pure email (contains @ and .)
            elif '@' in identifier and '.' in identifier:
                emails.append(identifier)
            # Check if it's a user_id (no spaces, typically alphanumeric with possible dots/underscores)
            elif ' ' not in identifier and identifier.replace('.', '').replace('_', '').replace('-', '').isalnum():
                user_ids.append(identifier)
            # Otherwise, treat as full name
            else:
                full_names.append(identifier)
        
        return {
            'user_ids': user_ids,
            'full_names': full_names,
            'emails': emails
        }
    
    def find_users_by_mixed_identifiers(self, input_text: str) -> List[User]:
        """
        Find users using mixed identifiers input.
        
        Args:
            input_text: String containing mixed identifiers separated by comma or semicolon
            
        Returns:
            List of found User objects
        """
        categorized = self.parse_mixed_identifiers(input_text)
        found_users = []
        processed_identifiers = set()  # To avoid duplicates
        
        # Process user_ids
        for user_id in categorized['user_ids']:
            if user_id not in processed_identifiers:
                user = self.find_user_by_identifier(user_id)
                if user:
                    found_users.append(user)
                    processed_identifiers.add(user_id)
        
        # Process emails
        for email in categorized['emails']:
            if email not in processed_identifiers:
                user = self.find_user_by_identifier(email)
                if user:
                    found_users.append(user)
                    processed_identifiers.add(email)
        
        # Process full names
        for full_name in categorized['full_names']:
            if full_name not in processed_identifiers:
                user = self.find_user_by_identifier(full_name)
                if user:
                    found_users.append(user)
                    processed_identifiers.add(full_name)
        
        return found_users

def main():
    """Main interactive interface"""
    print("=" * 60)
    print("POLARION LICENSE MANAGEMENT AUTOMATION TOOL")
    print("=" * 60)
    
    manager = PolarionLicenseManager()
    
    # Database connection setup
    print("\n1. DATABASE CONNECTION SETUP")
    print("-" * 30)
    
    use_database = input("Do you want to connect to Polarion database? (y/n): ").lower().strip()
    
    if use_database == 'y':
        host = input("Database host (default: localhost): ").strip() or "localhost"
        port = input("Database port (default: 5432): ").strip() or "5432"
        database = input("Database name: ").strip()
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        try:
            port = int(port)
        except ValueError:
            print("Invalid port number. Using default 5432.")
            port = 5432
        
        if not manager.connect_to_database(host, port, database, username, password):
            print("Failed to connect to database.")
            
            # Offer to load users from file instead
            load_from_file = input("Would you like to load users from a file instead? (y/n): ").lower().strip()
            if load_from_file == 'y':
                user_file = input("Enter path to user file (CSV/Excel): ").strip().strip('"').strip("'")
                if manager.load_users_from_file(user_file):
                    print(f"Successfully loaded {len(manager.users)} users from file.")
                else:
                    print("Failed to load users from file.")
        else:
            if not manager.fetch_active_users():
                print("Failed to fetch users from database.")
                
                # Offer to load users from file instead
                load_from_file = input("Would you like to load users from a file instead? (y/n): ").lower().strip()
                if load_from_file == 'y':
                    user_file = input("Enter path to user file (CSV/Excel): ").strip().strip('"').strip("'")
                    if manager.load_users_from_file(user_file):
                        print(f"Successfully loaded {len(manager.users)} users from file.")
                    else:
                        print("Failed to load users from file.")
    else:
        # Offer to load users from file
        load_from_file = input("Would you like to load users from a file? (y/n): ").lower().strip()
        if load_from_file == 'y':
            user_file = input("Enter path to user file (CSV/Excel): ").strip().strip('"').strip("'")
            if manager.load_users_from_file(user_file):
                print(f"Successfully loaded {len(manager.users)} users from file.")
            else:
                print("Failed to load users from file.")
    
    # Show user loading status
    if manager.users:
        print(f"\n✓ Loaded {len(manager.users)} users successfully")
    else:
        print("\n⚠ Warning: No users loaded. Some features may not work properly.")
        print("You can load users later using option 8 (Database status and connection info)")
    
    # License configuration input
    print("\n2. LICENSE CONFIGURATION INPUT")
    print("-" * 30)
    
    config_source = input("Enter license configuration from (file/excel/paste) or provide file path directly: ").strip()
    
    # Check if user provided a file path directly
    if config_source.lower().endswith(('.csv', '.xlsx', '.xls')) or '\\' in config_source or '/' in config_source:
        # User provided a file path directly
        filename = config_source.strip().strip('"').strip("'")
        try:
            if filename.lower().endswith('.csv') or filename.lower().endswith(('.xlsx', '.xls')):
                # It's an Excel/CSV file
                config_text = manager.read_excel_or_csv_file(filename)
                print(f"Generated configuration with {len(config_text.split(chr(10)))} lines")
            else:
                # Try as regular text file
                with open(filename, 'r', encoding='utf-8') as f:
                    config_text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    elif config_source.lower() == 'file':
        filename = input("Enter filename: ").strip().strip('"').strip("'")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    elif config_source.lower() == 'excel':
        filename = input("Enter Excel/CSV file path: ").strip().strip('"').strip("'")
        try:
            config_text = manager.read_excel_or_csv_file(filename)
            print(f"Generated configuration with {len(config_text.split(chr(10)))} lines")
        except Exception as e:
            print(f"Error reading Excel/CSV file: {e}")
            return
    else:
        print("Paste your license configuration text (press Ctrl+D or Ctrl+Z when done):")
        config_lines = []
        try:
            while True:
                line = input()
                config_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        config_text = '\n'.join(config_lines)
    
    if not manager.parse_license_configuration(config_text):
        print("Failed to parse license configuration.")
        return
    
    # Create backup
    backup_file = manager.backup_original_config()
    if backup_file:
        print(f"Original configuration backed up to: {backup_file}")
    
    # Main menu loop
    while True:
        print("\n" + "=" * 60)
        print("MAIN MENU")
        print("=" * 60)
        print("1. Query user license status")
        print("2. List inactive users with licenses")
        print("3. Add user(s) to license")
        print("4. Remove user(s) from license")
        print("5. Switch user license type")
        print("6. Show current license summary")
        print("7. Apply changes and generate output")
        print("8. Database status and connection info")
        print("9. Exit")
        
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            # Query user licenses
            print("\n--- QUERY USER LICENSE STATUS ---")
            
            # Show database status if no users loaded
            if not manager.users:
                print("Warning: No users loaded from database.")
                print("Please ensure database connection is established and users are fetched.")
                continue
            
            identifiers_input = input("Enter user identifiers (comma or semicolon separated, can mix user IDs, names, emails): ").strip()
            
            # Parse and categorize the input
            categorized = manager.parse_mixed_identifiers(identifiers_input)
            print(f"\nParsed identifiers:")
            if categorized['user_ids']:
                print(f"  User IDs: {', '.join(categorized['user_ids'])}")
            if categorized['full_names']:
                print(f"  Full Names: {', '.join(categorized['full_names'])}")
            if categorized['emails']:
                print(f"  Emails: {', '.join(categorized['emails'])}")
            
            # Get all identifiers as a flat list for processing
            all_identifiers = categorized['user_ids'] + categorized['full_names'] + categorized['emails']
            
            results = manager.query_user_licenses(all_identifiers)
            
            print("Results:")
            
            # Print individual user results first (no extra spaces)
            for result in results:
                print(f"{result['message']}")
            
            # After all individual user results, print the aggregate and overall stats once
            # Check if any user was found with licenses to decide if stats should be printed
            if results and any(r['status'] == 'has_license' for r in results):
                # Get the stats from the first 'has_license' result (they should be the same for all)
                first_has_license_result = next((r for r in results if r['status'] == 'has_license'), None)
                if first_has_license_result:
                    print("\nLicense Allocations for Specified Users")
                    print(f"{first_has_license_result['user_stats_message']}")
                    
                    print("\nOverall License Statistics:")
                    print(f"{first_has_license_result['overall_stats_message']}")
            print()
        
        elif choice == '2':
            # List inactive users
            print("\n--- INACTIVE USERS WITH LICENSES ---")
            inactive_entries = manager.find_inactive_users_with_licenses()
            
            if not inactive_entries:
                print("No inactive users with licenses found.")
            else:
                print(f"Found {len(inactive_entries)} inactive users with licenses:")
                for entry in inactive_entries:
                    print(f"  - {entry.user_id} - {entry.assignment_type} {entry.license_type}")
                
                remove_inactive = input("\nDo you want to remove these inactive users? (y/n): ").lower().strip()
                if remove_inactive == 'y':
                    for entry in inactive_entries:
                        manager.remove_user_license(entry.user_id, entry.license_type, entry.assignment_type)
                    print("Inactive users removed from licenses.")
        
        elif choice == '3':
            # Add users
            print("\n--- ADD USER(S) TO LICENSE ---")
            
            # Show database status if no users loaded
            if not manager.users:
                print("Warning: No users loaded from database.")
                print("Please ensure database connection is established and users are fetched.")
                continue
            
            print("Choose input method:")
            print("1. Enter multiple users at once (comma or semicolon separated)")
            print("2. Enter users one by one")
            
            input_method = input("Select method (1-2): ").strip()
            
            if input_method == '1':
                # Multiple users at once
                identifiers_input = input("Enter user identifiers (comma or semicolon separated, can mix user IDs, names, emails): ").strip()
                
                # Parse and categorize the input
                categorized = manager.parse_mixed_identifiers(identifiers_input)
                print(f"\nParsed identifiers:")
                if categorized['user_ids']:
                    print(f"  User IDs: {', '.join(categorized['user_ids'])}")
                if categorized['full_names']:
                    print(f"  Full Names: {', '.join(categorized['full_names'])}")
                if categorized['emails']:
                    print(f"  Emails: {', '.join(categorized['emails'])}")
                
                # Get all identifiers as a flat list for processing
                all_identifiers = categorized['user_ids'] + categorized['full_names'] + categorized['emails']
                
                # Find all users
                found_users = []
                for identifier in all_identifiers:
                    user = manager.find_user_by_identifier(identifier)
                    if user:
                        found_users.append(user)
                    else:
                        print(f"User '{identifier}' not found. Skipping.")
                
                if not found_users:
                    print("No valid users found. Exiting.")
                    continue
                
                print(f"\nFound {len(found_users)} users:")
                for user in found_users:
                    print(f"  - {user.full_name} ({user.email})")
                
                # Get license type and assignment type for all users
                print("\nAvailable license types:")
                for j, category in enumerate(manager.license_categories.keys(), 1):
                    print(f"  {j}. {category}")
                
                license_choice = int(input("Select license type (1-5): ").strip())
                license_type = list(manager.license_categories.keys())[license_choice - 1]
                
                print("Assignment type:")
                print("  1. Named")
                print("  2. Concurrent")
                assignment_choice = int(input("Select assignment type (1-2): ").strip())
                assignment_type = manager.assignment_types[assignment_choice - 1]
                
                # Add licenses for all found users
                success_count = 0
                for user in found_users:
                    if manager.add_user_license(user, license_type, assignment_type):
                        print(f"Added {assignment_type} {license_type} license for {user.user_id}")
                        success_count += 1
                    else:
                        print(f"Failed to add license for {user.user_id}")
                
                print(f"\nSuccessfully added licenses for {success_count} out of {len(found_users)} users.")
                
            else:
                # Individual users
                num_users = int(input("How many users to add? ").strip())
                
                for i in range(num_users):
                    print(f"\nUser {i+1}:")
                    identifier = input("Enter user identifier (name/email/ID): ").strip()
                    user = manager.find_user_by_identifier(identifier)
                    
                    if not user:
                        print(f"User '{identifier}' not found. Skipping.")
                        continue
                    
                    print(f"Found user: {user.full_name} ({user.email})")
                    
                    print("Available license types:")
                    for j, category in enumerate(manager.license_categories.keys(), 1):
                        print(f"  {j}. {category}")
                    
                    license_choice = int(input("Select license type (1-5): ").strip())
                    license_type = list(manager.license_categories.keys())[license_choice - 1]
                    
                    print("Assignment type:")
                    print("  1. Named")
                    print("  2. Concurrent")
                    assignment_choice = int(input("Select assignment type (1-2): ").strip())
                    assignment_type = manager.assignment_types[assignment_choice - 1]
                    
                    if manager.add_user_license(user, license_type, assignment_type):
                        print(f"Added {assignment_type} {license_type} license for {user.user_id}")
                    else:
                        print(f"Failed to add license for {user.user_id}")
        
        elif choice == '4':
            # Remove users
            print("\n--- REMOVE USER(S) FROM LICENSE ---")
            identifiers_input = input("Enter user identifiers to remove (comma or semicolon separated, can mix user IDs, names, emails): ").strip()
            
            # Parse and categorize the input
            categorized = manager.parse_mixed_identifiers(identifiers_input)
            print(f"\nParsed identifiers:")
            if categorized['user_ids']:
                print(f"  User IDs: {', '.join(categorized['user_ids'])}")
            if categorized['full_names']:
                print(f"  Full Names: {', '.join(categorized['full_names'])}")
            if categorized['emails']:
                print(f"  Emails: {', '.join(categorized['emails'])}")
            
            # Get all identifiers as a flat list for processing
            identifiers = categorized['user_ids'] + categorized['full_names'] + categorized['emails']
            
            user_licenses = manager.build_combined_user_license_table()
            
            for identifier in identifiers:
                user = manager.find_user_by_identifier(identifier)
                if not user:
                    print(f"User '{identifier}' not found. Skipping.")
                    continue
                
                user_entries = user_licenses.get(user.user_id.lower(), [])
                if not user_entries:
                    print(f"User '{identifier}' has no licenses. Skipping.")
                    continue
                
                print(f"\nUser: {user.full_name} ({user.email})")
                print("Current licenses:")
                for j, entry in enumerate(user_entries, 1):
                    print(f"  {j}. {entry.assignment_type} {entry.license_type}")
                
                if len(user_entries) == 1:
                    entry = user_entries[0]
                    if manager.remove_user_license(user.user_id, entry.license_type, entry.assignment_type):
                        print(f"Removed {entry.assignment_type} {entry.license_type} license")
                else:
                    choice = int(input("Select license to remove (1-{}): ".format(len(user_entries))))
                    if 1 <= choice <= len(user_entries):
                        entry = user_entries[choice - 1]
                        
                        if manager.remove_user_license(user.user_id, entry.license_type, entry.assignment_type):
                            print(f"Removed {entry.assignment_type} {entry.license_type} license")
        
        elif choice == '5':
            # Switch licenses
            print("\n--- SWITCH USER LICENSE TYPE ---")
            identifier = input("Enter user identifier: ").strip()
            user = manager.find_user_by_identifier(identifier)
            
            if not user:
                print(f"User '{identifier}' not found.")
                continue
            
            user_licenses = manager.build_combined_user_license_table()
            user_entries = user_licenses.get(user.user_id.lower(), [])
            
            if not user_entries:
                print(f"User '{identifier}' has no licenses to switch.")
                continue
            
            print(f"User: {user.full_name} ({user.email})")
            print("Current licenses:")
            for j, entry in enumerate(user_entries, 1):
                print(f"  {j}. {entry.assignment_type} {entry.license_type}")
            
            old_choice = int(input("Select license to switch from (1-{}): ".format(len(user_entries))))
            if not (1 <= old_choice <= len(user_entries)):
                continue
            
            old_entry = user_entries[old_choice - 1]
            
            print("New license type:")
            for j, category in enumerate(manager.license_categories.keys(), 1):
                print(f"  {j}. {category}")
            
            new_license_choice = int(input("Select new license type (1-5): ").strip())
            new_license_type = list(manager.license_categories.keys())[new_license_choice - 1]
            
            print("New assignment type:")
            print("  1. Named")
            print("  2. Concurrent")
            new_assignment_choice = int(input("Select new assignment type (1-2): ").strip())
            new_assignment_type = manager.assignment_types[new_assignment_choice - 1]
            
            if manager.switch_user_license(user, old_entry.license_type, old_entry.assignment_type, 
                                        new_license_type, new_assignment_type):
                print(f"Switched {user.user_id} from {old_entry.assignment_type} {old_entry.license_type} to {new_assignment_type} {new_license_type}")
        
        elif choice == '6':
            # Show current summary
            print("\n--- CURRENT LICENSE SUMMARY ---")
            user_licenses = manager.build_combined_user_license_table()
            
            print("Active Users with Licenses:")
            for user_id, entries in user_licenses.items():
                if entries:
                    user = manager.users.get(user_id, User(user_id, user_id, ''))
                    license_types = [f"{e.assignment_type} {e.license_type}" for e in entries if e.is_active]
                    if license_types:
                        print(f"  {user.full_name} ({user.email}) - {'; '.join(license_types)}")
            
            print("\nInactive Users with Licenses:")
            inactive_entries = manager.find_inactive_users_with_licenses()
            for entry in inactive_entries:
                print(f"  {entry.user_id} - {entry.assignment_type} {entry.license_type}")
        
        elif choice == '7':
            # Apply changes and generate output
            print("\n--- APPLY CHANGES AND GENERATE OUTPUT ---")
            
            if not manager.changes:
                print("No changes to apply.")
                continue
            
            # Validate changes
            errors = manager.validate_changes()
            if errors:
                print("Validation errors found:")
                for error in errors:
                    print(f"  - {error}")
                continue
            
            # Show change summary
            print(manager.generate_change_summary())
            
            confirm = input("\nApply these changes? (y/n): ").lower().strip()
            if confirm != 'y':
                print("Changes cancelled.")
                continue
            
            # Generate updated configuration
            updated_config = manager.update_license_config_text()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"polarion_license_updated_{timestamp}.txt"
            
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(updated_config)
                print(f"\nUpdated license configuration saved to: {output_filename}")
                
                # Also save change summary
                summary_filename = f"polarion_license_changes_{timestamp}.txt"
                with open(summary_filename, 'w', encoding='utf-8') as f:
                    f.write(manager.generate_change_summary())
                    f.write("\n\n=== UPDATED LICENSE CONFIGURATION ===\n\n")
                    f.write(updated_config)
                print(f"Complete change summary saved to: {summary_filename}")
                
            except Exception as e:
                print(f"Error saving files: {e}")
            
            # Clear changes after successful application
            manager.changes.clear()
        
        elif choice == '8':
            # Database status
            print("\n--- DATABASE STATUS ---")
            print(manager.get_database_status())
            
            if manager.db_connection:
                # Offer to refresh users
                refresh = input("\nDo you want to refresh user data from database? (y/n): ").lower().strip()
                if refresh == 'y':
                    if manager.fetch_active_users():
                        print(f"Successfully refreshed {len(manager.users)} users from database.")
                    else:
                        print("Failed to refresh users from database.")
            else:
                # Offer to load users from file
                load_from_file = input("\nDo you want to load users from a file? (y/n): ").lower().strip()
                if load_from_file == 'y':
                    user_file = input("Enter path to user file (CSV/Excel): ").strip().strip('"').strip("'")
                    if manager.load_users_from_file(user_file):
                        print(f"Successfully loaded {len(manager.users)} users from file.")
                    else:
                        print("Failed to load users from file.")
        
        elif choice == '9':
            # Exit
            if manager.changes:
                print("Warning: You have unsaved changes!")
                save_changes = input("Save changes before exiting? (y/n): ").lower().strip()
                if save_changes == 'y':
                    # Apply the same logic as option 7
                    updated_config = manager.update_license_config_text()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"polarion_license_updated_{timestamp}.txt"
                    
                    try:
                        with open(output_filename, 'w', encoding='utf-8') as f:
                            f.write(updated_config)
                        print(f"Updated license configuration saved to: {output_filename}")
                    except Exception as e:
                        print(f"Error saving file: {e}")
            
            print("Exiting Polarion License Manager.")
            break
        
        else:
            print("Invalid option. Please select 1-9.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An error occurred: {e}")
        print("Check the log file for details.") 