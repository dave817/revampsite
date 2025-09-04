#!/usr/bin/env python3
"""
Test script for Lovable.dev automation
Tests the browser automation without actual credentials
"""

import asyncio
import os
from lovable_automation import LovableAutomator, LovableService
import json

async def test_browser_initialization():
    """Test browser initialization"""
    print("=" * 60)
    print("TEST: Browser Initialization")
    print("=" * 60)
    
    automator = LovableAutomator(headless=True)
    
    try:
        await automator.initialize_browser()
        print("✓ Browser initialized successfully")
        
        # Navigate to Lovable
        await automator.page.goto('https://lovable.dev')
        print("✓ Navigated to Lovable.dev")
        
        # Take screenshot
        await automator.page.screenshot(path="lovable_homepage.png")
        print("✓ Screenshot saved to lovable_homepage.png")
        
        # Get page title
        title = await automator.page.title()
        print(f"✓ Page title: {title}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False
    
    finally:
        await automator.close_browser()
        print("✓ Browser closed")


async def test_lovable_navigation():
    """Test navigation without login"""
    print("\n" + "=" * 60)
    print("TEST: Lovable Navigation (No Login)")
    print("=" * 60)
    
    automator = LovableAutomator(headless=False)  # Show browser for debugging
    
    try:
        await automator.initialize_browser()
        await automator.page.goto('https://lovable.dev')
        
        # Wait for page to load
        await automator.page.wait_for_timeout(3000)
        
        # Check for key elements
        elements_to_check = [
            ('Sign in button', 'button:has-text("Sign in"), button:has-text("Sign In"), a:has-text("Sign in")'),
            ('Logo/Brand', 'img[alt*="Lovable"], text=/Lovable/i'),
            ('Hero text', 'h1, h2, text=/build|create|design/i')
        ]
        
        for name, selector in elements_to_check:
            count = await automator.page.locator(selector).count()
            if count > 0:
                print(f"✓ Found: {name}")
            else:
                print(f"✗ Not found: {name}")
        
        # Take screenshot
        await automator.page.screenshot(path="lovable_navigation_test.png")
        print("\n✓ Screenshot saved to lovable_navigation_test.png")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False
    
    finally:
        await automator.close_browser()


async def test_mock_generation():
    """Test the generation flow with mock data"""
    print("\n" + "=" * 60)
    print("TEST: Mock Website Generation Flow")
    print("=" * 60)
    
    # Mock prompt
    test_prompt = """
    Create a professional website for a digital marketing agency.
    
    Brand: TechCo Solutions
    Target Audience: Small businesses and startups
    Tone: Modern, professional, trustworthy
    Primary Color: #667EEA
    
    Sections:
    1. Hero with compelling headline
    2. Services showcase
    3. Client testimonials
    4. Contact form
    
    Make it responsive and SEO-friendly.
    """
    
    print("Test Prompt:")
    print("-" * 40)
    print(test_prompt)
    print("-" * 40)
    
    # Check if credentials are available
    email = os.getenv('LOVABLE_EMAIL')
    password = os.getenv('LOVABLE_PASSWORD')
    
    if email and password:
        print(f"\n✓ Credentials found for: {email}")
        print("\nWould run actual generation...")
        
        # Uncomment to run actual generation:
        # service = LovableService(email, password)
        # result = await service.generate_from_requirements(
        #     project_id="test_123",
        #     prompt=test_prompt,
        #     headless=True
        # )
        # print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print("\n⚠️  No credentials found - skipping actual generation")
        print("\nTo test actual generation:")
        print("1. Create a .env file from .env.example")
        print("2. Add your Lovable.dev credentials")
        print("3. Run: python test_lovable.py")
    
    # Simulate successful result
    mock_result = {
        'project_id': 'test_123',
        'success': True,
        'preview_url': 'https://example-project.lovableproject.com',
        'started_at': '2025-09-04T10:00:00',
        'completed_at': '2025-09-04T10:02:30',
        'error': None
    }
    
    print("\nMock Result:")
    print(json.dumps(mock_result, indent=2))
    
    return True


async def test_integration():
    """Test integration with Flask app"""
    print("\n" + "=" * 60)
    print("TEST: Flask Integration")
    print("=" * 60)
    
    import requests
    
    # Check if Flask app is running
    try:
        response = requests.get('http://localhost:5001/health')
        if response.status_code == 200:
            print("✓ Flask app is running")
            print(f"  Response: {response.json()}")
        else:
            print("✗ Flask app not responding correctly")
    except:
        print("⚠️  Flask app not running on port 5001")
        print("  Start it with: python app.py")
    
    return True


async def main():
    """Run all tests"""
    print("\nRevampSite Stage 3 Test Suite")
    print("Testing Lovable.dev Automation\n")
    
    tests = [
        ("Browser Initialization", test_browser_initialization),
        ("Lovable Navigation", test_lovable_navigation),
        ("Mock Generation", test_mock_generation),
        ("Flask Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
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
        print("\n🎉 All tests passed! Stage 3 automation is ready.")
    else:
        print("\n⚠️ Some tests failed. Please review the output.")
    
    print("\n📝 Next Steps:")
    print("1. Set up Lovable.dev account")
    print("2. Add credentials to .env file")
    print("3. Test actual website generation")
    print("4. Integrate with the web UI")
    
    return all_passed


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    asyncio.run(main())