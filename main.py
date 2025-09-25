import schedule
import time
import sys
from datetime import datetime
from news_processor import CannabisNewsProcessor
from canadian_news_processor import CanadianNewsProcessor
from wordpress_api import WordPressAPI
from image_manager import ImageManager
from config import POSTING_HOURS

class ContentAutomation:
   def __init__(self):
       self.wp_api = WordPressAPI()
       self.news_processor = CannabisNewsProcessor()
       self.canadian_processor = CanadianNewsProcessor()
       self.image_manager = ImageManager()
       self.daily_news_count = 0
   
   def post_us_news_content(self):
       """Post single US cannabis news content"""
       print(f"[{datetime.now()}] Posting US cannabis news...")
       
       try:
           rewritten_article = self.news_processor.get_cannabis_article()
           if rewritten_article:
               # Add ad inserter shortcode to content
               rewritten_article['content'] = '[adinserter block="3"]\n\n' + rewritten_article['content']
               
               # Get featured image
               featured_image_id = self.image_manager.get_featured_image_for_article(
                   rewritten_article['category'], 
                   rewritten_article['title']
               )
               
               # Post to WordPress
               result = self.wp_api.create_news_post(
                   rewritten_article['title'], 
                   rewritten_article['content'], 
                   status='publish',
                   categories=['Cannabis News'],
                   tags=rewritten_article['tags'],
                   featured_image_id=featured_image_id,
                   author_name='rohan'
               )
               
               if result:
                   print(f"✅ Posted US cannabis news: {rewritten_article['title']}")
                   print(f"Category: {rewritten_article['category']}, Tags: {', '.join(rewritten_article['tags'])}")
                   if featured_image_id:
                       print(f"✅ Added featured image: {featured_image_id}")
                   
                   # Update tracking with WordPress post ID
                   if 'original_url' in rewritten_article:
                       self.news_processor.article_tracker.update_wordpress_id(
                           rewritten_article['original_url'], 
                           result.get('id')
                       )
                   return True
               else:
                   print("❌ Failed to post US cannabis news")
                   return False
           else:
               print("No US cannabis articles found")
               return False
               
       except Exception as e:
           print(f"❌ Error posting US cannabis content: {e}")
           import traceback
           traceback.print_exc()
           return False

   def post_us_news_content_2(self):
       """Post single US cannabis news content using processor 2"""
       print(f"[{datetime.now()}] Posting US cannabis news 2...")
       
       try:
           from news_processor_2 import CannabisNewsProcessor2
           news_processor_2 = CannabisNewsProcessor2()
           
           rewritten_article = news_processor_2.get_cannabis_article()
           if rewritten_article:
               # Add ad inserter shortcode to content
               rewritten_article['content'] = '[adinserter block="3"]\n\n' + rewritten_article['content']
               
               # Get featured image
               featured_image_id = self.image_manager.get_featured_image_for_article(
                   rewritten_article['category'], 
                   rewritten_article['title']
               )
               
               # Post to WordPress
               result = self.wp_api.create_news_post(
                   rewritten_article['title'], 
                   rewritten_article['content'], 
                   status='publish',
                   categories=['Cannabis News'],
                   tags=rewritten_article['tags'],
                   featured_image_id=featured_image_id,
                   author_name='kaleb'
               )
               
               if result:
                   print(f"✅ Posted US cannabis news 2: {rewritten_article['title']}")
                   print(f"Category: {rewritten_article['category']}, Tags: {', '.join(rewritten_article['tags'])}")
                   if featured_image_id:
                       print(f"✅ Added featured image: {featured_image_id}")
                   
                   # Update tracking with WordPress post ID
                   if 'original_url' in rewritten_article:
                       news_processor_2.article_tracker.update_wordpress_id(
                           rewritten_article['original_url'], 
                           result.get('id')
                       )
                   return True
               else:
                   print("❌ Failed to post US cannabis news 2")
                   return False
           else:
               print("No US cannabis news 2 articles found")
               return False
               
       except Exception as e:
           print(f"❌ Error posting US cannabis news 2 content: {e}")
           import traceback
           traceback.print_exc()
           return False

   def post_canadian_news_content(self):
       """Post single Canadian cannabis news content"""
       print(f"[{datetime.now()}] Posting Canadian cannabis news...")
       
       try:
           rewritten_article = self.canadian_processor.get_canadian_article()
           if rewritten_article:
               # Add ad inserter shortcode to content
               rewritten_article['content'] = '[adinserter block="3"]\n\n' + rewritten_article['content']
               
               # Get featured image
               featured_image_id = self.image_manager.get_featured_image_for_article(
                   'canadian', 
                   rewritten_article['title']
               )
               
               # Post to WordPress
               result = self.wp_api.create_news_post(
                   rewritten_article['title'], 
                   rewritten_article['content'], 
                   status='publish',
                   categories=['Cannabis News'],
                   tags=rewritten_article['tags'],
                   featured_image_id=featured_image_id,
                   author_name='kaleb'
               )
               
               if result:
                   print(f"✅ Posted Canadian cannabis news: {rewritten_article['title']}")
                   print(f"Category: {rewritten_article['category']}, Tags: {', '.join(rewritten_article['tags'])}")
                   if featured_image_id:
                       print(f"✅ Added featured image: {featured_image_id}")
                   
                   # Update tracking with WordPress post ID
                   if 'original_url' in rewritten_article:
                       self.canadian_processor.article_tracker.update_wordpress_id(
                           rewritten_article['original_url'], 
                           result.get('id')
                       )
                   return True
               else:
                   print("❌ Failed to post Canadian cannabis news")
                   return False
           else:
               print("No Canadian cannabis articles found")
               return False
               
       except Exception as e:
           print(f"❌ Error posting Canadian cannabis content: {e}")
           import traceback
           traceback.print_exc()
           return False

# Test functions for manual testing
def test_news_setup():
   print("Testing cannabis NEWS setup...")
   automation = ContentAutomation()
   
   # Test WordPress connection with news post type
   print("Testing WordPress API and News post type...")
   if automation.wp_api.test_news_endpoint():
       print("✅ News post type endpoint found!")
       return automation.post_us_news_content()
   else:
       print("❌ News post type endpoint not found")
       return False

def test_canadian_news_setup():
    print("Testing Canadian cannabis NEWS setup...")
    automation = ContentAutomation()
    return automation.post_canadian_news_content()

def test_mixed_news_content():
    print("Testing mixed US and Canadian news content...")
    automation = ContentAutomation()
    
    # Test US news
    print("\n=== Testing US Cannabis News ===")
    us_success = automation.post_us_news_content()
    
    # Test Canadian news  
    print("\n=== Testing Canadian Cannabis News ===")
    can_success = automation.post_canadian_news_content()
    
    return us_success or can_success

# Command line automation functions
def post_us_news():
    """Post a single US news article - for cron scheduling"""
    print(f"=== SCHEDULED US NEWS POST - {datetime.now()} ===")
    automation = ContentAutomation()
    success = automation.post_us_news_content()
    if success:
        print("✅ US news post completed successfully")
    else:
        print("❌ US news post failed")
        sys.exit(1)

def post_us_news_2():
    """Post a single US news 2 article - for cron scheduling"""
    print(f"=== SCHEDULED US NEWS 2 POST - {datetime.now()} ===")
    automation = ContentAutomation()
    success = automation.post_us_news_content_2()
    if success:
        print("✅ US news 2 post completed successfully")
    else:
        print("❌ US news 2 post failed")
        sys.exit(1)

def post_canadian_news():
    """Post a single Canadian news article - for cron scheduling"""
    print(f"=== SCHEDULED CANADIAN NEWS POST - {datetime.now()} ===")
    automation = ContentAutomation()
    success = automation.post_canadian_news_content()
    if success:
        print("✅ Canadian news post completed successfully")
    else:
        print("❌ Canadian news post failed")
        sys.exit(1)

if __name__ == "__main__":
   # Check for command line arguments for automated scheduling
   if len(sys.argv) > 1:
       command = sys.argv[1]
       
       if command == "post_us":
           post_us_news()
       elif command == "post_us_2":
           post_us_news_2()
       elif command == "post_canadian":
           post_canadian_news()
       elif command == "test_us":
           test_news_setup()
       elif command == "test_canadian":
           test_canadian_news_setup()
       elif command == "test_mixed":
           test_mixed_news_content()
       else:
           print(f"Unknown command: {command}")
           print("Available commands:")
           print("  python main.py post_us")
           print("  python main.py post_us_2")
           print("  python main.py post_canadian") 
           print("  python main.py test_us")
           print("  python main.py test_canadian")
           print("  python main.py test_mixed")
           sys.exit(1)
   else:
       # Interactive menu for manual testing
       print("Cannabis Content Automation")
       print("1. Test US news setup")
       print("2. Test Canadian news setup") 
       print("3. Test mixed news content")
       print("4. Post single US news article")
       print("5. Post single Canadian news article")
       
       choice = input("Choose option (1-5): ")
       
       if choice == "1":
           test_news_setup()
       elif choice == "2":
           test_canadian_news_setup()
       elif choice == "3":
           test_mixed_news_content()
       elif choice == "4":
           post_us_news()
       elif choice == "5":
           post_canadian_news()
       else:
           print("Invalid choice")

