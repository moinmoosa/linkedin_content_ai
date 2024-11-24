import os
from content_engine.enhanced_generator import EnhancedContentGenerator
import json
import openai
from dotenv import load_dotenv

def test_enhanced_generator():
    """Test the enhanced content generator"""
    
    # Load environment variables
    load_dotenv()
    
    # Set OpenAI API key
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    
    # Test story about Amul
    test_story = {
        'company_name': 'Amul',
        'industry': 'Dairy and Food Products',
        'product': 'Dairy products and cooperative model',
        'innovation': 'Farmer-owned cooperative model and integrated supply chain',
        'impact': 'Revolutionized India\'s dairy industry and empowered millions of farmers',
        'dates': ['1946-12-14', '2022-03-31'],
        'figures': [
            '3.6 million milk producer members',
            'Rs. 61,000 crore ($7.5B) annual revenue',
            '15 million liters daily milk procurement'
        ],
        'recent_news': [
            {
                'title': 'Amul Achieves Record Revenue',
                'date': '2023-04-12',
                'summary': 'GCMMF reports 18.5% growth in 2022-23 with turnover reaching Rs. 55,055 crore'
            },
            {
                'title': 'Amul Digital Payments to Farmers',
                'date': '2023-03-15',
                'summary': 'Successfully implements direct digital payments to 3.6 million farmer members'
            },
            {
                'title': 'Amul\'s Brand Value Growth',
                'date': '2023-01-20',
                'summary': 'Ranked as 8th largest dairy organization globally by Rabobank'
            }
        ]
    }
    
    # Initialize generator
    generator = EnhancedContentGenerator()
    
    print("\n=== Generating Post ===\n")
    
    # Generate content
    content = generator._generate_single_post(test_story, 'innovation')
    
    print(content)
    print("\n=== Validation Results ===\n")
    
    # Validate content
    authenticity_score = generator._validate_authenticity(content)
    insight_score = generator._validate_insights(content)
    
    print(f"Authenticity Score: {'PASS' if authenticity_score else 'FAIL'}")
    print(f"Insight Score: {'PASS' if insight_score else 'FAIL'}")
    
    print("\n=== Detected Quality Markers ===\n")
    
    # Check for quality markers
    authenticity_markers = generator._check_authenticity_markers(content)
    insight_markers = generator._check_insight_markers(content)
    
    print("Authenticity Markers Found:")
    for marker, present in authenticity_markers.items():
        print(f"- {marker}: {'✓' if present else '✗'}")
    
    print("\nInsight Quality Markers Found:")
    for marker, present in insight_markers.items():
        print(f"- {marker}: {'✓' if present else '✗'}")

if __name__ == '__main__':
    test_enhanced_generator()
