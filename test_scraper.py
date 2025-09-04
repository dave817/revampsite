#!/usr/bin/env python3
"""
Test script for Instagram Scraper
Tests the scraper with sample profiles to ensure it works correctly
"""

import json
import sys
import time
from instagram_scraper import InstagramScraper
from config import Config

def test_profile_extraction():
    """Test basic profile data extraction"""
    print("=" * 60)
    print("INSTAGRAM SCRAPER TEST")
    print("=" * 60)
    
    # Initialize scraper
    scraper = InstagramScraper(use_proxy=Config.USE_PROXY)
    
    # Test profiles (popular public accounts that should always be available)
    test_profiles = [
        "cristiano",  # Cristiano Ronaldo - Sports/Celebrity
        "nike",       # Nike - Fashion/Sports brand
        "natgeo",     # National Geographic - Photography/Education
    ]
    
    results = []
    
    for username in test_profiles:
        print(f"\n[TEST] Analyzing @{username}...")
        print("-" * 40)
        
        try:
            # Get profile analysis
            profile_data = scraper.get_full_profile_analysis(username)
            
            if profile_data:
                # Display results
                print(f"✓ Username: @{profile_data['username']}")
                print(f"✓ Full Name: {profile_data.get('full_name', 'N/A')}")
                print(f"✓ Followers: {profile_data.get('follower_count', 0):,}")
                print(f"✓ Posts: {profile_data.get('post_count', 0):,}")
                print(f"✓ Bio Length: {len(profile_data.get('biography', ''))} chars")
                
                # Check brand colors
                if profile_data.get('brand_colors'):
                    print(f"✓ Brand Colors: {len(profile_data['brand_colors'])} extracted")
                    for i, color in enumerate(profile_data['brand_colors'][:3], 1):
                        print(f"  Color {i}: RGB({color['r']}, {color['g']}, {color['b']})")
                else:
                    print("⚠ No brand colors extracted")
                
                # Check business info
                business_info = profile_data.get('business_info', {})
                if business_info:
                    print(f"✓ Business Type: {business_info.get('business_type', 'Unknown')}")
                    
                    if business_info.get('tone'):
                        print(f"✓ Brand Tone: {', '.join(business_info['tone'])}")
                    
                    if business_info.get('keywords'):
                        print(f"✓ Keywords: {len(business_info['keywords'])} found")
                        print(f"  Top 5: {', '.join(business_info['keywords'][:5])}")
                
                # Check posts
                posts = profile_data.get('posts', [])
                if posts:
                    print(f"✓ Recent Posts: {len(posts)} retrieved")
                    print(f"  Average likes: {sum(p.get('likes', 0) for p in posts) // len(posts):,}")
                else:
                    print("⚠ No posts retrieved")
                
                results.append({
                    "username": username,
                    "status": "SUCCESS",
                    "data_points": {
                        "profile": bool(profile_data.get('biography')),
                        "colors": bool(profile_data.get('brand_colors')),
                        "business_info": bool(business_info),
                        "posts": len(posts) > 0
                    }
                })
                
            else:
                print(f"✗ Failed to fetch profile data for @{username}")
                results.append({
                    "username": username,
                    "status": "FAILED",
                    "data_points": {}
                })
                
        except Exception as e:
            print(f"✗ Error testing @{username}: {str(e)}")
            results.append({
                "username": username,
                "status": "ERROR",
                "error": str(e),
                "data_points": {}
            })
        
        # Add delay between tests
        if username != test_profiles[-1]:
            print("\nWaiting before next test...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] in ["FAILED", "ERROR"])
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful == len(results):
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to test_results.json")
    
    return successful == len(results)


def test_single_profile():
    """Test with a specific profile provided by user"""
    print("\n" + "=" * 60)
    print("SINGLE PROFILE TEST")
    print("=" * 60)
    
    username = input("\nEnter Instagram username to test (without @): ").strip()
    
    if not username:
        print("No username provided. Exiting.")
        return False
    
    scraper = InstagramScraper(use_proxy=Config.USE_PROXY)
    
    print(f"\n[TEST] Analyzing @{username}...")
    print("-" * 40)
    
    try:
        profile_data = scraper.get_full_profile_analysis(username)
        
        if profile_data:
            # Save full data
            filename = f"{username}_test.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Profile data successfully extracted!")
            print(f"✓ Data saved to {filename}")
            
            # Quick stats
            print("\nQuick Stats:")
            print(f"- Followers: {profile_data.get('follower_count', 0):,}")
            print(f"- Posts analyzed: {len(profile_data.get('posts', []))}")
            print(f"- Brand colors found: {len(profile_data.get('brand_colors', []))}")
            print(f"- Business type: {profile_data.get('business_info', {}).get('business_type', 'Unknown')}")
            
            return True
        else:
            print(f"✗ Failed to fetch profile data for @{username}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Main test runner"""
    print("\nRevampSite Instagram Scraper Test Suite")
    print("Choose test option:")
    print("1. Run automated tests with sample profiles")
    print("2. Test with specific username")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        success = test_profile_extraction()
    elif choice == "2":
        success = test_single_profile()
    elif choice == "3":
        success1 = test_profile_extraction()
        success2 = test_single_profile()
        success = success1 and success2
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    if success:
        print("\n✓ Testing completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠ Testing completed with some failures.")
        sys.exit(1)


if __name__ == "__main__":
    main()