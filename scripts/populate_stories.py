import os
import sys
from pathlib import Path

# Add parent directory to path to import from project
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from content_engine.story_collector import BusinessStoryCollector
from database.db_manager import DatabaseManager

def main():
    """Populate the database with sample business stories"""
    print("Starting database population...")
    
    # Initialize components
    collector = BusinessStoryCollector()
    db = DatabaseManager()
    
    # Create stories table if it doesn't exist
    db.execute("""
        CREATE TABLE IF NOT EXISTS business_stories (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            company_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            story_type TEXT NOT NULL,
            source TEXT,
            url TEXT,
            reliability_score FLOAT,
            engagement_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sample business stories
    stories = [
        {
            'title': 'Tesla Revolutionizes Electric Vehicle Market',
            'content': 'Tesla has transformed the automotive industry with its innovative approach to electric vehicles. Starting with the Model S in 2012, Tesla has consistently pushed the boundaries of what\'s possible in electric vehicle technology. The company\'s focus on software integration, battery efficiency, and autonomous driving capabilities has forced traditional automakers to accelerate their own electric vehicle programs.',
            'company_name': 'Tesla',
            'industry': 'Automotive',
            'story_type': 'Innovation_stories',
            'source': 'Internal Database',
            'url': 'https://www.tesla.com',
            'reliability_score': 0.9,
            'engagement_score': 0.95
        },
        {
            'title': 'Zoom\'s Rapid Growth During Global Pandemic',
            'content': 'Zoom Video Communications saw unprecedented growth during the COVID-19 pandemic, becoming essential for remote work and education. The company\'s user-friendly platform and quick adaptation to security challenges demonstrated remarkable business agility. Zoom\'s daily meeting participants grew from 10 million in December 2019 to over 300 million by April 2020.',
            'company_name': 'Zoom',
            'industry': 'Technology',
            'story_type': 'Growth_stories',
            'source': 'Internal Database',
            'url': 'https://www.zoom.us',
            'reliability_score': 0.95,
            'engagement_score': 0.9
        },
        {
            'title': 'Stripe Simplifies Online Payments',
            'content': 'Stripe has revolutionized online payments by making it incredibly simple for businesses to accept payments online. Their API-first approach and developer-friendly tools have made them the preferred choice for both startups and enterprises. The company\'s valuation reached $95 billion in 2021, making it one of the most valuable private companies globally.',
            'company_name': 'Stripe',
            'industry': 'Finance',
            'story_type': 'Success_stories',
            'source': 'Internal Database',
            'url': 'https://www.stripe.com',
            'reliability_score': 0.9,
            'engagement_score': 0.85
        }
    ]
    
    print(f"Inserting {len(stories)} sample stories...")
    
    # Insert stories into database
    for story in stories:
        db.execute("""
            INSERT INTO business_stories 
            (title, content, company_name, industry, story_type, source, url, reliability_score, engagement_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            story['title'],
            story['content'],
            story['company_name'],
            story['industry'],
            story['story_type'],
            story['source'],
            story['url'],
            story['reliability_score'],
            story['engagement_score']
        ))
    
    print("Database population completed!")

if __name__ == "__main__":
    main()
