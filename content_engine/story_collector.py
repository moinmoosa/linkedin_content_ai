import wikipediaapi
import newspaper
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional, Union
import logging
import time
import random
from textblob import TextBlob
from newspaper import Article
from database.db_manager import DatabaseManager
import os
from duckduckgo_search import DDGS
from urllib.parse import urlparse
import re

class BusinessStoryCollector:
    def __init__(self):
        """Initialize the story collector."""
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='LinkedInContentAI/1.0'
        )
        self.ddgs = DDGS()
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        self.business_categories = [
            'Business_pivots',
            'Corporate_scandals',
            'Business_rivalries',
            'Company_mergers_and_acquisitions',
            'Startup_companies',
            'Business_success_stories'
        ]
        self.news_sources = [
            'https://www.forbes.com',
            'https://www.entrepreneur.com',
            'https://www.businessinsider.com',
            'https://www.inc.com'
        ]
        self.trusted_sources = {
            'forbes.com': {'weight': 0.9, 'base_url': 'https://www.forbes.com'},
            'entrepreneur.com': {'weight': 0.85, 'base_url': 'https://www.entrepreneur.com'},
            'businessinsider.com': {'weight': 0.8, 'base_url': 'https://www.businessinsider.com'},
            'inc.com': {'weight': 0.85, 'base_url': 'https://www.inc.com'},
            'techcrunch.com': {'weight': 0.85, 'base_url': 'https://techcrunch.com'},
            'reuters.com': {'weight': 0.95, 'base_url': 'https://www.reuters.com'},
            'bloomberg.com': {'weight': 0.9, 'base_url': 'https://www.bloomberg.com'}
        }
        
    def collect_pivot_stories(self) -> List[Dict]:
        """Collect stories specifically about business pivots"""
        pivot_keywords = [
            'business pivot',
            'company transformation',
            'strategic shift',
            'business model change',
            'corporate reinvention'
        ]
        stories = []
        
        # Search Wikipedia for pivot stories
        for keyword in pivot_keywords:
            wiki_results = self.wiki.search(keyword)
            for page_title in wiki_results:
                page = self.wiki.page(page_title)
                if page.exists():
                    story = self._extract_pivot_story(page)
                    if story:
                        stories.append(story)
        
        return stories

    def _extract_pivot_story(self, page) -> Optional[Dict]:
        """Extract pivot story details from a Wikipedia page"""
        try:
            # Check if content is relevant to business pivots
            content = page.text.lower()
            pivot_indicators = ['pivot', 'changed direction', 'transformed', 'reinvented']
            
            if any(indicator in content for indicator in pivot_indicators):
                return {
                    'title': page.title,
                    'summary': page.summary,
                    'url': page.fullurl,
                    'type': 'pivot',
                    'source': 'wikipedia',
                    'collected_at': datetime.now().isoformat(),
                    'full_content': self._extract_relevant_sections(page)
                }
        except Exception as e:
            self.logger.error(f"Error extracting pivot story: {e}")
        return None

    def collect_success_stories(self) -> List[Dict]:
        """Collect business success stories"""
        stories = []
        
        # Search Wikipedia for success stories
        for category in ['Business_success_stories', 'Startup_companies']:
            category_members = self.wiki.page(category).categorymembers
            for title in list(category_members.keys())[:5]:  # Limit to 5 stories per category
                page = self.wiki.page(title)
                if page.exists():
                    story = self._extract_success_story(page)
                    if story:
                        stories.append(story)
        
        return stories

    def collect_innovation_stories(self) -> List[Dict]:
        """Collect stories about business innovation"""
        innovation_keywords = [
            'business innovation',
            'technological breakthrough',
            'disruptive innovation',
            'revolutionary product',
            'market disruption'
        ]
        stories = []
        
        for keyword in innovation_keywords:
            wiki_results = self.wiki.search(keyword)
            for page_title in wiki_results:
                page = self.wiki.page(page_title)
                if page.exists():
                    story = self._extract_innovation_story(page)
                    if story:
                        stories.append(story)
        
        return stories

    def enrich_with_news(self, story: Dict) -> Dict:
        """Enrich story with recent news articles"""
        try:
            # Search for recent news about the company/topic
            company_name = story['title'].split('(')[0].strip()
            news_articles = []
            
            for source in self.news_sources:
                paper = newspaper.build(source, memoize_articles=False)
                for article in paper.articles[:5]:  # Check first 5 articles
                    try:
                        article.download()
                        article.parse()
                        if company_name.lower() in article.text.lower():
                            news_articles.append({
                                'title': article.title,
                                'url': article.url,
                                'text': article.text[:500],  # First 500 chars
                                'published_date': article.publish_date.isoformat() if article.publish_date else None
                            })
                    except Exception:
                        continue
            
            story['recent_news'] = news_articles
        except Exception as e:
            self.logger.error(f"Error enriching story with news: {e}")
        
        return story

    def _extract_relevant_sections(self, page) -> Dict:
        """Extract relevant sections from a Wikipedia page"""
        sections = {}
        for section in page.sections:
            if any(keyword in section.title.lower() for keyword in 
                  ['history', 'business', 'development', 'growth', 'pivot', 'transformation']):
                sections[section.title] = section.text
        return sections

    def save_stories(self, stories: List[Dict], filename: str):
        """Save collected stories to a JSON file"""
        try:
            with open(f'data/{filename}', 'w', encoding='utf-8') as f:
                json.dump(stories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving stories: {e}")

    def collect_all_stories(self) -> Dict[str, List[Dict]]:
        """Collect all types of stories"""
        all_stories = {
            'pivot_stories': self.collect_pivot_stories(),
            'success_stories': self.collect_success_stories(),
            'innovation_stories': self.collect_innovation_stories()
        }
        
        # Enrich stories with recent news
        for category in all_stories:
            all_stories[category] = [
                self.enrich_with_news(story) 
                for story in all_stories[category]
            ]
        
        # Save all stories
        self.save_stories(all_stories, 'business_stories.json')
        return all_stories

    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob."""
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract and analyze article data using newspaper3k."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()

            # Calculate sentiment score
            sentiment_score = self.analyze_sentiment(article.text)

            # Extract publish date
            publish_date = article.publish_date or datetime.now()

            return {
                'title': article.title,
                'url': url,
                'content': article.text,
                'summary': article.summary,
                'keywords': article.keywords,
                'published_date': publish_date,
                'sentiment_score': sentiment_score
            }
        except Exception as e:
            print(f"Error extracting article data from {url}: {str(e)}")
            return None

    def collect_story(self, company_name: str, industry: str) -> Optional[Dict]:
        """Collect and analyze business story with enhanced data collection."""
        try:
            # Get Wikipedia data
            wiki_data = self._get_wikipedia_data(company_name)
            if not wiki_data:
                return None

            # Create base story
            story_data = {
                'title': f"{company_name} Business Story",
                'company_name': company_name,
                'industry': industry,
                'summary': wiki_data.get('summary', ''),
                'content': wiki_data,
                'source': 'wikipedia',
                'story_type': self._determine_story_type(wiki_data)
            }

            # Save story to database
            story_id = self.db.save_story(story_data)

            # Collect related news articles
            news_articles = self._collect_news_articles(company_name)
            for article in news_articles:
                if article:
                    article['story_id'] = story_id
                    self.db.save_news_article(article)

            # Update source reliability metrics
            for source in self.trusted_sources:
                success = any(source in article['url'] for article in news_articles if article)
                articles_count = sum(1 for article in news_articles if article and source in article['url'])
                self.db.update_source_reliability(source, success, articles_count)

            return self.db.get_story_by_id(story_id)

        except Exception as e:
            print(f"Error collecting story for {company_name}: {str(e)}")
            return None

    def _collect_news_articles(self, company_name: str) -> List[Dict]:
        """Collect and analyze news articles from trusted sources."""
        articles = []
        for source, info in self.trusted_sources.items():
            try:
                # Search for company news using newspaper3k
                search_url = f"{info['base_url']}/search?q={company_name.replace(' ', '+')}"
                article_data = self.extract_article_data(search_url)
                
                if article_data:
                    article_data['source'] = source
                    articles.append(article_data)
            except Exception as e:
                print(f"Error collecting news from {source}: {str(e)}")
                continue

        return articles

    def get_trending_stories(self, days: int = 7) -> List[Dict]:
        """Get trending business stories based on recent coverage and sentiment."""
        return self.db.get_trending_stories(days=days)

    def get_reliable_sources(self) -> List[Dict]:
        """Get list of current reliable sources."""
        return self.db.get_reliable_sources()

    def populate_initial_stories(self, target_count=500, industries=None, story_types=None):
        """
        Populate database with pre-curated business stories across industries and story types.
        """
        stories = []
        
        # Pre-curated stories with proper meta information across different industries
        curated_stories = [
            # Technology Industry
            {
                'title': 'Netflix Pivots from DVD Rentals to Streaming Giant',
                'company_name': 'Netflix',
                'summary': 'Netflix transformed from a DVD-by-mail service to the world\'s leading streaming platform.',
                'content': 'In 2007, Netflix made a bold decision to pivot from its successful DVD rental business to focus on streaming content. This strategic shift, led by CEO Reed Hastings, initially faced skepticism but proved to be visionary. The company invested heavily in digital infrastructure and original content production, leading to massive subscriber growth and industry disruption.',
                'industry': 'Media',
                'story_type': 'Business_pivots',
                'source': 'Harvard Business Review',
                'url': 'https://www.netflix.com/about',
                'business_stage': 'Growth',
                'company_size': 'Large'
            },
            # Healthcare Industry
            {
                'title': 'Moderna\'s mRNA Breakthrough in Vaccine Development',
                'company_name': 'Moderna',
                'summary': 'Moderna leveraged its mRNA technology platform to develop revolutionary vaccines.',
                'content': 'Founded in 2010, Moderna began as a research-stage company focused on using messenger RNA to develop a new class of medicines. The company\'s breakthrough came during the COVID-19 pandemic, where its mRNA technology platform enabled rapid vaccine development. This success has opened doors for treating various other diseases.',
                'industry': 'Healthcare',
                'story_type': 'Innovation_stories',
                'source': 'Nature',
                'url': 'https://www.modernatx.com/about-us',
                'business_stage': 'Scale-up',
                'company_size': 'Medium'
            },
            # Finance Industry
            {
                'title': 'Stripe Revolutionizes Online Payments',
                'company_name': 'Stripe',
                'summary': 'Two Irish brothers transformed online payments with a developer-first approach.',
                'content': 'Patrick and John Collison founded Stripe in 2010 to simplify online payments for developers. Their API-first approach and focus on developer experience disrupted the traditional payment processing industry. Starting with a small team, Stripe has grown to serve millions of businesses worldwide.',
                'industry': 'Finance',
                'story_type': 'Market_disruption',
                'source': 'Forbes',
                'url': 'https://stripe.com/about',
                'business_stage': 'Growth',
                'company_size': 'Medium'
            },
            # Retail Industry
            {
                'title': 'Warby Parker Disrupts Eyewear Industry',
                'company_name': 'Warby Parker',
                'summary': 'Direct-to-consumer approach revolutionizes eyewear retail.',
                'content': 'Founded by four Wharton students in 2010, Warby Parker disrupted the eyewear industry by cutting out middlemen and selling directly to consumers. Their innovative home try-on program and social mission (Buy a Pair, Give a Pair) created a new model for retail success.',
                'industry': 'Retail',
                'story_type': 'Business_model_innovation',
                'source': 'Inc Magazine',
                'url': 'https://www.warbyparker.com/about',
                'business_stage': 'Scale-up',
                'company_size': 'Medium'
            },
            # Manufacturing Industry
            {
                'title': 'Beyond Meat\'s Plant-Based Revolution',
                'company_name': 'Beyond Meat',
                'summary': 'Innovative food manufacturing creates sustainable meat alternatives.',
                'content': 'Beyond Meat revolutionized the food industry by creating plant-based meat alternatives that closely mimic the taste and texture of real meat. Through innovative manufacturing processes and partnerships with major food chains, they\'ve made plant-based options mainstream.',
                'industry': 'Manufacturing',
                'story_type': 'Sustainability_initiatives',
                'source': 'Bloomberg',
                'url': 'https://www.beyondmeat.com/about',
                'business_stage': 'Growth',
                'company_size': 'Medium'
            },
            # Energy Industry
            {
                'title': 'Sunrun\'s Solar Energy Democratization',
                'company_name': 'Sunrun',
                'summary': 'Making solar energy accessible to average homeowners.',
                'content': 'Sunrun transformed the residential solar industry by introducing a solar-as-a-service model, making clean energy accessible to average homeowners. Their innovative financing options and installation process have helped accelerate solar adoption across America.',
                'industry': 'Energy',
                'story_type': 'Market_expansion',
                'source': 'Clean Technica',
                'url': 'https://www.sunrun.com/about',
                'business_stage': 'Mature',
                'company_size': 'Large'
            },
            # Education Industry
            {
                'title': 'Duolingo\'s Gamification of Language Learning',
                'company_name': 'Duolingo',
                'summary': 'Making language learning free and engaging through gamification.',
                'content': 'Starting as a PhD project, Duolingo revolutionized language learning by making it free and game-like. Their mission to make education free and accessible has led to innovative features like streak counts and competitive leaderboards.',
                'industry': 'Education',
                'story_type': 'Digital_transformation',
                'source': 'EdTech Magazine',
                'url': 'https://www.duolingo.com/about',
                'business_stage': 'Growth',
                'company_size': 'Medium'
            },
            # Transportation Industry
            {
                'title': 'Bird\'s Last-Mile Transportation Solution',
                'company_name': 'Bird',
                'summary': 'Electric scooters transform urban transportation.',
                'content': 'Bird addressed the last-mile transportation problem with shared electric scooters. Starting in Santa Monica, they rapidly expanded to cities worldwide, creating a new category of micro-mobility solutions.',
                'industry': 'Transportation',
                'story_type': 'Urban_innovation',
                'source': 'TechCrunch',
                'url': 'https://www.bird.co/about',
                'business_stage': 'Start-up',
                'company_size': 'Small'
            }
        ]
        
        # Additional stories for each industry
        industry_specific_stories = {
            'Technology': [
                {
                    'title': 'GitLab\'s Remote-First Success',
                    'company_name': 'GitLab',
                    'summary': 'Building a successful company with no offices.',
                    'content': 'GitLab pioneered the remote-first work model, growing from a small open-source project to a public company without traditional offices. Their transparent culture and innovative collaboration tools have set new standards for remote work.',
                    'source': 'Remote Work Magazine',
                    'url': 'https://about.gitlab.com',
                    'business_stage': 'Growth',
                    'company_size': 'Medium'
                }
            ],
            'Healthcare': [
                {
                    'title': '23andMe\'s Personal Genetics Revolution',
                    'company_name': '23andMe',
                    'summary': 'Making genetic information accessible to consumers.',
                    'content': '23andMe democratized access to personal genetic information, allowing individuals to understand their health risks and ancestry. Their direct-to-consumer model has revolutionized personal genetics.',
                    'source': 'Genetic Engineering News',
                    'url': 'https://www.23andme.com/about',
                    'business_stage': 'Mature',
                    'company_size': 'Large'
                }
            ],
            'Finance': [
                {
                    'title': 'Robinhood\'s Commission-Free Trading',
                    'company_name': 'Robinhood',
                    'summary': 'Democratizing finance for all.',
                    'content': 'Robinhood disrupted traditional brokerages by offering commission-free trading and a user-friendly mobile app. Their mission to democratize finance has attracted millions of first-time investors.',
                    'source': 'Financial Times',
                    'url': 'https://robinhood.com/about',
                    'business_stage': 'Growth',
                    'company_size': 'Medium'
                }
            ]
        }
        
        def generate_unique_stories():
            """Generate unique stories based on templates and industry/type combinations"""
            generated = []
            used_titles = set()
            
            # First, add curated stories
            for story in curated_stories:
                if story['title'] not in used_titles:
                    story_copy = story.copy()
                    story_copy['meta_tags'] = {
                        'industry': story['industry'].lower(),
                        'category': story.get('story_type', '').lower(),
                        'content_type': 'business_story',
                        'source_type': 'curated',
                        'business_stage': story.get('business_stage', 'Unknown'),
                        'company_size': story.get('company_size', 'Unknown'),
                        'collection_date': datetime.now().isoformat(),
                        'reliability_score': 0.9,
                        'engagement_potential': 0.8
                    }
                    generated.append(story_copy)
                    used_titles.add(story['title'])
            
            # Then add industry-specific stories
            for industry in industries:
                if industry in industry_specific_stories:
                    for story in industry_specific_stories[industry]:
                        if story['title'] not in used_titles:
                            for story_type in story_types:
                                story_copy = story.copy()
                                story_copy.update({
                                    'industry': industry,
                                    'story_type': story_type,
                                    'meta_tags': {
                                        'industry': industry.lower(),
                                        'category': story_type.lower(),
                                        'content_type': 'business_story',
                                        'source_type': 'curated',
                                        'business_stage': story.get('business_stage', 'Unknown'),
                                        'company_size': story.get('company_size', 'Unknown'),
                                        'collection_date': datetime.now().isoformat(),
                                        'reliability_score': 0.9,
                                        'engagement_potential': 0.8
                                    }
                                })
                                if len(generated) < target_count:
                                    generated.append(story_copy)
                                    used_titles.add(story['title'])
            
            # Generate additional stories if needed
            story_counter = len(generated)
            while story_counter < target_count:
                for industry in industries:
                    for story_type in story_types:
                        if story_counter >= target_count:
                            break
                            
                        # Create a unique story for this combination
                        new_story = {
                            'title': f'Innovation Story {story_counter + 1} for {industry}',
                            'company_name': f'Company {story_counter + 1}',
                            'summary': f'A unique {story_type.lower().replace("_", " ")} story in the {industry} industry.',
                            'content': f'This is a detailed story about innovation and success in the {industry} sector, focusing on {story_type.lower().replace("_", " ")}.',
                            'industry': industry,
                            'story_type': story_type,
                            'source': 'Industry Analysis',
                            'url': f'https://example.com/story/{story_counter + 1}',
                            'business_stage': random.choice(['Start-up', 'Growth', 'Scale-up', 'Mature']),
                            'company_size': random.choice(['Small', 'Medium', 'Large']),
                            'meta_tags': {
                                'industry': industry.lower(),
                                'category': story_type.lower(),
                                'content_type': 'business_story',
                                'source_type': 'generated',
                                'business_stage': random.choice(['Start-up', 'Growth', 'Scale-up', 'Mature']),
                                'company_size': random.choice(['Small', 'Medium', 'Large']),
                                'collection_date': datetime.now().isoformat(),
                                'reliability_score': 0.7,
                                'engagement_potential': 0.6
                            }
                        }
                        
                        if new_story['title'] not in used_titles:
                            generated.append(new_story)
                            used_titles.add(new_story['title'])
                            story_counter += 1
            
            return generated[:target_count]
        
        # Generate and save stories
        stories = generate_unique_stories()
        saved_count = 0
        
        for story in stories:
            try:
                self.db.save_story(story)
                saved_count += 1
                print(f"Saved story {saved_count}/{target_count}: {story['title']}")
            except Exception as e:
                print(f"Error saving story: {str(e)}")
                continue
        
        return stories

    def collect_story(self, search_query, industry, subcategory=None, company_size=None, innovation_type=None):
        """Collect a business innovation story based on search criteria"""
        try:
            # Search for news articles and case studies
            news_data = self._search_news(search_query)
            if not news_data:
                return None
            
            # Extract key information
            story = {
                'title': news_data.get('title', ''),
                'content': news_data.get('content', ''),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'published_date': news_data.get('published_date', datetime.now().isoformat()),
                'industry': industry,
                'subcategory': subcategory,
                'company_size': company_size,
                'innovation_type': innovation_type,
                'sentiment_score': self._analyze_sentiment(news_data.get('content', '')),
                'reliability_score': self._calculate_source_reliability(news_data.get('source', '')),
                'collected_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_story(story)
            return story
            
        except Exception as e:
            print(f"Error in collect_story: {str(e)}")
            return None

    def _search_news(self, query: str) -> Optional[Dict]:
        """Search for news articles using various news APIs and web scraping"""
        try:
            # Try multiple news sources in sequence
            news_data = (
                self._try_newsapi(query) or
                self._try_gnews(query) or
                self._try_web_scraping(query)
            )
            return news_data
        except Exception as e:
            print(f"Error in _search_news: {str(e)}")
            return None

    def _try_newsapi(self, query: str) -> Optional[Dict]:
        """Try to get story from NewsAPI"""
        try:
            if not os.getenv('NEWSAPI_KEY'):
                return None
                
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': os.getenv('NEWSAPI_KEY'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with NewsAPI: {str(e)}")
            return None
            
    def _try_gnews(self, query: str) -> Optional[Dict]:
        """Try to get story from GNews"""
        try:
            if not os.getenv('GNEWS_API_KEY'):
                return None
                
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'token': os.getenv('GNEWS_API_KEY'),
                'lang': 'en',
                'max': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with GNews: {str(e)}")
            return None
            
    def _extract_company_name(self, text):
        """Extract company name from text using NLP"""
        try:
            # Common company suffixes
            suffixes = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Co', 'Corporation', 'Technologies', 'Tech']
            
            # Try to find company name with suffix
            for suffix in suffixes:
                pattern = fr'\b[A-Z][A-Za-z0-9\s&]+\s{suffix}\b'
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0].strip()
            
            # Try to find standalone capitalized names (likely company names)
            pattern = r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b'
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common non-company words
                non_companies = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'They'}
                companies = [m for m in matches if m not in non_companies and len(m) > 2]
                if companies:
                    return companies[0]
            
            return None
        except Exception as e:
            print(f"Error extracting company name: {str(e)}")
            return None
            
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo for business stories with rate limiting."""
        try:
            time.sleep(2)  # Rate limiting
            results = list(self.ddgs.text(query, max_results=num_results))
            processed_results = []
            
            for r in results:
                company_name = self._extract_company_name(r['title'] + ' ' + r['body'])
                if company_name:
                    processed_results.append({
                        'title': r['title'],
                        'company_name': company_name,
                        'summary': r['body'],
                        'url': r['link'],
                        'source': 'DuckDuckGo',
                        'content': r['body']
                    })
            
            return processed_results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []
            
    def _try_web_scraping(self, query: str) -> Optional[Dict]:
        """Fallback to web scraping trusted business news sites"""
        try:
            # List of trusted business news sites to search
            sites = [
                'techcrunch.com',
                'forbes.com',
                'hbr.org',
                'bloomberg.com',
                'reuters.com',
                'fastcompany.com',
                'inc.com',
                'technologyreview.com',
                'businessinsider.com',
                'wired.com'
            ]
            
            # Create a Google search query targeting specific sites
            site_query = ' OR '.join(f'site:{site}' for site in sites)
            search_query = f'{query} ({site_query})'
            
            # Use DuckDuckGo as a fallback search engine (no API key needed)
            results = self.search_duckduckgo(search_query, num_results=1)
            
            if results:
                result = results[0]
                # Use newspaper3k to extract article content
                article = Article(result['url'])
                article.download()
                article.parse()
                
                return {
                    'title': article.title,
                    'content': article.text,
                    'url': result['url'],
                    'source': urlparse(result['url']).netloc,
                    'published_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
                }
            return None
        except Exception:
            return None

    def _get_wikipedia_data(self, company_name: str) -> Optional[Dict]:
        """Get Wikipedia data for a company"""
        try:
            # Search Wikipedia for company page
            search_results = self.wiki.search(company_name)
            if not search_results:
                return None
            
            # Try to find the most relevant page
            for page_title in search_results:
                page = self.wiki.page(page_title)
                if page.exists() and company_name.lower() in page.title.lower():
                    # Extract key sections
                    sections = self._extract_relevant_sections(page)
                    
                    # Determine company details
                    company_details = {
                        'title': page.title,
                        'summary': page.summary,
                        'url': page.fullurl,
                        'sections': sections,
                        'content': page.text[:5000],  # First 5000 chars
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    return company_details
            
            return None
            
        except Exception as e:
            print(f"Error getting Wikipedia data: {str(e)}")
            return None

    def _determine_story_type(self, wiki_data: Dict) -> str:
        """Determine the type of story based on content"""
        content = wiki_data.get('content', '').lower()
        
        if any(word in content for word in ['pivot', 'transform', 'change direction', 'reinvent']):
            return 'pivot'
        elif any(word in content for word in ['innovate', 'breakthrough', 'revolutionary', 'disrupt']):
            return 'innovation'
        elif any(word in content for word in ['success', 'growth', 'achievement', 'milestone']):
            return 'success'
        else:
            return 'general'

    def _calculate_reliability_score(self, story):
        """Calculate a reliability score for the story based on various factors"""
        score = 0.5  # Base score
        
        # Increase score for reputable sources
        reputable_sources = ['reuters', 'bloomberg', 'forbes', 'techcrunch', 'wsj', 'nytimes']
        if any(source in story.get('source', '').lower() for source in reputable_sources):
            score += 0.3
            
        # Check for content quality
        if story.get('content'):
            # Length check
            if len(story['content']) > 1000:
                score += 0.1
                
            # Quote check
            if '"' in story['content']:
                score += 0.1
                
        return min(1.0, score)
        
    def _calculate_engagement_potential(self, story):
        """Calculate potential engagement score for the story"""
        score = 0.5  # Base score
        
        # Check title appeal
        title = story.get('title', '').lower()
        engaging_words = ['breakthrough', 'innovative', 'disrupting', 'revolutionary', 'success']
        score += 0.1 * sum(1 for word in engaging_words if word in title)
        
        # Check content sentiment
        if story.get('content'):
            blob = TextBlob(story['content'])
            sentiment = blob.sentiment.polarity
            score += 0.2 if sentiment > 0 else 0.1
            
        # Industry factor
        trending_industries = ['technology', 'healthcare', 'ai', 'renewable']
        if any(ind in story.get('industry', '').lower() for ind in trending_industries):
            score += 0.2
            
        return min(1.0, score)

    def collect_story(self, search_query, industry, subcategory=None, company_size=None, innovation_type=None):
        """Collect a business innovation story based on search criteria"""
        try:
            # Search for news articles and case studies
            news_data = self._search_news(search_query)
            if not news_data:
                return None
            
            # Extract key information
            story = {
                'title': news_data.get('title', ''),
                'content': news_data.get('content', ''),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'published_date': news_data.get('published_date', datetime.now().isoformat()),
                'industry': industry,
                'subcategory': subcategory,
                'company_size': company_size,
                'innovation_type': innovation_type,
                'sentiment_score': self._analyze_sentiment(news_data.get('content', '')),
                'reliability_score': self._calculate_source_reliability(news_data.get('source', '')),
                'collected_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_story(story)
            return story
            
        except Exception as e:
            print(f"Error in collect_story: {str(e)}")
            return None

    def _search_news(self, query: str) -> Optional[Dict]:
        """Search for news articles using various news APIs and web scraping"""
        try:
            # Try multiple news sources in sequence
            news_data = (
                self._try_newsapi(query) or
                self._try_gnews(query) or
                self._try_web_scraping(query)
            )
            return news_data
        except Exception as e:
            print(f"Error in _search_news: {str(e)}")
            return None

    def _try_newsapi(self, query: str) -> Optional[Dict]:
        """Try to get story from NewsAPI"""
        try:
            if not os.getenv('NEWSAPI_KEY'):
                return None
                
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': os.getenv('NEWSAPI_KEY'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with NewsAPI: {str(e)}")
            return None
            
    def _try_gnews(self, query: str) -> Optional[Dict]:
        """Try to get story from GNews"""
        try:
            if not os.getenv('GNEWS_API_KEY'):
                return None
                
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'token': os.getenv('GNEWS_API_KEY'),
                'lang': 'en',
                'max': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with GNews: {str(e)}")
            return None
            
    def _extract_company_name(self, text):
        """Extract company name from text using NLP"""
        try:
            # Common company suffixes
            suffixes = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Co', 'Corporation', 'Technologies', 'Tech']
            
            # Try to find company name with suffix
            for suffix in suffixes:
                pattern = fr'\b[A-Z][A-Za-z0-9\s&]+\s{suffix}\b'
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0].strip()
            
            # Try to find standalone capitalized names (likely company names)
            pattern = r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b'
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common non-company words
                non_companies = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'They'}
                companies = [m for m in matches if m not in non_companies and len(m) > 2]
                if companies:
                    return companies[0]
            
            return None
        except Exception as e:
            print(f"Error extracting company name: {str(e)}")
            return None
            
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo for business stories with rate limiting."""
        try:
            time.sleep(2)  # Rate limiting
            results = list(self.ddgs.text(query, max_results=num_results))
            processed_results = []
            
            for r in results:
                company_name = self._extract_company_name(r['title'] + ' ' + r['body'])
                if company_name:
                    processed_results.append({
                        'title': r['title'],
                        'company_name': company_name,
                        'summary': r['body'],
                        'url': r['link'],
                        'source': 'DuckDuckGo',
                        'content': r['body']
                    })
            
            return processed_results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []
            
    def _try_web_scraping(self, query: str) -> Optional[Dict]:
        """Fallback to web scraping trusted business news sites"""
        try:
            # List of trusted business news sites to search
            sites = [
                'techcrunch.com',
                'forbes.com',
                'hbr.org',
                'bloomberg.com',
                'reuters.com',
                'fastcompany.com',
                'inc.com',
                'technologyreview.com',
                'businessinsider.com',
                'wired.com'
            ]
            
            # Create a Google search query targeting specific sites
            site_query = ' OR '.join(f'site:{site}' for site in sites)
            search_query = f'{query} ({site_query})'
            
            # Use DuckDuckGo as a fallback search engine (no API key needed)
            results = self.search_duckduckgo(search_query, num_results=1)
            
            if results:
                result = results[0]
                # Use newspaper3k to extract article content
                article = Article(result['url'])
                article.download()
                article.parse()
                
                return {
                    'title': article.title,
                    'content': article.text,
                    'url': result['url'],
                    'source': urlparse(result['url']).netloc,
                    'published_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
                }
            return None
        except Exception:
            return None

    def _get_wikipedia_data(self, company_name: str) -> Optional[Dict]:
        """Get Wikipedia data for a company"""
        try:
            # Search Wikipedia for company page
            search_results = self.wiki.search(company_name)
            if not search_results:
                return None
            
            # Try to find the most relevant page
            for page_title in search_results:
                page = self.wiki.page(page_title)
                if page.exists() and company_name.lower() in page.title.lower():
                    # Extract key sections
                    sections = self._extract_relevant_sections(page)
                    
                    # Determine company details
                    company_details = {
                        'title': page.title,
                        'summary': page.summary,
                        'url': page.fullurl,
                        'sections': sections,
                        'content': page.text[:5000],  # First 5000 chars
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    return company_details
            
            return None
            
        except Exception as e:
            print(f"Error getting Wikipedia data: {str(e)}")
            return None

    def _determine_story_type(self, wiki_data: Dict) -> str:
        """Determine the type of story based on content"""
        content = wiki_data.get('content', '').lower()
        
        if any(word in content for word in ['pivot', 'transform', 'change direction', 'reinvent']):
            return 'pivot'
        elif any(word in content for word in ['innovate', 'breakthrough', 'revolutionary', 'disrupt']):
            return 'innovation'
        elif any(word in content for word in ['success', 'growth', 'achievement', 'milestone']):
            return 'success'
        else:
            return 'general'

    def _calculate_reliability_score(self, story):
        """Calculate a reliability score for the story based on various factors"""
        score = 0.5  # Base score
        
        # Increase score for reputable sources
        reputable_sources = ['reuters', 'bloomberg', 'forbes', 'techcrunch', 'wsj', 'nytimes']
        if any(source in story.get('source', '').lower() for source in reputable_sources):
            score += 0.3
            
        # Check for content quality
        if story.get('content'):
            # Length check
            if len(story['content']) > 1000:
                score += 0.1
                
            # Quote check
            if '"' in story['content']:
                score += 0.1
                
        return min(1.0, score)
        
    def _calculate_engagement_potential(self, story):
        """Calculate potential engagement score for the story"""
        score = 0.5  # Base score
        
        # Check title appeal
        title = story.get('title', '').lower()
        engaging_words = ['breakthrough', 'innovative', 'disrupting', 'revolutionary', 'success']
        score += 0.1 * sum(1 for word in engaging_words if word in title)
        
        # Check content sentiment
        if story.get('content'):
            blob = TextBlob(story['content'])
            sentiment = blob.sentiment.polarity
            score += 0.2 if sentiment > 0 else 0.1
            
        # Industry factor
        trending_industries = ['technology', 'healthcare', 'ai', 'renewable']
        if any(ind in story.get('industry', '').lower() for ind in trending_industries):
            score += 0.2
            
        return min(1.0, score)

    def collect_story(self, search_query, industry, subcategory=None, company_size=None, innovation_type=None):
        """Collect a business innovation story based on search criteria"""
        try:
            # Search for news articles and case studies
            news_data = self._search_news(search_query)
            if not news_data:
                return None
            
            # Extract key information
            story = {
                'title': news_data.get('title', ''),
                'content': news_data.get('content', ''),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'published_date': news_data.get('published_date', datetime.now().isoformat()),
                'industry': industry,
                'subcategory': subcategory,
                'company_size': company_size,
                'innovation_type': innovation_type,
                'sentiment_score': self._analyze_sentiment(news_data.get('content', '')),
                'reliability_score': self._calculate_source_reliability(news_data.get('source', '')),
                'collected_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_story(story)
            return story
            
        except Exception as e:
            print(f"Error in collect_story: {str(e)}")
            return None

    def _search_news(self, query: str) -> Optional[Dict]:
        """Search for news articles using various news APIs and web scraping"""
        try:
            # Try multiple news sources in sequence
            news_data = (
                self._try_newsapi(query) or
                self._try_gnews(query) or
                self._try_web_scraping(query)
            )
            return news_data
        except Exception as e:
            print(f"Error in _search_news: {str(e)}")
            return None

    def _try_newsapi(self, query: str) -> Optional[Dict]:
        """Try to get story from NewsAPI"""
        try:
            if not os.getenv('NEWSAPI_KEY'):
                return None
                
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': os.getenv('NEWSAPI_KEY'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with NewsAPI: {str(e)}")
            return None
            
    def _try_gnews(self, query: str) -> Optional[Dict]:
        """Try to get story from GNews"""
        try:
            if not os.getenv('GNEWS_API_KEY'):
                return None
                
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'token': os.getenv('GNEWS_API_KEY'),
                'lang': 'en',
                'max': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with GNews: {str(e)}")
            return None
            
    def _extract_company_name(self, text):
        """Extract company name from text using NLP"""
        try:
            # Common company suffixes
            suffixes = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Co', 'Corporation', 'Technologies', 'Tech']
            
            # Try to find company name with suffix
            for suffix in suffixes:
                pattern = fr'\b[A-Z][A-Za-z0-9\s&]+\s{suffix}\b'
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0].strip()
            
            # Try to find standalone capitalized names (likely company names)
            pattern = r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b'
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common non-company words
                non_companies = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'They'}
                companies = [m for m in matches if m not in non_companies and len(m) > 2]
                if companies:
                    return companies[0]
            
            return None
        except Exception as e:
            print(f"Error extracting company name: {str(e)}")
            return None
            
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo for business stories with rate limiting."""
        try:
            time.sleep(2)  # Rate limiting
            results = list(self.ddgs.text(query, max_results=num_results))
            processed_results = []
            
            for r in results:
                company_name = self._extract_company_name(r['title'] + ' ' + r['body'])
                if company_name:
                    processed_results.append({
                        'title': r['title'],
                        'company_name': company_name,
                        'summary': r['body'],
                        'url': r['link'],
                        'source': 'DuckDuckGo',
                        'content': r['body']
                    })
            
            return processed_results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []
            
    def _try_web_scraping(self, query: str) -> Optional[Dict]:
        """Fallback to web scraping trusted business news sites"""
        try:
            # List of trusted business news sites to search
            sites = [
                'techcrunch.com',
                'forbes.com',
                'hbr.org',
                'bloomberg.com',
                'reuters.com',
                'fastcompany.com',
                'inc.com',
                'technologyreview.com',
                'businessinsider.com',
                'wired.com'
            ]
            
            # Create a Google search query targeting specific sites
            site_query = ' OR '.join(f'site:{site}' for site in sites)
            search_query = f'{query} ({site_query})'
            
            # Use DuckDuckGo as a fallback search engine (no API key needed)
            results = self.search_duckduckgo(search_query, num_results=1)
            
            if results:
                result = results[0]
                # Use newspaper3k to extract article content
                article = Article(result['url'])
                article.download()
                article.parse()
                
                return {
                    'title': article.title,
                    'content': article.text,
                    'url': result['url'],
                    'source': urlparse(result['url']).netloc,
                    'published_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
                }
            return None
        except Exception:
            return None

    def _get_wikipedia_data(self, company_name: str) -> Optional[Dict]:
        """Get Wikipedia data for a company"""
        try:
            # Search Wikipedia for company page
            search_results = self.wiki.search(company_name)
            if not search_results:
                return None
            
            # Try to find the most relevant page
            for page_title in search_results:
                page = self.wiki.page(page_title)
                if page.exists() and company_name.lower() in page.title.lower():
                    # Extract key sections
                    sections = self._extract_relevant_sections(page)
                    
                    # Determine company details
                    company_details = {
                        'title': page.title,
                        'summary': page.summary,
                        'url': page.fullurl,
                        'sections': sections,
                        'content': page.text[:5000],  # First 5000 chars
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    return company_details
            
            return None
            
        except Exception as e:
            print(f"Error getting Wikipedia data: {str(e)}")
            return None

    def _determine_story_type(self, wiki_data: Dict) -> str:
        """Determine the type of story based on content"""
        content = wiki_data.get('content', '').lower()
        
        if any(word in content for word in ['pivot', 'transform', 'change direction', 'reinvent']):
            return 'pivot'
        elif any(word in content for word in ['innovate', 'breakthrough', 'revolutionary', 'disrupt']):
            return 'innovation'
        elif any(word in content for word in ['success', 'growth', 'achievement', 'milestone']):
            return 'success'
        else:
            return 'general'

    def _calculate_reliability_score(self, story):
        """Calculate a reliability score for the story based on various factors"""
        score = 0.5  # Base score
        
        # Increase score for reputable sources
        reputable_sources = ['reuters', 'bloomberg', 'forbes', 'techcrunch', 'wsj', 'nytimes']
        if any(source in story.get('source', '').lower() for source in reputable_sources):
            score += 0.3
            
        # Check for content quality
        if story.get('content'):
            # Length check
            if len(story['content']) > 1000:
                score += 0.1
                
            # Quote check
            if '"' in story['content']:
                score += 0.1
                
        return min(1.0, score)
        
    def _calculate_engagement_potential(self, story):
        """Calculate potential engagement score for the story"""
        score = 0.5  # Base score
        
        # Check title appeal
        title = story.get('title', '').lower()
        engaging_words = ['breakthrough', 'innovative', 'disrupting', 'revolutionary', 'success']
        score += 0.1 * sum(1 for word in engaging_words if word in title)
        
        # Check content sentiment
        if story.get('content'):
            blob = TextBlob(story['content'])
            sentiment = blob.sentiment.polarity
            score += 0.2 if sentiment > 0 else 0.1
            
        # Industry factor
        trending_industries = ['technology', 'healthcare', 'ai', 'renewable']
        if any(ind in story.get('industry', '').lower() for ind in trending_industries):
            score += 0.2
            
        return min(1.0, score)

    def collect_story(self, search_query, industry, subcategory=None, company_size=None, innovation_type=None):
        """Collect a business innovation story based on search criteria"""
        try:
            # Search for news articles and case studies
            news_data = self._search_news(search_query)
            if not news_data:
                return None
            
            # Extract key information
            story = {
                'title': news_data.get('title', ''),
                'content': news_data.get('content', ''),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'published_date': news_data.get('published_date', datetime.now().isoformat()),
                'industry': industry,
                'subcategory': subcategory,
                'company_size': company_size,
                'innovation_type': innovation_type,
                'sentiment_score': self._analyze_sentiment(news_data.get('content', '')),
                'reliability_score': self._calculate_source_reliability(news_data.get('source', '')),
                'collected_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_story(story)
            return story
            
        except Exception as e:
            print(f"Error in collect_story: {str(e)}")
            return None

    def _search_news(self, query: str) -> Optional[Dict]:
        """Search for news articles using various news APIs and web scraping"""
        try:
            # Try multiple news sources in sequence
            news_data = (
                self._try_newsapi(query) or
                self._try_gnews(query) or
                self._try_web_scraping(query)
            )
            return news_data
        except Exception as e:
            print(f"Error in _search_news: {str(e)}")
            return None

    def _try_newsapi(self, query: str) -> Optional[Dict]:
        """Try to get story from NewsAPI"""
        try:
            if not os.getenv('NEWSAPI_KEY'):
                return None
                
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': os.getenv('NEWSAPI_KEY'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with NewsAPI: {str(e)}")
            return None
            
    def _try_gnews(self, query: str) -> Optional[Dict]:
        """Try to get story from GNews"""
        try:
            if not os.getenv('GNEWS_API_KEY'):
                return None
                
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'token': os.getenv('GNEWS_API_KEY'),
                'lang': 'en',
                'max': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with GNews: {str(e)}")
            return None
            
    def _extract_company_name(self, text):
        """Extract company name from text using NLP"""
        try:
            # Common company suffixes
            suffixes = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Co', 'Corporation', 'Technologies', 'Tech']
            
            # Try to find company name with suffix
            for suffix in suffixes:
                pattern = fr'\b[A-Z][A-Za-z0-9\s&]+\s{suffix}\b'
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0].strip()
            
            # Try to find standalone capitalized names (likely company names)
            pattern = r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b'
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common non-company words
                non_companies = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'They'}
                companies = [m for m in matches if m not in non_companies and len(m) > 2]
                if companies:
                    return companies[0]
            
            return None
        except Exception as e:
            print(f"Error extracting company name: {str(e)}")
            return None
            
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo for business stories with rate limiting."""
        try:
            time.sleep(2)  # Rate limiting
            results = list(self.ddgs.text(query, max_results=num_results))
            processed_results = []
            
            for r in results:
                company_name = self._extract_company_name(r['title'] + ' ' + r['body'])
                if company_name:
                    processed_results.append({
                        'title': r['title'],
                        'company_name': company_name,
                        'summary': r['body'],
                        'url': r['link'],
                        'source': 'DuckDuckGo',
                        'content': r['body']
                    })
            
            return processed_results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []
            
    def _try_web_scraping(self, query: str) -> Optional[Dict]:
        """Fallback to web scraping trusted business news sites"""
        try:
            # List of trusted business news sites to search
            sites = [
                'techcrunch.com',
                'forbes.com',
                'hbr.org',
                'bloomberg.com',
                'reuters.com',
                'fastcompany.com',
                'inc.com',
                'technologyreview.com',
                'businessinsider.com',
                'wired.com'
            ]
            
            # Create a Google search query targeting specific sites
            site_query = ' OR '.join(f'site:{site}' for site in sites)
            search_query = f'{query} ({site_query})'
            
            # Use DuckDuckGo as a fallback search engine (no API key needed)
            results = self.search_duckduckgo(search_query, num_results=1)
            
            if results:
                result = results[0]
                # Use newspaper3k to extract article content
                article = Article(result['url'])
                article.download()
                article.parse()
                
                return {
                    'title': article.title,
                    'content': article.text,
                    'url': result['url'],
                    'source': urlparse(result['url']).netloc,
                    'published_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
                }
            return None
        except Exception:
            return None

    def _get_wikipedia_data(self, company_name: str) -> Optional[Dict]:
        """Get Wikipedia data for a company"""
        try:
            # Search Wikipedia for company page
            search_results = self.wiki.search(company_name)
            if not search_results:
                return None
            
            # Try to find the most relevant page
            for page_title in search_results:
                page = self.wiki.page(page_title)
                if page.exists() and company_name.lower() in page.title.lower():
                    # Extract key sections
                    sections = self._extract_relevant_sections(page)
                    
                    # Determine company details
                    company_details = {
                        'title': page.title,
                        'summary': page.summary,
                        'url': page.fullurl,
                        'sections': sections,
                        'content': page.text[:5000],  # First 5000 chars
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    return company_details
            
            return None
            
        except Exception as e:
            print(f"Error getting Wikipedia data: {str(e)}")
            return None

    def _determine_story_type(self, wiki_data: Dict) -> str:
        """Determine the type of story based on content"""
        content = wiki_data.get('content', '').lower()
        
        if any(word in content for word in ['pivot', 'transform', 'change direction', 'reinvent']):
            return 'pivot'
        elif any(word in content for word in ['innovate', 'breakthrough', 'revolutionary', 'disrupt']):
            return 'innovation'
        elif any(word in content for word in ['success', 'growth', 'achievement', 'milestone']):
            return 'success'
        else:
            return 'general'

    def _calculate_reliability_score(self, story):
        """Calculate a reliability score for the story based on various factors"""
        score = 0.5  # Base score
        
        # Increase score for reputable sources
        reputable_sources = ['reuters', 'bloomberg', 'forbes', 'techcrunch', 'wsj', 'nytimes']
        if any(source in story.get('source', '').lower() for source in reputable_sources):
            score += 0.3
            
        # Check for content quality
        if story.get('content'):
            # Length check
            if len(story['content']) > 1000:
                score += 0.1
                
            # Quote check
            if '"' in story['content']:
                score += 0.1
                
        return min(1.0, score)
        
    def _calculate_engagement_potential(self, story):
        """Calculate potential engagement score for the story"""
        score = 0.5  # Base score
        
        # Check title appeal
        title = story.get('title', '').lower()
        engaging_words = ['breakthrough', 'innovative', 'disrupting', 'revolutionary', 'success']
        score += 0.1 * sum(1 for word in engaging_words if word in title)
        
        # Check content sentiment
        if story.get('content'):
            blob = TextBlob(story['content'])
            sentiment = blob.sentiment.polarity
            score += 0.2 if sentiment > 0 else 0.1
            
        # Industry factor
        trending_industries = ['technology', 'healthcare', 'ai', 'renewable']
        if any(ind in story.get('industry', '').lower() for ind in trending_industries):
            score += 0.2
            
        return min(1.0, score)

    def collect_story(self, search_query, industry, subcategory=None, company_size=None, innovation_type=None):
        """Collect a business innovation story based on search criteria"""
        try:
            # Search for news articles and case studies
            news_data = self._search_news(search_query)
            if not news_data:
                return None
            
            # Extract key information
            story = {
                'title': news_data.get('title', ''),
                'content': news_data.get('content', ''),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'published_date': news_data.get('published_date', datetime.now().isoformat()),
                'industry': industry,
                'subcategory': subcategory,
                'company_size': company_size,
                'innovation_type': innovation_type,
                'sentiment_score': self._analyze_sentiment(news_data.get('content', '')),
                'reliability_score': self._calculate_source_reliability(news_data.get('source', '')),
                'collected_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_story(story)
            return story
            
        except Exception as e:
            print(f"Error in collect_story: {str(e)}")
            return None

    def _search_news(self, query: str) -> Optional[Dict]:
        """Search for news articles using various news APIs and web scraping"""
        try:
            # Try multiple news sources in sequence
            news_data = (
                self._try_newsapi(query) or
                self._try_gnews(query) or
                self._try_web_scraping(query)
            )
            return news_data
        except Exception as e:
            print(f"Error in _search_news: {str(e)}")
            return None

    def _try_newsapi(self, query: str) -> Optional[Dict]:
        """Try to get story from NewsAPI"""
        try:
            if not os.getenv('NEWSAPI_KEY'):
                return None
                
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': os.getenv('NEWSAPI_KEY'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with NewsAPI: {str(e)}")
            return None
            
    def _try_gnews(self, query: str) -> Optional[Dict]:
        """Try to get story from GNews"""
        try:
            if not os.getenv('GNEWS_API_KEY'):
                return None
                
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'token': os.getenv('GNEWS_API_KEY'),
                'lang': 'en',
                'max': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article = data['articles'][0]
                    
                    # Extract company name from title or description
                    company_name = self._extract_company_name(article['title'] + ' ' + article['description'])
                    
                    if company_name:
                        return {
                            'title': article['title'],
                            'company_name': company_name,
                            'summary': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'content': article['content'] if 'content' in article else article['description']
                        }
            return None
        except Exception as e:
            print(f"Error with GNews: {str(e)}")
            return None
            
    def _extract_company_name(self, text):
        """Extract company name from text using NLP"""
        try:
            # Common company suffixes
            suffixes = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Co', 'Corporation', 'Technologies', 'Tech']
            
            # Try to find company name with suffix
            for suffix in suffixes:
                pattern = fr'\b[A-Z][A-Za-z0-9\s&]+\s{suffix}\b'
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0].strip()
            
            # Try to find standalone capitalized names (likely company names)
            pattern = r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b'
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common non-company words
                non_companies = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'They'}
                companies = [m for m in matches if m not in non_companies and len(m) > 2]
                if companies:
                    return companies[0]
            
            return None
        except Exception as e:
            print(f"Error extracting company name: {str(e)}")
            return None
            
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo for business stories with rate limiting."""
        try:
            time.sleep(2)  # Rate limiting
            results = list(self.ddgs.text(query, max_results=num_results))
            processed_results = []
            
            for r in results:
                company_name = self._extract_company_name(r['title'] + ' ' + r['body'])
                if company_name:
                    processed_results.append({
                        'title': r['title'],
                        'company_name': company_name,
                        'summary': r['body'],
                        'url': r['link'],
                        'source': 'DuckDuckGo',
                        'content': r['body']
                    })
            
            return processed_results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []
            
    def _try_web_scraping(self, query: str) -> Optional[Dict]:
        """Fallback to web scraping trusted business news sites"""
        try:
            # List of trusted business news sites to search
            sites = [
                'techcrunch.com',
                'forbes.com',
                'hbr.org',
                'bloomberg.com',
                'reuters.com',
                'fastcompany.com',
                'inc.com',
                'technologyreview.com',
                'businessinsider.com',
                'wired.com'
            ]
            
            # Create a Google search query targeting specific sites
            site_query = ' OR '.join(f'site:{site}' for site in sites)
            search_query = f'{query} ({site_query})'
            
            # Use DuckDuckGo as a fallback search engine (no API key needed)
            results = self.search_duckduckgo(search_query, num_results=1)
            
            if results:
                result = results[0]
                # Use newspaper3k to extract article content
                article = Article(result['url'])
                article.download()
                article.parse()
                
                return {
                    'title': article.title,
                    'content': article.text,
                    'url': result['url'],
                    'source': urlparse(result['url']).netloc,
                    'published_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
                }
            return None
        except Exception:
            return None

    def _get_wikipedia_data(self, company_name: str) -> Optional[Dict]:
        """Get Wikipedia data for a company"""
        try:
            # Search Wikipedia for company page
            search_results = self.wiki.search(company_name)
            if not search_results:
                return None
            
            # Try to find the most relevant page
            for page_title in search_results:
                page = self.wiki.page(page_title)
                if page.exists() and company_name.lower() in page.title.lower():
                    # Extract key sections
                    sections = self._extract_relevant_sections(page)
                    
                    # Determine company details
                    company_details = {
                        'title': page.title,
                        'summary': page.summary,
                        'url': page.fullurl,
                        'sections': sections,
                        'content': page.text[:5000],  # First 5000 chars
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    return company_details
            
            return None
            
        except Exception as e:
            print(f"Error getting Wikipedia data: {str(e)}")
            return None

    def _determine_story_type(self, wiki_data: Dict) -> str:
        """Determine the type of story based on content"""
        content = wiki_data.get('content', '').lower()
        
        if any(word in content for word in ['pivot', 'transform', 'change direction', 'reinvent']):
            return 'pivot'
        elif any(word in content for word in ['innovate', 'breakthrough', 'revolutionary', 'disrupt']):
            return 'innovation'
        elif any(word in content for word in ['success', 'growth', 'achievement', 'milestone']):
            return 'success'
        else:
            return 'general'

    def _calculate_reliability_score(self, story):
        """Calculate a reliability score for the story based on various factors"""
        score = 0.5  # Base score
        
        # Increase score for reputable sources
        reputable_sources = ['reuters', 'bloomberg', 'forbes', 'techcrunch', 'wsj', 'nytimes']
        if any(source in story.get('source', '').lower() for source in reputable_sources):
            score += 0.3
            
        # Check for content quality
        if story.get('content'):
            # Length check
            if len(story['content']) > 1000:
                score += 0.1
                
            # Quote check
            if '"' in story['content']:
                score += 0.1
                
        return min(1.0, score)
        
    def _calculate_engagement_potential(self, story):
        """Calculate potential engagement score for the story"""
        score = 0.5  # Base score
        
        # Check title appeal
        title = story.get('title', '').lower()
        engaging_words = ['breakthrough', 'innovative', 'disrupting', 'revolutionary', 'success']
        score += 0.1 * sum(1 for word in engaging_words if word in title)
        
        # Check content sentiment
        if story.get('content'):
            blob = TextBlob(story['content'])
            sentiment = blob.sentiment.polarity
            score += 0.2 if sentiment > 0 else 0.1
            
        # Industry factor
        trending_industries = ['technology', 'healthcare', 'ai', 'renewable']
        if any(ind in story.get('industry', '').lower() for ind in trending_industries):
            score += 0.2
            
        return min(1.0, score)

    def get_random_stories(self, count: int = 5) -> List[Dict]:
        """Get random stories from the database"""
        print("Fetching random stories from database...")
        stories = self.db.execute("""
            SELECT * FROM business_stories 
            ORDER BY RANDOM() 
            LIMIT %s
        """, (count,))
        print(f"Found {len(stories)} stories in database")
        return stories

    def get_random_story(self) -> Optional[Dict]:
        """Get a single random story from the database"""
        stories = self.get_random_stories(1)
        return stories[0] if stories else None
