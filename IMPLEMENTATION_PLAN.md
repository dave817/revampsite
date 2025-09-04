# RevampSite Implementation Plan (AI-Only Development)

## Executive Summary
Zero-cost, AI-developed solution that transforms Instagram profiles into professional websites using Instagram scraping and Lovable.dev automation via Claude Computer Use.

## System Architecture

### Simplified AI-Driven Flow
```
┌─────────────────────────────────────────────────────┐
│           User Input (Web App/WhatsApp)             │
│                 Instagram @username                  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            Instagram Scraper (Python)                │
│        Extract profile, posts, colors, content       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         Requirements Collector (LLM-based)           │
│      3 quick questions via chat interface            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│    Claude Computer Use + Lovable.dev Automation      │
│         Generate website automatically               │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│          Delivery & Payment (Automated)              │
│        Send preview link + Stripe payment            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Manual Domain Deployment                │
│           (Final step after payment)                 │
└──────────────────────────────────────────────────────┘
```

### Tech Stack (Minimal Cost)
- **Instagram Scraping**: Python with httpx (no API costs)
- **Web Automation**: Claude Computer Use API + Docker
- **Website Builder**: Lovable.dev ($29/month unlimited)
- **LLM**: Claude API for chat and automation
- **Hosting**: Cheap VPS ($5-10/month) or free tier
- **Queue**: Python asyncio (built-in, free)
- **Database**: SQLite (free, simple)

## Development Stages (AI-Built, No Human Developers)

## Stage 1: Instagram Scraper Setup
**Goal**: Build scraper to extract Instagram data without API
**Success Criteria**: 
- Extract profile info, posts, images ✓
- Avoid detection/blocking ✓
- Extract brand colors from images ✓
**Implementation**: Claude Code builds the entire scraper
**Status**: ✅ COMPLETE

### AI Tasks:
```python
# Claude Code will build:
1. Instagram scraper using httpx
2. Residential proxy rotation
3. User agent randomization  
4. Color extraction from images
5. Content categorization from captions
```

## Stage 2: Requirements Collection System
**Goal**: LLM-powered chat to collect user requirements
**Success Criteria**:
- Collect brand name, colors, tone, audience ✓
- Natural conversation flow ✓
- Store requirements in structured format ✓
**Implementation**: Claude builds chat interface with LLM
**Status**: ✅ COMPLETE

### AI Tasks:
```python
# Claude Code will build:
1. Simple web form or WhatsApp handler
2. LLM prompt engineering for questions
3. Response parser and validator
4. Requirements storage in SQLite
```

## Stage 3: Lovable.dev Automation
**Goal**: Automate website generation using Claude Computer Use
**Success Criteria**:
- Control Lovable.dev via browser automation
- Generate website from requirements
- Extract preview URL
**Implementation**: Claude Computer Use API
**Status**: Not Started

### AI Tasks:
```python
# Claude Code will build:
1. Docker container setup for browser
2. Claude Computer Use integration
3. Lovable prompt generator from requirements
4. Preview URL extractor
5. Error handling and retries
```

## Stage 4: Delivery & Payment System
**Goal**: Send preview and payment links automatically
**Success Criteria**:
- Send preview URL to user
- Generate Stripe payment link
- Track payment status
**Implementation**: Claude builds notification system
**Status**: Not Started

### AI Tasks:
```python
# Claude Code will build:
1. Email/WhatsApp sender for preview
2. Stripe payment link generator
3. Payment webhook handler
4. Status tracking in database
```

## Stage 5: Manual Domain Deployment
**Goal**: Deploy to customer domain after payment
**Success Criteria**:
- Export from Lovable
- Deploy to customer domain
- SSL setup
**Implementation**: Semi-manual process
**Status**: Not Started

### Process:
1. Download site from Lovable
2. Upload to hosting (Netlify/Vercel)
3. Connect custom domain
4. Verify SSL certificate

## Implementation Code Examples

### Stage 1: Instagram Scraper
```python
import httpx
import json
import random
import time
from colorthief import ColorThief

class InstagramScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        self.client = httpx.Client(
            headers={
                "x-ig-app-id": "936619743392459",
                "User-Agent": random.choice(self.user_agents)
            },
            timeout=30.0
        )
    
    def get_profile(self, username):
        time.sleep(random.uniform(2, 5))  # Avoid detection
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        response = self.client.get(url)
        return response.json()
    
    def extract_colors(self, image_urls):
        # Extract dominant colors from profile images
        colors = []
        for url in image_urls[:5]:
            # Download and analyze image
            color_thief = ColorThief(url)
            palette = color_thief.get_palette(color_count=3)
            colors.extend(palette)
        return colors
```

### Stage 2: Requirements Collector
```python
class RequirementsCollector:
    def __init__(self, claude_api_key):
        self.claude = Anthropic(api_key=claude_api_key)
        
    async def collect_via_chat(self, instagram_data):
        questions = [
            "What's your brand name?",
            "Describe your brand in 3 keywords (e.g., minimal, trustworthy)",
            "Who is your target audience?"
        ]
        
        requirements = {
            "instagram_handle": instagram_data["username"],
            "bio": instagram_data["biography"],
            "extracted_colors": instagram_data["colors"]
        }
        
        for question in questions:
            # Send to user via chosen channel
            answer = await self.get_user_response(question)
            requirements[question.lower().replace(" ", "_")] = answer
            
        return requirements
```

### Stage 3: Lovable Automation
```python
from anthropic import Anthropic

class LovableAutomator:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        
    async def generate_website(self, requirements):
        # Build comprehensive prompt
        lovable_prompt = f"""
        Create a professional website for {requirements['brand_name']}.
        
        Business Info:
        - Bio: {requirements['bio']}
        - Target Audience: {requirements['target_audience']}
        - Brand Keywords: {requirements['tone_keywords']}
        
        Design Requirements:
        - Primary Colors: {requirements['extracted_colors']}
        - Style: Modern, responsive, mobile-first
        
        Sections to include:
        1. Hero section with compelling headline
        2. About section using bio
        3. Services/Products gallery
        4. Contact form with social links
        5. Footer with copyright
        
        Make it look professional and trustworthy.
        """
        
        # Use Claude Computer Use to control Lovable
        response = await self.client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=[{
                "type": "computer_20241022",
                "display_width_px": 1920,
                "display_height_px": 1080
            }],
            messages=[{
                "role": "user",
                "content": f"""
                1. Navigate to lovable.dev
                2. Click "New Project"
                3. Enter this prompt: {lovable_prompt}
                4. Wait for generation to complete
                5. Copy the preview URL
                6. Return the URL
                """
            }]
        )
        
        return response.content[0].text  # Extract URL from response
```

## MVP Definition (AI-Built in 2 Weeks)

### Week 1: Core Functionality
1. **Day 1-2**: Instagram scraper with Claude Code
2. **Day 3-4**: Requirements collector
3. **Day 5-7**: Lovable automation setup

### Week 2: Integration & Testing
1. **Day 8-9**: Connect all components
2. **Day 10-11**: Payment integration
3. **Day 12-14**: Testing and refinement

## Cost Breakdown (Ultra-Low)

### One-Time Costs
- Claude Code development: $0 (AI-built)
- Initial setup time: ~20 hours

### Monthly Operating Costs
- Lovable.dev: $29/month (unlimited sites)
- VPS hosting: $5/month (DigitalOcean droplet)
- Proxies: $10/month (residential pool)
- Claude API: ~$20/month (for automation)
- **Total: $64/month**

### Per-Site Costs
- Instagram scraping: ~$0.01 (proxy usage)
- Claude Computer Use: ~$0.30
- **Total per site: < $0.50**

### Revenue Model
- Price per website: $99
- Profit per website: ~$98.50
- Break-even: 1 website/month
- Target: 50 websites/month = $4,900 profit

## Technical Implementation Notes

### Instagram Scraping Safety
```python
# Implement these safety measures:
1. Random delays (2-5 seconds between requests)
2. Rotate user agents
3. Use residential proxies
4. Limit to 20 requests per hour per IP
5. Cache results for 24 hours
```

### Lovable Automation Tips
```python
# Best practices:
1. Run in Docker container for isolation
2. Use VNC to monitor automation
3. Implement retry logic (max 3 attempts)
4. Save screenshots for debugging
5. Queue requests to avoid overload
```

### Simple Queue System
```python
import asyncio
from collections import deque

class JobQueue:
    def __init__(self):
        self.queue = deque()
        self.processing = False
        
    async def add_job(self, job):
        self.queue.append(job)
        if not self.processing:
            await self.process_queue()
    
    async def process_queue(self):
        self.processing = True
        while self.queue:
            job = self.queue.popleft()
            try:
                await self.process_job(job)
            except Exception as e:
                print(f"Job failed: {e}")
        self.processing = False
```

## Risk Mitigation

### Technical Risks
1. **Instagram blocks scraping**
   - Solution: Multiple proxy providers, fallback to manual input
   
2. **Lovable.dev changes interface**
   - Solution: Use Playwright as backup, maintain multiple automation scripts
   
3. **Claude Computer Use limits**
   - Solution: Batch processing, caching, fallback to Playwright

### Business Risks
1. **Low initial adoption**
   - Solution: Free trials, money-back guarantee, local testimonials
   
2. **Competitor with API access**
   - Solution: Focus on speed and simplicity, not features

## Next Actions (AI-Driven Development)

### Day 1-2: Instagram Scraper
```bash
# Claude Code command:
"Build Instagram scraper using httpx that extracts profile, posts, and colors from images. Include proxy rotation and user agent randomization for safety."
```

### Day 3-4: Requirements Collector
```bash
# Claude Code command:
"Create a simple Flask/FastAPI app that collects user requirements via chat interface, stores in SQLite, and prepares data for Lovable automation."
```

### Day 5-7: Lovable Automation
```bash
# Claude Code command:
"Implement Claude Computer Use automation to control Lovable.dev - login, create project, enter prompt, extract preview URL."
```

### Day 8-9: Integration
```bash
# Claude Code command:
"Connect all components: Instagram scraper → requirements collector → Lovable automation → delivery system. Add error handling and retries."
```

### Day 10-11: Payment & Delivery
```bash
# Claude Code command:
"Add Stripe payment link generation and email/WhatsApp delivery of preview links. Include payment webhook handler."
```

### Day 12-14: Testing & Deployment
```bash
# Claude Code command:
"Create test suite, deploy to VPS, set up monitoring, and prepare for first real customer test."
```

## Quick Start Commands

### 1. Project Setup
```bash
mkdir revampsite
cd revampsite
python -m venv venv
source venv/bin/activate
pip install httpx anthropic flask stripe colorthief pillow
```

### 2. Environment Variables
```bash
export ANTHROPIC_API_KEY="your-key"
export STRIPE_API_KEY="your-key"
export LOVABLE_EMAIL="your-email"
export LOVABLE_PASSWORD="your-password"
```

### 3. Docker Setup (for Computer Use)
```bash
docker run -d \
  --name revampsite-browser \
  -p 5900:5900 \
  -e VNC_PASSWORD=secret \
  browserless/chrome
```

## Conclusion

RevampSite can be built entirely by AI (Claude Code) in 2 weeks with:
- **Zero human developers** - All code written by AI
- **Minimal costs** - $64/month operating costs
- **High margins** - $98.50 profit per $99 sale
- **Quick iteration** - Lovable handles the complex website generation
- **Proven approach** - Instagram scraping and browser automation are established patterns

The key innovation is using Claude Computer Use to control Lovable.dev, turning it into an API-less website generator. This eliminates the need for complex website generation code while maintaining professional output quality.

Following CLAUDE.md principles:
- Small, testable stages (2-3 days each)
- Working code at each step
- Pragmatic use of existing tools (Lovable)
- Simple architecture (scraper → automation → delivery)
- Clear success metrics (preview URL generated)