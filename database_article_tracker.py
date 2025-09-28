
import os
import psycopg2
from datetime import datetime, timedelta
import re

class DatabaseArticleTracker:
    def __init__(self):
        # Railway automatically provides DATABASE_URL
        self.database_url = os.getenv('DATABASE_URL')
        self.cutoff_date = datetime.now() - timedelta(days=14)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def init_database(self):
        """Create table if it doesn't exist"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS used_articles (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        wordpress_post_id INTEGER
                    )
                """)
                conn.commit()
                cursor.close()
                conn.close()
                print("Database table initialized")
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def is_article_used(self, article_url):
        """Check if an article has already been used"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM used_articles WHERE url = %s", (article_url,))
                count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                return count > 0
        except Exception as e:
            print(f"Error checking article: {e}")
            return False
    
    def is_article_too_old(self, article_data):
        """Check if article is older than 2 weeks"""
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
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
        
        return False
    
    def mark_article_used(self, article_url, article_title, category):
        """Mark an article as used"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO used_articles (url, title, category) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (article_url, article_title, category))
                conn.commit()
                cursor.close()
                conn.close()
                print(f"✓ Marked article as used: {article_title[:50]}...")
        except Exception as e:
            print(f"Error marking article as used: {e}")
    
    def update_wordpress_id(self, article_url, wordpress_id):
        """Update the WordPress post ID for tracking"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE used_articles 
                    SET wordpress_post_id = %s 
                    WHERE url = %s
                """, (wordpress_id, article_url))
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"Error updating WordPress ID: {e}")
    
    def get_unused_articles(self, articles_list):
        """Filter out articles that have already been used"""
        unused_articles = []
        
        for article in articles_list:
            # Skip if already used
            if self.is_article_used(article['url']):
                print(f"  Skipping already used article: {article['title'][:50]}...")
                continue
            
            # Skip if too old (older than 2 weeks)
            if self.is_article_too_old(article):
                continue
            
            unused_articles.append(article)
        
        print(f"Found {len(unused_articles)} unused recent articles out of {len(articles_list)} total")
        return unused_articles
    
    def get_stats(self):
        """Get statistics about used articles"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                
                # Total count
                cursor.execute("SELECT COUNT(*) FROM used_articles")
                total_used = cursor.fetchone()[0]
                
                # By category
                cursor.execute("SELECT category, COUNT(*) FROM used_articles GROUP BY category")
                categories = dict(cursor.fetchall())
                
                cursor.close()
                conn.close()
                
                return {
                    'total_used': total_used,
                    'by_category': categories
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'total_used': 0, 'by_category': {}}
