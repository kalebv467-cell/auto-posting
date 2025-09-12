import os
import re
from wordpress_api import WordPressAPI
from image_manager import ImageManager
from internal_linking import InternalLinking
from external_linking import ExternalLinking

class SEOFileProcessor:
    def __init__(self):
        self.wp_api = WordPressAPI()
        self.image_manager = ImageManager()
        self.internal_linking = InternalLinking()
        self.external_linking = ExternalLinking()
        self.seo_file = "SEO_Article.txt"
    
    def read_seo_file(self):
        """Read and parse the SEO article file"""
        if not os.path.exists(self.seo_file):
            print(f"SEO file not found: {self.seo_file}")
            return None
        
        try:
            with open(self.seo_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                print("SEO file is empty")
                return None
            
            # Parse the file content
            parsed = self.parse_seo_content(content)
            if parsed:
                print(f"✓ Successfully parsed SEO file")
                print(f"  Title: {parsed['title']}")
                print(f"  Categories: {parsed['categories']}")
                print(f"  Tags: {parsed['tags']}")
                print(f"  Content length: {len(parsed['content'])} characters")
                return parsed
            else:
                print("✗ Failed to parse SEO file - check format")
                return None
                
        except Exception as e:
            print(f"Error reading SEO file: {e}")
            return None
    
    def parse_seo_content(self, content):
        """Parse the SEO file content to extract title, URL, categories, tags, and content"""
        lines = content.split('\n')
        
        title = ""
        url = ""
        categories = []
        tags = []
        article_content = ""
        
        content_started = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('URL:'):
                url = line.replace('URL:', '').strip()
            elif line.startswith('CATEGORIES:'):
                cats = line.replace('CATEGORIES:', '').strip()
                categories = [cat.strip() for cat in cats.split(',') if cat.strip()]
            elif line.startswith('TAGS:'):
                tags_str = line.replace('TAGS:', '').strip()
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            elif line.startswith('CONTENT:'):
                article_content = line.replace('CONTENT:', '').strip()
                content_started = True
            elif content_started and line:
                article_content += "\n" + line
        
        # Validation
        if not title:
            print("✗ No title found in SEO file")
            return None
        
        if not article_content:
            print("✗ No content found in SEO file")
            return None
        
        # Set defaults if not provided
        if not categories:
            categories = ['Cannabis Lifestyle']
        
        if not tags:
            tags = ['seo', 'cannabis-lifestyle']
        
        return {
            'title': title,
            'url': url,
            'categories': categories,
            'tags': tags,
            'content': article_content.strip()
        }
    
    def add_linking_to_seo_content(self, seo_data):
        """Add internal and external linking to SEO content"""
        print("=== ADDING LINKS TO SEO CONTENT ===")
        
        content = seo_data['content']
        title = seo_data['title']
        
        # Step 1: Add internal links
        print("Adding internal links...")
        content = self.internal_linking.add_internal_links(content, title)
        
        # Step 2: Find external sources with Claude
        print("Finding external sources...")
        external_sources = self.external_linking.find_additional_sources(
            content, 
            title, 
            0  # Start with 0 existing links, try to find 1-3
        )
        
        # Step 3: Add external links if found
        if external_sources:
            print("Adding external links...")
            content = self.external_linking.add_external_links_to_content(
                content, 
                external_sources
            )
        else:
            print("No external sources found or added")
        
        # Update the content in seo_data
        seo_data['content'] = content
        return seo_data
    
    def post_seo_article(self):
        """Read SEO file and post to WordPress"""
        print("=== PROCESSING SEO ARTICLE FROM FILE ===")
        
        # Read and parse the file
        seo_data = self.read_seo_file()
        if not seo_data:
            return False
        
        try:
            # Add internal and external linking
            seo_data = self.add_linking_to_seo_content(seo_data)
            
            # Get featured image
            print("Getting featured image...")
            featured_image_id = self.image_manager.get_featured_image_for_article(
                'lifestyle', 
                seo_data['title']
            )
            
            # Post to WordPress
            print("Posting to WordPress...")
            result = self.wp_api.create_cannabis_lifestyle_post(
                seo_data['title'],
                seo_data['content'],
                status='draft',  # Start as draft for review
                categories=seo_data['categories'],
                tags=seo_data['tags'],
                featured_image_id=featured_image_id
            )
            
            if result:
                post_id = result.get('id')
                post_url = result.get('link', 'N/A')
                
                print(f"✓ Successfully posted SEO article!")
                print(f"  WordPress Post ID: {post_id}")
                print(f"  WordPress URL: {post_url}")
                print(f"  Title: {seo_data['title']}")
                print(f"  Categories: {', '.join(seo_data['categories'])}")
                print(f"  Tags: {', '.join(seo_data['tags'])}")
                
                if featured_image_id:
                    print(f"  Featured Image ID: {featured_image_id}")
                
                # Archive the processed file
                self.archive_processed_file()
                
                return True
            else:
                print("✗ Failed to post SEO article to WordPress")
                return False
                
        except Exception as e:
            print(f"Error posting SEO article: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def archive_processed_file(self):
        """Archive the processed SEO file"""
        try:
            if os.path.exists(self.seo_file):
                # Create archive filename with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"SEO_Article_processed_{timestamp}.txt"
                
                # Create archives folder if it doesn't exist
                if not os.path.exists('archives'):
                    os.makedirs('archives')
                
                # Move file to archives
                archive_path = os.path.join('archives', archive_name)
                os.rename(self.seo_file, archive_path)
                
                print(f"✓ Archived processed file to: {archive_path}")
                
        except Exception as e:
            print(f"Warning: Could not archive file: {e}")
    
    def create_sample_file(self):
        """Create a sample SEO article file for reference"""
        sample_content = """TITLE: The Ultimate Guide to Cannabis Terpenes and Their Effects
URL: https://budscannacorner.ca/cannabis-lifestyle/ultimate-guide-cannabis-terpenes-effects/
CATEGORIES: Cannabis Lifestyle, Education
TAGS: terpenes, cannabis education, effects, guide
CONTENT: <h2>Understanding Cannabis Terpenes</h2>

<p>Cannabis terpenes are aromatic compounds that give different cannabis strains their unique scents and flavors. But these compounds do much more than just provide pleasant aromas - they play a crucial role in the overall effects and therapeutic benefits of cannabis.</p>

<h2>The Most Common Cannabis Terpenes</h2>

<h3>Myrcene</h3>
<p>Myrcene is one of the most abundant terpenes in cannabis and is known for its sedating effects. This terpene is also found in mangoes, hops, and lemongrass.</p>

<h3>Limonene</h3>
<p>Limonene provides citrusy aromas and is associated with elevated mood and stress relief. It's commonly found in citrus fruit peels.</p>

<h3>Pinene</h3>
<p>As the name suggests, pinene has a pine-like aroma and may help with alertness and memory retention.</p>

<h2>How Terpenes Work with Cannabinoids</h2>

<p>The interaction between terpenes and cannabinoids creates what's known as the "entourage effect." This synergistic relationship can enhance or modify the effects of THC and CBD, creating a more nuanced and potentially therapeutic experience.</p>

<h2>Understanding THC and CBD</h2>

<p>While THC is the psychoactive compound in cannabis, CBD offers therapeutic benefits without the high. Both work together with terpenes in sativa and indica strains to create unique effects.</p>

<h2>Choosing Strains Based on Terpenes</h2>

<p>Understanding terpene profiles can help you select cannabis products that align with your desired effects, whether you're seeking relaxation, energy, focus, or pain relief.</p>"""
        
        try:
            with open('SEO_Article_SAMPLE.txt', 'w', encoding='utf-8') as f:
                f.write(sample_content)
            print(f"✓ Created sample file: SEO_Article_SAMPLE.txt")
            print("Use this as a template for your SEO articles!")
            print("\nNOTE: The sample includes keywords like 'THC', 'CBD', 'sativa', 'indica'")
            print("that will automatically get internal links when processed!")
        except Exception as e:
            print(f"Error creating sample file: {e}")