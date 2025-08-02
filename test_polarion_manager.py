#!/usr/bin/env python3
"""
Test script for Polarion License Manager

This script helps test the functionality of the Polarion License Manager
without requiring a full database connection.
"""

import sys
import os
from polarion_license_manager import PolarionLicenseManager, User

def test_basic_functionality():
    """Test basic functionality without database connection"""
    print("Testing basic Polarion License Manager functionality...")
    
    manager = PolarionLicenseManager()
    
    # Test user loading from file
    print("\n1. Testing user loading from file...")
    
    # Create a sample user file
    sample_users = """user_id,full_name,email
bshrager,Bob Shrager,bob.shrager@company.com
uhizi,User Hizi,user.hizi@company.com
asegal1,Alice Segal,alice.segal@company.com
ilanc,Ilan Cohen,ilan.cohen@company.com
yossira,Yossi Rabin,yossi.rabin@company.com"""
    
    with open('test_users.csv', 'w') as f:
        f.write(sample_users)
    
    if manager.load_users_from_file('test_users.csv'):
        print(f"✓ Successfully loaded {len(manager.users)} users from test file")
        
        # Test user finding
        print("\n2. Testing user finding...")
        test_identifiers = ['bshrager', 'bob.shrager@company.com', 'Bob Shrager', 'bsh']
        
        for identifier in test_identifiers:
            user = manager.find_user_by_identifier(identifier)
            if user:
                print(f"✓ Found user '{identifier}' -> {user.user_id} ({user.full_name})")
            else:
                print(f"✗ User '{identifier}' not found")
    else:
        print("✗ Failed to load users from test file")
    
    # Test license configuration parsing
    print("\n3. Testing license configuration parsing...")
    
    sample_config = """# ------------------------------- POLARION ALM -------------------------------
# NAMED USERS:
namedALMUser1=bshrager
namedALMUser2=uhizi
# CONCURRENT USERS:
concurrentALMUser1=asegal1
concurrentALMUser2=ilanc

# ------------------------------- POLARION QA -------------------------------
# NAMED USERS:
namedQAUser1=yossira
# CONCURRENT USERS:
concurrentQAUser1=bshrager"""
    
    if manager.parse_license_configuration(sample_config):
        print(f"✓ Successfully parsed license configuration with {len(manager.license_entries)} entries")
        
        # Test user license querying
        print("\n4. Testing user license querying...")
        results = manager.query_user_licenses(['bshrager', 'uhizi', 'asegal1'])
        
        for result in results:
            print(f"  {result['message']}")
    else:
        print("✗ Failed to parse license configuration")
    
    # Test license operations
    print("\n5. Testing license operations...")
    
    # Add a license
    test_user = manager.find_user_by_identifier('ilanc')
    if test_user:
        if manager.add_user_license(test_user, 'Pro', 'Named'):
            print(f"✓ Successfully added Pro license for {test_user.user_id}")
        else:
            print(f"✗ Failed to add license for {test_user.user_id}")
    
    # Remove a license
    if manager.remove_user_license('bshrager', 'ALM', 'Named'):
        print("✓ Successfully removed ALM license for bshrager")
    else:
        print("✗ Failed to remove license for bshrager")
    
    # Generate change summary
    print("\n6. Testing change summary...")
    print(manager.generate_change_summary())
    
    # Clean up test file
    if os.path.exists('test_users.csv'):
        os.remove('test_users.csv')
    
    print("\n✓ Basic functionality test completed!")

def test_database_connection():
    """Test database connection if credentials are provided"""
    print("\nTesting database connection...")
    
    manager = PolarionLicenseManager()
    
    # You can modify these values for testing
    host = input("Database host (or press Enter to skip): ").strip()
    if not host:
        print("Skipping database connection test")
        return
    
    port = input("Database port (default: 5432): ").strip() or "5432"
    database = input("Database name: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    try:
        port = int(port)
    except ValueError:
        print("Invalid port number. Using default 5432.")
        port = 5432
    
    if manager.connect_to_database(host, port, database, username, password):
        print("✓ Database connection successful!")
        
        # Test user fetching
        if manager.fetch_active_users():
            print(f"✓ Successfully fetched {len(manager.users)} users from database")
            
            # Show sample users
            if manager.users:
                sample_users = list(manager.users.values())[:5]
                print("Sample users:")
                for user in sample_users:
                    print(f"  - {user.user_id}: {user.full_name} ({user.email})")
        else:
            print("✗ Failed to fetch users from database")
    else:
        print("✗ Database connection failed")

if __name__ == "__main__":
    print("=" * 60)
    print("POLARION LICENSE MANAGER - TEST SCRIPT")
    print("=" * 60)
    
    test_basic_functionality()
    
    # Uncomment the line below to test database connection
    # test_database_connection()
    
    print("\nTest completed!") 