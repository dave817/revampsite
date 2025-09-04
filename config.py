"""
Configuration settings for RevampSite
"""

import os
from typing import List, Optional

class Config:
    """Configuration class for RevampSite"""
    
    # Environment
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"
    
    # Instagram Scraper Settings
    INSTAGRAM_APP_ID = "936619743392459"
    SCRAPER_DELAY_MIN = 2  # seconds
    SCRAPER_DELAY_MAX = 5  # seconds
    MAX_POSTS_TO_ANALYZE = 12
    MAX_COLORS_TO_EXTRACT = 5
    
    # Proxy Settings (Optional)
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_LIST: List[str] = [
        # Add your proxy URLs here if needed
        # Format: "http://username:password@proxy-host:port"
    ]
    
    # Rate Limiting
    REQUESTS_PER_HOUR = 20
    CACHE_TTL = 86400  # 24 hours in seconds
    
    # API Keys (to be added)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
    
    # Lovable Settings
    LOVABLE_EMAIL = os.getenv("LOVABLE_EMAIL", "")
    LOVABLE_PASSWORD = os.getenv("LOVABLE_PASSWORD", "")
    
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "revampsite.db")
    
    # Output Settings
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")
    
    @classmethod
    def get_proxy(cls) -> Optional[str]:
        """Get a random proxy from the list"""
        if cls.USE_PROXY and cls.PROXY_LIST:
            import random
            return random.choice(cls.PROXY_LIST)
        return None
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        import os
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)