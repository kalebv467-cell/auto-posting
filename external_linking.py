import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY
import re
import time

class ExternalLinking:
   def __init__(self):
       self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
       self.headers = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
       }
       
       # Domains to exclude from linking
       self.excluded_domains = [
           'marijuanamoment.net',
           'stratcann.com',  # Added Canadian source
           'newcannabisventures.com',  # Added Canadian source
           'seekingalpha.com',
           'cannabisbusinesstimes.com',
           'internationalcbc.com',
           'hemptoday.net',
           'form.jotform.com',
           'patreon.com',
           'facebook.com',
           'twitter.com',
           'instagram.com',
           'youtube.com',
           'linkedin.com',
           'pinterest.com',
           'bit.ly',
           'reddit.com'
       ]
   
   def extract_links_from_original(self, original_url):
       """Extract external links from the original article"""
       print(f"Extracting external links from original article...")
       
       try:
           response = requests.get(original_url, headers=self.headers, timeout=15)
           if response.status_code != 200:
               print(f"Failed to fetch original article: {response.status_code}")
               return []
           
           soup = BeautifulSoup(response.content, 'html.parser')
           article_element = soup.select_one('article')
           
           if not article_element:
               print("No article element found in original")
               return []
           
           # Find all links in the article
           links = article_element.find_all('a', href=True)
           external_links = []
           
           for link in links:
               href = link.get('href', '')
               
               # Skip if not a full URL
               if not href.startswith('http'):
                   continue
               
               # Skip excluded domains (including Canadian sources)
               if any(domain in href.lower() for domain in self.excluded_domains):
                   continue
               
               # Get link text
               link_text = link.get_text().strip()
               if len(link_text) > 5:  # Only meaningful link text
                   external_links.append({
                       'url': href,
                       'text': link_text,
                       'source': 'original_article'
                   })
                   print(f"  Found original link: {link_text} -> {href}")
           
           print(f"Found {len(external_links)} external links from original article")
           return external_links[:3]  # Limit to 3 links
           
       except Exception as e:
           print(f"Error extracting links from original: {e}")
           return []
   
   def find_additional_sources(self, article_content, article_title, existing_links_count):
       """Use Claude to find additional reliable sources"""
       needed_links = max(1, 3 - existing_links_count)  # Ensure at least 1, max 3 total
       
       if needed_links <= 0:
           print("Already have enough external links")
           return []
       
       print(f"Looking for {needed_links} additional reliable sources...")
       
       prompt = f"""
       You are a fact-checker and researcher. Based on this cannabis news article, find {needed_links} reliable external sources that would add credibility and context to the article.

       ARTICLE TITLE: {article_title}
       ARTICLE CONTENT: {article_content[:1500]}...

       REQUIREMENTS:
       1. Find {needed_links} reliable, authoritative sources
       2. Sources should be government websites (.gov), research institutions (.edu), reputable news organizations, or industry authorities
       3. Sources should be directly relevant to the topic discussed
       4. Provide the exact URL and a brief description of why it's relevant
       5. NEVER suggest marijuanamoment.net, stratcann.com, newcannabisventures.com, or social media links

       FORMAT YOUR RESPONSE EXACTLY AS:
       SOURCE 1: [URL] | [Brief description of relevance]
       SOURCE 2: [URL] | [Brief description of relevance]
       SOURCE 3: [URL] | [Brief description of relevance]

       Only provide as many sources as needed ({needed_links}). Focus on quality over quantity.
       """
       
       try:
           response = self.client.messages.create(
               model="claude-sonnet-4-20250514",
               max_tokens=1000,
               messages=[{"role": "user", "content": prompt}]
           )
           
           claude_response = response.content[0].text
           sources = self.parse_claude_sources(claude_response)
           
           # Validate the sources
           validated_sources = []
           for source in sources:
               if self.validate_source(source):
                   validated_sources.append(source)
           
           print(f"Claude suggested {len(validated_sources)} valid sources")
           return validated_sources
           
       except Exception as e:
           print(f"Error getting sources from Claude: {e}")
           return []
   
   def parse_claude_sources(self, response):
       """Parse Claude's response to extract sources"""
       sources = []
       lines = response.split('\n')
       
       for line in lines:
           if line.startswith('SOURCE'):
               parts = line.split('|', 1)
               if len(parts) == 2:
                   url_part = parts[0].split(':', 1)[1].strip()
                   description = parts[1].strip()
                   
                   # Clean URL
                   url = url_part.strip()
                   if url.startswith('http'):
                       sources.append({
                           'url': url,
                           'description': description,
                           'text': description[:50] + "..." if len(description) > 50 else description,
                           'source': 'claude_suggested'
                       })
       
       return sources
   
   def validate_source(self, source):
       """Validate that a source is accessible and not excluded"""
       url = source['url']
       
       # Check against excluded domains (including Canadian sources)
       if any(domain in url.lower() for domain in self.excluded_domains):
           print(f"  Excluding {url} - contains excluded domain")
           return False
       
       # Try to access the URL
       try:
           response = requests.head(url, headers=self.headers, timeout=10)
           if response.status_code in [200, 301, 302]:
               print(f"  ✓ Validated source: {url}")
               return True
           else:
               print(f"  ✗ Source returned {response.status_code}: {url}")
               return False
       except Exception as e:
           print(f"  ✗ Could not access source: {url} - {e}")
           return False
   
   def add_external_links_to_content(self, content, external_links):
       """Add external links to the article content"""
       if not external_links:
           print("No external links to add")
           return content
       
       print(f"Adding {len(external_links)} external links to content...")
       
       # Use Claude to intelligently place the links
       links_info = []
       for i, link in enumerate(external_links):
           links_info.append(f"LINK {i+1}: {link['url']} - {link.get('description', link.get('text', 'Source'))}")
       
       prompt = f"""
       You are an editor adding external source links to a cannabis news article. Add these external links naturally into the content where they are most relevant and credible.

       ARTICLE CONTENT:
       {content}

       EXTERNAL LINKS TO ADD:
       {chr(10).join(links_info)}

       REQUIREMENTS:
       1. Add each link naturally where it supports or adds credibility to a statement
       2. Use appropriate anchor text that describes what the link is about
       3. Add links as: <a href="URL" target="_blank" rel="noopener">anchor text</a>
       4. Don't change the existing content structure, just add the links
       5. Place links where they add the most value to readers
       6. Make sure the anchor text flows naturally with the sentence

       Return the complete article content with the external links added naturally.
       """
       
       try:
           response = self.client.messages.create(
               model="claude-sonnet-4-20250514",
               max_tokens=4000,
               messages=[{"role": "user", "content": prompt}]
           )
           
           linked_content = response.content[0].text
           print(f"✓ Added external links to content")
           
           # Show what links were added
           for link in external_links:
               if link['url'] in linked_content:
                   print(f"  ✓ Added: {link['url']}")
               else:
                   print(f"  ✗ Could not add: {link['url']}")
           
           return linked_content
           
       except Exception as e:
           print(f"Error adding external links: {e}")

           return content


