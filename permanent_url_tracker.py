import os
from datetime import datetime, date

class PermanentURLTracker:
    def __init__(self):
        self.blacklist_file = "permanent_url_blacklist.txt"
        self.used_urls = self.load_blacklisted_urls()
        # Cutoff date - don't process articles before this date
        self.cutoff_date = date(2025, 9, 23)
    
    def is_article_too_old(self, article_data):
        """Check if article is older than our cutoff date"""
        # Try to extract date from article data if available
        # This is a basic implementation - you might need to adjust based on your article structure
        
        # For now, we'll try to parse common date formats from the URL or title
        url = article_data.get('url', '')
        title = article_data.get('title', '')
        
        # Look for date patterns in URL like /2025/09/22/ or /2025-09-22/
        import re
        date_patterns = [
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2025/09/22/
            r'/(\d{4})-(\d{1,2})-(\d{1,2})/',  # /2025-09-22/
            r'(\d{4})/(\d{1,2})/(\d{1,2})',   # 2025/09/22
            r'(\d{4})-(\d{1,2})-(\d{1,2})'    # 2025-09-2
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    article_date = date(year, month, day)
                    
                    if article_date < self.cutoff_date:
                        print(f"Skipping old article from {article_date}: {title[:50]}...")
                        return True
                except ValueError:
                    continue
        
    def should_skip_article(self, article_data):
        """Check if article should be skipped (blacklisted OR too old)"""
        url = article_data.get('url', '')
        
        # Check if blacklisted
        if self.is_url_blacklisted(url):
            return True
        
        # Check if too old
        if self.is_article_too_old(article_data):
            return True
        
        return False
    
    def normalize_url(self, url):
        """Normalize URL to catch variations"""
        url = url.lower().strip()
        # Remove www prefix
        if url.startswith('https://www.'):
            url = url.replace('https://www.', 'https://')
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
        # Remove common URL parameters
        if '?' in url:
            url = url.split('?')[0]
        return url
    
    def load_blacklisted_urls(self):
        """Load all blacklisted URLs from file"""
        if os.path.exists(self.blacklist_file):
            try:
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    urls = set(line.strip() for line in f if line.strip())
                print(f"Loaded {len(urls)} blacklisted URLs")
                return urls
            except Exception as e:
                print(f"Error loading blacklist file: {e}")
                return set()
        print("No existing blacklist file found, starting fresh")
        return set()
    
    def is_url_blacklisted(self, url):
        """Check if URL is already blacklisted"""
        normalized_url = self.normalize_url(url)
        is_blacklisted = normalized_url in self.used_urls
        print(f"Checking URL: {url[:80]}... -> {'BLACKLISTED' if is_blacklisted else 'OK'}")
        return is_blacklisted
    
    def blacklist_url(self, url, title="Unknown"):
        """Permanently blacklist a URL"""
        normalized_url = self.normalize_url(url)
        
        if normalized_url not in self.used_urls:
            self.used_urls.add(normalized_url)
            
            # Append to file immediately
            try:
                with open(self.blacklist_file, 'a', encoding='utf-8') as f:
                    f.write(f"{normalized_url}\n")
                print(f"✓ PERMANENTLY BLACKLISTED: {title[:50]}...")
                print(f"  URL: {normalized_url}")
            except Exception as e:
                print(f"✗ ERROR blacklisting URL: {e}")
        else:
            print(f"URL already blacklisted: {normalized_url}")
    
    def get_stats(self):
        """Get blacklist statistics"""
        return {
            'total_blacklisted_urls': len(self.used_urls),
            'blacklist_file': self.blacklist_file
        }
    
    def force_save_all(self):
        """Force save all URLs to file (backup method)"""
        try:
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                for url in sorted(self.used_urls):
                    f.write(f"{url}\n")
            print(f"Force saved {len(self.used_urls)} URLs to blacklist")
        except Exception as e:
            print(f"Error force saving blacklist: {e}")
    
    def check_url_and_blacklist_if_new(self, url, title="Unknown"):
        """Check if URL is blacklisted, if not blacklist it and return False (meaning it's new)"""
        if self.is_url_blacklisted(url):
            return True  # URL is blacklisted (already used)
        else:
            self.blacklist_url(url, title)
            return False  # URL was new, now blacklisted
