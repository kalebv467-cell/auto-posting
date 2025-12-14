import re
import requests
import base64
from config import WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD

class InternalLinking:
   def __init__(self):
       self.base_url = f"{WORDPRESS_URL}/wp-json/wp/v2"
       credentials = f"{WORDPRESS_USERNAME}:{WORDPRESS_PASSWORD}"
       token = base64.b64encode(credentials.encode()).decode()
       self.headers = {
           'Authorization': f'Basic {token}',
           'Content-Type': 'application/json'
       }
       
       # Static internal links (ordered by specificity - more specific first)
       self.static_links = {
           'https://budscannacorner.ca/cannabis-blog/thc-vs-cbd-vs-cbn-vs-cbg-effects-benefits-and-key-differences/': [
               'thc', 'cbd', 'cbg', 'cbn'
           ],
           'https://budscannacorner.ca/cannabis-blog/how-to-decarboxylate-cannabis-complete-guide-to-decarbing-weed/': [
               'decarboxylate', 'decarbing', 'decarb'
           ],
           'https://budscannacorner.ca/sativa-strain-reviews/': [
               'sativa strain', 'sativa strains', 'sativa strain review'
           ],
           'https://budscannacorner.ca/cbd-products/best-cbd-pain-cream-canada/': [
               'CBD pain creams', 'pain cream' 'topical CBD products', 'CBD pain relief products', 'CBD topicals for pain', 'legal CBD pain relief products', 'Health Canada-approved CBD topicals', 'compliant CBD pain creams', 'regulated CBD products for pain', 'licensed CBD pain relief options', 'federally legal CBD topicals', 'CBD pain products meeting Health Canada standards', 'topical CBD for pain management', 'CBD creams for arthritis relief', 'cannabidiol topical applications', 'therapeutic CBD topicals', 'CBD for chronic pain treatment', 'evidence-based CBD pain creams', 'CBD pain cream market in Canada', 'available CBD topical products', 'Canadian CBD pain relief market', 'CBD cream options for Canadians', 'top-rated CBD pain products', 'premium CBD pain creams', 'high-potency CBD topicals', 'CBD alternatives for pain relief', 'natural pain management with CBD', 'CBD topicals for inflammation', 'non-prescription CBD pain options', 'CBD for joint and muscle pain', 'holistic pain relief with CBD', 'CBD solutions for chronic pain', 'choosing CBD pain creams', 'CBD pain product selection', 'quality CBD topicals', 'third-party tested CBD creams', 'verified CBD pain relief products', 'Canadian CBD pain cream reviews', 'cannabidiol pain relief', 'CBD cream options', 'therapeutic CBD products'
           ],
           'https://budscannacorner.ca/sativa-weed-high-and-effects/': [
               'sativa', 'sativa effects', 'sativa high'
           ],
           'https://budscannacorner.ca/indica-strain-reviews/': [
               'indica strain', 'indica strains', 'indica strain review'
           ],
           'https://budscannacorner.ca/what-is-indica-cannabis/': [
               'indica', 'indica effects', 'indica cannabis'
           ],
           'https://budscannacorner.ca/hybrid-strain-reviews/': [
               'hybrid strain', 'hybrid strains'
           ],
           'https://budscannacorner.ca/strain-reviews/': [
               'strain reviews', 'strain review', 'weed review', 'product review'
           ],
           'https://budscannacorner.ca/news/': [
               'cannabis news', 'weed news', 'marijuana news', 'smoking news', 'news'
           ],
           'https://budscannacorner.ca/cannabis-blog/beginners-guide-to-cannabis-dosing-complete-thc-mg-dosage-chart/': [
               'Weed dosage', 'dosing', 'marijuana dosage', 'how much to smoke', 'cannabis dosage'
           ],
           'https://budscannacorner.ca/cannabis-blog/the-entourage-effect-what-is-it-and-what-does-it-actually-feel-like/': [
               'Weed dosage', 'dosing', 'marijuana dosage', 'how much to smoke', 'cannabis dosage'
           ],
           'https://budscannacorner.ca/cannabis-blog/how-does-cannabis-work-what-is-the-endocannabinoid-system-explained/': [
               'endocannabinoid system'
           ],
           'https://budscannacorner.ca/strain-reviews/blue-dream-strain-review-effects-thc-and-more/': [
               'blue dream', 'blue dream strain'
           ],
           'https://budscannacorner.ca/strain-reviews/liquid-imagination-strain-review-effects-thc/': [
               'liquid imagination'
           ]
       }
       
       # Cache for existing articles
       self.existing_articles_cache = None
   
   def get_existing_articles(self):
       """Get existing articles from WordPress for internal linking"""
       if self.existing_articles_cache is not None:
           return self.existing_articles_cache
       
       try:
           print("Fetching existing articles for internal linking...")
           
           # Get news articles
           news_response = requests.get(
               f"{self.base_url}/news?per_page=50",
               headers=self.headers,
               timeout=10
           )
           
           articles = []
           
           if news_response.status_code == 200:
               news_articles = news_response.json()
               for article in news_articles:
                   articles.append({
                       'title': article['title']['rendered'],
                       'url': article['link'],
                       'excerpt': article['excerpt']['rendered'][:200] if article['excerpt']['rendered'] else ''
                   })
           
           # Get cannabis lifestyle articles
           lifestyle_response = requests.get(
               f"{self.base_url}/cannabis-lifestyle?per_page=50",
               headers=self.headers,
               timeout=10
           )
           
           if lifestyle_response.status_code == 200:
               lifestyle_articles = lifestyle_response.json()
               for article in lifestyle_articles:
                   articles.append({
                       'title': article['title']['rendered'],
                       'url': article['link'],
                       'excerpt': article['excerpt']['rendered'][:200] if article['excerpt']['rendered'] else ''
                   })
           
           self.existing_articles_cache = articles
           print(f"Found {len(articles)} existing articles for internal linking")
           return articles
           
       except Exception as e:
           print(f"Error fetching existing articles: {e}")
           return []
   
   def find_keywords_in_content(self, content):
       """Find static keywords in content that should be linked"""
       links_to_add = {}
       used_phrases = set()  # Track what we've already linked
       
       # Process links in order (most specific first)
       for url, keywords in self.static_links.items():
           for keyword in keywords:
               # Skip if we've already linked a variation of this phrase
               keyword_lower = keyword.lower()
               if any(keyword_lower in existing.lower() or existing.lower() in keyword_lower 
                      for existing in used_phrases):
                   continue
               
               # Case-insensitive search for keyword
               pattern = r'\b' + re.escape(keyword) + r'\b'
               matches = re.finditer(pattern, content, re.IGNORECASE)
               
               for match in matches:
                   # Only link the first occurrence of each keyword type
                   if keyword.lower() not in [k.lower() for k in links_to_add.keys()]:
                       links_to_add[match.group()] = url
                       used_phrases.add(keyword)
                       print(f"Found keyword for linking: '{keyword}' -> {url}")
                       break
                       
               if keyword in [k.lower() for k in links_to_add.keys()]:
                   break  # Move to next URL once we've found a match for this one
       
       return links_to_add
   
   def find_related_articles(self, content, current_title):
       """Find existing articles that could be linked to"""
       existing_articles = self.get_existing_articles()
       related_links = {}
       
       for article in existing_articles:
           article_title = article['title']
           
           # Skip linking to the same article
           if article_title.lower() == current_title.lower():
               continue
           
           # Look for key phrases from the article title in the content
           title_words = article_title.split()
           
           # Try different combinations of words from the title
           found_match = False
           for i in range(len(title_words)):
               if found_match:
                   break
                   
               for j in range(i + 2, min(i + 5, len(title_words) + 1)):  # 2-4 word phrases
                   phrase = ' '.join(title_words[i:j])
                   
                   # Skip very common words
                   if any(common in phrase.lower() for common in ['the', 'and', 'or', 'of', 'in', 'to', 'a', 'an']):
                       continue
                   
                   # Look for this phrase in the content
                   pattern = r'\b' + re.escape(phrase) + r'\b'
                   if re.search(pattern, content, re.IGNORECASE):
                       # Only add if we haven't already linked this phrase
                       if phrase.lower() not in [k.lower() for k in related_links.keys()]:
                           related_links[phrase] = article['url']
                           print(f"Found related article link: '{phrase}' -> {article['title']}")
                           found_match = True
                           break
       
       return related_links
   
   def add_internal_links(self, content, article_title):
       """Add internal links to content"""
       print("Adding internal links...")
       
       # Find static keyword links
       static_links = self.find_keywords_in_content(content)
       print(f"Found {len(static_links)} static keyword links")
       
       # Find related article links
       related_links = self.find_related_articles(content, article_title)
       print(f"Found {len(related_links)} related article links")
       
       # Combine all links
       all_links = {**static_links, **related_links}
       
       if not all_links:
           print("No internal links found")
           return content
       
       # Apply links to content (only first occurrence of each phrase)
       linked_content = content
       linked_phrases = set()
       
       for phrase, url in all_links.items():
           # Skip if we've already linked a variation of this phrase
           phrase_lower = phrase.lower()
           if any(phrase_lower in existing.lower() or existing.lower() in phrase_lower 
                  for existing in linked_phrases):
               continue
           
           # Create the link
           pattern = r'\b' + re.escape(phrase) + r'\b'
           replacement = f'<a href="{url}" target="_blank">{phrase}</a>'
           
           # Replace only the first occurrence
           linked_content = re.sub(pattern, replacement, linked_content, count=1, flags=re.IGNORECASE)
           linked_phrases.add(phrase)
           print(f"Added link: '{phrase}' -> {url}")
       
       print(f"Added {len(linked_phrases)} internal links total")

       return linked_content
