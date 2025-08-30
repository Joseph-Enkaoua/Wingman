#!/usr/bin/env python
"""
Railway PostgreSQL Connection Checker
This script helps diagnose database connection issues on Railway
"""

import os
import sys

def check_environment():
    print("=== Railway PostgreSQL Connection Checker ===")
    
    # Check environment variables
    print("\n1. Environment Variables:")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Mask the password for security
        masked_url = database_url.replace(
            database_url.split('@')[0].split(':')[-1], 
            '***'
        )
        print(f"   DATABASE_URL: {masked_url}")
        
        # Parse the URL
        if 'railway.internal' in database_url:
            print("   ⚠️  Using internal Railway hostname")
            print("   💡 Try using the public PostgreSQL endpoint instead")
        elif 'railway.app' in database_url:
            print("   ✅ Using public Railway endpoint")
        else:
            print("   ℹ️  Using custom database endpoint")
    else:
        print("   ❌ DATABASE_URL not set!")
        return False
    
    # Check other relevant variables
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
    print(f"   RAILWAY_ENVIRONMENT: {railway_env}")
    
    return True

def check_network_connectivity():
    print("\n2. Network Connectivity:")
    
    # Try to resolve the hostname
    import socket
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        try:
            # Extract hostname from DATABASE_URL
            hostname = database_url.split('@')[1].split(':')[0]
            print(f"   Testing hostname resolution: {hostname}")
            
            try:
                ip = socket.gethostbyname(hostname)
                print(f"   ✅ Hostname resolved to: {ip}")
            except socket.gaierror as e:
                print(f"   ❌ Hostname resolution failed: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Could not parse DATABASE_URL: {e}")
            return False
    
    return True

def check_postgresql_client():
    print("\n3. PostgreSQL Client:")
    
    try:
        import psycopg2
        print(f"   ✅ psycopg2 version: {psycopg2.__version__}")
    except ImportError:
        print("   ❌ psycopg2 not installed")
        return False
    
    return True

def main():
    print("Checking Railway PostgreSQL configuration...\n")
    
    # Run all checks
    checks = [
        check_environment(),
        check_network_connectivity(),
        check_postgresql_client()
    ]
    
    print("\n=== Summary ===")
    if all(checks):
        print("✅ All basic checks passed")
        print("💡 If you're still having issues, check:")
        print("   - PostgreSQL service is running in Railway")
        print("   - Service is properly linked to your app")
        print("   - Using the correct DATABASE_URL format")
    else:
        print("❌ Some checks failed")
        print("💡 Please fix the issues above before proceeding")
    
    print("\n=== Next Steps ===")
    print("1. Go to your Railway dashboard")
    print("2. Check if PostgreSQL service is running")
    print("3. Verify the service is linked to your app")
    print("4. Copy the correct DATABASE_URL from the PostgreSQL service")
    print("5. Update your app's environment variables")

if __name__ == '__main__':
    main()
