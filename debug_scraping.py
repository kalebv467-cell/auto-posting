import requests
from bs4 import BeautifulSoup
from config import CANNABIS_NEWS_SOURCES

print("Testing cannabis news scraping...")

for category, urls in CANNABIS_NEWS_SOURCES.items():
    print(f"\n=== Testing {category} ===")
    
    for hub_url in urls:
        print(f"\nTesting URL: {hub_url}")
        
        try:
            # Test basic connection
            response = requests.get(hub_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links
                all_links = soup.find_all('a', href=True)
                print(f"Found {len(all_links)} total links")
                
                # Show first 5 links
                print("First 5 links:")
                for i, link in enumerate(all_links[:5]):
                    href = link.get('href')
                    text = link.get_text().strip()[:50]
                    print(f"  {i+1}. {href} - {text}")
                
                # Look for article-like links
                article_links = []
                for link in all_links:
                    href = link.get('href')
                    if href and ('http' in href or href.startswith('/')):
                        if any(word in href.lower() for word in ['cannabis', 'marijuana', 'hemp', 'thc', 'cbd']):
                            article_links.append(href)
                
                print(f"Found {len(article_links)} potential cannabis article links")
                
                if article_links:
                    print("Sample cannabis links:")
                    for link in article_links[:3]:
                        print(f"  - {link}")
                
        except Exception as e:
            print(f"Error: {e}")

print("\n=== Testing Article Content Extraction ===")

# Test extracting content from a specific article
test_urls = [
    "https://www.marijuanamoment.net/",  # Try homepage first
    "https://mjbizdaily.com/"
]

for test_url in test_urls:
    print(f"\nTesting content extraction from: {test_url}")
    
    try:
        response = requests.get(test_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different content selectors
            selectors = ['.entry-content', '.article-content', '.post-content', 'article', '.content']
            
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    text = content_div.get_text(separator=' ', strip=True)
                    word_count = len(text.split())
                    print(f"  Selector '{selector}': Found {word_count} words")
                    if word_count > 50:
                        print(f"    Sample: {text[:200]}...")
                        break
                else:
                    print(f"  Selector '{selector}': No content found")
        
    except Exception as e:
        print(f"Error testing {test_url}: {e}")