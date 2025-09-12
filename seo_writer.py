from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

class SEOWriter:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def write_seo_article(self, structure, keywords, word_count):
        prompt = f"""
        Write an SEO-optimized article following these specifications:
        
        Structure: {structure}
        Target Keywords: {keywords}
        Word Count: {word_count} words
        
        Requirements:
        - Natural keyword integration (avoid keyword stuffing)
        - Engaging, valuable content for readers
        - Clear headings and subheadings
        - Include relevant examples and actionable advice
        - Write in a conversational, authoritative tone
        
        Format the response with proper HTML headings (h2, h3) and paragraphs.
        """
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text