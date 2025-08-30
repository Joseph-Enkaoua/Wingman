#!/usr/bin/env python
"""
Railway DATABASE_URL Fix Script
This script helps detect and fix Railway PostgreSQL connection issues
"""

import os
import re
import subprocess
import sys

def check_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        result = subprocess.run(['railway', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_railway_variables():
    """Get Railway variables using CLI"""
    if not check_railway_cli():
        print("❌ Railway CLI not found. Please install it first:")
        print("   npm install -g @railway/cli")
        return None
    
    try:
        result = subprocess.run(['railway', 'variables'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"❌ Failed to get Railway variables: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error running Railway CLI: {e}")
        return None

def detect_internal_url(database_url):
    """Detect if DATABASE_URL is using internal Railway hostname"""
    if not database_url:
        return False
    
    internal_patterns = [
        r'railway\.internal',
        r'postgres\.railway\.internal',
        r'\.railway\.internal:'
    ]
    
    for pattern in internal_patterns:
        if re.search(pattern, database_url):
            return True
    return False

def suggest_public_url(database_url):
    """Suggest a public URL format"""
    if not database_url:
        return None
    
    # Extract components from internal URL
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        return None
    
    username, password, host, port, database = match.groups()
    
    # Replace internal hostname with public format
    if 'railway.internal' in host:
        # Suggest the public Railway format
        public_host = f"containers-us-west-XX.railway.app"
        return f"postgresql://{username}:{password}@{public_host}:{port}/{database}"
    
    return None

def main():
    print("=== Railway DATABASE_URL Fix Script ===")
    
    # Check current DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("\nTo fix this:")
        print("1. Go to your Railway dashboard")
        print("2. Select your app service")
        print("3. Go to Variables tab")
        print("4. Add DATABASE_URL with your PostgreSQL connection string")
        return False
    
    print(f"Current DATABASE_URL: {database_url.replace(database_url.split('@')[0].split(':')[-1], '***')}")
    
    # Check if it's using internal URL
    if detect_internal_url(database_url):
        print("❌ Using internal Railway hostname!")
        print("   This will cause connection issues in deployment.")
        
        # Suggest public URL
        public_url = suggest_public_url(database_url)
        if public_url:
            print(f"\n💡 Suggested public URL format:")
            print(f"   {public_url.replace(public_url.split('@')[0].split(':')[-1], '***')}")
        
        print("\n🔧 To fix this:")
        print("1. Go to your Railway PostgreSQL service")
        print("2. Click 'Connect' tab")
        print("3. Copy the 'Public Endpoint' URL")
        print("4. Update DATABASE_URL in your app's Variables")
        
        # Try to get Railway variables
        print("\n📋 Checking Railway variables...")
        variables = get_railway_variables()
        if variables:
            print("Available Railway variables:")
            print(variables)
        
        return False
    else:
        print("✅ DATABASE_URL looks good (not using internal hostname)")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
