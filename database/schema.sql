-- Database schema for LinkedIn Content AI

-- Stories table to store collected business stories
CREATE TABLE stories (
    story_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    story_type VARCHAR(50),  -- 'pivot', 'success', 'innovation'
    source VARCHAR(50),      -- 'wikipedia', 'forbes', etc.
    content JSONB,           -- Structured content
    industry VARCHAR(100),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News articles related to stories
CREATE TABLE news_articles (
    article_id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(story_id),
    title TEXT NOT NULL,
    url TEXT,
    source VARCHAR(100),
    content TEXT,
    published_date TIMESTAMP,
    sentiment_score FLOAT,
    engagement_metrics JSONB,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Engagement metrics for generated posts
CREATE TABLE post_metrics (
    metric_id SERIAL PRIMARY KEY,
    post_id INTEGER,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    click_through_rate FLOAT,
    engagement_rate FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- A/B testing results
CREATE TABLE ab_tests (
    test_id SERIAL PRIMARY KEY,
    post_id INTEGER,
    test_name VARCHAR(100),
    variant VARCHAR(50),
    metrics JSONB,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_winner BOOLEAN
);

-- Source reliability tracking
CREATE TABLE source_reliability (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE,
    accuracy_score FLOAT,
    freshness_score FLOAT,
    engagement_score FLOAT,
    last_fetch_success BOOLEAN,
    last_fetch_time TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    total_articles INTEGER DEFAULT 0
);

-- Create indexes for better performance
CREATE INDEX idx_stories_company ON stories(company_name);
CREATE INDEX idx_stories_industry ON stories(industry);
CREATE INDEX idx_stories_type ON stories(story_type);
CREATE INDEX idx_news_source ON news_articles(source);
CREATE INDEX idx_news_date ON news_articles(published_date);

-- Create a view for trending stories
CREATE VIEW trending_stories AS
SELECT 
    s.story_id,
    s.title,
    s.company_name,
    s.industry,
    COUNT(n.article_id) as news_count,
    AVG(n.sentiment_score) as avg_sentiment,
    MAX(n.published_date) as latest_news_date
FROM stories s
LEFT JOIN news_articles n ON s.story_id = n.story_id
WHERE n.published_date >= NOW() - INTERVAL '7 days'
GROUP BY s.story_id, s.title, s.company_name, s.industry
HAVING COUNT(n.article_id) > 2
ORDER BY news_count DESC, avg_sentiment DESC;
