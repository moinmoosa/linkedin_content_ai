from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from content_engine.content_generator import ContentGenerator
from content_engine.enhanced_generator import EnhancedContentGenerator
from content_engine.post_recommender import PostRecommender
from content_engine.story_collector import BusinessStoryCollector
from content_engine.auto_recommender import AutoPostRecommender
import os
from dotenv import load_dotenv
import openai
import json
from datetime import datetime
from scripts.setup import setup_environment
from database.db_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize the application
def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Ensure environment is set up
    if not setup_environment():
        raise RuntimeError("Failed to initialize application environment")
    
    # Initialize OpenAI
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    # Initialize components
    app.content_generator = ContentGenerator()
    app.generator = EnhancedContentGenerator()
    app.recommender = PostRecommender()
    app.collector = BusinessStoryCollector()
    app.auto_recommender = AutoPostRecommender()  # Add auto recommender
    app.db = DatabaseManager()
    
    return app

app = create_app()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommender')
def recommender_page():
    return render_template('recommender.html')

@app.route('/auto_recommender')
def auto_recommender_page():
    return render_template('auto_recommender.html')

@app.route('/add-example', methods=['POST'])
def add_example():
    data = request.json
    content = data.get('content')
    metadata = {
        'industry': data.get('industry'),
        'story_type': data.get('story_type'),
        'topic': data.get('topic'),
        'tone': data.get('tone', 'professional')
    }
    
    app.content_generator.add_training_example(content, metadata)
    return jsonify({'status': 'success'})

@app.route('/generate-post', methods=['POST'])
def generate_post():
    data = request.json
    params = {
        'topic': data.get('topic'),
        'industry': data.get('industry'),
        'tone': data.get('tone', 'professional'),
        'story_type': data.get('story_type', 'insight')
    }
    
    try:
        content = app.content_generator.generate_content(params)
        return jsonify({
            'status': 'success',
            'content': content
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/schedule-post', methods=['POST'])
def schedule_post():
    data = request.json
    scheduled_time = data.get('scheduled_time')
    content = data.get('content')
    
    # Load existing scheduled posts
    try:
        with open('scheduled_posts.json', 'r') as f:
            scheduled_posts = json.load(f)
    except FileNotFoundError:
        scheduled_posts = []
    
    # Add new post
    scheduled_posts.append({
        'content': content,
        'scheduled_time': scheduled_time,
        'created_at': datetime.now().isoformat()
    })
    
    # Save updated posts
    with open('scheduled_posts.json', 'w') as f:
        json.dump(scheduled_posts, f, indent=2)
    
    return jsonify({'status': 'success'})

@app.route('/get-scheduled-posts', methods=['GET'])
def get_scheduled_posts():
    try:
        with open('scheduled_posts.json', 'r') as f:
            scheduled_posts = json.load(f)
    except FileNotFoundError:
        scheduled_posts = []
    
    return jsonify(scheduled_posts)

@app.route('/api/generate', methods=['POST'])
def generate_post_recommender():
    try:
        data = request.json
        company_name = data.get('company_name')
        industry = data.get('industry')
        post_type = data.get('post_type')
        
        # Get recommended settings based on past feedback
        settings = app.recommender.get_recommended_settings(company_name, industry)
        
        # Collect company story
        story = app.collector.collect_story(company_name)
        if not story:
            return jsonify({
                'success': False,
                'error': 'Could not find company story'
            })
        
        # Generate post with recommended settings
        content = app.generator._generate_single_post(story, settings['post_type'])
        
        # Save post to database
        post_id = app.recommender.save_post(
            content=content,
            company_name=company_name,
            industry=industry,
            post_type=post_type,
            metrics=app.generator.quality_metrics
        )
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'content': content
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/generate-batch', methods=['POST'])
def generate_batch():
    try:
        data = request.json
        company_names = data.get('company_names', [])
        industry = data.get('industry')
        
        if not company_names or not industry:
            return jsonify({
                'success': False,
                'error': 'Company names and industry are required'
            })
        
        # Check if there's a pending batch that needs feedback
        current_batch = app.recommender.get_current_batch_status()
        if current_batch and current_batch['total_posts'] > current_batch['posts_with_feedback']:
            return jsonify({
                'success': False,
                'error': 'Previous batch requires feedback',
                'pending_batch': current_batch
            })
        
        # Create new batch
        batch_id = app.recommender.create_batch()
        
        # Generate 5 posts
        generated_posts = []
        for company_name in company_names[:5]:  # Limit to 5 companies
            # Get recommended settings
            settings = app.recommender.get_recommended_settings(company_name, industry)
            
            # Collect company story
            story = app.collector.collect_story(company_name)
            if story:
                # Generate post
                content = app.generator._generate_single_post(story, settings['post_type'])
                
                # Save post
                post_id = app.recommender.save_post(
                    content=content,
                    company_name=company_name,
                    industry=industry,
                    post_type=settings['post_type'],
                    metrics=app.generator.quality_metrics,
                    batch_id=batch_id
                )
                
                generated_posts.append({
                    'post_id': post_id,
                    'content': content,
                    'company_name': company_name
                })
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'posts': generated_posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/batch/<int:batch_id>/posts', methods=['GET'])
def get_batch_posts(batch_id):
    try:
        posts = app.recommender.get_batch_posts(batch_id)
        return jsonify({
            'success': True,
            'posts': posts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/current-batch', methods=['GET'])
def get_current_batch():
    try:
        current_batch = app.recommender.get_current_batch_status()
        return jsonify({
            'success': True,
            'batch': current_batch
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/batch/<int:batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    try:
        current_batch = app.recommender.get_current_batch_status()
        if current_batch and current_batch['batch_id'] == batch_id:
            return jsonify({
                'success': True,
                'status': current_batch['status'],
                'total_posts': current_batch['total_posts'],
                'posts_with_feedback': current_batch['posts_with_feedback']
            })
        return jsonify({
            'success': True,
            'status': 'completed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        post_id = data.get('post_id')
        feedback_type = data.get('feedback_type')
        additional_text = data.get('additional_text')
        
        success = app.recommender.save_feedback(
            post_id=post_id,
            feedback_type=feedback_type,
            additional_text=additional_text
        )
        
        return jsonify({
            'success': success
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/submit-feedback', methods=['POST'])
def submit_feedback_batch():
    try:
        data = request.json
        post_id = data.get('post_id')
        feedback_type = data.get('feedback_type')
        feedback_text = data.get('feedback_text')
        
        if not post_id or not feedback_type:
            return jsonify({
                'success': False,
                'error': 'Post ID and feedback type are required'
            })
        
        # Save feedback
        app.recommender.save_feedback(post_id, feedback_type, feedback_text)
        
        # Check if all posts in the batch have feedback
        current_batch = app.recommender.get_current_batch_status()
        if current_batch and current_batch['total_posts'] == current_batch['posts_with_feedback']:
            app.recommender.mark_batch_complete(current_batch['batch_id'])
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/history')
def get_history():
    try:
        company_name = request.args.get('company_name')
        industry = request.args.get('industry')
        
        history = app.recommender.get_feedback_history(
            company_name=company_name,
            industry=industry
        )
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recommendations')
def get_recommendations():
    """Get automatic post recommendations"""
    try:
        num_recommendations = int(request.args.get('num', 5))
        recommender = PostRecommender()
        recommendations = recommender.get_automatic_recommendations(num_recommendations)
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Auto Recommender Routes
@app.route('/api/generate_posts', methods=['POST'])
def generate_posts():
    """Generate a batch of posts"""
    try:
        print("Starting post generation...")
        count = request.json.get('count', 5)
        print(f"Requested {count} posts")
        posts = app.auto_recommender.generate_batch_posts(count)
        print(f"Generated {len(posts)} posts")
        return jsonify(posts), 200
    except Exception as e:
        print(f"Error in generate_posts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pending_posts', methods=['GET'])
def get_pending_posts():
    """Get posts pending review"""
    try:
        posts = app.auto_recommender.get_pending_posts()
        return jsonify(posts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/approve_post', methods=['POST'])
def approve_post():
    """Approve or reject a post"""
    try:
        post_id = request.json['post_id']
        approved = request.json['approved']
        feedback_tags = request.json.get('feedback_tags', [])
        
        # Record approval
        app.auto_recommender.record_approval(post_id, approved)
        
        # If not approved, record feedback
        if not approved and feedback_tags:
            app.auto_recommender.add_feedback(post_id, feedback_tags)
        
        # Learn from feedback
        app.auto_recommender.learn_from_feedback()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_stats', methods=['GET'])
def get_system_stats():
    """Get system performance statistics"""
    try:
        stats = app.auto_recommender.get_system_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback_tags', methods=['GET'])
def get_feedback_tags():
    """Get available feedback tags"""
    try:
        return jsonify(app.auto_recommender.FEEDBACK_TAGS), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_post', methods=['POST'])
def generate_auto_post():
    """Generate a new post automatically"""
    try:
        post_data = app.auto_recommender.generate_post()
        return jsonify(post_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_feedback', methods=['POST'])
def submit_auto_feedback():
    """Submit feedback tags for a post"""
    try:
        data = request.json
        post_id = data.get('post_id')
        feedback_tags = data.get('feedback_tags')
        
        if post_id is None or not feedback_tags:
            return jsonify({'error': 'Missing required fields'}), 400
        
        app.auto_recommender.add_feedback(post_id, feedback_tags)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback_stats/<int:post_id>', methods=['GET'])
def get_feedback_stats(post_id):
    """Get feedback statistics for a post"""
    try:
        stats = app.auto_recommender.get_feedback_stats(post_id)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
