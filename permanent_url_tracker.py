import os
from datetime import datetime, date

class PermanentURLTracker:
    def __init__(self):
        self.blacklist_file = "permanent_url_blacklist.txt"
        self.used_urls = self.load_blacklisted_urls()
        # Cutoff date - don't process articles before this date
        self.cutoff_date = date(2025, 9, 23)
    
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
                print(f"DEBUG: Attempting to write to {self.blacklist_file}")
                print(f"DEBUG: Current working directory: {os.getcwd()}")
                print(f"DEBUG: File exists before write: {os.path.exists(self.blacklist_file)}")
                
                with open(self.blacklist_file, 'a', encoding='utf-8') as f:
                    f.write(f"{normalized_url}\n")
                    f.flush()  # Force write to disk
                    
                print(f"DEBUG: File exists after write: {os.path.exists(self.blacklist_file)}")
                
                # Verify the write worked
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"DEBUG: File now contains {len(lines)} lines")
                    if lines and normalized_url in lines[-1]:
                        print(f"DEBUG: Successfully verified URL was written")
                    else:
                        print(f"DEBUG: URL was NOT found in file after write")
                
                print(f"✓ PERMANENTLY BLACKLISTED: {title[:50]}...")
                print(f"  URL: {normalized_url}")
            except Exception as e:
                print(f"✗ ERROR blacklisting URL: {e}")
                print(f"DEBUG: Error type: {type(e).__name__}")
                import traceback
                print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        else:
            print(f"URL already blacklisted: {normalized_url}")
    
    def is_article_too_old(self, article_data):
        """Check if article is older than our cutoff date"""
        url = article_data.get('url', '')
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        # Look for date patterns like "September 25, 2025" or "Sep 25, 2025"
        import re
        
        # All text to search for dates
        search_text = f"{title} {content}"
        
        # Month name patterns
        month_patterns = [
            # Full month names
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            # Abbreviated month names  
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
            # URL date patterns (backup)
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',
            r'/(\d{4})-(\d{1,2})-(\d{1,2})/'
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
                    if len(match.groups()) == 3:
                        # Month name format: "September 25, 2025"
                        month_name = match.group(1).lower()
                        day = int(match.group(2))
                        year = int(match.group(3))
                        
                        if month_name in month_map:
                            month = month_map[month_name]
                            article_date = date(year, month, day)
                            
                            if article_date < self.cutoff_date:
                                print(f"Skipping old article from {article_date}: {title[:50]}...")
                                return True
                    else:
                        # URL format: /2025/09/22/
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        article_date = date(year, month, day)
                        
                        if article_date < self.cutoff_date:
                            print(f"Skipping old article from {article_date}: {title[:50]}...")
                            return True
                except (ValueError, IndexError):
                    continue
        
        # If no date found, assume it's recent enough
        return False
    
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
