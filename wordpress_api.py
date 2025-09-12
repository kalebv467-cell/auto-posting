import requests
import base64
from config import WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD

class WordPressAPI:
    def __init__(self):
        self.base_url = f"{WORDPRESS_URL}/wp-json/wp/v2"
        credentials = f"{WORDPRESS_USERNAME}:{WORDPRESS_PASSWORD}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }
        self.author_cache = {}
    
    def get_author_id(self, author_name):
        """Get author ID by name, cache results"""
        if author_name in self.author_cache:
            return self.author_cache[author_name]
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                params={'search': author_name},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user['name'].lower() == author_name.lower():
                        self.author_cache[author_name] = user['id']
                        print(f"Found author '{author_name}' with ID: {user['id']}")
                        return user['id']
            
            print(f"Author '{author_name}' not found")
            return None
            
        except Exception as e:
            print(f"Error finding author '{author_name}': {e}")
            return None
    
    def create_post(self, title, content, status='publish', categories=None, tags=None, post_type='posts', featured_image_id=None, author_name=None):
        """Create a post - can be regular post or custom post type"""
        
        # For custom post types, use different endpoints
        if post_type == 'news':
            endpoint = f"{self.base_url}/news"
        elif post_type == 'cannabis-lifestyle':
            endpoint = f"{self.base_url}/cannabis-lifestyle"
        else:
            endpoint = f"{self.base_url}/posts"
        
        data = {
            'title': title,
            'content': content,
            'status': status
        }
        
        if categories:
            data['categories'] = self._get_or_create_categories(categories)
        
        if tags:
            data['tags'] = self._get_or_create_tags(tags)
        
        if featured_image_id:
            data['featured_media'] = featured_image_id
        
        # Add author if provided
        if author_name:
            author_id = self.get_author_id(author_name)
            if author_id:
                data['author'] = author_id
                print(f"Setting author to '{author_name}' (ID: {author_id})")
            else:
                print(f"Warning: Could not set author '{author_name}', using default")
            
        response = requests.post(
            endpoint,
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Error creating {post_type}: {response.status_code}")
            print(response.text)
            return None
    
    def create_news_post(self, title, content, status='publish', categories=None, tags=None, featured_image_id=None, author_name=None):
        """Specific method for creating news posts"""
        return self.create_post(title, content, status, categories, tags, post_type='news', featured_image_id=featured_image_id, author_name=author_name)
    
    def create_cannabis_lifestyle_post(self, title, content, status='publish', categories=None, tags=None, featured_image_id=None, author_name=None):
        """Specific method for creating cannabis-lifestyle posts"""
        return self.create_post(title, content, status, categories, tags, post_type='cannabis-lifestyle', featured_image_id=featured_image_id, author_name=author_name)
    
    def test_news_endpoint(self):
        """Test if the news custom post type endpoint exists"""
        try:
            response = requests.get(f"{self.base_url}/news", headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_cannabis_lifestyle_endpoint(self):
        """Test if the cannabis-lifestyle custom post type endpoint exists"""
        try:
            response = requests.get(f"{self.base_url}/cannabis-lifestyle", headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _get_or_create_categories(self, category_names):
        """Get category IDs, create if they don't exist"""
        category_ids = []
        
        for cat_name in category_names:
            try:
                response = requests.get(
                    f"{self.base_url}/categories",
                    params={'search': cat_name},
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    categories = response.json()
                    if categories:
                        category_ids.append(categories[0]['id'])
                    else:
                        new_cat_response = requests.post(
                            f"{self.base_url}/categories",
                            json={'name': cat_name},
                            headers=self.headers,
                            timeout=10
                        )
                        if new_cat_response.status_code == 201:
                            category_ids.append(new_cat_response.json()['id'])
            except:
                continue
        
        return category_ids
    
    def _get_or_create_tags(self, tag_names):
        """Get tag IDs, create if they don't exist"""
        tag_ids = []
        
        for tag_name in tag_names:
            try:
                response = requests.get(
                    f"{self.base_url}/tags",
                    params={'search': tag_name},
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    tags = response.json()
                    if tags:
                        tag_ids.append(tags[0]['id'])
                    else:
                        new_tag_response = requests.post(
                            f"{self.base_url}/tags",
                            json={'name': tag_name},
                            headers=self.headers,
                            timeout=10
                        )
                        if new_tag_response.status_code == 201:
                            tag_ids.append(new_tag_response.json()['id'])
            except:
                continue
        
        return tag_ids