from news_processor import CannabisNewsProcessor
import requests
from bs4 import BeautifulSoup

processor = CannabisNewsProcessor()

print("=== DETAILED SCRAPING DEBUG ===")

# Test each category individually
categories = {
    'politics': 'https://www.marijuanamoment.net/category/politics/',
    'business': 'https://www.marijuanamoment.net/category/business/',
    'culture': 'https://www.marijuanamoment.net/category/culture/'
}

for category, url in categories.items():
    print(f"\n{'='*50}")
    print(f"TESTING CATEGORY: {category.upper()}")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    try:
        # Get the page
        response = requests.get(url, headers=processor.headers, timeout=15)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            print(f"Total links found: {len(all_links)}")
            
            # Filter for article URLs
            article_count = 0
            available_count = 0
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Make full URL
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = 'https://www.marijuanamoment.net' + href
                    else:
                        continue
                
                # Check if it's an article
                if processor.is_article_url(href) and len(text) > 10:
                    article_count += 1
                    
                    # Check if already used
                    if processor.article_tracker.is_article_used(href):
                        status = "ALREADY USED"
                    else:
                        status = "AVAILABLE"
                        available_count += 1
                        
                        # Show first 5 available articles in detail
                        if available_count <= 5:
                            print(f"  AVAILABLE ARTICLE {available_count}: {text[:60]}...")
                            print(f"    URL: {href}")
                            
                            # Try to extract content
                            content = processor.extract_marijuana_moment_content(href)
                            if content:
                                word_count = len(content.split())
                                if word_count >= 200:
                                    print(f"    CONTENT: {word_count} words - GOOD ✓")
                                else:
                                    print(f"    CONTENT: {word_count} words - TOO SHORT ✗")
                            else:
                                print(f"    CONTENT: FAILED TO EXTRACT ✗")
                            print()
            
            print(f"SUMMARY for {category}:")
            print(f"  Total articles found: {article_count}")
            print(f"  Available (unused): {available_count}")
            print(f"  Already used: {article_count - available_count}")
            
    except Exception as e:
        print(f"Error testing {category}: {e}")
        import traceback
        traceback.print_exc()

# Check used articles tracking
print(f"\n{'='*50}")
print("USED ARTICLES TRACKING")
print(f"{'='*50}")

stats = processor.article_tracker.get_stats()
print(f"Total articles used: {stats['total_used']}")
print(f"By category: {stats['by_category']}")

# Check if we're hitting a limit
if stats['total_used'] > 50:
    print(f"⚠️  WARNING: {stats['total_used']} articles used. Consider clearing old entries.")
    
# Test the full workflow
print(f"\n{'='*50}")
print("TESTING FULL WORKFLOW")
print(f"{'='*50}")

try:
    articles = processor.scrape_cannabis_articles()
    print(f"scrape_cannabis_articles() returned: {len(articles)} articles")
    
    if articles:
        print("Sample available articles:")
        for i, article in enumerate(articles[:3]):
            print(f"  {i+1}. {article['title'][:60]}...")
            print(f"     Category: {article['category']}")
            print(f"     Words: {article['word_count']}")
            print(f"     URL: {article['url']}")
    else:
        print("No articles returned by scrape_cannabis_articles()")
        
except Exception as e:
    print(f"Error in full workflow test: {e}")
    import traceback
    traceback.print_exc()