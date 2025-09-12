import os
import random
import requests
import base64
from config import WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD

class ImageManager:
    def __init__(self):
        self.images_folder = "images"
        self.base_url = f"{WORDPRESS_URL}/wp-json/wp/v2"
        credentials = f"{WORDPRESS_USERNAME}:{WORDPRESS_PASSWORD}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {token}'
        }
    
    def get_random_image_for_category(self, category):
        """Get a random image that matches the category"""
        if not os.path.exists(self.images_folder):
            print(f"Images folder not found: {self.images_folder}")
            return None
        
        # Look for images that match the category
        all_images = [f for f in os.listdir(self.images_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        
        if not all_images:
            print("No images found in images folder")
            return None
        
        print(f"Found {len(all_images)} total images")
        
        # Filter by category if possible
        category_images = [img for img in all_images if category.lower() in img.lower()]
        print(f"Found {len(category_images)} images for category '{category}'")
        
        # If no category-specific images, use any image
        if not category_images:
            print(f"No category-specific images, using random image from all {len(all_images)} images")
            category_images = all_images
        
        # Return random image path
        chosen_image = random.choice(category_images)
        full_path = os.path.join(self.images_folder, chosen_image)
        print(f"Chose image: {chosen_image}")
        return full_path
    
    def upload_image_to_wordpress(self, image_path, title="Cannabis News Image"):
        """Upload image to WordPress media library"""
        try:
            print(f"Uploading image: {image_path}")
            with open(image_path, 'rb') as img_file:
                files = {
                    'file': (os.path.basename(image_path), img_file, 'image/jpeg')
                }
                
                data = {
                    'title': title,
                    'alt_text': title
                }
                
                response = requests.post(
                    f"{self.base_url}/media",
                    files=files,
                    data=data,
                    headers={'Authorization': self.headers['Authorization']}
                )
                
                if response.status_code == 201:
                    media_data = response.json()
                    print(f"✓ Uploaded image with ID: {media_data['id']}")
                    return media_data['id']
                else:
                    print(f"✗ Failed to upload image: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    def get_featured_image_for_article(self, category, article_title):
        """Get and upload a featured image for an article"""
        print(f"Getting featured image for category: {category}")
        
        # Get random image for this category
        image_path = self.get_random_image_for_category(category)
        
        if not image_path:
            print(f"✗ No image path found for category: {category}")
            return None
        
        # Upload to WordPress
        image_title = f"{category.title()} Cannabis News - {article_title[:50]}"
        media_id = self.upload_image_to_wordpress(image_path, image_title)
        
        return media_id