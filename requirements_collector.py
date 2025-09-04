#!/usr/bin/env python3
"""
Requirements collector for RevampSite
Collects user requirements through conversational interface
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class RequirementsCollector:
    """Manages requirements collection through conversation"""
    
    def __init__(self):
        """Initialize requirements collector"""
        self.questions = self._initialize_questions()
        self.current_step = 0
        self.collected_data = {}
        self.instagram_data = {}
    
    def _initialize_questions(self) -> List[Dict]:
        """Initialize the question flow"""
        return [
            {
                "id": "brand_name",
                "question": "What's your brand or business name? (If different from your Instagram handle)",
                "type": "text",
                "required": False,
                "default_from": "instagram_username",
                "validation": "text",
                "follow_up": "Great! I'll use '{answer}' as your brand name."
            },
            {
                "id": "tone_keywords", 
                "question": "Describe your brand personality in 3 keywords (e.g., 'modern, professional, friendly' or 'luxury, elegant, exclusive')",
                "type": "keywords",
                "required": True,
                "validation": "keywords",
                "examples": ["modern, professional, friendly", "luxury, elegant, exclusive", "fun, casual, vibrant"],
                "follow_up": "Perfect! Your brand tone is: {answer}"
            },
            {
                "id": "target_audience",
                "question": "Who is your target audience? (e.g., 'young professionals', 'local families', 'fitness enthusiasts')",
                "type": "text",
                "required": True,
                "validation": "text",
                "examples": ["young professionals", "local families", "fitness enthusiasts", "small business owners"],
                "follow_up": "Got it! Targeting: {answer}"
            },
            {
                "id": "primary_color",
                "question": "Do you have a preferred primary color for your website? (or type 'auto' to use colors from your Instagram)",
                "type": "color",
                "required": False,
                "default": "auto",
                "validation": "color",
                "follow_up": "Color preference noted: {answer}"
            },
            {
                "id": "main_goal",
                "question": "What's the main goal of your website? (e.g., 'showcase portfolio', 'get bookings', 'sell products', 'share information')",
                "type": "text",
                "required": True,
                "validation": "text",
                "examples": ["showcase portfolio", "get bookings", "sell products", "share information"],
                "follow_up": "Excellent! Main goal: {answer}"
            }
        ]
    
    def set_instagram_data(self, instagram_data: Dict):
        """Set Instagram data for context"""
        self.instagram_data = instagram_data
        
        # Pre-fill some defaults from Instagram
        if instagram_data:
            username = instagram_data.get('username', '')
            self.collected_data['instagram_username'] = username
            
            # Use Instagram name as default brand name
            full_name = instagram_data.get('full_name', '')
            if full_name:
                self.collected_data['brand_name_default'] = full_name
            
            # Extract language from bio if possible
            bio = instagram_data.get('biography', '')
            self.collected_data['bio_context'] = bio[:200] if bio else ''
    
    def get_next_question(self) -> Optional[Dict]:
        """Get the next question to ask"""
        if self.current_step < len(self.questions):
            question = self.questions[self.current_step].copy()
            
            # Add context from Instagram if available
            if question['id'] == 'brand_name' and self.collected_data.get('brand_name_default'):
                question['default'] = self.collected_data['brand_name_default']
                question['question'] += f" (Press Enter to use '{question['default']}')"
            
            return question
        return None
    
    def process_answer(self, answer: str, question_id: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process user answer
        Returns: (is_valid, response_message, next_question)
        """
        if question_id is None and self.current_step < len(self.questions):
            question_id = self.questions[self.current_step]['id']
        
        question = self.questions[self.current_step]
        
        # Handle empty answers for optional questions
        if not answer.strip() and not question.get('required', True):
            if question.get('default'):
                answer = question['default']
            elif question.get('default_from') and self.collected_data.get(question['default_from']):
                answer = self.collected_data[question['default_from']]
        
        # Validate answer
        is_valid, cleaned_answer = self._validate_answer(answer, question)
        
        if not is_valid:
            error_msg = self._get_validation_error(question)
            return False, error_msg, question
        
        # Store answer
        self.collected_data[question_id] = cleaned_answer
        
        # Generate follow-up message
        follow_up = question.get('follow_up', 'Got it!')
        if '{answer}' in follow_up:
            follow_up = follow_up.replace('{answer}', cleaned_answer)
        
        # Move to next question
        self.current_step += 1
        next_question = self.get_next_question()
        
        return True, follow_up, next_question
    
    def _validate_answer(self, answer: str, question: Dict) -> Tuple[bool, str]:
        """Validate answer based on question type"""
        answer = answer.strip()
        
        if question.get('required', True) and not answer:
            return False, ""
        
        validation_type = question.get('validation', 'text')
        
        if validation_type == 'text':
            # Basic text validation - just check it's not empty if required
            return (True, answer) if answer or not question.get('required', True) else (False, "")
        
        elif validation_type == 'keywords':
            # Clean up keywords - remove extra spaces, normalize
            keywords = [k.strip() for k in answer.replace(',', ' ').split() if k.strip()]
            if len(keywords) < 2:
                return False, ""
            # Return first 5 keywords max
            return True, ', '.join(keywords[:5])
        
        elif validation_type == 'color':
            # Validate color input
            if answer.lower() == 'auto':
                return True, 'auto'
            
            # Check for hex color
            hex_match = re.match(r'^#?([A-Fa-f0-9]{6})$', answer)
            if hex_match:
                return True, f"#{hex_match.group(1)}"
            
            # Check for common color names
            common_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 
                           'pink', 'black', 'white', 'gray', 'grey', 'brown']
            if answer.lower() in common_colors:
                return True, answer.lower()
            
            return False, ""
        
        return True, answer
    
    def _get_validation_error(self, question: Dict) -> str:
        """Get validation error message"""
        validation_type = question.get('validation', 'text')
        
        if validation_type == 'keywords':
            return "Please provide at least 2 keywords separated by commas or spaces."
        elif validation_type == 'color':
            return "Please provide a color (hex code like #FF5733, color name like 'blue', or 'auto')."
        else:
            return f"Please provide a valid answer for: {question['question']}"
    
    def is_complete(self) -> bool:
        """Check if all required questions have been answered"""
        required_fields = [q['id'] for q in self.questions if q.get('required', True)]
        return all(field in self.collected_data for field in required_fields)
    
    def get_summary(self) -> Dict:
        """Get summary of collected requirements"""
        summary = self.collected_data.copy()
        
        # Add metadata
        summary['collected_at'] = datetime.now().isoformat()
        summary['completion_status'] = 'complete' if self.is_complete() else 'partial'
        
        # Add Instagram context if available
        if self.instagram_data:
            summary['instagram_context'] = {
                'username': self.instagram_data.get('username'),
                'business_type': self.instagram_data.get('business_info', {}).get('business_type'),
                'followers': self.instagram_data.get('follower_count')
            }
        
        return summary
    
    def generate_lovable_prompt(self) -> str:
        """Generate a prompt for Lovable.dev based on collected requirements"""
        req = self.collected_data
        ig = self.instagram_data
        
        # Build comprehensive prompt
        prompt_parts = []
        
        # Brand identity
        brand_name = req.get('brand_name', ig.get('full_name', ig.get('username', 'Business')))
        prompt_parts.append(f"Create a professional website for {brand_name}.")
        
        # Business context from Instagram
        if ig.get('biography'):
            prompt_parts.append(f"\nBusiness Description: {ig['biography'][:200]}")
        
        # Target audience and tone
        if req.get('target_audience'):
            prompt_parts.append(f"\nTarget Audience: {req['target_audience']}")
        
        if req.get('tone_keywords'):
            prompt_parts.append(f"Brand Personality: {req['tone_keywords']}")
        
        # Main goal
        if req.get('main_goal'):
            prompt_parts.append(f"Primary Goal: {req['main_goal']}")
        
        # Design specifications
        prompt_parts.append("\nDesign Requirements:")
        
        # Colors
        if req.get('primary_color') and req['primary_color'] != 'auto':
            prompt_parts.append(f"- Primary Color: {req['primary_color']}")
        elif ig.get('brand_colors'):
            colors = ig['brand_colors'][:3]
            color_strs = [f"rgb({c['r']}, {c['g']}, {c['b']})" for c in colors]
            prompt_parts.append(f"- Brand Colors: {', '.join(color_strs)}")
        
        # Style based on tone keywords
        tone = req.get('tone_keywords', '').lower()
        if 'modern' in tone or 'minimal' in tone:
            prompt_parts.append("- Style: Clean, minimalist, modern")
        elif 'luxury' in tone or 'elegant' in tone:
            prompt_parts.append("- Style: Elegant, sophisticated, premium")
        elif 'fun' in tone or 'casual' in tone:
            prompt_parts.append("- Style: Friendly, approachable, vibrant")
        else:
            prompt_parts.append("- Style: Professional, trustworthy")
        
        # Sections to include
        prompt_parts.append("\nWebsite Sections:")
        prompt_parts.append("1. Hero section with compelling headline and call-to-action")
        prompt_parts.append("2. About section explaining the business")
        
        # Add sections based on goal
        goal = req.get('main_goal', '').lower()
        if 'portfolio' in goal or 'showcase' in goal:
            prompt_parts.append("3. Portfolio/Gallery showcasing work")
            prompt_parts.append("4. Services section with detailed offerings")
        elif 'booking' in goal or 'appointment' in goal:
            prompt_parts.append("3. Services with pricing")
            prompt_parts.append("4. Booking/Contact form for appointments")
        elif 'sell' in goal or 'product' in goal:
            prompt_parts.append("3. Products/Services showcase")
            prompt_parts.append("4. Features and benefits section")
        else:
            prompt_parts.append("3. Services or products section")
            prompt_parts.append("4. Blog or resources section")
        
        prompt_parts.append("5. Contact section with form and social links")
        prompt_parts.append("6. Footer with copyright and links")
        
        # Technical requirements
        prompt_parts.append("\nTechnical Requirements:")
        prompt_parts.append("- Mobile responsive design")
        prompt_parts.append("- SEO optimized")
        prompt_parts.append("- Fast loading")
        prompt_parts.append("- Accessible")
        
        # Instagram integration hint
        if ig.get('posts'):
            prompt_parts.append(f"\nInclude imagery that matches their Instagram aesthetic (@{ig.get('username')})")
        
        return "\n".join(prompt_parts)


class ConversationManager:
    """Manages the conversation flow for requirements collection"""
    
    def __init__(self, project_id: str):
        """Initialize conversation manager"""
        self.project_id = project_id
        self.collector = RequirementsCollector()
        self.messages = []
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import hashlib
        import time
        timestamp = str(time.time())
        return hashlib.md5(f"{self.project_id}_{timestamp}".encode()).hexdigest()[:16]
    
    def start_conversation(self, instagram_data: Dict = None) -> Dict:
        """Start the conversation"""
        self.collector.set_instagram_data(instagram_data or {})
        
        # Add welcome message
        welcome = {
            "role": "assistant",
            "content": "Hi! I'll help you create a website from your Instagram profile. I just need to ask you a few quick questions to understand your brand better. This will take about 2 minutes.",
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(welcome)
        
        # Get first question
        first_question = self.collector.get_next_question()
        if first_question:
            question_msg = {
                "role": "assistant", 
                "content": first_question['question'],
                "question_id": first_question['id'],
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(question_msg)
        
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "current_question": first_question,
            "progress": f"1/{len(self.collector.questions)}"
        }
    
    def process_user_input(self, user_input: str) -> Dict:
        """Process user input and return response"""
        # Add user message
        user_msg = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(user_msg)
        
        # Process answer
        is_valid, response, next_question = self.collector.process_answer(user_input)
        
        # Add assistant response
        assistant_msg = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(assistant_msg)
        
        # If valid and there's a next question, add it
        if is_valid and next_question:
            question_msg = {
                "role": "assistant",
                "content": next_question['question'],
                "question_id": next_question['id'],
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(question_msg)
        elif is_valid and not next_question:
            # Conversation complete
            complete_msg = {
                "role": "assistant",
                "content": "Perfect! I have all the information I need. Now I'll generate your website. This will take about 2-3 minutes...",
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(complete_msg)
        
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "current_question": next_question,
            "is_complete": self.collector.is_complete(),
            "progress": f"{self.collector.current_step}/{len(self.collector.questions)}",
            "requirements": self.collector.get_summary() if self.collector.is_complete() else None
        }
    
    def get_conversation_state(self) -> Dict:
        """Get current conversation state"""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "current_question": self.collector.get_next_question(),
            "is_complete": self.collector.is_complete(),
            "progress": f"{self.collector.current_step}/{len(self.collector.questions)}",
            "requirements": self.collector.get_summary()
        }