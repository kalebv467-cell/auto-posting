import requests
import base64
from dotenv import load_dotenv
import os

load_dotenv()

# Get credentials
wp_url = os.getenv('WORDPRESS_URL')
wp_user = os.getenv('WORDPRESS_USERNAME') 
wp_pass = os.getenv('WORDPRESS_PASSWORD')

print(f"Testing connection to: {wp_url}")
print(f"Username: {wp_user}")
print(f"Password length: {len(wp_pass)}")

# Test basic API access
response = requests.get(f"{wp_url}/wp-json/wp/v2/posts")
print(f"Basic API test: {response.status_code}")

# Test with authentication
credentials = f"{wp_user}:{wp_pass}"
token = base64.b64encode(credentials.encode()).decode()
headers = {
    'Authorization': f'Basic {token}',
    'Content-Type': 'application/json'
}

# Try to create a test post
data = {
    'title': 'API Test Post',
    'content': 'This is a test',
    'status': 'draft'
}

response = requests.post(
    f"{wp_url}/wp-json/wp/v2/posts",
    json=data,
    headers=headers
)

print(f"Post creation test: {response.status_code}")
print(f"Response: {response.text}")