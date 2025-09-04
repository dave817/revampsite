#!/usr/bin/env python3
"""
Lovable.dev Automation for RevampSite
Automates website generation using Playwright browser automation
"""

import asyncio
import os
import json
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LovableAutomator:
    """Automates Lovable.dev website generation"""
    
    def __init__(self, email: str = None, password: str = None, headless: bool = False):
        """
        Initialize Lovable automator
        
        Args:
            email: Lovable account email
            password: Lovable account password
            headless: Run browser in headless mode
        """
        self.email = email or os.getenv('LOVABLE_EMAIL', '')
        self.password = password or os.getenv('LOVABLE_PASSWORD', '')
        self.headless = headless
        self.browser = None
        self.page = None
        self.context = None
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        
        # Launch browser with specific settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Create context with viewport and user agent
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Create page
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
        
    async def close_browser(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")
    
    async def login_to_lovable(self) -> bool:
        """
        Login to Lovable.dev
        
        Returns:
            bool: True if login successful
        """
        try:
            logger.info("Navigating to Lovable.dev...")
            await self.page.goto('https://lovable.dev', wait_until='networkidle')
            
            # Wait a bit for page to fully load
            await self.page.wait_for_timeout(2000)
            
            # Check if already logged in
            if await self.page.locator('button:has-text("New Project")').count() > 0:
                logger.info("Already logged in")
                return True
            
            # Look for sign in button
            sign_in_button = self.page.locator('button:has-text("Sign in"), button:has-text("Sign In"), button:has-text("Login"), a:has-text("Sign in")')
            
            if await sign_in_button.count() > 0:
                logger.info("Found sign in button, clicking...")
                await sign_in_button.first.click()
                await self.page.wait_for_timeout(2000)
            
            # Check for email input
            email_input = self.page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]')
            if await email_input.count() > 0:
                logger.info("Entering email...")
                await email_input.fill(self.email)
                
                # Look for password input
                password_input = self.page.locator('input[type="password"], input[name="password"]')
                if await password_input.count() > 0:
                    logger.info("Entering password...")
                    await password_input.fill(self.password)
                    
                    # Submit login
                    submit_button = self.page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login")')
                    if await submit_button.count() > 0:
                        logger.info("Submitting login...")
                        await submit_button.click()
                        
                        # Wait for navigation
                        await self.page.wait_for_timeout(5000)
                        
                        # Check if login successful
                        if await self.page.locator('button:has-text("New Project")').count() > 0:
                            logger.info("Login successful!")
                            return True
            
            # Alternative: OAuth login (Google, GitHub, etc.)
            logger.warning("Standard login not found, may need OAuth")
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    async def create_new_project(self, prompt: str) -> Optional[str]:
        """
        Create a new project with the given prompt
        
        Args:
            prompt: The website generation prompt
            
        Returns:
            str: Preview URL if successful, None otherwise
        """
        try:
            logger.info("Creating new project...")
            
            # Look for New Project button
            new_project_btn = self.page.locator('button:has-text("New Project"), button:has-text("New"), button:has-text("Create")')
            
            if await new_project_btn.count() > 0:
                await new_project_btn.first.click()
                await self.page.wait_for_timeout(2000)
            else:
                # Try to navigate directly to new project
                await self.page.goto('https://lovable.dev/new', wait_until='networkidle')
                await self.page.wait_for_timeout(2000)
            
            # Find the prompt input area
            prompt_input = self.page.locator('textarea, [contenteditable="true"], input[type="text"][placeholder*="describe" i]')
            
            if await prompt_input.count() > 0:
                logger.info("Entering prompt...")
                await prompt_input.first.fill(prompt)
                await self.page.wait_for_timeout(1000)
                
                # Find and click generate/submit button
                generate_btn = self.page.locator('button:has-text("Generate"), button:has-text("Create"), button:has-text("Build"), button[type="submit"]')
                
                if await generate_btn.count() > 0:
                    logger.info("Submitting prompt...")
                    await generate_btn.first.click()
                    
                    # Wait for generation to start
                    await self.page.wait_for_timeout(3000)
                    
                    # Wait for preview URL to appear (max 3 minutes)
                    logger.info("Waiting for website generation...")
                    preview_url = await self.wait_for_preview_url(timeout=180000)
                    
                    if preview_url:
                        logger.info(f"Preview URL generated: {preview_url}")
                        return preview_url
                    else:
                        logger.warning("Timeout waiting for preview URL")
                        return None
            else:
                logger.error("Could not find prompt input area")
                return None
                
        except Exception as e:
            logger.error(f"Project creation failed: {str(e)}")
            return None
    
    async def wait_for_preview_url(self, timeout: int = 180000) -> Optional[str]:
        """
        Wait for preview URL to appear
        
        Args:
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            str: Preview URL if found
        """
        start_time = time.time()
        max_time = start_time + (timeout / 1000)
        
        while time.time() < max_time:
            try:
                # Check for preview URL in various possible locations
                
                # Method 1: Look for iframe with preview
                iframe = self.page.locator('iframe[src*="lovableproject"], iframe[src*="vercel"], iframe[src*="netlify"]')
                if await iframe.count() > 0:
                    src = await iframe.first.get_attribute('src')
                    if src and src.startswith('http'):
                        return src
                
                # Method 2: Look for preview link
                preview_link = self.page.locator('a[href*="lovableproject"], a[href*="vercel"], a[href*="netlify"], a:has-text("Preview"), a:has-text("View")')
                if await preview_link.count() > 0:
                    href = await preview_link.first.get_attribute('href')
                    if href and href.startswith('http'):
                        return href
                
                # Method 3: Look for URL in text
                url_text = self.page.locator('text=/https:\\/\\/[\\w\\-]+\\.(lovableproject|vercel|netlify)\\.\\w+/')
                if await url_text.count() > 0:
                    text = await url_text.first.text_content()
                    # Extract URL from text
                    import re
                    url_match = re.search(r'https://[\w\-]+\.(lovableproject|vercel|netlify)\.\w+', text)
                    if url_match:
                        return url_match.group(0)
                
                # Method 4: Check current URL for project ID
                current_url = self.page.url
                if 'project' in current_url or 'preview' in current_url:
                    # Extract project ID and construct preview URL
                    project_match = re.search(r'project/([a-zA-Z0-9\-]+)', current_url)
                    if project_match:
                        project_id = project_match.group(1)
                        # Common preview URL patterns
                        possible_urls = [
                            f"https://{project_id}.lovableproject.com",
                            f"https://{project_id}.vercel.app",
                            f"https://lovable-{project_id}.netlify.app"
                        ]
                        # Return the first one (actual pattern depends on Lovable's setup)
                        return possible_urls[0]
                
                await self.page.wait_for_timeout(2000)
                
            except Exception as e:
                logger.debug(f"Error while waiting for preview: {str(e)}")
                await self.page.wait_for_timeout(2000)
        
        return None
    
    async def generate_website(self, prompt: str, retry_count: int = 3) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Main method to generate website from prompt
        
        Args:
            prompt: Website generation prompt
            retry_count: Number of retries on failure
            
        Returns:
            Tuple of (success, preview_url, error_message)
        """
        attempt = 0
        
        while attempt < retry_count:
            try:
                attempt += 1
                logger.info(f"Attempt {attempt}/{retry_count}")
                
                # Initialize browser if not already done
                if not self.browser:
                    await self.initialize_browser()
                
                # Login to Lovable
                if not self.email or not self.password:
                    return False, None, "Lovable credentials not provided"
                
                login_success = await self.login_to_lovable()
                if not login_success:
                    if attempt < retry_count:
                        logger.warning(f"Login failed, retrying...")
                        await self.page.wait_for_timeout(5000)
                        continue
                    return False, None, "Failed to login to Lovable"
                
                # Create project with prompt
                preview_url = await self.create_new_project(prompt)
                
                if preview_url:
                    return True, preview_url, None
                elif attempt < retry_count:
                    logger.warning(f"Generation failed, retrying...")
                    await self.page.wait_for_timeout(5000)
                else:
                    return False, None, "Failed to generate website preview"
                    
            except Exception as e:
                error_msg = f"Error during generation: {str(e)}"
                logger.error(error_msg)
                
                if attempt < retry_count:
                    await self.page.wait_for_timeout(5000)
                else:
                    return False, None, error_msg
        
        return False, None, "Maximum retry attempts reached"
    
    async def take_screenshot(self, filename: str = "lovable_screenshot.png"):
        """Take screenshot of current page"""
        if self.page:
            await self.page.screenshot(path=filename)
            logger.info(f"Screenshot saved to {filename}")


class LovableService:
    """Service layer for Lovable automation"""
    
    def __init__(self, email: str = None, password: str = None):
        """Initialize Lovable service"""
        self.email = email or os.getenv('LOVABLE_EMAIL', '')
        self.password = password or os.getenv('LOVABLE_PASSWORD', '')
    
    async def generate_from_requirements(self, project_id: str, prompt: str, 
                                        headless: bool = False) -> Dict:
        """
        Generate website from requirements
        
        Args:
            project_id: Project ID for tracking
            prompt: Lovable generation prompt
            headless: Run browser in headless mode
            
        Returns:
            Dict with generation results
        """
        automator = LovableAutomator(
            email=self.email,
            password=self.password,
            headless=headless
        )
        
        result = {
            'project_id': project_id,
            'started_at': datetime.now().isoformat(),
            'success': False,
            'preview_url': None,
            'error': None
        }
        
        try:
            # Generate website
            success, preview_url, error = await automator.generate_website(prompt)
            
            result['success'] = success
            result['preview_url'] = preview_url
            result['error'] = error
            result['completed_at'] = datetime.now().isoformat()
            
            # Take screenshot if successful
            if success and not headless:
                await automator.take_screenshot(f"preview_{project_id}.png")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Service error: {str(e)}")
        
        finally:
            # Clean up
            await automator.close_browser()
        
        return result


# Testing function
async def test_lovable_automation():
    """Test Lovable automation with a sample prompt"""
    
    print("=" * 60)
    print("LOVABLE AUTOMATION TEST")
    print("=" * 60)
    
    # Check for credentials
    email = os.getenv('LOVABLE_EMAIL')
    password = os.getenv('LOVABLE_PASSWORD')
    
    if not email or not password:
        print("\n⚠️  Lovable credentials not found!")
        print("Please set environment variables:")
        print("  export LOVABLE_EMAIL='your-email@example.com'")
        print("  export LOVABLE_PASSWORD='your-password'")
        return False
    
    # Sample prompt
    test_prompt = """
    Create a modern portfolio website for a photographer.
    
    Design Requirements:
    - Dark theme with elegant typography
    - Hero section with stunning photography
    - Gallery grid layout
    - About section
    - Contact form
    - Mobile responsive
    
    Style: Minimal, elegant, professional
    Primary Color: #1a1a1a
    """
    
    print(f"\nUsing email: {email}")
    print("\nTest Prompt:")
    print("-" * 40)
    print(test_prompt)
    print("-" * 40)
    
    # Run automation
    service = LovableService(email, password)
    
    print("\nStarting automation (this may take 2-3 minutes)...")
    result = await service.generate_from_requirements(
        project_id="test_" + str(int(time.time())),
        prompt=test_prompt,
        headless=False  # Set to True for headless mode
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result['success']:
        print(f"✅ SUCCESS!")
        print(f"Preview URL: {result['preview_url']}")
        print(f"Time taken: Started at {result['started_at']}")
        print(f"           Completed at {result['completed_at']}")
    else:
        print(f"❌ FAILED!")
        print(f"Error: {result['error']}")
    
    return result['success']


if __name__ == "__main__":
    # Run test
    asyncio.run(test_lovable_automation())