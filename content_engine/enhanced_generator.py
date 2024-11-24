import openai
from typing import List, Dict, Optional, Union
import json
import concurrent.futures
from datetime import datetime
import logging
from .story_collector import BusinessStoryCollector
from .templates import ContentTemplates

class EnhancedContentGenerator:
    def __init__(self):
        self.story_collector = BusinessStoryCollector()
        self.templates = ContentTemplates()
        self.logger = logging.getLogger(__name__)
        
        # OpenAI configuration
        self.models = {
            'primary': 'gpt-4',
            'fallback': 'gpt-3.5-turbo'
        }
        
        # Quality thresholds
        self.min_word_count = 100
        self.max_word_count = 300
        self.quality_metrics = {
            'engagement_triggers': ['story', 'lesson', 'question', 'statistic'],
            'required_elements': ['context', 'insight', 'takeaway'],
            'authenticity_markers': {
                'specific_dates': True,
                'real_numbers': True,
                'named_sources': True,
                'direct_quotes': True,
                'verifiable_facts': True
            },
            'insight_quality': {
                'behind_scenes': True,  # Behind-the-scenes details
                'counter_intuitive': True,  # Counter-intuitive findings
                'industry_specific': True,  # Industry-specific knowledge
                'decision_rationale': True,  # Why certain decisions were made
                'failure_lessons': True  # Lessons from failures/challenges
            }
        }

    def _prepare_story_prompt(self, story: Dict, template: Union[str, Dict]) -> str:
        """Prepare a prompt for story generation"""
        if isinstance(template, str):
            # For string templates (like aerospace)
            return template.format(
                company_name=story.get('company_name', ''),
                industry=story.get('industry', ''),
                product=story.get('product', ''),
                innovation=story.get('innovation', ''),
                impact=story.get('impact', '')
            )
        else:
            # For dictionary templates
            return f"""
Generate a compelling LinkedIn post about {story.get('company_name', '')} in the {story.get('industry', '')} industry.

Company Details:
- Product: {story.get('product', '')}
- Innovation: {story.get('innovation', '')}
- Impact: {story.get('impact', '')}
- Key Dates: {', '.join(story.get('dates', []))}
- Key Figures: {', '.join(story.get('figures', []))}

Recent News:
{self._format_recent_news(story.get('recent_news', []))}

Post Structure:
{json.dumps(template['structure'], indent=2)}

Required Elements:
{json.dumps(template['requirements'], indent=2)}

Important Instructions:
1. Use ONLY factual information provided above
2. Do NOT make up or invent any details not provided
3. Include specific dates, numbers, and figures from the provided information
4. Focus on the actual industry and business model described
5. Use appropriate technical terms for the specific industry
6. Format with emojis and proper LinkedIn spacing

Generate the post now:
"""

    def _format_recent_news(self, news_articles: List[Dict]) -> str:
        """Format recent news articles for context"""
        if not news_articles:
            return "No recent news available."
        
        formatted_news = []
        for article in news_articles[:2]:  # Use only the 2 most recent articles
            formatted_news.append(f"- {article.get('title', '')}: {article.get('text', '')[:200]}...")
        
        return "\n".join(formatted_news)

    def _call_openai(self, prompt: str, model: str = None) -> str:
        """Make an API call to OpenAI with fallback"""
        try:
            print(f"Calling OpenAI API with model: {model or self.models['primary']}")
            model = model or self.models['primary']
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional business content writer creating engaging LinkedIn posts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            print("Successfully received response from OpenAI")
            return response.choices[0].message.content
        except Exception as e:
            if model == self.models['primary']:
                print(f"Primary model failed with error: {str(e)}, falling back to {self.models['fallback']}")
                return self._call_openai(prompt, self.models['fallback'])
            print(f"OpenAI API call failed: {str(e)}")
            raise e

    def _check_authenticity_markers(self, content: str) -> Dict[str, bool]:
        """Check for authenticity markers in the content"""
        content = content.lower()
        return {
            'specific_dates': any(char.isdigit() and ("," in content or "-" in content) for char in content),
            'real_numbers': any(char.isdigit() for char in content),
            'named_sources': any(m in content for m in ["according to", "said", "stated", "ceo", "founder", "director", "leader"]),
            'direct_quotes': '"' in content or '"' in content or '"' in content,
            'verifiable_facts': any(m in content for m in ["reported", "announced", "published", "confirmed", "launched", "achieved", "milestone"])
        }

    def _check_insight_markers(self, content: str) -> Dict[str, bool]:
        """Check for insight quality markers in the content"""
        content = content.lower()
        return {
            'behind_scenes': any(m in content for m in [
                "internally", "behind the scenes", "within the company",
                "process", "system", "building", "development", "integration"
            ]),
            'counter_intuitive': any(m in content for m in [
                "surprisingly", "contrary to", "unexpected", "unlike",
                "instead of", "rather than", "despite", "however"
            ]),
            'industry_specific': any(m in content for m in [
                "in the industry", "sector-specific", "market dynamics",
                "landscape", "segment", "vertical", "market"
            ]),
            'decision_rationale': any(m in content for m in [
                "decided to", "chose to", "reasoning behind",
                "strategy", "approach", "solution", "method"
            ]),
            'failure_lessons': any(m in content for m in [
                "learned from", "mistake", "challenge", "hurdle",
                "obstacle", "issue", "problem", "difficulty"
            ])
        }

    def _validate_authenticity(self, content: str) -> bool:
        """Validate the authenticity markers in the content"""
        metrics = self._check_authenticity_markers(content)
        required_metrics = self.quality_metrics['authenticity_markers']
        # Require at least 4 out of 5 authenticity markers
        return sum(metrics[marker] for marker in required_metrics if required_metrics[marker]) >= 4

    def _validate_insights(self, content: str) -> bool:
        """Validate the quality of insights in the content"""
        metrics = self._check_insight_markers(content)
        required_metrics = self.quality_metrics['insight_quality']
        # Require at least 4 out of 5 insight markers
        return sum(metrics[marker] for marker in required_metrics if required_metrics[marker]) >= 4

    def _enhance_content(self, content: str) -> str:
        """Enhance the generated content with engagement elements"""
        # First validate the content quality
        if not self._validate_authenticity(content) or not self._validate_insights(content):
            # If content doesn't meet quality standards, regenerate with stronger emphasis on quality
            enhance_prompt = f"""Significantly improve this LinkedIn post to include more authentic details and unique insights:

Original Post:
{content}

Requirements:
1. Add specific dates and verifiable numbers
2. Include direct quotes or references to sources
3. Reveal behind-the-scenes details or decision-making processes
4. Share counter-intuitive findings or unexpected outcomes
5. Add industry-specific insights that casual observers might miss
6. Discuss both successes and challenges/failures
7. Maintain natural flow and engagement
8. Add relevant emojis where appropriate
9. Break long paragraphs into shorter ones
10. Include relevant hashtags

Enhanced version:"""
        else:
            enhance_prompt = f"""Improve this LinkedIn post while maintaining its core message and authenticity:

Original Post:
{content}

Requirements:
1. Add one thought-provoking question
2. Ensure there's a clear call-to-action
3. Add relevant emojis where appropriate
4. Break long paragraphs into shorter ones
5. Ensure hashtags are relevant and trending
6. Maintain all specific details and unique insights

Enhanced version:"""

        return self._call_openai(enhance_prompt)

    def _generate_single_post(self, story: Dict, post_type: str) -> str:
        """Generate a single post from a story"""
        # Get appropriate template
        template = None
        if post_type == 'pivot':
            template = self.templates.get_pivot_template()
        elif post_type == 'success':
            template = self.templates.get_success_template()
        elif post_type == 'innovation':
            template = self.templates.get_innovation_template()
        elif post_type == 'aerospace':
            template = self.templates.get_aerospace_template()
        
        if not template:
            raise ValueError(f"Invalid post type: {post_type}")
        
        # Generate initial content
        prompt = self._prepare_story_prompt(story, template)
        content = self._call_openai(prompt)
        
        # Enhance content
        enhanced_content = self._enhance_content(content)
        
        return enhanced_content

    def generate_multiple_posts(self, num_posts: int = 3) -> List[str]:
        """Generate multiple unique posts in parallel"""
        # Collect fresh stories
        all_stories = self.story_collector.collect_all_stories()
        
        # Prepare generation tasks
        tasks = []
        for post_type, stories in all_stories.items():
            for story in stories[:num_posts]:
                tasks.append((story, post_type.replace('_stories', '')))
        
        # Generate posts in parallel
        posts = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_task = {
                executor.submit(self._generate_single_post, story, post_type): (story, post_type)
                for story, post_type in tasks[:num_posts]  # Limit to requested number of posts
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                story, post_type = future_to_task[future]
                try:
                    post = future.result()
                    posts.append({
                        'content': post,
                        'type': post_type,
                        'story_title': story.get('title', ''),
                        'generated_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    self.logger.error(f"Error generating post: {e}")
        
        return posts

    def save_generated_posts(self, posts: List[Dict], filename: str = 'generated_posts.json'):
        """Save generated posts to a JSON file"""
        try:
            with open(f'data/{filename}', 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving posts: {e}")

    def generate_and_save_posts(self, num_posts: int = 3) -> List[Dict]:
        """Generate posts and save them to a file"""
        posts = self.generate_multiple_posts(num_posts)
        self.save_generated_posts(posts)
        return posts
