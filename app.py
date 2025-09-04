#!/usr/bin/env python3
"""
Flask API for RevampSite
Main application server handling requirements collection
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
from datetime import datetime

from instagram_scraper import InstagramScraper
from requirements_collector import ConversationManager, RequirementsCollector
from database import Database
from config import Config

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database()
scraper = InstagramScraper()

# Store active sessions in memory (in production, use Redis)
active_sessions = {}


@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(CHAT_INTERFACE_HTML)


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


# Simple HTML interface for testing
CHAT_INTERFACE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>RevampSite - Requirements Collector</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            text-align: right;
        }
        .message.assistant {
            text-align: left;
        }
        .message-bubble {
            display: inline-block;
            padding: 12px 18px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.assistant .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            border-color: #667eea;
        }
        button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .start-screen {
            padding: 40px;
            text-align: center;
        }
        .start-screen h2 {
            color: #333;
            margin-bottom: 20px;
        }
        .start-screen p {
            color: #666;
            margin-bottom: 30px;
        }
        .progress {
            padding: 10px 20px;
            background: #f0f0f0;
            text-align: center;
            font-size: 14px;
            color: #666;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RevampSite</h1>
            <p>Transform your Instagram into a stunning website</p>
        </div>
        
        <div id="startScreen" class="start-screen">
            <h2>Let's create your website!</h2>
            <p>Enter your Instagram username to begin</p>
            <div class="input-group">
                <input type="text" id="instagramUsername" placeholder="@yourusername" />
                <button onclick="startProject()">Start</button>
            </div>
        </div>
        
        <div id="chatScreen" style="display: none;">
            <div class="progress" id="progress">Step 1/5</div>
            <div class="chat-container" id="chatContainer"></div>
            <div class="input-container">
                <div class="input-group">
                    <input type="text" id="userInput" placeholder="Type your answer..." disabled />
                    <button id="sendButton" onclick="sendMessage()" disabled>Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let sessionId = null;
        let projectId = null;
        
        async function startProject() {
            const username = document.getElementById('instagramUsername').value.trim();
            if (!username) {
                alert('Please enter an Instagram username');
                return;
            }
            
            const button = event.target;
            button.disabled = true;
            button.innerHTML = 'Loading... <span class="loading"></span>';
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({instagram_username: username})
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to start project');
                }
                
                sessionId = data.session_id;
                projectId = data.project_id;
                
                // Switch to chat screen
                document.getElementById('startScreen').style.display = 'none';
                document.getElementById('chatScreen').style.display = 'block';
                
                // Display messages
                displayConversation(data.conversation);
                
                // Enable input
                document.getElementById('userInput').disabled = false;
                document.getElementById('sendButton').disabled = false;
                document.getElementById('userInput').focus();
                
            } catch (error) {
                alert('Error: ' + error.message);
                button.disabled = false;
                button.innerHTML = 'Start';
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message || !sessionId) return;
            
            input.disabled = true;
            document.getElementById('sendButton').disabled = true;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to send message');
                }
                
                // Clear input
                input.value = '';
                
                // Display updated conversation
                displayConversation(data);
                
                // Check if complete
                if (data.is_complete) {
                    input.placeholder = 'Requirements collected! Generating website...';
                    if (data.lovable_prompt) {
                        setTimeout(() => {
                            displayPrompt(data.lovable_prompt);
                        }, 2000);
                    }
                } else {
                    input.disabled = false;
                    document.getElementById('sendButton').disabled = false;
                    input.focus();
                }
                
            } catch (error) {
                alert('Error: ' + error.message);
                input.disabled = false;
                document.getElementById('sendButton').disabled = false;
            }
        }
        
        function displayConversation(data) {
            const container = document.getElementById('chatContainer');
            const progress = document.getElementById('progress');
            
            // Update progress
            if (data.progress) {
                progress.textContent = `Step ${data.progress}`;
            }
            
            // Clear and redisplay messages
            container.innerHTML = '';
            
            if (data.messages) {
                data.messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.role}`;
                    
                    const bubbleDiv = document.createElement('div');
                    bubbleDiv.className = 'message-bubble';
                    bubbleDiv.textContent = msg.content;
                    
                    messageDiv.appendChild(bubbleDiv);
                    container.appendChild(messageDiv);
                });
                
                // Scroll to bottom
                container.scrollTop = container.scrollHeight;
            }
        }
        
        function displayPrompt(prompt) {
            const container = document.getElementById('chatContainer');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.innerHTML = '<strong>Generated Website Prompt:</strong><br><br>' + 
                                 prompt.replace(/\n/g, '<br>');
            
            messageDiv.appendChild(bubbleDiv);
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        // Handle Enter key
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !this.disabled) {
                sendMessage();
            }
        });
        
        document.getElementById('instagramUsername').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                startProject();
            }
        });
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    # Ensure database is initialized
    db.init_database()
    
    print("=" * 60)
    print("RevampSite Requirements Collector")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("API endpoints:")
    print("  POST /api/start - Start new project")
    print("  POST /api/chat - Send chat message")  
    print("  GET /api/project/<id> - Get project details")
    print("=" * 60)
    
    app.run(debug=True, port=5000)