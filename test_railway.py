#!/usr/bin/env python3
"""
Test script to debug Railway deployment
"""

import os
import sys

def main():
    print("=== RAILWAY DEPLOYMENT TEST ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print(f"Environment variables:")
    for key, value in os.environ.items():
        if 'RAILWAY' in key or 'DJANGO' in key:
            print(f"  {key}: {value}")
    
    print("\n=== FILE SYSTEM TEST ===")
    files = os.listdir('.')
    print(f"Files in current directory: {files}")
    
    if 'static' in files:
        static_files = os.listdir('static')
        print(f"Static directory contents: {static_files}")
    
    print("\n=== DJANGO TEST ===")
    try:
        import django
        print("Django imported successfully")
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
        django.setup()
        print("Django setup completed")
        
        from django.conf import settings
        print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"STATIC_URL: {settings.STATIC_URL}")
        print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        
    except Exception as e:
        print(f"Django test failed: {e}")
    
    print("=== TEST COMPLETED ===")

if __name__ == '__main__':
    main()
