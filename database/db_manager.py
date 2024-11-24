import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'linkedin_content_ai'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.connect()

    def connect(self):
        """Connect to the database, creating it if it doesn't exist"""
        try:
            # Try connecting to the target database
            self.conn = psycopg2.connect(**self.db_params)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                # Connect to default postgres database to create our database
                temp_params = dict(self.db_params)
                temp_params['dbname'] = 'postgres'
                temp_conn = psycopg2.connect(**temp_params)
                temp_conn.autocommit = True
                temp_cur = temp_conn.cursor()
                
                # Create database
                temp_cur.execute(f"CREATE DATABASE {self.db_params['dbname']}")
                
                temp_cur.close()
                temp_conn.close()
                
                # Connect to the newly created database
                self.conn = psycopg2.connect(**self.db_params)
                self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
                
                # Initialize schema
                self.initialize_schema()
            else:
                raise e

    def execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            self.cur.execute(query, params)
            self.conn.commit()
            
            try:
                return self.cur.fetchall()
            except psycopg2.ProgrammingError:
                # No results to fetch (e.g., for INSERT/UPDATE)
                return []
                
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # Try reconnecting once
            self.connect()
            self.cur.execute(query, params)
            self.conn.commit()
            
            try:
                return self.cur.fetchall()
            except psycopg2.ProgrammingError:
                return []

    def get_last_row_id(self) -> int:
        """Get the ID of the last inserted row"""
        self.cur.execute("SELECT lastval()")
        return self.cur.fetchone()['lastval']

    def initialize_schema(self):
        """Initialize the database schema"""
        # Create stories table
        self.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                industry TEXT NOT NULL,
                company_name TEXT NOT NULL,
                company_size TEXT,
                story_type TEXT NOT NULL,
                source TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create posts table
        self.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                story_id INTEGER REFERENCES stories(id),
                content TEXT NOT NULL,
                post_type TEXT NOT NULL,
                scheduled_time TIMESTAMP,
                published BOOLEAN DEFAULT FALSE,
                engagement_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create examples table
        self.execute("""
            CREATE TABLE IF NOT EXISTS examples (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create batches table
        self.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id SERIAL PRIMARY KEY,
                status TEXT NOT NULL,
                total_posts INTEGER NOT NULL,
                approved_posts INTEGER DEFAULT 0,
                rejected_posts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create batch_posts table
        self.execute("""
            CREATE TABLE IF NOT EXISTS batch_posts (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id),
                story_id INTEGER REFERENCES stories(id),
                content TEXT NOT NULL,
                approved BOOLEAN,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def __del__(self):
        """Clean up database connections"""
        if hasattr(self, 'cur') and self.cur is not None:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn is not None:
            self.conn.close()
