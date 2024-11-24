import os
import sys
from pathlib import Path

# Add parent directory to path to import from content_engine
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from content_engine.story_collector import BusinessStoryCollector
from database.db_manager import DatabaseManager
import psycopg2
from dotenv import load_dotenv

def initialize_database():
    """Initialize the database and populate it with initial stories"""
    load_dotenv()
    
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
    
    try:
        # Create database if it doesn't exist
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port']
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_params['dbname']}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database {db_params['dbname']}...")
            cur.execute(f"CREATE DATABASE {db_params['dbname']}")
        
        cur.close()
        conn.close()
        
        # Initialize database schema
        db_manager = DatabaseManager()
        schema_path = os.path.join(parent_dir, 'database', 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            db_manager.execute_query(schema_sql)
        
        # Initialize story collector and populate stories
        collector = BusinessStoryCollector()
        print("Populating initial stories...")
        stories_added = collector.populate_initial_stories()
        print(f"Successfully added {stories_added} stories to the database")
        
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    success = initialize_database()
    if success:
        print("Database initialization complete!")
    else:
        print("Database initialization failed!")
