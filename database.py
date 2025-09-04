#!/usr/bin/env python3
"""
Database management for RevampSite
Handles storage of scraped data and user requirements
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class Database:
    """SQLite database manager for RevampSite"""
    
    def __init__(self, db_path: str = "revampsite.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Projects table - main table for each website project
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                instagram_username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                preview_url TEXT,
                final_url TEXT,
                payment_status TEXT DEFAULT 'unpaid',
                payment_id TEXT
            )
        ''')
        
        # Instagram data table - stores scraped Instagram data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                profile_data TEXT NOT NULL,
                brand_colors TEXT,
                business_info TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        # Requirements table - stores user requirements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                brand_name TEXT,
                primary_color TEXT,
                tone_keywords TEXT,
                target_audience TEXT,
                reference_sites TEXT,
                language TEXT DEFAULT 'en',
                additional_notes TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        # Chat sessions table - stores conversation history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                messages TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        # Generated content table - stores Lovable prompts and results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                lovable_prompt TEXT NOT NULL,
                preview_url TEXT,
                generation_status TEXT DEFAULT 'pending',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_project(self, instagram_username: str) -> str:
        """Create a new project"""
        import hashlib
        import time
        
        # Generate unique project ID
        timestamp = str(time.time())
        project_id = hashlib.md5(f"{instagram_username}_{timestamp}".encode()).hexdigest()[:12]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (project_id, instagram_username)
            VALUES (?, ?)
        ''', (project_id, instagram_username))
        
        conn.commit()
        conn.close()
        
        return project_id
    
    def save_instagram_data(self, project_id: str, profile_data: Dict, 
                           brand_colors: List, business_info: Dict):
        """Save Instagram scraped data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO instagram_data (project_id, profile_data, brand_colors, business_info)
            VALUES (?, ?, ?, ?)
        ''', (
            project_id,
            json.dumps(profile_data),
            json.dumps(brand_colors),
            json.dumps(business_info)
        ))
        
        conn.commit()
        conn.close()
    
    def save_requirements(self, project_id: str, requirements: Dict):
        """Save user requirements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requirements (
                project_id, brand_name, primary_color, tone_keywords,
                target_audience, reference_sites, language, additional_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id,
            requirements.get('brand_name'),
            requirements.get('primary_color'),
            requirements.get('tone_keywords'),
            requirements.get('target_audience'),
            requirements.get('reference_sites'),
            requirements.get('language', 'en'),
            requirements.get('additional_notes')
        ))
        
        conn.commit()
        conn.close()
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM projects WHERE project_id = ?
        ''', (project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_instagram_data(self, project_id: str) -> Optional[Dict]:
        """Get Instagram data for a project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM instagram_data WHERE project_id = ?
            ORDER BY scraped_at DESC LIMIT 1
        ''', (project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            data['profile_data'] = json.loads(data['profile_data'])
            data['brand_colors'] = json.loads(data['brand_colors']) if data['brand_colors'] else []
            data['business_info'] = json.loads(data['business_info']) if data['business_info'] else {}
            return data
        return None
    
    def get_requirements(self, project_id: str) -> Optional[Dict]:
        """Get requirements for a project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM requirements WHERE project_id = ?
            ORDER BY collected_at DESC LIMIT 1
        ''', (project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_project_status(self, project_id: str, status: str, **kwargs):
        """Update project status and optional fields"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        values = [status]
        
        for key, value in kwargs.items():
            if key in ['preview_url', 'final_url', 'payment_status', 'payment_id']:
                updates.append(f'{key} = ?')
                values.append(value)
        
        values.append(project_id)
        
        cursor.execute(f'''
            UPDATE projects 
            SET {', '.join(updates)}
            WHERE project_id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def save_chat_session(self, project_id: str, session_id: str, messages: List[Dict]):
        """Save chat session messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_sessions (project_id, session_id, messages)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                messages = ?,
                ended_at = CURRENT_TIMESTAMP
        ''', (project_id, session_id, json.dumps(messages), json.dumps(messages)))
        
        conn.commit()
        conn.close()
    
    def save_generated_content(self, project_id: str, lovable_prompt: str, 
                              preview_url: str = None, status: str = 'pending',
                              error_message: str = None):
        """Save generated content information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generated_content 
            (project_id, lovable_prompt, preview_url, generation_status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, lovable_prompt, preview_url, status, error_message))
        
        conn.commit()
        conn.close()
    
    def get_all_projects(self, limit: int = 50) -> List[Dict]:
        """Get all projects"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM projects 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]