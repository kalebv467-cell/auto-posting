import json
import os
from datetime import datetime

class ArticleTracker:
    def __init__(self):
        self.tracking_file = "used_articles.json"
        self.used_articles = self.load_used_articles()
    
    def load_used_articles(self):
        """Load the list of previously used articles"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} previously used articles")
                    return data
            except Exception as e:
                print(f"Error loading tracking file: {e}")
                return {}
        return {}
    
    def save_used_articles(self):
        """Save the list of used articles to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.used_articles, f, indent=2)
        except Exception as e:
            print(f"Error saving tracking file: {e}")
    
    def is_article_used(self, article_url):
        """Check if an article has already been used"""
        return article_url in self.used_articles
    
    def mark_article_used(self, article_url, article_title, category):
        """Mark an article as used"""
        self.used_articles[article_url] = {
            'title': article_title,
            'category': category,
            'used_date': datetime.now().isoformat(),
            'wordpress_post_id': None  # Will be updated when posted
        }
        self.save_used_articles()
        print(f"✓ Marked article as used: {article_title[:50]}...")
    
    def update_wordpress_id(self, article_url, wordpress_id):
        """Update the WordPress post ID for tracking"""
        if article_url in self.used_articles:
            self.used_articles[article_url]['wordpress_post_id'] = wordpress_id
            self.save_used_articles()
    
    def get_unused_articles(self, articles_list):
        """Filter out articles that have already been used"""
        unused_articles = []
        
        for article in articles_list:
            if not self.is_article_used(article['url']):
                unused_articles.append(article)
            else:
                print(f"  Skipping already used article: {article['title'][:50]}...")
        
        print(f"Found {len(unused_articles)} unused articles out of {len(articles_list)} total")
        return unused_articles
    
    def get_stats(self):
        """Get statistics about used articles"""
        total_used = len(self.used_articles)
        
        categories = {}
        for data in self.used_articles.values():
            cat = data.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_used': total_used,
            'by_category': categories
        }
