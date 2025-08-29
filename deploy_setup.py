#!/usr/bin/env python
"""
Deployment Setup Script for Wingman Flight Logbook
This script helps prepare your Django project for deployment.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("🚀 Wingman Flight Logbook - Deployment Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: manage.py not found. Please run this script from your project root.")
        sys.exit(1)
    
    # Step 1: Install production dependencies
    print("\n📦 Installing production dependencies...")
    run_command("pip install -r requirements.txt", "Installing dependencies")
    
    # Step 2: Run migrations
    print("\n🗄️ Setting up database...")
    run_command("python manage.py makemigrations", "Creating migrations")
    run_command("python manage.py migrate", "Running migrations")
    
    # Step 3: Collect static files
    print("\n📁 Collecting static files...")
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    # Step 4: Generate secret key
    print("\n🔑 Generating secret key...")
    try:
        from django.core.management.utils import get_random_secret_key
        secret_key = get_random_secret_key()
        print(f"✅ Generated Secret Key: {secret_key}")
        print("\n💡 Copy this secret key and use it as your SECRET_KEY environment variable!")
    except ImportError:
        print("❌ Could not generate secret key. Make sure Django is installed.")
    
    # Step 5: Test production settings
    print("\n🧪 Testing production settings...")
    result = run_command("python manage.py check --settings=wingman.production", "Testing production settings")
    
    if result:
        print("\n🎉 Deployment setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Choose a deployment platform (Railway, Render, etc.)")
        print("3. Set up environment variables:")
        print("   - SECRET_KEY: (use the key generated above)")
        print("   - ALLOWED_HOSTS: your-domain.com")
        print("   - DATABASE_URL: (provided by your platform)")
        print("4. Deploy!")
        print("\n📖 See DEPLOYMENT.md for detailed instructions.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
