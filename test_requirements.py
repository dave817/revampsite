#!/usr/bin/env python3
"""
Test script for Requirements Collector
Tests the conversation flow and prompt generation
"""

import json
from requirements_collector import RequirementsCollector, ConversationManager
from instagram_scraper import InstagramScraper
from database import Database

def test_requirements_collector():
    """Test the requirements collector with sample data"""
    print("=" * 60)
    print("REQUIREMENTS COLLECTOR TEST")
    print("=" * 60)
    
    # Initialize components
    collector = RequirementsCollector()
    
    # Sample Instagram data
    sample_instagram_data = {
        "username": "testuser",
        "full_name": "Test Business",
        "biography": "We create amazing products for amazing people 🚀",
        "follower_count": 5000,
        "brand_colors": [
            {"r": 102, "g": 126, "b": 234},
            {"r": 118, "g": 75, "b": 162}
        ],
        "business_info": {
            "business_type": "tech",
            "tone": ["modern", "innovative"]
        }
    }
    
    collector.set_instagram_data(sample_instagram_data)
    
    # Simulate conversation
    print("\n📝 Testing Question Flow:\n")
    
    # Test answers
    test_answers = [
        "TechCo Solutions",  # brand name
        "modern, innovative, trustworthy",  # tone keywords
        "startup founders and small businesses",  # target audience
        "#667EEA",  # primary color
        "showcase our products and get leads"  # main goal
    ]
    
    answer_index = 0
    while not collector.is_complete() and answer_index < len(test_answers):
        question = collector.get_next_question()
        if question:
            print(f"Q: {question['question']}")
            answer = test_answers[answer_index]
            print(f"A: {answer}")
            
            is_valid, response, next_q = collector.process_answer(answer)
            print(f"Response: {response}\n")
            
            if is_valid:
                answer_index += 1
    
    # Get summary
    summary = collector.get_summary()
    print("\n📊 Collected Requirements:")
    print(json.dumps(summary, indent=2))
    
    # Generate Lovable prompt
    prompt = collector.generate_lovable_prompt()
    print("\n🎨 Generated Lovable Prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    return True

def test_conversation_manager():
    """Test the conversation manager"""
    print("\n" + "=" * 60)
    print("CONVERSATION MANAGER TEST")
    print("=" * 60)
    
    # Create test project
    manager = ConversationManager("test_project_123")
    
    # Sample Instagram data
    sample_instagram_data = {
        "username": "nike",
        "full_name": "Nike",
        "biography": "Just Do It 🏃‍♂️",
        "follower_count": 300000000,
        "brand_colors": [
            {"r": 0, "g": 0, "b": 0},
            {"r": 255, "g": 255, "b": 255}
        ],
        "business_info": {
            "business_type": "fashion",
            "tone": ["bold", "inspiring"]
        }
    }
    
    # Start conversation
    print("\n🚀 Starting Conversation:")
    result = manager.start_conversation(sample_instagram_data)
    print(f"Session ID: {result['session_id']}")
    print(f"Progress: {result['progress']}")
    
    # Simulate chat
    test_inputs = [
        "Nike Sports",
        "bold, inspiring, athletic",
        "athletes and fitness enthusiasts",
        "auto",
        "sell products and inspire athletes"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = manager.process_user_input(user_input)
        
        # Get last assistant message
        assistant_messages = [m for m in response['messages'] if m['role'] == 'assistant']
        if assistant_messages:
            print(f"Assistant: {assistant_messages[-1]['content']}")
        
        print(f"Progress: {response['progress']}")
        
        if response.get('is_complete'):
            print("\n✅ Conversation Complete!")
            print("\n📋 Final Requirements:")
            print(json.dumps(response['requirements'], indent=2))
            break
    
    return True

def test_database_integration():
    """Test database integration"""
    print("\n" + "=" * 60)
    print("DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize database
    db = Database("test_revampsite.db")
    
    # Create project
    project_id = db.create_project("testuser")
    print(f"\n✓ Created project: {project_id}")
    
    # Save Instagram data
    instagram_data = {
        "username": "testuser",
        "full_name": "Test User",
        "biography": "Test bio",
        "follower_count": 1000
    }
    
    brand_colors = [{"r": 100, "g": 150, "b": 200}]
    business_info = {"business_type": "general"}
    
    db.save_instagram_data(project_id, instagram_data, brand_colors, business_info)
    print("✓ Saved Instagram data")
    
    # Save requirements
    requirements = {
        "brand_name": "Test Brand",
        "tone_keywords": "modern, clean",
        "target_audience": "everyone",
        "primary_color": "#6495ED",
        "main_goal": "showcase products"
    }
    
    db.save_requirements(project_id, requirements)
    print("✓ Saved requirements")
    
    # Retrieve data
    project = db.get_project(project_id)
    ig_data = db.get_instagram_data(project_id)
    req_data = db.get_requirements(project_id)
    
    print(f"\n📁 Retrieved Project:")
    print(f"  ID: {project['project_id']}")
    print(f"  Username: {project['instagram_username']}")
    print(f"  Status: {project['status']}")
    
    if ig_data:
        print(f"\n📷 Instagram Data:")
        print(f"  Username: {ig_data['profile_data']['username']}")
        print(f"  Colors: {len(ig_data['brand_colors'])} found")
    
    if req_data:
        print(f"\n📝 Requirements:")
        print(f"  Brand: {req_data['brand_name']}")
        print(f"  Tone: {req_data['tone_keywords']}")
    
    # Clean up test database
    import os
    if os.path.exists("test_revampsite.db"):
        os.remove("test_revampsite.db")
        print("\n✓ Cleaned up test database")
    
    return True

def main():
    """Run all tests"""
    print("\nRevampSite Stage 2 Test Suite")
    print("Testing Requirements Collection System\n")
    
    tests = [
        ("Requirements Collector", test_requirements_collector),
        ("Conversation Manager", test_conversation_manager),
        ("Database Integration", test_database_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed! Stage 2 is ready.")
    else:
        print("\n⚠️ Some tests failed. Please review the output.")
    
    return all_passed

if __name__ == "__main__":
    main()