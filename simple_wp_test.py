import requests
from dotenv import load_dotenv
import os

load_dotenv()

wp_url = os.getenv('WORDPRESS_URL')
wp_user = os.getenv('WORDPRESS_USERNAME') 
wp_pass = os.getenv('WORDPRESS_PASSWORD')

print(f"Testing: {wp_url}")

# Test basic WordPress connection
try:
    response = requests.get(f"{wp_url}/wp-json/wp/v2", timeout=10)
    print(f"Basic WordPress API: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ WordPress API is accessible")
    else:
        print("✗ WordPress API not accessible")
        
except Exception as e:
    print(f"Connection error: {e}")

# Test what post types are available
try:
    response = requests.get(f"{wp_url}/wp-json/wp/v2/types", timeout=10)
    if response.status_code == 200:
        types = response.json()
        print("\nAvailable post types:")
        for type_name, type_info in types.items():
            print(f"- {type_name}: {type_info.get('name', 'No name')}")
    else:
        print(f"Could not fetch post types: {response.status_code}")
        
except Exception as e:
    print(f"Error fetching post types: {e}")