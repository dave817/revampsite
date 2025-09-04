#!/usr/bin/env python3
"""
Flask API for RevampSite
Main application server handling requirements collection
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime

from instagram_scraper import InstagramScraper
from requirements_collector import ConversationManager, RequirementsCollector
from database import Database
from config import Config
import asyncio
from lovable_automation import LovableService

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize components
db = Database()
scraper = InstagramScraper()

# Store active sessions in memory (in production, use Redis)
active_sessions = {}


@app.route('/')
def index():
    """Serve the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Template error: {e}")
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>RevampSite</title></head>
        <body style="font-family: sans-serif; padding: 50px;">
            <h1>RevampSite API Server</h1>
            <p>The server is running!</p>
            <p>API Endpoints:</p>
            <ul>
                <li>POST /api/start - Start new project</li>
                <li>POST /api/chat - Send chat message</li>
                <li>GET /api/project/&lt;id&gt; - Get project details</li>
            </ul>
            <p style="color: red;">Note: Template not found. Please check templates/index.html exists.</p>
        </body>
        </html>
        '''


@app.route('/api/start', methods=['POST'])
def start_project():
    """Start a new project with Instagram username"""
    try:
        data = request.json
        instagram_username = data.get('instagram_username', '').strip().replace('@', '')
        
        if not instagram_username:
            return jsonify({'error': 'Instagram username is required'}), 400
        
        # Create project in database
        project_id = db.create_project(instagram_username)
        
        # Scrape Instagram data
        print(f"Scraping Instagram profile: @{instagram_username}")
        instagram_data = scraper.get_full_profile_analysis(instagram_username)
        
        if not instagram_data:
            return jsonify({'error': 'Failed to fetch Instagram profile. Please check the username.'}), 404
        
        # Save Instagram data to database
        db.save_instagram_data(
            project_id,
            instagram_data,
            instagram_data.get('brand_colors', []),
            instagram_data.get('business_info', {})
        )
        
        # Initialize conversation
        conversation = ConversationManager(project_id)
        conversation_state = conversation.start_conversation(instagram_data)
        
        # Store session in memory
        active_sessions[conversation.session_id] = conversation
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'session_id': conversation.session_id,
            'instagram_data': {
                'username': instagram_data.get('username'),
                'full_name': instagram_data.get('full_name'),
                'bio': instagram_data.get('biography', '')[:200],
                'followers': instagram_data.get('follower_count'),
                'business_type': instagram_data.get('business_info', {}).get('business_type')
            },
            'conversation': conversation_state
        })
    
    except Exception as e:
        print(f"Error starting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_input = data.get('message', '').strip()
        
        if not session_id or session_id not in active_sessions:
            return jsonify({'error': 'Invalid or expired session'}), 400
        
        # Get conversation manager
        conversation = active_sessions[session_id]
        
        # Process user input
        response = conversation.process_user_input(user_input)
        
        # If complete, save requirements and generate prompt
        if response.get('is_complete'):
            requirements = response.get('requirements')
            if requirements:
                # Save to database
                db.save_requirements(conversation.project_id, requirements)
                
                # Generate Lovable prompt
                lovable_prompt = conversation.collector.generate_lovable_prompt()
                response['lovable_prompt'] = lovable_prompt
                
                # Save prompt to database
                db.save_generated_content(conversation.project_id, lovable_prompt)
                
                # Update project status
                db.update_project_status(conversation.project_id, 'requirements_collected')
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details"""
    try:
        project = db.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        instagram_data = db.get_instagram_data(project_id)
        requirements = db.get_requirements(project_id)
        
        return jsonify({
            'project': project,
            'instagram_data': instagram_data,
            'requirements': requirements
        })
    
    except Exception as e:
        print(f"Error getting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = db.get_all_projects(limit=50)
        return jsonify({'projects': projects})
    
    except Exception as e:
        print(f"Error getting projects: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_prompt/<project_id>', methods=['GET'])
def generate_prompt(project_id):
    """Generate Lovable prompt for a project"""
    try:
        # Get project data
        instagram_data = db.get_instagram_data(project_id)
        requirements = db.get_requirements(project_id)
        
        if not instagram_data or not requirements:
            return jsonify({'error': 'Missing data for prompt generation'}), 400
        
        # Create collector and generate prompt
        collector = RequirementsCollector()
        collector.set_instagram_data(instagram_data['profile_data'])
        collector.collected_data = {
            k: v for k, v in requirements.items() 
            if k in ['brand_name', 'tone_keywords', 'target_audience', 'primary_color', 'main_goal']
        }
        
        lovable_prompt = collector.generate_lovable_prompt()
        
        return jsonify({
            'project_id': project_id,
            'lovable_prompt': lovable_prompt
        })
    
    except Exception as e:
        print(f"Error generating prompt: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate/<project_id>', methods=['POST'])
def generate_website(project_id):
    """Generate website using Lovable automation"""
    try:
        # Get project data
        project = db.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get the Lovable prompt
        instagram_data = db.get_instagram_data(project_id)
        requirements = db.get_requirements(project_id)
        
        if not requirements:
            return jsonify({'error': 'Requirements not collected yet'}), 400
        
        # Create collector and generate prompt
        collector = RequirementsCollector()
        collector.set_instagram_data(instagram_data['profile_data'])
        collector.collected_data = {
            k: v for k, v in requirements.items() 
            if k in ['brand_name', 'tone_keywords', 'target_audience', 'primary_color', 'main_goal']
        }
        
        lovable_prompt = collector.generate_lovable_prompt()
        
        # Check for Lovable credentials
        email = os.getenv('LOVABLE_EMAIL')
        password = os.getenv('LOVABLE_PASSWORD')
        
        if not email or not password:
            return jsonify({
                'error': 'Lovable credentials not configured',
                'message': 'Please set LOVABLE_EMAIL and LOVABLE_PASSWORD environment variables'
            }), 500
        
        # Run Lovable automation
        service = LovableService(email, password)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            service.generate_from_requirements(
                project_id=project_id,
                prompt=lovable_prompt,
                headless=True  # Run headless in production
            )
        )
        
        # Update database with results
        if result['success']:
            db.update_project_status(
                project_id, 
                'website_generated',
                preview_url=result['preview_url']
            )
            db.save_generated_content(
                project_id,
                lovable_prompt,
                result['preview_url'],
                'completed'
            )
        else:
            db.save_generated_content(
                project_id,
                lovable_prompt,
                None,
                'failed',
                result.get('error')
            )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error generating website: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'RevampSite API'})


if __name__ == '__main__':
    # Ensure database is initialized
    db.init_database()
    
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    print("=" * 60)
    print("RevampSite Requirements Collector")
    print("=" * 60)
    print("Server running at: http://localhost:5001")
    print("API endpoints:")
    print("  POST /api/start - Start new project")
    print("  POST /api/chat - Send chat message")  
    print("  GET /api/project/<id> - Get project details")
    print("  GET /api/projects - Get all projects")
    print("  GET /health - Health check")
    print("=" * 60)
    
    app.run(debug=True, port=5001, host='0.0.0.0')