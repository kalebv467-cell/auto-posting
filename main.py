import schedule
import time
from datetime import datetime
from news_processor import CannabisNewsProcessor
from canadian_news_processor import CanadianNewsProcessor
from seo_writer import SEOWriter
from wordpress_api import WordPressAPI
from image_manager import ImageManager
from seo_file_processor import SEOFileProcessor
from config import POSTING_HOURS

class ContentAutomation:
   def __init__(self):
       self.wp_api = WordPressAPI()
       self.news_processor = CannabisNewsProcessor()
       self.canadian_processor = CanadianNewsProcessor()
       self.seo_writer = SEOWriter()
       self.image_manager = ImageManager()
       self.seo_file_processor = SEOFileProcessor()
       self.daily_news_count = 0
   
   def post_news_content(self):
       if self.daily_news_count >= 5:
           print("Daily news limit reached")
           return
           
       try:
           rewritten_article = self.news_processor.get_cannabis_article()
           if rewritten_article:
               # Get featured image
               featured_image_id = self.image_manager.get_featured_image_for_article(
                   rewritten_article['category'], 
                   rewritten_article['title']
               )
               
               # Use create_news_post for news articles with updated tags structure
               result = self.wp_api.create_news_post(
                   rewritten_article['title'], 
                   rewritten_article['content'], 
                   status='publish',  # Changed from draft to publish
                   categories=['Cannabis News'],
                   tags=rewritten_article['tags'],  # Now uses tags array instead of single tag
                   featured_image_id=featured_image_id,
                   author_name='rohan'  # Added author
               )
               if result:
                   self.daily_news_count += 1
                   print(f"Posted cannabis news: {rewritten_article['title']}")
                   print(f"Category: {rewritten_article['category']}, Tags: {', '.join(rewritten_article['tags'])}")
                   if featured_image_id:
                       print(f"✓ Added featured image: {featured_image_id}")
                   
                   # Update tracking with WordPress post ID
                   if 'original_url' in rewritten_article:
                       self.news_processor.article_tracker.update_wordpress_id(
                           rewritten_article['original_url'], 
                           result.get('id')
                       )
       except Exception as e:
           print(f"Error posting cannabis content: {e}")

   def post_canadian_news_content(self):
       """Post Canadian cannabis news content"""
       if self.daily_news_count >= 5:
           print("Daily news limit reached")
           return
           
       try:
           rewritten_article = self.canadian_processor.get_canadian_article()
           if rewritten_article:
               # Get featured image
               featured_image_id = self.image_manager.get_featured_image_for_article(
                   'canadian', 
                   rewritten_article['title']
               )
               
               # Use create_news_post for Canadian news articles
               result = self.wp_api.create_news_post(
                   rewritten_article['title'], 
                   rewritten_article['content'], 
                   status='publish',  # Changed from draft to publish
                   categories=['Cannabis News'],
                   tags=rewritten_article['tags'],  # Already uses tags array
                   featured_image_id=featured_image_id,
                   author_name='kaleb'  # Added author (lowercase)
               )
               if result:
                   self.daily_news_count += 1
                   print(f"Posted Canadian cannabis news: {rewritten_article['title']}")
                   print(f"Category: {rewritten_article['category']}, Tags: {', '.join(rewritten_article['tags'])}")
                   if featured_image_id:
                       print(f"✓ Added featured image: {featured_image_id}")
                   
                   # Update tracking with WordPress post ID
                   if 'original_url' in rewritten_article:
                       self.canadian_processor.article_tracker.update_wordpress_id(
                           rewritten_article['original_url'], 
                           result.get('id')
                       )
       except Exception as e:
           print(f"Error posting Canadian content: {e}")
   
   def reset_daily_counter(self):
       self.daily_news_count = 0
       print("Daily counter reset")
   
   def post_seo_content(self, structure, keywords, word_count):
       try:
           content = self.seo_writer.write_seo_article(structure, keywords, word_count)
           
           # Extract title from content
           lines = content.split('\n')
           title = lines[0].replace('#', '').strip() if lines else "SEO Article"
           
           # Get featured image for SEO articles
           featured_image_id = self.image_manager.get_featured_image_for_article('lifestyle', title)
           
           # Use cannabis-lifestyle post type for SEO articles
           result = self.wp_api.create_cannabis_lifestyle_post(
               title, 
               content, 
               status='draft',
               categories=['Cannabis Lifestyle'],
               tags=['seo', 'cannabis-lifestyle'],
               featured_image_id=featured_image_id
           )
           if result:
               print(f"Posted cannabis lifestyle article: {title}")
               if featured_image_id:
                   print(f"✓ Added featured image: {featured_image_id}")
       except Exception as e:
           print(f"Error posting SEO content: {e}")

# Test function - NEWS ONLY
def test_news_setup():
   print("Testing cannabis NEWS setup...")
   automation = ContentAutomation()
   
   # Test WordPress connection with news post type ONLY
   print("Testing WordPress API and News post type...")
   if automation.wp_api.test_news_endpoint():
       print("✓ News post type endpoint found!")
       result = automation.wp_api.create_news_post("Test News Post", "This is a test news article", status='draft')
       if result:
           print("✓ News post creation working!")
       else:
           print("✗ News post creation failed")
           return False
   else:
       print("✗ News post type endpoint not found")
       return False
   
   # Test cannabis news processing
   print("Testing cannabis news processing...")
   try:
       article = automation.news_processor.get_cannabis_article()
       if article:
           print(f"✓ Successfully processed cannabis article: {article['title'][:50]}...")
           print(f"✓ Category: {article['category']}, Tags: {', '.join(article['tags'])}")
           
           # Get featured image
           print("Getting featured image...")
           featured_image_id = automation.image_manager.get_featured_image_for_article(
               article['category'], 
               article['title']
           )
           
           # NOW ACTUALLY POST IT TO WORDPRESS
           print("Posting article to WordPress...")
           result = automation.wp_api.create_news_post(
               article['title'],
               article['content'],
               status='publish',
               categories=['Cannabis News'],
               tags=article['tags'],  # Updated to use tags array
               featured_image_id=featured_image_id,
               author_name='rohan'  # Fixed - added comma and author
           )
           
           if result:
               print(f"✓ Posted cannabis article with ID: {result.get('id')}")
               print(f"✓ Tags applied: {', '.join(article['tags'])}")
               if featured_image_id:
                   print(f"✓ Added featured image: {featured_image_id}")
               print(f"✓ Check your WordPress News section!")
           else:
               print("✗ Failed to post cannabis article")
       else:
           print("✗ No cannabis articles found")
   except Exception as e:
       print(f"✗ Error processing cannabis news: {e}")
       import traceback
       traceback.print_exc()
   
   return True

# Test function - LIFESTYLE ONLY  
def test_lifestyle_setup():
   print("Testing cannabis LIFESTYLE setup...")
   automation = ContentAutomation()
   
   # Test cannabis-lifestyle post type
   print("Testing Cannabis Lifestyle post type...")
   if automation.wp_api.test_cannabis_lifestyle_endpoint():
       print("✓ Cannabis Lifestyle post type endpoint found!")
       
       # Get featured image for test
       featured_image_id = automation.image_manager.get_featured_image_for_article('lifestyle', 'Test Lifestyle Post')
       
       result = automation.wp_api.create_cannabis_lifestyle_post(
           "Test Lifestyle Post", 
           "This is a test lifestyle article", 
           status='draft',
           featured_image_id=featured_image_id
       )
       if result:
           print("✓ Cannabis Lifestyle post creation working!")
           if featured_image_id:
               print(f"✓ Added featured image: {featured_image_id}")
       else:
           print("✗ Cannabis Lifestyle post creation failed")
   else:
       print("✗ Cannabis Lifestyle post type endpoint not found")
   
   return True

# For manual SEO posting
def post_seo_manually():
   automation = ContentAutomation()
   
   print("Enter your SEO article details:")
   structure = input("Structure/outline: ")
   keywords = input("Keywords (comma-separated): ")
   word_count = input("Word count: ")
   
   automation.post_seo_content(structure, keywords, int(word_count))

# For SEO file processing
def process_seo_file():
   automation = ContentAutomation()
   success = automation.seo_file_processor.post_seo_article()
   
   if not success:
       print("\nWould you like to create a sample SEO file template?")
       choice = input("Enter 'y' for yes: ").lower()
       if choice == 'y':
           automation.seo_file_processor.create_sample_file()

# Test function - CANADIAN NEWS
def test_canadian_news_setup():
    print("Testing Canadian cannabis NEWS setup...")
    automation = ContentAutomation()
    
    # Test Canadian news processing
    print("Testing Canadian cannabis news processing...")
    try:
        article = automation.canadian_processor.get_canadian_article()
        if article:
            print(f"✓ Successfully processed Canadian article: {article['title'][:50]}...")
            print(f"✓ Category: {article['category']}, Tags: {', '.join(article['tags'])}")
            
            # Get featured image
            print("Getting featured image for Canadian article...")
            featured_image_id = automation.image_manager.get_featured_image_for_article(
                'canadian', 
                article['title']
            )
            
            # Post to WordPress
            print("Posting Canadian article to WordPress...")
            result = automation.wp_api.create_news_post(
                article['title'],
                article['content'],
                status='publish',  # Changed to publish
                categories=['Cannabis News'],
                tags=article['tags'],  # Already uses tags array
                featured_image_id=featured_image_id,
                author_name='kaleb'  # Set author to kaleb (lowercase)
            )
            
            if result:
                print(f"✓ Posted Canadian article with ID: {result.get('id')}")
                print(f"✓ Tags: {', '.join(article['tags'])}")
                if featured_image_id:
                    print(f"✓ Added featured image: {featured_image_id}")
                print(f"✓ Check your WordPress News section!")
            else:
                print("✗ Failed to post Canadian article")
        else:
            print("✗ No Canadian articles found")
    except Exception as e:
        print(f"✗ Error processing Canadian news: {e}")
        import traceback
        traceback.print_exc()
    
    return True

# Test function for image functionality
def test_image_system():
   print("Testing image system...")
   automation = ContentAutomation()
   
   # Test image manager
   print("Testing image manager...")
   try:
       # Test getting images for different categories
       for category in ['politics', 'business', 'culture', 'lifestyle', 'canadian']:
           image_id = automation.image_manager.get_featured_image_for_article(category, f"Test {category} Article")
           if image_id:
               print(f"✓ Got image for {category}: {image_id}")
           else:
               print(f"✗ No image found for {category}")
   except Exception as e:
       print(f"✗ Error testing image system: {e}")
       import traceback
       traceback.print_exc()

# Test both US and Canadian news together
def test_mixed_news_content():
    print("Testing mixed US and Canadian news content...")
    automation = ContentAutomation()
    
    # Test US news
    print("\n=== Testing US Cannabis News ===")
    try:
        us_article = automation.news_processor.get_cannabis_article()
        if us_article:
            print(f"✓ US Article: {us_article['title'][:50]}...")
            print(f"✓ US Tags: {', '.join(us_article['tags'])}")
        else:
            print("✗ No US articles found")
    except Exception as e:
        print(f"✗ Error with US news: {e}")
    
    # Test Canadian news
    print("\n=== Testing Canadian Cannabis News ===")
    try:
        can_article = automation.canadian_processor.get_canadian_article()
        if can_article:
            print(f"✓ Canadian Article: {can_article['title'][:50]}...")
            print(f"✓ Canadian Tags: {', '.join(can_article['tags'])}")
        else:
            print("✗ No Canadian articles found")
    except Exception as e:
        print(f"✗ Error with Canadian news: {e}")

if __name__ == "__main__":
   print("Cannabis Content Automation")
   print("1. Test news setup")
   print("2. Test lifestyle setup") 
   print("3. Post SEO article manually")
   print("4. Process SEO article from file")
   print("5. Test Canadian news setup")
   print("6. Test image system")
   print("7. Test mixed news content")
   print("8. Start automation")
   
   choice = input("Choose option (1-8): ")
   
   if choice == "1":
       test_news_setup()
   elif choice == "2":
       test_lifestyle_setup()
   elif choice == "3":
       post_seo_manually()
   elif choice == "4":
       process_seo_file()
   elif choice == "5":
       test_canadian_news_setup()
   elif choice == "6":
       test_image_system()
   elif choice == "7":
       test_mixed_news_content()
   elif choice == "8":
       # Set up automation
       automation = ContentAutomation()
       
       # Schedule news posts (mix US and Canadian)
       for hour in POSTING_HOURS:
           schedule.every().day.at(f"{hour:02d}:00").do(automation.post_news_content)
           # Optionally add Canadian news posting on different schedule
           # schedule.every().day.at(f"{hour:02d}:30").do(automation.post_canadian_news_content)
       
       # Reset counter at midnight
       schedule.every().day.at("00:01").do(automation.reset_daily_counter)
       
       print("Cannabis content automation started...")
       print("Press Ctrl+C to stop")
       
       try:
           while True:
               schedule.run_pending()
               time.sleep(60)  # Check every minute
       except KeyboardInterrupt:
           print("\nAutomation stopped.")