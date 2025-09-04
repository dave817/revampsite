#!/usr/bin/env python3
"""
Instagram Scraper for RevampSite
Extracts profile data, posts, and brand elements from Instagram profiles
"""

import httpx
import json
import random
import time
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
import hashlib
from PIL import Image
from io import BytesIO
import requests
from collections import Counter
from datetime import datetime

class InstagramScraper:
    """Scrapes Instagram profiles without using official API"""
    
    def __init__(self, use_proxy: bool = False):
        self.use_proxy = use_proxy
        self.session_id = self._generate_session_id()
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Initialize HTTP client
        self.client = self._create_client()
        
        # Cache for scraped data
        self.cache = {}
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = str(time.time())
        random_str = str(random.randint(1000000, 9999999))
        return hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()
    
    def _create_client(self) -> httpx.Client:
        """Create HTTP client with appropriate headers"""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "X-IG-App-ID": "936619743392459",  # Instagram web app ID
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.instagram.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
        
        client_config = {
            "headers": headers,
            "timeout": 30.0,
            "follow_redirects": True
        }
        
        if self.use_proxy:
            # Proxy configuration (to be implemented with actual proxy service)
            pass
            
        return httpx.Client(**client_config)
    
    def _add_delay(self):
        """Add random delay to avoid detection"""
        delay = random.uniform(2, 5)
        time.sleep(delay)
    
    def get_profile_data(self, username: str) -> Optional[Dict]:
        """
        Fetch Instagram profile data
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            Dictionary containing profile data or None if failed
        """
        # Check cache first
        cache_key = f"profile_{username}"
        if cache_key in self.cache:
            print(f"Using cached data for {username}")
            return self.cache[cache_key]
        
        print(f"Fetching profile data for @{username}...")
        self._add_delay()
        
        try:
            # Try the web profile info endpoint
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            # Update referer for this specific request
            self.client.headers.update({
                "Referer": f"https://www.instagram.com/{username}/",
                "X-Instagram-AJAX": "1"
            })
            
            response = self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and "user" in data["data"]:
                    user_data = data["data"]["user"]
                    
                    # Extract relevant information
                    profile_info = {
                        "username": user_data.get("username", username),
                        "full_name": user_data.get("full_name", ""),
                        "biography": user_data.get("biography", ""),
                        "profile_pic_url": user_data.get("profile_pic_url_hd", user_data.get("profile_pic_url", "")),
                        "follower_count": user_data.get("edge_followed_by", {}).get("count", 0),
                        "following_count": user_data.get("edge_follow", {}).get("count", 0),
                        "post_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                        "is_business": user_data.get("is_business_account", False),
                        "is_verified": user_data.get("is_verified", False),
                        "category": user_data.get("category_name", ""),
                        "external_url": user_data.get("external_url", ""),
                        "posts": self._extract_posts(user_data),
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = profile_info
                    
                    print(f"Successfully scraped profile for @{username}")
                    return profile_info
                    
            elif response.status_code == 404:
                print(f"Profile @{username} not found")
                return None
            else:
                print(f"Failed to fetch profile. Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching profile: {str(e)}")
            return None
    
    def _extract_posts(self, user_data: Dict) -> List[Dict]:
        """Extract posts from user data"""
        posts = []
        
        try:
            media_data = user_data.get("edge_owner_to_timeline_media", {})
            edges = media_data.get("edges", [])
            
            for edge in edges[:12]:  # Get up to 12 recent posts
                node = edge.get("node", {})
                
                post = {
                    "id": node.get("id", ""),
                    "shortcode": node.get("shortcode", ""),
                    "caption": self._extract_caption(node),
                    "image_url": node.get("display_url", ""),
                    "thumbnail_url": node.get("thumbnail_src", node.get("display_url", "")),
                    "is_video": node.get("is_video", False),
                    "likes": node.get("edge_liked_by", {}).get("count", 0),
                    "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                    "timestamp": node.get("taken_at_timestamp", 0),
                    "hashtags": self._extract_hashtags(self._extract_caption(node))
                }
                
                posts.append(post)
                
        except Exception as e:
            print(f"Error extracting posts: {str(e)}")
            
        return posts
    
    def _extract_caption(self, node: Dict) -> str:
        """Extract caption text from post node"""
        try:
            edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if edges:
                return edges[0].get("node", {}).get("text", "")
        except:
            pass
        return ""
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags
    
    def extract_brand_colors(self, profile_data: Dict) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors from profile images
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            List of RGB color tuples
        """
        print("Extracting brand colors from images...")
        colors = []
        
        # Get profile picture
        if profile_data.get("profile_pic_url"):
            profile_colors = self._get_image_colors(profile_data["profile_pic_url"])
            colors.extend(profile_colors[:2])  # Get top 2 colors from profile pic
        
        # Get colors from recent posts
        posts = profile_data.get("posts", [])
        for post in posts[:3]:  # Analyze first 3 posts
            if post.get("image_url"):
                post_colors = self._get_image_colors(post["image_url"])
                if post_colors:
                    colors.append(post_colors[0])  # Get dominant color from each
        
        # Remove duplicates and return top colors
        unique_colors = []
        for color in colors:
            if color and not any(self._colors_similar(color, c) for c in unique_colors):
                unique_colors.append(color)
        
        return unique_colors[:5]  # Return top 5 unique colors
    
    def _get_image_colors(self, image_url: str) -> List[Tuple[int, int, int]]:
        """Get dominant colors from an image URL"""
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for faster processing
            img.thumbnail((150, 150))
            
            # Get all pixels
            pixels = list(img.getdata())
            
            # Filter out white, black, and gray colors
            filtered_pixels = []
            for pixel in pixels:
                r, g, b = pixel
                # Skip if too close to white, black, or gray
                if not (
                    (r > 240 and g > 240 and b > 240) or  # Nearly white
                    (r < 30 and g < 30 and b < 30) or      # Nearly black
                    (abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20)  # Gray
                ):
                    filtered_pixels.append(pixel)
            
            if not filtered_pixels:
                filtered_pixels = pixels
            
            # Get most common colors
            color_counter = Counter(filtered_pixels)
            dominant_colors = [color for color, count in color_counter.most_common(5)]
            
            return dominant_colors
            
        except Exception as e:
            print(f"Error extracting colors from image: {str(e)}")
            return []
    
    def _colors_similar(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], threshold: int = 50) -> bool:
        """Check if two colors are similar"""
        if not color1 or not color2:
            return False
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2) < threshold
    
    def extract_business_info(self, profile_data: Dict) -> Dict:
        """
        Extract business-related information from profile
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Dictionary with business information
        """
        print("Extracting business information...")
        
        business_info = {
            "business_type": self._detect_business_type(profile_data),
            "services": self._extract_services(profile_data),
            "contact_info": self._extract_contact_info(profile_data),
            "location": self._extract_location(profile_data),
            "keywords": self._extract_keywords(profile_data),
            "tone": self._detect_brand_tone(profile_data)
        }
        
        return business_info
    
    def _detect_business_type(self, profile_data: Dict) -> str:
        """Detect the type of business from profile and posts"""
        category = profile_data.get("category", "")
        if category is None:
            category = ""
        category = category.lower()
        bio = profile_data.get("biography", "")
        if bio is None:
            bio = ""
        bio = bio.lower()
        
        # Check posts for keywords
        all_text = bio
        for post in profile_data.get("posts", []):
            caption = post.get("caption", "")
            if caption is None:
                caption = ""
            all_text += " " + caption.lower()
        
        # Business type patterns
        patterns = {
            "restaurant": ["food", "menu", "restaurant", "cafe", "dining", "chef", "cuisine"],
            "fashion": ["fashion", "style", "clothing", "boutique", "wear", "outfit", "collection"],
            "beauty": ["beauty", "salon", "makeup", "hair", "skincare", "spa", "cosmetics"],
            "fitness": ["fitness", "gym", "workout", "training", "yoga", "health", "wellness"],
            "photography": ["photography", "photographer", "photo", "shoot", "camera", "portrait"],
            "real_estate": ["real estate", "property", "realtor", "homes", "listing", "rent"],
            "consulting": ["consulting", "consultant", "advisor", "strategy", "business", "coach"],
            "art": ["art", "artist", "gallery", "painting", "design", "creative", "illustration"],
            "education": ["education", "course", "training", "learn", "workshop", "tutorial"],
            "tech": ["tech", "software", "app", "digital", "development", "coding", "startup"]
        }
        
        scores = {}
        for biz_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                scores[biz_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return category if category else "general"
    
    def _extract_services(self, profile_data: Dict) -> List[str]:
        """Extract services offered from bio and posts"""
        services = []
        
        bio = profile_data.get("biography", "")
        
        # Look for service indicators
        service_patterns = [
            r'(?:we offer|offering|services|specializing in)[:\s]+([^.\n]+)',
            r'✓\s*([^✓\n]+)',
            r'•\s*([^•\n]+)',
            r'[-]\s*([^-\n]+)',
            r'\d+\.\s*([^.\n]+)'
        ]
        
        for pattern in service_patterns:
            matches = re.findall(pattern, bio, re.IGNORECASE)
            services.extend([match.strip() for match in matches])
        
        # Clean up services
        services = [s for s in services if len(s) > 5 and len(s) < 100]
        
        return services[:10]  # Return top 10 services
    
    def _extract_contact_info(self, profile_data: Dict) -> Dict:
        """Extract contact information"""
        contact = {}
        
        bio = profile_data.get("biography", "")
        
        # Email pattern
        email_match = re.search(r'[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}', bio)
        if email_match:
            contact["email"] = email_match.group()
        
        # Phone pattern
        phone_match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}', bio)
        if phone_match:
            contact["phone"] = phone_match.group()
        
        # WhatsApp pattern
        whatsapp_match = re.search(r'whatsapp[:\s]+([+0-9\s-]+)', bio, re.IGNORECASE)
        if whatsapp_match:
            contact["whatsapp"] = whatsapp_match.group(1).strip()
        
        # External URL
        if profile_data.get("external_url"):
            contact["website"] = profile_data["external_url"]
        
        return contact
    
    def _extract_location(self, profile_data: Dict) -> str:
        """Extract location information"""
        bio = profile_data.get("biography", "")
        
        # Look for location indicators
        location_patterns = [
            r'📍\s*([^\n]+)',
            r'(?:located in|based in|from)\s+([^\n,.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*(?:[A-Z]{2}|[A-Z][a-z]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, bio, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_keywords(self, profile_data: Dict) -> List[str]:
        """Extract relevant keywords from profile"""
        keywords = []
        
        # Get all hashtags
        for post in profile_data.get("posts", []):
            keywords.extend(post.get("hashtags", []))
        
        # Get unique keywords
        keyword_counts = Counter(keywords)
        
        # Return top keywords
        return [keyword for keyword, count in keyword_counts.most_common(20)]
    
    def _detect_brand_tone(self, profile_data: Dict) -> List[str]:
        """Detect brand tone from content"""
        bio = profile_data.get("biography", "")
        if bio is None:
            bio = ""
        bio = bio.lower()
        
        tone_indicators = {
            "professional": ["professional", "expert", "certified", "licensed", "qualified"],
            "friendly": ["friendly", "welcome", "happy", "love", "❤️", "😊"],
            "luxury": ["luxury", "premium", "exclusive", "vip", "elite"],
            "casual": ["casual", "fun", "chill", "relax", "easy"],
            "modern": ["modern", "innovative", "cutting-edge", "latest", "new"],
            "traditional": ["traditional", "classic", "authentic", "original", "established"],
            "minimal": ["minimal", "simple", "clean", "pure", "essential"],
            "bold": ["bold", "vibrant", "dynamic", "powerful", "strong"]
        }
        
        detected_tones = []
        for tone, indicators in tone_indicators.items():
            if any(indicator in bio for indicator in indicators):
                detected_tones.append(tone)
        
        return detected_tones[:3]  # Return top 3 tones
    
    def get_full_profile_analysis(self, username: str) -> Optional[Dict]:
        """
        Get complete profile analysis including all extracted data
        
        Args:
            username: Instagram username
            
        Returns:
            Complete profile analysis or None if failed
        """
        # Get basic profile data
        profile_data = self.get_profile_data(username)
        
        if not profile_data:
            return None
        
        # Extract additional information
        brand_colors = self.extract_brand_colors(profile_data)
        business_info = self.extract_business_info(profile_data)
        
        # Combine everything
        full_analysis = {
            **profile_data,
            "brand_colors": [{"r": c[0], "g": c[1], "b": c[2]} for c in brand_colors if c],
            "business_info": business_info
        }
        
        return full_analysis


def main():
    """Main function for testing the scraper"""
    scraper = InstagramScraper(use_proxy=False)
    
    # Test with a username
    test_username = input("Enter Instagram username (without @): ").strip()
    
    if test_username:
        print(f"\nAnalyzing @{test_username}...\n")
        
        result = scraper.get_full_profile_analysis(test_username)
        
        if result:
            print("\n=== PROFILE ANALYSIS ===\n")
            print(f"Username: @{result['username']}")
            print(f"Full Name: {result['full_name']}")
            print(f"Bio: {result['biography'][:200]}...")
            print(f"Followers: {result['follower_count']:,}")
            print(f"Posts: {result['post_count']}")
            
            if result.get('brand_colors'):
                print(f"\nBrand Colors:")
                for i, color in enumerate(result['brand_colors'][:3], 1):
                    print(f"  {i}. RGB({color['r']}, {color['g']}, {color['b']})")
            
            if result.get('business_info'):
                info = result['business_info']
                print(f"\nBusiness Type: {info.get('business_type', 'Unknown')}")
                
                if info.get('services'):
                    print(f"Services: {', '.join(info['services'][:3])}")
                
                if info.get('tone'):
                    print(f"Brand Tone: {', '.join(info['tone'])}")
                
                if info.get('contact_info'):
                    print(f"Contact: {info['contact_info']}")
            
            # Save to JSON file
            filename = f"{test_username}_profile.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Full analysis saved to {filename}")
        else:
            print("Failed to analyze profile. Please check the username and try again.")


if __name__ == "__main__":
    main()