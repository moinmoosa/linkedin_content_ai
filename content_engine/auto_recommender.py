from typing import List, Dict, Optional
import json
import logging
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from content_engine.story_collector import BusinessStoryCollector
from content_engine.enhanced_generator import EnhancedContentGenerator
from textblob import TextBlob
import re

class AutoPostRecommender:
    """Automatic LinkedIn post recommender with feedback system"""
    
    FEEDBACK_TAGS = {
        "content": [
            "too_technical",
            "not_technical_enough",
            "missing_context",
            "too_long",
            "too_short"
        ],
        "style": [
            "wrong_tone",
            "not_engaging",
            "too_formal",
            "too_casual",
            "needs_examples"
        ],
        "structure": [
            "poor_flow",
            "weak_hook",
            "weak_conclusion",
            "needs_bullets",
            "needs_statistics"
        ],
        "relevance": [
            "wrong_industry",
            "outdated_info",
            "wrong_audience",
            "not_actionable",
            "not_valuable"
        ]
    }
    
    def __init__(self):
        """Initialize the recommender system"""
        self.db_manager = DatabaseManager()
        self.story_collector = BusinessStoryCollector()
        self.post_generator = EnhancedContentGenerator()
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        # Create posts table
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS auto_posts (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                story_id INTEGER NOT NULL,
                industry TEXT NOT NULL,
                company_name TEXT NOT NULL,
                post_type TEXT NOT NULL,
                engagement_score FLOAT,
                relevance_score FLOAT,
                readability_score FLOAT,
                authenticity_score FLOAT,
                approved BOOLEAN DEFAULT FALSE,
                scheduled_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create feedback table
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS post_feedback (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES auto_posts(id),
                feedback_category TEXT NOT NULL,
                feedback_tag TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create story preferences table
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS story_preferences (
                id SERIAL PRIMARY KEY,
                industry TEXT,
                company_size TEXT,
                story_type TEXT,
                weight FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create post cache table
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS post_cache (
                id SERIAL PRIMARY KEY,
                cache_key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

    def generate_batch_posts(self, count: int = 5) -> List[Dict]:
        """Generate a batch of posts"""
        print(f"AutoPostRecommender: Starting batch generation of {count} posts")
        try:
            # Get stories from database
            stories = self.story_collector.get_random_stories(count)
            print(f"Retrieved {len(stories)} stories from database")
            
            if not stories:
                print("No stories found in database")
                return []
            
            # Generate posts in parallel
            posts = []
            for story in stories:
                try:
                    print(f"Generating post for story: {story.get('company_name', 'Unknown Company')}")
                    post = self.post_generator.generate_single_post(story)
                    if post:
                        posts.append(post)
                except Exception as e:
                    print(f"Error generating post for story: {str(e)}")
            
            print(f"Successfully generated {len(posts)} posts")
            return posts
            
        except Exception as e:
            print(f"Error in batch post generation: {str(e)}")
            raise

    def get_pending_posts(self) -> List[Dict]:
        """Get posts that haven't been reviewed yet"""
        return self.db_manager.execute("""
            SELECT * FROM auto_posts 
            WHERE approved IS NULL 
            ORDER BY created_at DESC 
            LIMIT 10
        """)

    def generate_post(self) -> Optional[Dict]:
        """Generate a new post automatically with quality checks"""
        try:
            # Get a random story from the database
            story = self.story_collector.get_random_story()
            if not story:
                self.logger.error("No stories found in database")
                return None
            
            # Check cache first
            cache_key = self._cache_key(story)
            cached_content = self._get_cached_post(cache_key)
            
            if cached_content:
                post_content = cached_content
            else:
                # Generate post content
                post_content = self.post_generator.generate_post(
                    story["content"],
                    story["industry"],
                    story["company_name"]
                )
                # Cache the content
                self._cache_post(cache_key, post_content)
            
            # Validate quality
            quality_scores = self._validate_post_quality(post_content)
            
            # Regenerate if quality is poor
            if self._should_regenerate(quality_scores):
                self.logger.info("Post quality below threshold, regenerating...")
                return self.generate_post()  # Recursive call
            
            # Save to database
            self.db_manager.execute("""
                INSERT INTO auto_posts (
                    content, story_id, industry, company_name, 
                    post_type, engagement_score, relevance_score,
                    readability_score, authenticity_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                post_content,
                story["id"],
                story["industry"],
                story["company_name"],
                story["type"],
                quality_scores['engagement_score'],
                quality_scores['relevance_score'],
                quality_scores['readability_score'],
                quality_scores['authenticity_score']
            ))
            
            post_id = self.db_manager.get_last_row_id()
            
            return {
                "post_id": post_id,
                "content": post_content,
                "industry": story["industry"],
                "company_name": story["company_name"],
                **quality_scores
            }
            
        except Exception as e:
            self.logger.error(f"Error in generate_post: {str(e)}")
            return None

    def _validate_post_quality(self, content: str) -> Dict[str, float]:
        """Validate post quality using multiple metrics"""
        return {
            'engagement_score': self._calculate_engagement_score(content),
            'relevance_score': self._calculate_relevance_score(content),
            'readability_score': self._calculate_readability_score(content),
            'authenticity_score': self._calculate_authenticity_score(content)
        }

    def _should_regenerate(self, scores: Dict[str, float]) -> bool:
        """Determine if post should be regenerated based on quality scores"""
        return any(score < 0.7 for score in scores.values())

    def _calculate_engagement_score(self, content: str) -> float:
        """Calculate predicted engagement score for post content"""
        score = 0.5  # Base score
        
        # Check for engagement elements
        engagement_elements = {
            'question_marks': '?',
            'call_to_action': ['comment', 'share', 'like', 'follow', 'thoughts'],
            'emojis': r'[\U0001F300-\U0001F9FF]',
            'hashtags': '#',
            'numbers': r'\d+'
        }
        
        for element, pattern in engagement_elements.items():
            if isinstance(pattern, list):
                if any(word in content.lower() for word in pattern):
                    score += 0.1
            else:
                if re.search(pattern, content):
                    score += 0.1
        
        # Analyze sentiment
        blob = TextBlob(content)
        sentiment = blob.sentiment.polarity
        score += 0.2 if sentiment > 0 else 0.1
        
        return min(1.0, score)

    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score using various metrics"""
        words = content.split()
        sentences = content.split('.')
        
        if not words or not sentences:
            return 0.0
        
        # Basic metrics
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / len(sentences)
        
        # Penalize very long or very short content
        length_score = 1.0
        if len(words) < 50:
            length_score = 0.5
        elif len(words) > 300:
            length_score = 0.7
            
        # Calculate final score
        readability_score = 1.0
        if avg_word_length > 8:  # Penalize too many long words
            readability_score -= 0.2
        if avg_sentence_length > 20:  # Penalize too long sentences
            readability_score -= 0.2
            
        return max(0.0, min(1.0, readability_score * length_score))

    def _calculate_authenticity_score(self, content: str) -> float:
        """Calculate authenticity score based on various markers"""
        score = 0.5  # Base score
        
        # Check for authenticity markers
        authenticity_markers = {
            'specific_dates': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            'numbers_and_stats': r'\b\d+%|\$\d+|\d+x|\d+\+\b',
            'credible_sources': ['according to', 'research shows', 'study finds'],
            'industry_terms': ['market', 'industry', 'sector', 'technology'],
            'real_examples': ['for example', 'such as', 'like']
        }
        
        for marker, pattern in authenticity_markers.items():
            if isinstance(pattern, list):
                if any(phrase in content.lower() for phrase in pattern):
                    score += 0.1
            else:
                if re.search(pattern, content):
                    score += 0.1
        
        return min(1.0, score)

    def learn_from_feedback(self):
        """Analyze feedback patterns to improve generation"""
        feedback_patterns = self.db_manager.execute("""
            SELECT 
                feedback_category,
                feedback_tag,
                COUNT(*) as frequency,
                AVG(p.engagement_score) as avg_engagement
            FROM post_feedback f
            JOIN auto_posts p ON f.post_id = p.id
            GROUP BY feedback_category, feedback_tag
            ORDER BY frequency DESC
        """)
        
        # Update generation preferences based on feedback
        for pattern in feedback_patterns:
            self._adjust_generation_parameters(pattern)

    def _adjust_generation_parameters(self, pattern: Dict):
        """Adjust generation parameters based on feedback pattern"""
        category = pattern['feedback_category']
        tag = pattern['feedback_tag']
        frequency = pattern['frequency']
        avg_engagement = pattern['avg_engagement']
        
        # Update story preferences based on feedback
        if category == 'relevance' and tag == 'wrong_industry':
            self.db_manager.execute("""
                UPDATE story_preferences 
                SET weight = weight * 0.9 
                WHERE industry = %s
            """, (pattern['industry'],))
        
        # Log the adjustment for monitoring
        self.logger.info(f"Adjusted parameters for {category}:{tag} based on {frequency} occurrences")

    def _cache_key(self, story: Dict) -> str:
        """Generate cache key for a story"""
        return f"{story['id']}:{story['industry']}:{story['type']}"

    def _get_cached_post(self, cache_key: str) -> Optional[str]:
        """Get cached post if available and not expired"""
        result = self.db_manager.execute("""
            SELECT content 
            FROM post_cache 
            WHERE cache_key = %s 
            AND expires_at > NOW()
        """, (cache_key,))
        return result[0]['content'] if result else None

    def _cache_post(self, cache_key: str, content: str):
        """Cache generated post with expiration"""
        expires_at = datetime.now() + timedelta(days=7)  # Cache for 7 days
        self.db_manager.execute("""
            INSERT INTO post_cache (cache_key, content, expires_at) 
            VALUES (%s, %s, %s)
            ON CONFLICT (cache_key) 
            DO UPDATE SET content = EXCLUDED.content, 
                         expires_at = EXCLUDED.expires_at
        """, (cache_key, content, expires_at))

    def get_system_stats(self) -> Dict:
        """Get system performance statistics"""
        try:
            total_posts = self.db_manager.execute(
                "SELECT COUNT(*) as count FROM auto_posts"
            )[0]['count']
            
            approval_stats = self.db_manager.execute("""
                SELECT 
                    COUNT(*) as total_reviewed,
                    COUNT(CASE WHEN approved THEN 1 END) as approved_count,
                    COUNT(CASE WHEN approved THEN 1 END) * 100.0 / COUNT(*) as approval_rate
                FROM auto_posts
                WHERE approved IS NOT NULL
            """)[0]
            
            avg_scores = self.db_manager.execute("""
                SELECT 
                    AVG(engagement_score) as avg_engagement,
                    AVG(relevance_score) as avg_relevance,
                    AVG(readability_score) as avg_readability,
                    AVG(authenticity_score) as avg_authenticity
                FROM auto_posts
            """)[0]
            
            common_feedback = self.db_manager.execute("""
                SELECT 
                    feedback_category,
                    feedback_tag, 
                    COUNT(*) as count 
                FROM post_feedback 
                GROUP BY feedback_category, feedback_tag 
                ORDER BY count DESC 
                LIMIT 5
            """)
            
            return {
                'total_posts': total_posts,
                'approval_rate': approval_stats['approval_rate'],
                'total_reviewed': approval_stats['total_reviewed'],
                'approved_count': approval_stats['approved_count'],
                'average_scores': {
                    'engagement': avg_scores['avg_engagement'],
                    'relevance': avg_scores['avg_relevance'],
                    'readability': avg_scores['avg_readability'],
                    'authenticity': avg_scores['avg_authenticity']
                },
                'common_feedback': [
                    {
                        'category': fb['feedback_category'],
                        'tag': fb['feedback_tag'],
                        'count': fb['count']
                    }
                    for fb in common_feedback
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting system stats: {str(e)}")
            return {}
