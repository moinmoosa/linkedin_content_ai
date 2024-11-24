import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_path: str = "stories.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create stories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    summary TEXT,
                    content TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    industry TEXT,
                    story_type TEXT,
                    meta_tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_story(self, story: Dict) -> bool:
        """Save a story to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO stories (
                        title, company_name, summary, content, url, source,
                        industry, story_type, meta_tags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    story['title'],
                    story['company_name'],
                    story.get('summary', ''),
                    story['content'],
                    story.get('url', ''),
                    story.get('source', ''),
                    story.get('industry', ''),
                    story.get('story_type', ''),
                    str(story.get('meta_tags', {})),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving story: {str(e)}")
            return False
    
    def get_story(self, story_id: int) -> Optional[Dict]:
        """Retrieve a story by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'title': row[1],
                        'company_name': row[2],
                        'summary': row[3],
                        'content': row[4],
                        'url': row[5],
                        'source': row[6],
                        'industry': row[7],
                        'story_type': row[8],
                        'meta_tags': eval(row[9]),
                        'created_at': row[10]
                    }
                return None
                
        except Exception as e:
            print(f"Error getting story: {str(e)}")
            return None
    
    def get_stories(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve multiple stories with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM stories
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                rows = cursor.fetchall()
                return [{
                    'id': row[0],
                    'title': row[1],
                    'company_name': row[2],
                    'summary': row[3],
                    'content': row[4],
                    'url': row[5],
                    'source': row[6],
                    'industry': row[7],
                    'story_type': row[8],
                    'meta_tags': eval(row[9]),
                    'created_at': row[10]
                } for row in rows]
                
        except Exception as e:
            print(f"Error getting stories: {str(e)}")
            return []
    
    def get_stories_by_industry(self, industry: str, limit: int = 100) -> List[Dict]:
        """Retrieve stories filtered by industry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM stories
                    WHERE industry = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (industry, limit))
                
                rows = cursor.fetchall()
                return [{
                    'id': row[0],
                    'title': row[1],
                    'company_name': row[2],
                    'summary': row[3],
                    'content': row[4],
                    'url': row[5],
                    'source': row[6],
                    'industry': row[7],
                    'story_type': row[8],
                    'meta_tags': eval(row[9]),
                    'created_at': row[10]
                } for row in rows]
                
        except Exception as e:
            print(f"Error getting stories by industry: {str(e)}")
            return []
    
    def get_stories_by_type(self, story_type: str, limit: int = 100) -> List[Dict]:
        """Retrieve stories filtered by type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM stories
                    WHERE story_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (story_type, limit))
                
                rows = cursor.fetchall()
                return [{
                    'id': row[0],
                    'title': row[1],
                    'company_name': row[2],
                    'summary': row[3],
                    'content': row[4],
                    'url': row[5],
                    'source': row[6],
                    'industry': row[7],
                    'story_type': row[8],
                    'meta_tags': eval(row[9]),
                    'created_at': row[10]
                } for row in rows]
                
        except Exception as e:
            print(f"Error getting stories by type: {str(e)}")
            return []
