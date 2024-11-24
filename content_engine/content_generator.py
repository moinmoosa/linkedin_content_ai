import random
from typing import Dict, List, Optional
import openai
from .content_analyzer import ContentAnalyzer
from .enhanced_generator import EnhancedContentGenerator

class ContentGenerator:
    def __init__(self):
        self.analyzer = ContentAnalyzer()
        self.enhanced_generator = EnhancedContentGenerator()
        self.models = {
            'primary': 'gpt-4',
            'fallback': 'gpt-3.5-turbo'
        }
        
    def add_training_example(self, content: str, metadata: Dict):
        """Add a new training example"""
        self.analyzer.add_example(content, metadata)
    
    def generate_content(self, params: Dict) -> str:
        """Generate content using the enhanced generator"""
        try:
            # Generate multiple posts
            posts = self.enhanced_generator.generate_multiple_posts(num_posts=3)
            
            # Save the generated posts
            self.enhanced_generator.save_generated_posts(posts)
            
            # Return the best post based on the parameters
            return self._select_best_post(posts, params)
        except Exception as e:
            # Fallback to simple generation if enhanced generator fails
            return self._simple_generate(params)
    
    def _select_best_post(self, posts: List[Dict], params: Dict) -> str:
        """Select the best post based on parameters"""
        if not posts:
            return self._simple_generate(params)
        
        # If a specific type is requested, filter for that type
        if 'type' in params:
            filtered_posts = [p for p in posts if p['type'] == params['type']]
            if filtered_posts:
                return filtered_posts[0]['content']
        
        # Otherwise return the first post
        return posts[0]['content']
    
    def _simple_generate(self, params: Dict) -> str:
        """Simple fallback generation method"""
        prompt = f"""Create a compelling LinkedIn post about {params.get('topic', 'business')}. 
        Focus on providing valuable insights and engaging the audience. 
        Include relevant hashtags."""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.models['primary'],
                messages=[
                    {"role": "system", "content": "You are a professional business content writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            # Final fallback to GPT-3.5-turbo
            response = openai.ChatCompletion.create(
                model=self.models['fallback'],
                messages=[
                    {"role": "system", "content": "You are a professional business content writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
