import requests
from bs4 import BeautifulSoup

# Test one specific article we know exists
test_url = "https://www.marijuanamoment.net/indiana-gop-governor-says-federal-marijuana-rescheduling-under-trump-could-add-fire-to-legalization-push-in-his-state/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Testing: {test_url}")

try:
    response = requests.get(test_url, headers=headers, timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check what we get with the 'article' selector
        print("\n=== TESTING 'article' SELECTOR ===")
        article_element = soup.select_one('article')
        if article_element:
            text = article_element.get_text(strip=True)
            print(f"Article element found: {len(text)} characters")
            print(f"First 500 chars: {text[:500]}")
            
            # Check for paragraphs within article
            paragraphs = article_element.find_all('p')
            print(f"Paragraphs in article: {len(paragraphs)}")
            
            substantial_paragraphs = []
            for i, p in enumerate(paragraphs[:10]):  # Check first 10 paragraphs
                p_text = p.get_text(strip=True)
                print(f"  P{i+1}: {len(p_text)} chars - {p_text[:100]}...")
                if len(p_text) > 30:
                    substantial_paragraphs.append(p_text)
            
            print(f"Substantial paragraphs: {len(substantial_paragraphs)}")
            
            if substantial_paragraphs:
                combined = ' '.join(substantial_paragraphs)
                print(f"Combined substantial text: {len(combined.split())} words")
                print(f"Sample: {combined[:300]}...")
        else:
            print("No article element found!")
            
        # Let's also save the HTML to a file so we can inspect it
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nSaved page HTML to debug_page.html for inspection")
        
except Exception as e:
    print(f"Error: {e}")