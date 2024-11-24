from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta
import sqlite3
import os
from database.db_manager import DatabaseManager
from content_engine.story_collector import BusinessStoryCollector

class PostRecommender:
    """Recommender system for LinkedIn posts with feedback tracking"""
    
    FEEDBACK_OPTIONS = {
        1: "Too technical - needs simpler language",
        2: "Not technical enough - needs more depth",
        3: "Wrong tone/style for my audience",
        4: "Missing key information/context",
        5: "Not engaging enough"
    }
    
    def __init__(self, db_path: str = "post_feedback.db"):
        """Initialize the recommender system"""
        self.db_path = db_path
        self.db_manager = DatabaseManager()
        self.story_collector = BusinessStoryCollector()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    post_type TEXT NOT NULL,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    batch_id INTEGER,
                    feedback_received BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    feedback_type TEXT NOT NULL,
                    feedback_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (post_id)
                )
            """)
            
            # Create batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.commit()

    def create_batch(self) -> int:
        """Create a new batch and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO batches (status) VALUES ('pending')")
            conn.commit()
            return cursor.lastrowid

    def get_current_batch_status(self) -> Optional[Dict]:
        """Get status of the most recent batch"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.batch_id, b.status, 
                       COUNT(p.post_id) as total_posts,
                       SUM(CASE WHEN p.feedback_received THEN 1 ELSE 0 END) as posts_with_feedback
                FROM batches b
                LEFT JOIN posts p ON b.batch_id = p.batch_id
                WHERE b.status = 'pending'
                GROUP BY b.batch_id
                ORDER BY b.created_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                batch_id, status, total_posts, posts_with_feedback = result
                return {
                    'batch_id': batch_id,
                    'status': status,
                    'total_posts': total_posts or 0,
                    'posts_with_feedback': posts_with_feedback or 0
                }
            return None

    def mark_batch_complete(self, batch_id: int):
        """Mark a batch as complete"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE batches 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, (batch_id,))
            conn.commit()

    def save_post(self, content: str, company_name: str, industry: str, post_type: str, metrics: Dict, batch_id: Optional[int] = None) -> int:
        """Save generated post to database"""
        metrics_json = json.dumps(metrics)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posts (content, company_name, industry, post_type, metrics, batch_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (content, company_name, industry, post_type, metrics_json, batch_id))
            conn.commit()
            return cursor.lastrowid

    def save_feedback(self, post_id: int, feedback_type: str, feedback_text: Optional[str] = None):
        """Save feedback for a post"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (post_id, feedback_type, feedback_text)
                VALUES (?, ?, ?)
            """, (post_id, feedback_type, feedback_text))
            
            # Mark post as having received feedback
            cursor.execute("""
                UPDATE posts
                SET feedback_received = TRUE
                WHERE post_id = ?
            """, (post_id,))
            
            conn.commit()

    def get_batch_posts(self, batch_id: int) -> List[Dict]:
        """Get all posts for a specific batch"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT post_id, content, company_name, industry, post_type, feedback_received
                FROM posts
                WHERE batch_id = ?
                ORDER BY created_at DESC
            """, (batch_id,))
            
            posts = []
            for row in cursor.fetchall():
                post_id, content, company_name, industry, post_type, feedback_received = row
                posts.append({
                    'post_id': post_id,
                    'content': content,
                    'company_name': company_name,
                    'industry': industry,
                    'post_type': post_type,
                    'feedback_received': feedback_received
                })
            return posts

    def get_recommended_settings(self, company_name: str, industry: str) -> Dict:
        """Get recommended settings based on past successful posts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get posts without negative feedback in same industry
            cursor.execute("""
                SELECT p.post_type, p.metrics, COUNT(*) as count
                FROM posts p
                LEFT JOIN feedback f ON p.post_id = f.post_id
                WHERE p.industry = ? AND f.feedback_id IS NULL
                GROUP BY p.post_type
                ORDER BY count DESC
                LIMIT 1
            """, (industry,))
            
            result = cursor.fetchone()
            if result:
                post_type, metrics_json, _ = result
                return {
                    'post_type': post_type,
                    'metrics': json.loads(metrics_json)
                }
            
            # Default recommendations if no data
            return {
                'post_type': 'innovation',
                'metrics': {
                    'authenticity_markers': {
                        'specific_dates': True,
                        'real_numbers': True,
                        'named_sources': True,
                        'direct_quotes': True,
                        'verifiable_facts': True
                    },
                    'insight_quality': {
                        'behind_scenes': True,
                        'counter_intuitive': True,
                        'industry_specific': True,
                        'decision_rationale': True,
                        'failure_lessons': True
                    }
                }
            }
    
    def get_feedback_history(self, company_name: Optional[str] = None, 
                           industry: Optional[str] = None) -> List[Dict]:
        """Get feedback history with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    p.post_id,
                    p.company_name,
                    p.industry,
                    p.post_type,
                    f.feedback_type,
                    f.feedback_text,
                    f.created_at
                FROM posts p
                JOIN feedback f ON p.post_id = f.post_id
                WHERE 1=1
            """
            params = []
            
            if company_name:
                query += " AND p.company_name = ?"
                params.append(company_name)
            
            if industry:
                query += " AND p.industry = ?"
                params.append(industry)
                
            query += " ORDER BY f.created_at DESC"
            
            cursor.execute(query, params)
            
            feedback_history = []
            for row in cursor.fetchall():
                feedback_history.append({
                    'post_id': row[0],
                    'company_name': row[1],
                    'industry': row[2],
                    'post_type': row[3],
                    'feedback_type': row[4],
                    'feedback_text': row[5],
                    'created_at': row[6]
                })
            
            return feedback_history

    def get_automatic_recommendations(self, num_recommendations: int = 5) -> List[Dict]:
        """Get automatic post recommendations based on trending stories and performance"""
        try:
            # Get trending stories from the last 7 days
            trending_stories = self.db_manager.get_trending_stories(days=7, min_news_count=2)
            
            # Get top performing industries based on engagement
            top_industries = self._get_top_performing_industries()
            
            recommendations = []
            stories_used = set()
            
            # First, try to get recommendations from trending stories in top performing industries
            for industry in top_industries:
                if len(recommendations) >= num_recommendations:
                    break
                    
                industry_stories = [story for story in trending_stories 
                                  if story['industry'] == industry 
                                  and story['story_id'] not in stories_used]
                
                for story in industry_stories:
                    if len(recommendations) >= num_recommendations:
                        break
                        
                    # Get recommended settings based on past performance
                    settings = self.get_recommended_settings(
                        story['company_name'], 
                        story['industry']
                    )
                    
                    recommendation = {
                        'story': story,
                        'settings': settings,
                        'source': 'trending',
                        'confidence_score': self._calculate_confidence_score(story, settings)
                    }
                    
                    recommendations.append(recommendation)
                    stories_used.add(story['story_id'])
            
            # If we still need more recommendations, get them from recent stories
            if len(recommendations) < num_recommendations:
                recent_stories = self._get_recent_stories(
                    limit=num_recommendations - len(recommendations),
                    exclude_ids=stories_used
                )
                
                for story in recent_stories:
                    settings = self.get_recommended_settings(
                        story['company_name'], 
                        story['industry']
                    )
                    
                    recommendation = {
                        'story': story,
                        'settings': settings,
                        'source': 'recent',
                        'confidence_score': self._calculate_confidence_score(story, settings)
                    }
                    
                    recommendations.append(recommendation)
            
            # Sort recommendations by confidence score
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            return recommendations

        except Exception as e:
            print(f"Error getting automatic recommendations: {str(e)}")
            return []

    def _get_top_performing_industries(self, limit: int = 5) -> List[str]:
        """Get top performing industries based on engagement metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.industry, 
                       AVG(CAST(json_extract(p.metrics, '$.engagement_rate') AS FLOAT)) as avg_engagement
                FROM posts p
                LEFT JOIN feedback f ON p.post_id = f.post_id
                WHERE f.feedback_id IS NULL  -- No negative feedback
                  AND p.created_at >= datetime('now', '-30 days')  -- Last 30 days
                GROUP BY p.industry
                ORDER BY avg_engagement DESC
                LIMIT ?
            """, (limit,))
            
            return [row[0] for row in cursor.fetchall()]

    def _get_recent_stories(self, limit: int = 5, exclude_ids: set = None) -> List[Dict]:
        """Get recent stories excluding specified IDs"""
        if exclude_ids is None:
            exclude_ids = set()
            
        stories = self.db_manager.get_stories_by_industry(
            industry='',  # Get from all industries
            limit=limit * 2  # Get more than needed to account for exclusions
        )
        
        return [
            story for story in stories 
            if story['story_id'] not in exclude_ids
        ][:limit]

    def _calculate_confidence_score(self, story: Dict, settings: Dict) -> float:
        """Calculate a confidence score for a recommendation"""
        score = 0.0
        
        # Factor 1: Story freshness (up to 0.3)
        if 'latest_news_date' in story:
            days_old = (datetime.now() - story['latest_news_date']).days
            freshness_score = max(0, 0.3 - (days_old * 0.01))  # Decrease score with age
            score += freshness_score
        
        # Factor 2: News coverage (up to 0.2)
        if 'news_count' in story:
            coverage_score = min(0.2, story['news_count'] * 0.02)
            score += coverage_score
        
        # Factor 3: Sentiment (up to 0.2)
        if 'avg_sentiment' in story:
            sentiment_score = (story['avg_sentiment'] + 1) * 0.1  # Convert -1..1 to 0..0.2
            score += sentiment_score
        
        # Factor 4: Past performance in industry (up to 0.3)
        if 'metrics' in settings:
            metrics = settings['metrics']
            if isinstance(metrics, str):
                metrics = json.loads(metrics)
            engagement_rate = metrics.get('engagement_rate', 0)
            performance_score = min(0.3, engagement_rate * 0.3)
            score += performance_score
        
        return score
