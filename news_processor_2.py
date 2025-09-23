import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, WP_TAG_MAPPING
from article_tracker import ArticleTracker
from internal_linking import InternalLinking
from external_linking import ExternalLinking
import random
import time

class CannabisNewsProcessor2:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.article_tracker = ArticleTracker()
        self.internal_linking = InternalLinking()
        self.external_linking = ExternalLinking()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_cannabis_business_times_articles(self):
        """Scrape articles from Cannabis Business Times top stories"""
        articles = []
        
        try:
            print("Scraping from Cannabis Business Times top stories...")
            response = requests.get('https://www.cannabisbusinesstimes.com/top-stories', headers=self.headers, timeout=15)
            
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
                            href = 'https://www.cannabisbusinesstimes.com' + href
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
                
                # Process articles and randomize order
                random.shuffle(article_links)
                articles_to_process = min(10, len(article_links))
                
                for article_link in article_links[:articles_to_process]:
                    article_url = article_link['url']
                    title = article_link['title']
                    
                    # Skip if already used by ANY processor
                    if self.is_article_used_anywhere(article_url):
                        print(f"  Skipping already used: {title[:50]}...")
                        continue
                    
                    print(f"  Processing: {article_url}")
                    
                    # Get article content
                    content = self.extract_generic_content(article_url)
                    if content and len(content.split()) >= 200:
                        # Auto-categorize based on content or use business as default
                        category = self.determine_category(content, title)
                        articles.append({
                            'url': article_url,
                            'title': title,
                            'content': content,
                            'category': category,
                            'word_count': len(content.split())
                        })
                        print(f"  ✓ Added article: {title[:50]}... ({len(content.split())} words) - {category}")
                    else:
                        print(f"  ✗ Skipped (content too short or extraction failed)")
                    
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping Cannabis Business Times: {e}")
        
        return articles
    
    def scrape_hemp_today_articles(self):
        """Scrape articles from Hemp Today homepage"""
        articles = []
        
        try:
            print("Scraping from Hemp Today homepage...")
            response = requests.get('https://hemptoday.net/', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                article_links = []
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = 'https://hemptoday.net' + href
                        else:
                            continue
                    
                    # Check if this looks like a Hemp Today article
                    if (href.startswith('https://hemptoday.net/') and 
                        '/category/' not in href and
                        '/tag/' not in href and
                        '/author/' not in href and
                        '/page/' not in href and
                        len(href.split('/')) > 3 and
                        len(text) > 10):
                        article_links.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  Found Hemp Today article: {text[:60]}...")
                
                # Randomize and process articles
                random.shuffle(article_links)
                for article_link in article_links[:5]:
                    # Skip if already used by ANY processor
                    if self.is_article_used_anywhere(article_link['url']):
                        print(f"  Skipping already used: {article_link['title'][:50]}...")
                        continue
                        
                    content = self.extract_generic_content(article_link['url'])
                    if content and len(content.split()) >= 200:
                        category = self.determine_category(content, article_link['title'])
                        articles.append({
                            'url': article_link['url'],
                            'title': article_link['title'],
                            'content': content,
                            'category': category,
                            'word_count': len(content.split())
                        })
                        print(f"  ✓ Added Hemp Today article: {article_link['title'][:50]}... ({len(content.split())} words) - {category}")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error scraping Hemp Today: {e}")
        
        return articles
    
    def is_article_used_anywhere(self, url):
        """Check if article is used by ANY processor to prevent duplication"""
        # Check with the shared article tracker
        return self.article_tracker.is_article_used(url)
    
    def determine_category(self, content, title):
        """Determine article category based on content and title"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Politics keywords
        politics_keywords = [
            'regulation', 'law', 'legal', 'government', 'policy', 'legislation',
            'congress', 'senate', 'house', 'vote', 'bill', 'dea', 'fda',
            'state law', 'federal', 'politician', 'governor', 'mayor'
        ]
        
        # Business keywords  
        business_keywords = [
            'company', 'revenue', 'profit', 'investment', 'funding', 'ipo',
            'merger', 'acquisition', 'stock', 'market', 'sales', 'earnings',
            'business', 'industry', 'corporation', 'startup', 'ceo'
        ]
        
        # Culture keywords
        culture_keywords = [
            'consumer', 'lifestyle', 'community', 'social', 'culture',
            'trend', 'survey', 'study', 'research', 'opinion', 'behavior'
        ]
        
        # Count keyword matches
        text_to_check = content_lower + ' ' + title_lower
        
        politics_count = sum(1 for keyword in politics_keywords if keyword in text_to_check)
        business_count = sum(1 for keyword in business_keywords if keyword in text_to_check)
        culture_count = sum(1 for keyword in culture_keywords if keyword in text_to_check)
        
        # Return category with most matches, default to business
        if politics_count > business_count and politics_count > culture_count:
            return 'politics'
        elif culture_count > business_count and culture_count > politics_count:
            return 'culture'
        else:
            return 'business'
    
    def is_article_url(self, url):
        """Check if URL looks like an actual article (not navigation)"""
        if not url.startswith('https://www.cannabisbusinesstimes.com/'):
            return False
        
        # Remove the base URL to get the path
        path = url.replace('https://www.cannabisbusinesstimes.com/', '')
        
        # Skip patterns that are NOT articles
        skip_patterns = [
            'category/',
            'tag/',
            'author/',
            'page/',
            'about/',
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
        if path_clean.count('-') < 2:
            return False
        
        # Should not end with common non-article extensions
        if path.endswith(('.jpg', '.png', '.pdf', '.zip', '.css', '.js')):
            return False
        
        return True
        """Check if URL looks like an actual article (not navigation)"""
        if not url.startswith('https://www.cannabisbusinesstimes.com/'):
            return False
        
        # Remove the base URL to get the path
        path = url.replace('https://www.cannabisbusinesstimes.com/', '')
        
        # Skip patterns that are NOT articles
        skip_patterns = [
            'category/',
            'tag/',
            'author/',
            'page/',
            'about/',
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
        if path_clean.count('-') < 2:
            return False
        
        # Should not end with common non-article extensions
        if path.endswith(('.jpg', '.png', '.pdf', '.zip', '.css', '.js')):
            return False
        
        return True
    
    def extract_generic_content(self, url):
        """Extract content from any cannabis news article"""
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
    
    def scrape_cannabis_articles(self):
        """Main scraping method for processor 2"""
        print("Scraping cannabis news sources (Processor 2)...")
        
        all_articles = []
        all_articles.extend(self.scrape_cannabis_business_times_articles())
        all_articles.extend(self.scrape_hemp_today_articles())
        
        print(f"Total articles scraped: {len(all_articles)}")
        
        # Filter out already used articles
        unused_articles = self.article_tracker.get_unused_articles(all_articles)
        
        # Clean up old entries occasionally
        self.article_tracker.cleanup_old_entries()
        
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
        print("=== STARTING CANNABIS ARTICLE GENERATION (PROCESSOR 2) ===")
        
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
        
        # Step 3: Mark article as used BEFORE rewriting
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
