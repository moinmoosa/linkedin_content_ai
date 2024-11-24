import os
import sys
from pathlib import Path
import subprocess
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path to import from project
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from database.db_manager import DatabaseManager
from content_engine.story_collector import BusinessStoryCollector

def check_postgres():
    """Check if PostgreSQL server is running"""
    try:
        # Try connecting to default postgres database
        conn = psycopg2.connect(
            dbname='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

def start_postgres():
    """Start PostgreSQL server"""
    try:
        # Check if brew services is available (macOS)
        subprocess.run(['brew', '--version'], check=True, capture_output=True)
        print("Starting PostgreSQL using brew services...")
        subprocess.run(['brew', 'services', 'start', 'postgresql'], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Could not start PostgreSQL. Please ensure it's installed and running.")
        return False

def setup_environment():
    """Setup the environment and database"""
    load_dotenv()
    
    print("Checking PostgreSQL server...")
    if not check_postgres():
        if not start_postgres():
            print("Failed to start PostgreSQL. Please start it manually.")
            return False
    
    try:
        print("Initializing database...")
        db = DatabaseManager()
        
        # Initialize story collector to populate database
        print("Initializing story collector...")
        collector = BusinessStoryCollector()
        
        return True
        
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        return False

if __name__ == "__main__":
    if setup_environment():
        print("Setup completed successfully!")
    else:
        print("Setup failed. Please check the error messages above.")
