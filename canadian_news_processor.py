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

class CanadianNewsProcessor:
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
    
    def scrape_stratcann_articles(self):
        """Scrape articles from StratCann"""
        articles = []
        try:
            print("Scraping from StratCann...")
            response = requests.get('https://stratcann.com/news/', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                article_links = []
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = 'https://stratcann.com' + href
                        else:
                            continue
                    
                    # Check if this looks like a StratCann news article
                    if (href.startswith('https://stratcann.com/news/') and 
                        len(href.split('/')) > 4 and 
                        len(text) > 10):
                        article_links.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  Found StratCann article: {text[:60]}...")
                
                # Randomize and process articles
                random.shuffle(article_links)
                for article_link in article_links[:5]:
                    # Check if already used in JSON file
                    if self.article_tracker.is_article_used(article_link['url']):
                        print(f"  Skipping already used: {article_link['title'][:50]}...")
                        continue
                        
                    content = self.extract_generic_content(article_link['url'])
                    if content and len(content.split()) >= 200:
                        article_data = {
                            'url': article_link['url'],
                            'title': article_link['title'],
                            'content': content,
                            'category': 'canadian',
                            'word_count': len(content.split()),
                            'source': 'stratcann'
                        }
                        
                        # Check if article is too old (older than 2 weeks)
                        if self.is_article_too_old(article_data):
                            continue
                        
                        articles.append(article_data)
                        print(f"  ✓ Added StratCann article: {article_link['title'][:50]}... ({len(content.split())} words)")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping StratCann: {e}")
        
        return articles
    
    def scrape_newcannabisventures_articles(self):
        """Scrape articles from New Cannabis Ventures Canada"""
        articles = []
        try:
            print("Scraping from New Cannabis Ventures Canada...")
            response = requests.get('https://www.newcannabisventures.com/category/canada/', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                article_links = []
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Check if this looks like a New Cannabis Ventures article
                    if (href.startswith('https://www.newcannabisventures.com/') and 
                        '/category/' not in href and
                        '/tag/' not in href and
                        '/author/' not in href and
                        len(href.split('/')) > 3 and
                        len(text) > 10):
                        article_links.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  Found NCV article: {text[:60]}...")
                
                # Randomize and process articles
                random.shuffle(article_links)
                for article_link in article_links[:5]:
                    # Check if already used in JSON file
                    if self.article_tracker.is_article_used(article_link['url']):
                        print(f"  Skipping already used: {article_link['title'][:50]}...")
                        continue
                        
                    content = self.extract_generic_content(article_link['url'])
                    if content and len(content.split()) >= 200:
                        article_data = {
                            'url': article_link['url'],
                            'title': article_link['title'],
                            'content': content,
                            'category': 'canadian',
                            'word_count': len(content.split()),
                            'source': 'newcannabisventures'
                        }
                        
                        # Check if article is too old (older than 2 weeks)
                        if self.is_article_too_old(article_data):
                            continue
                        
                        articles.append(article_data)
                        print(f"  ✓ Added NCV article: {article_link['title'][:50]}... ({len(content.split())} words)")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping New Cannabis Ventures: {e}")
        
        return articles
    
    def scrape_health_canada_updates(self):
        """Scrape articles from Health Canada"""
        articles = []
        try:
            print("Scraping from Health Canada...")
            response = requests.get('https://www.canada.ca/en/health-canada/services/drugs-medication/cannabis/industry-licensees-applicants/updates-cannabis-industrial-hemp.html', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                content_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['content', 'update', 'news', 'main']))
                
                for section in content_sections:
                    links = section.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = 'https://www.canada.ca' + href
                            else:
                                continue
                        
                        if (href.startswith('https://www.canada.ca') and 
                            'cannabis' in href.lower() and
                            len(text) > 10):
                            
                            # Check if already used in JSON file
                            if self.article_tracker.is_article_used(href):
                                continue
                                
                            content = self.extract_generic_content(href)
                            if content and len(content.split()) >= 200:
                                article_data = {
                                    'url': href,
                                    'title': text,
                                    'content': content,
                                    'category': 'canadian',
                                    'word_count': len(content.split()),
                                    'source': 'health_canada'
                                }
                                
                                # Check if article is too old (older than 2 weeks)
                                if self.is_article_too_old(article_data):
                                    continue
                                
                                articles.append(article_data)
                                print(f"  ✓ Added Health Canada article: {text[:50]}... ({len(content.split())} words)")
                                break
                            time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping Health Canada: {e}")
        
        return articles
    
    def scrape_internationalcbc_articles(self):
        """Scrape articles from International CBC"""
        articles = []
        try:
            print("Scraping from International CBC...")
            response = requests.get('https://internationalcbc.com/blog/', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                article_links = []
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = 'https://internationalcbc.com' + href
                        else:
                            continue
                    
                    # Check if this looks like an International CBC blog article
                    # Exclude category pages and ensure it's a blog post
                    if (href.startswith('https://internationalcbc.com/blog/') and 
                        '/category' not in href and
                        len(href.split('/')) > 4 and
                        len(text) > 10):
                        article_links.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  Found International CBC article: {text[:60]}...")
                
                # Randomize and process articles
                random.shuffle(article_links)
                for article_link in article_links[:5]:
                    # Check if already used in JSON file
                    if self.article_tracker.is_article_used(article_link['url']):
                        print(f"  Skipping already used: {article_link['title'][:50]}...")
                        continue
                        
                    content = self.extract_generic_content(article_link['url'])
                    # Require at least 300 words
                    if content and len(content.split()) >= 300:
                        article_data = {
                            'url': article_link['url'],
                            'title': article_link['title'],
                            'content': content,
                            'category': 'canadian',
                            'word_count': len(content.split()),
                            'source': 'internationalcbc'
                        }
                        
                        # Check if article is too old (older than 2 weeks)
                        if self.is_article_too_old(article_data):
                            continue
                        
                        articles.append(article_data)
                        print(f"  ✓ Added International CBC article: {article_link['title'][:50]}... ({len(content.split())} words)")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping International CBC: {e}")
        
        return articles
    
    def extract_generic_content(self, url):
        """Extract content from any Canadian cannabis news article"""
        try:
            print(f"    Extracting content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"    Failed to fetch {url} (status: {response.status_code})")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            content_selectors = [
                'article',
                '.entry-content',
                '.post-content',
                '.article-content',
                '.content',
                'main',
                '[role="main"]',
                '.main-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    for unwanted in content_element.find_all(['script', 'style', 'nav', 'footer', 'aside', 'iframe', 'form']):
                        unwanted.decompose()
                    
                    paragraphs = content_element.find_all('p')
                    substantial_paragraphs = []
                    
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if (len(text) > 20 and 
                            not any(skip_phrase in text.lower() for skip_phrase in [
                                'subscribe', 'newsletter', 'follow us', 'share this',
                                'advertisement', 'sponsored', 'cookie', 'privacy'
                            ])):
                            substantial_paragraphs.append(text)
                    
                    if substantial_paragraphs:
                        clean_text = ' '.join(substantial_paragraphs)
                        word_count = len(clean_text.split())
                        
                        if word_count >= 200:
                            print(f"    ✓ Extracted {word_count} words using selector: {selector}")
                            return clean_text
            
            print(f"    ✗ No substantial content found")
            return None
            
        except Exception as e:
            print(f"    ✗ Error extracting content from {url}: {e}")
            return None
    
    def scrape_canadian_articles(self):
        """Main scraping method for Canadian cannabis news"""
        print("Scraping Canadian cannabis news sources...")
        
        all_articles = []
        all_articles.extend(self.scrape_stratcann_articles())
        all_articles.extend(self.scrape_newcannabisventures_articles())
        all_articles.extend(self.scrape_health_canada_updates())
        all_articles.extend(self.scrape_internationalcbc_articles())
        
        print(f"Total Canadian articles scraped: {len(all_articles)}")
        
        # Filter out already used articles (this is additional safety)
        unused_articles = self.article_tracker.get_unused_articles(all_articles)
        
        return unused_articles
    
    def choose_best_article(self, articles):
        """Choose the best article from scraped Canadian content"""
        if not articles:
            print("No Canadian articles to choose from")
            return None
        
        good_articles = [a for a in articles if a['word_count'] >= 200]
        
        if not good_articles:
            print("No Canadian articles with sufficient word count")
            return None
        
        chosen = random.choice(good_articles)
        print(f"Chose Canadian article: {chosen['title'][:50]}... ({chosen['word_count']} words from {chosen['source']})")
        return chosen
    
    def rewrite_canadian_article(self, original_article):
        """Rewrite Canadian cannabis article in Canadian English"""
        
        print(f"Rewriting Canadian article with Claude...")
        
        original_title = original_article['title']
        original_content = original_article['content']
        target_word_count = original_article['word_count']
        source = original_article['source']
        
        prompt = f"""
        You are a Canadian cannabis industry journalist. Rewrite this Canadian cannabis news article following these exact specifications:

        ORIGINAL ARTICLE:
        Title: {original_title}
        Content: {original_content[:2000]}...
        Source: {source}
        Original Word Count: {target_word_count}

        REQUIREMENTS:
        1. Create an original, engaging title based on the original but reworded
        2. Target word count: {target_word_count - 300} to {target_word_count + 300} words
        3. Write in a fresh, engaging way - keep key facts but change structure, wording, and approach
        4. Make it informative yet accessible for Canadian cannabis industry readers
        5. Use proper heading structure with H2 and H3 tags ONLY (NO H1 tags - WordPress will handle the main title)
        6. Write in CANADIAN ENGLISH with Canadian spelling (e.g., centre, colour, licence, organised, realise)
        7. Use Canadian terminology and references where appropriate
        8. If any article mentions 420 investor or Alan Crochstein on seeking alpha, remove that copy from text, do not include anything about 420 investor or seeking alpha.
        9. If there is any mention of "stratcann" interviewing or getting information from people/companies, replace it with "BudsCannaCorner". NEVER mention Stratcann
        10. Focus on the Canadian cannabis industry and regulatory environment
        11. Determine the most appropriate category for this article based on content
        12. Attempt to add something more than what the first text adds, give a canadian perspective and why it matters to canadians

        CANADIAN ENGLISH REQUIREMENTS:
        - Use Canadian spelling: centre (not center), colour (not color), licence (not license as noun), organised (not organized), realise (not realize)
        - Use Canadian terms: cannabis (preferred over marijuana), federal vs provincial jurisdiction
        - Reference Canadian regulations, provinces, and Canadian context

        CATEGORY ASSIGNMENT:
        Choose the most appropriate category based on the article content:
        - "politics" for: government policy, regulations, legislation, political decisions, Health Canada updates
        - "business" for: company news, financial reports, market analysis, industry trends, licensing, acquisitions
        - "culture" for: social acceptance, consumer trends, lifestyle topics, community events, social impact

        FORMAT YOUR RESPONSE EXACTLY AS:
        TITLE: [Your new title here]
        CATEGORY: [politics/business/culture]
        TAG: [politics/business/culture]
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
            
            parsed = self.parse_canadian_response(claude_response)
            print(f"Parsed Canadian response - Title: {parsed.get('title', 'NO TITLE')}")
            print(f"Parsed Canadian response - Content length: {len(parsed.get('content', ''))}")
            
            return parsed
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None
    
    def parse_canadian_response(self, response):
        """Parse the formatted response from Claude"""
        print("Parsing Canadian Claude response...")
        lines = response.split('\n')
        
        title = ""
        category = ""
        tag = ""
        content = ""
        
        content_started = False
        
        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
                print(f"Found Canadian title: {title}")
            elif line.startswith('CATEGORY:'):
                category = line.replace('CATEGORY:', '').strip()
                print(f"Found Canadian category: {category}")
            elif line.startswith('TAG:'):
                tag = line.replace('TAG:', '').strip()
                print(f"Found Canadian secondary tag: {tag}")
            elif line.startswith('CONTENT:'):
                content = line.replace('CONTENT:', '').strip()
                content_started = True
                print(f"Found Canadian content start")
            elif content_started and line.strip():
                content += "\n" + line
        
        result = {
            'title': title,
            'content': content.strip(),
            'category': category,
            'secondary_tag': tag
        }
        
        return result
    
    def get_canadian_article(self):
        """Main method to get and rewrite a Canadian cannabis article"""
        print("=== STARTING CANADIAN CANNABIS ARTICLE GENERATION ===")
        
        articles = self.scrape_canadian_articles()
        
        if not articles:
            print("No suitable unused Canadian articles found")
            return None
        
        print(f"Found {len(articles)} unused Canadian articles, selecting best one...")
        
        chosen_article = self.choose_best_article(articles)
        
        if not chosen_article:
            print("No suitable Canadian article found")
            return None
        
        # Mark article as used in JSON file
        self.article_tracker.mark_article_used(
            chosen_article['url'], 
            chosen_article['title'], 
            chosen_article['category']
        )
        
        print("Extracting external links from original Canadian article...")
        original_external_links = self.external_linking.extract_links_from_original(chosen_article['url'])
        
        print(f"Rewriting Canadian article: {chosen_article['title'][:50]}...")
        rewritten = self.rewrite_canadian_article(chosen_article)
        
        if rewritten:
            print("✓ Canadian article generation completed successfully")
            
            secondary_tag = rewritten.get('secondary_tag', 'business')
            rewritten['tags'] = ['Canadian Cannabis News', secondary_tag]
            
            if 'secondary_tag' in rewritten:
                del rewritten['secondary_tag']
            
            print("Adding internal links to Canadian article...")
            rewritten['content'] = self.internal_linking.add_internal_links(
                rewritten['content'], 
                rewritten['title']
            )
            
            additional_sources = self.external_linking.find_additional_sources(
                rewritten['content'], 
                rewritten['title'], 
                len(original_external_links)
            )
            
            all_external_links = original_external_links + additional_sources
            
            if all_external_links:
                rewritten['content'] = self.external_linking.add_external_links_to_content(
                    rewritten['content'], 
                    all_external_links
                )
            
            rewritten['original_url'] = chosen_article['url']
            
            print(f"Canadian article will be tagged with: {', '.join(rewritten['tags'])}")
        else:
            print("✗ Canadian article generation failed")
        
        return rewritten
