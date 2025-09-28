import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, WP_TAG_MAPPING
from database_article_tracker import DatabaseArticleTracker as ArticleTracker
from internal_linking import InternalLinking
from external_linking import ExternalLinking
import random
import time
from datetime import datetime, timedelta

class CannabisNewsProcessor:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.article_tracker = ArticleTracker()
        self.internal_linking = InternalLinking()
        self.external_linking = ExternalLinking()
        # Only process articles from last 2 weeks
        self.cutoff_date = datetime.now() - timedelta(days=14)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def is_article_too_old(self, article_data):
        """Check if article is older than 2 weeks"""
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        # Look for date patterns like "September 25, 2025"
        import re
        
        search_text = f"{title} {content}"
        
        month_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})'
        ]
        
        month_map = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        for pattern in month_patterns:
            matches = re.finditer(pattern, search_text, re.IGNORECASE)
            for match in matches:
                try:
                    month_name = match.group(1).lower()
                    day = int(match.group(2))
                    year = int(match.group(3))
                    
                    if month_name in month_map:
                        month = month_map[month_name]
                        article_date = datetime(year, month, day)
                        
                        if article_date < self.cutoff_date:
                            print(f"Skipping old article from {article_date.date()}: {title[:50]}...")
                            return True
                except (ValueError, IndexError):
                    continue
        
        # If no date found, assume it's recent enough
        return False
    
    def scrape_marijuana_moment_articles(self):
        """Scrape articles specifically from Marijuana Moment"""
        articles = []
        
        categories = {
            'politics': 'https://www.marijuanamoment.net/category/politics/',
            'business': 'https://www.marijuanamoment.net/category/business/',
            'culture': 'https://www.marijuanamoment.net/category/culture/'
        }
        
        for category, url in categories.items():
            try:
                print(f"Scraping {category} from Marijuana Moment...")
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all links on the page
                    all_links = soup.find_all('a', href=True)
                    
                    # Filter for actual article URLs
                    article_links = []
                    for link in all_links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        # Make sure it's a full URL
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = 'https://www.marijuanamoment.net' + href
                            else:
                                continue
                        
                        # Check if this looks like an actual article URL
                        if self.is_article_url(href) and len(text) > 10:
                            article_links.append({
                                'url': href,
                                'title': text
                            })
                            print(f"  Found article: {text[:60]}...")
                    
                    print(f"  Total article links found: {len(article_links)}")
                    
                    # Process more articles and randomize order
                    random.shuffle(article_links)
                    articles_to_process = min(10, len(article_links))
                    
                    for article_link in article_links[:articles_to_process]:
                        article_url = article_link['url']
                        title = article_link['title']
                        
                        # Check if already used in JSON file
                        if self.article_tracker.is_article_used(article_url):
                            print(f"  Skipping already used: {title[:50]}...")
                            continue
                        
                        print(f"  Processing: {article_url}")
                        
                        # Get article content
                        content = self.extract_marijuana_moment_content(article_url)
                        if content and len(content.split()) >= 200:
                            article_data = {
                                'url': article_url,
                                'title': title,
                                'content': content,
                                'category': category,
                                'word_count': len(content.split())
                            }
                            
                            # Check if article is too old (older than 2 weeks)
                            if self.is_article_too_old(article_data):
                                continue
                            
                            articles.append(article_data)
                            print(f"  ✓ Added article: {title[:50]}... ({len(content.split())} words)")
                        else:
                            print(f"  ✗ Skipped (content too short or extraction failed)")
                        
                        time.sleep(2)
                        
            except Exception as e:
                print(f"Error scraping {category}: {e}")
                continue
        
        return articles
    
    def is_article_url(self, url):
        """Check if URL looks like an actual article (not navigation)"""
        if not url.startswith('https://www.marijuanamoment.net/'):
            return False
        
        # Remove the base URL to get the path
        path = url.replace('https://www.marijuanamoment.net/', '')
        
        # Skip patterns that are NOT articles
        skip_patterns = [
            'category/',
            'tag/',
            'author/',
            'page/',
            'about/',
            'bills/',
            'contact/',
            'privacy/',
            'terms/',
            'feed/',
            'wp-',
            '?',
            '#'
        ]
        
        # If it contains any skip patterns, it's not an article
        if any(pattern in path for pattern in skip_patterns):
            return False
        
        # If it's just the homepage or very short, skip
        if len(path.strip('/')) < 10:
            return False
        
        # Article URLs should have multiple words separated by hyphens
        path_clean = path.strip('/')
        if path_clean.count('-') < 3:
            return False
        
        # Should not end with common non-article extensions
        if path.endswith(('.jpg', '.png', '.pdf', '.zip', '.css', '.js')):
            return False
        
        return True
    
    def extract_marijuana_moment_content(self, url):
        """Extract content specifically from Marijuana Moment articles"""
        try:
            print(f"    Extracting content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"    Failed to fetch {url} (status: {response.status_code})")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get the article element
            article_element = soup.select_one('article')
            if article_element:
                print(f"    Found article element")
                # Get all paragraphs from the article
                paragraphs = article_element.find_all('p')
                print(f"    Found {len(paragraphs)} paragraphs")
                substantial_paragraphs = []
                
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # Filter out very short paragraphs and navigation/metadata
                    if (len(text) > 20 and 
                        not any(skip_phrase in text.lower() for skip_phrase in [
                            'published', 'by kyle jaeger', 'marijuana moment',
                            'subscribe', 'remove ads', 'hours ago', 'minutes ago'
                        ]) and
                        not text in ['on', 'By']):
                        substantial_paragraphs.append(text)
                
                if substantial_paragraphs:
                    clean_text = ' '.join(substantial_paragraphs)
                    word_count = len(clean_text.split())
                    
                    print(f"    ✓ Extracted {word_count} words from article")
                    return clean_text
                else:
                    print(f"    ✗ No substantial paragraphs found after filtering")
                    return None
            else:
                print(f"    ✗ No article element found")
                return None
            
        except Exception as e:
            print(f"    ✗ Error extracting content from {url}: {e}")
            return None
    
    def scrape_cannabis_articles(self):
        """Main scraping method"""
        print("Scraping cannabis news sources...")
        
        articles = self.scrape_marijuana_moment_articles()
        
        print(f"Total articles scraped: {len(articles)}")
        
        # Filter out already used articles (this is additional safety)
        unused_articles = self.article_tracker.get_unused_articles(articles)
        
        return unused_articles
    
    def choose_best_article(self, articles):
        """Choose the best article from scraped content"""
        if not articles:
            print("No articles to choose from")
            return None
        
        # Filter articles with good length (200+ words)
        good_articles = [a for a in articles if a['word_count'] >= 200]
        
        if not good_articles:
            print("No articles with sufficient word count")
            return None
        
        # Randomly select from good articles
        chosen = random.choice(good_articles)
        print(f"Chose article: {chosen['title'][:50]}... ({chosen['word_count']} words)")
        return chosen
    
    def rewrite_cannabis_article(self, original_article):
        """Rewrite cannabis article with specific requirements"""
        
        print(f"Rewriting article with Claude...")
        
        original_title = original_article['title']
        original_content = original_article['content']
        category = original_article['category']
        target_word_count = original_article['word_count']
        
        # Map category to WordPress tag
        wp_tag = WP_TAG_MAPPING.get(category, 'cannabis-news')
        
        print(f"Original title: {original_title}")
        print(f"Category: {category}, Tag: {wp_tag}")
        print(f"Target word count: {target_word_count}")
        
        prompt = f"""
        You are a cannabis industry journalist. Rewrite this cannabis news article following these exact specifications:

        ORIGINAL ARTICLE:
        Title: {original_title}
        Content: {original_content[:2000]}...
        Category: {category}
        Original Word Count: {target_word_count}

        REQUIREMENTS:
        1. Create an original, engaging title based on the original but reworded
        2. Target word count: {target_word_count - 300} to {target_word_count + 300} words
        3. Write in a fresh, engaging way - keep key facts but change structure, wording, and approach
        4. Make it informative yet accessible for cannabis industry readers
        5. Use proper heading structure with H2 and H3 tags ONLY (NO H1 tags - WordPress will handle the main title)
        6. This will be tagged as: {wp_tag}
        7. Focus on the {category} aspect of cannabis news

        FORMAT YOUR RESPONSE EXACTLY AS:
        TITLE: [Your new title here]
        CATEGORY: {category}
        TAG: {wp_tag}
        CONTENT: [Your rewritten article with H2, H3 headings and HTML formatting - NO H1 tags]

        Write the content with proper HTML formatting including <h2>, <h3> tags for headings and <p> tags for paragraphs. DO NOT include any <h1> tags as WordPress will use the title as H1.
        """
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            print("✓ Received response from Claude")
            claude_response = response.content[0].text
            
            parsed = self.parse_cannabis_response(claude_response)
            print(f"Parsed response - Title: {parsed.get('title', 'NO TITLE')}")
            print(f"Parsed response - Content length: {len(parsed.get('content', ''))}")
            
            return parsed
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None
    
    def parse_cannabis_response(self, response):
        """Parse the formatted response from Claude"""
        print("Parsing Claude response...")
        lines = response.split('\n')
        
        title = ""
        category = ""
        tag = ""
        content = ""
        
        content_started = False
        
        for i, line in enumerate(lines):
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
                print(f"Found title: {title}")
            elif line.startswith('CATEGORY:'):
                category = line.replace('CATEGORY:', '').strip()
                print(f"Found category: {category}")
            elif line.startswith('TAG:'):
                tag = line.replace('TAG:', '').strip()
                print(f"Found tag: {tag}")
            elif line.startswith('CONTENT:'):
                content = line.replace('CONTENT:', '').strip()
                content_started = True
                print(f"Found content start")
            elif content_started and line.strip():
                content += "\n" + line
        
        result = {
            'title': title,
            'content': content.strip(),
            'category': category,
            'tag': tag
        }
        
        return result
    
    def get_cannabis_article(self):
        """Main method to get and rewrite a cannabis article"""
        print("=== STARTING CANNABIS ARTICLE GENERATION ===")
        
        # Step 1: Scrape articles
        articles = self.scrape_cannabis_articles()
        
        if not articles:
            print("No suitable unused articles found")
            return None
        
        print(f"Found {len(articles)} unused articles, selecting best one...")
        
        # Step 2: Choose best article
        chosen_article = self.choose_best_article(articles)
        
        if not chosen_article:
            print("No suitable article found")
            return None
        
        # Step 3: Mark article as used in JSON file
        self.article_tracker.mark_article_used(
            chosen_article['url'], 
            chosen_article['title'], 
            chosen_article['category']
        )
        
        # Step 4: Extract external links from original article
        print("Extracting external links from original article...")
        original_external_links = self.external_linking.extract_links_from_original(chosen_article['url'])
        
        # Step 5: Rewrite with Claude
        print(f"Rewriting article: {chosen_article['title'][:50]}...")
        rewritten = self.rewrite_cannabis_article(chosen_article)
        
        if rewritten:
            print("✓ Article generation completed successfully")
            
            # Step 6: Add primary tag and secondary tag
            secondary_tag = rewritten.get('tag', 'business')
            rewritten['tags'] = ['US Cannabis News', secondary_tag]
            
            # Remove the old single tag field since we now have tags array
            if 'tag' in rewritten:
                del rewritten['tag']
            
            # Step 7: Add internal links
            print("Adding internal links...")
            rewritten['content'] = self.internal_linking.add_internal_links(
                rewritten['content'], 
                rewritten['title']
            )
            
            # Step 8: Find additional external sources if needed
            additional_sources = self.external_linking.find_additional_sources(
                rewritten['content'], 
                rewritten['title'], 
                len(original_external_links)
            )
            
            # Step 9: Combine all external links
            all_external_links = original_external_links + additional_sources
            
            # Step 10: Add external links to content
            if all_external_links:
                rewritten['content'] = self.external_linking.add_external_links_to_content(
                    rewritten['content'], 
                    all_external_links
                )
            
            # Add original URL to rewritten article for tracking
            rewritten['original_url'] = chosen_article['url']
            
            print(f"Article will be tagged with: {', '.join(rewritten['tags'])}")
        else:
            print("✗ Article generation failed")
        
        return rewritten

