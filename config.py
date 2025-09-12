import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
WORDPRESS_URL = os.getenv('WORDPRESS_URL')
WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')

# Cannabis news sources with categories
CANNABIS_NEWS_SOURCES = {
    'politics': [
        'https://www.marijuanamoment.net/category/politics/',
        'https://mjbizdaily.com/legal/'
    ],
    'business': [
        'https://www.marijuanamoment.net/category/business/',
        'https://mjbizdaily.com/finance/'
    ],
    'culture': [
        'https://www.marijuanamoment.net/category/culture/'  # Add if they have one
    ]
}

# Content settings
NEWS_POSTS_PER_DAY = 5
POSTING_HOURS = [9, 12, 15, 18, 21]  # Times to post (24hr format)

# WordPress categories and tags
WP_CANNABIS_NEWS_CATEGORY = 'Cannabis News'
WP_TAG_MAPPING = {
    'business': 'Cannabis-business',
    'culture': 'culture', 
    'politics': 'politics'
}