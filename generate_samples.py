import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

PLATFORM_CHAR_LIMITS = {
    'instagram': 2200,
    'twitter': 280,
    'linkedin': 3000,
    'facebook': 63206,
    'tiktok': 150,
    'general': 1000
}

def generate_platform_content(topic, platform, tone):
    char_limit = PLATFORM_CHAR_LIMITS.get(platform, PLATFORM_CHAR_LIMITS['general'])
    
    prompt = f'''
You are an expert content creator or copywriter. Generate an engaging article/post on "{topic}".

Context:
- Target audience: {platform}
- Purpose: educate, inform, and engage
- Style: {tone}

Structure:
- Start with a catchy hook or headline.
- Use a story-like, narrative style to explore the topic in a way that is engaging and accessible for both techies and non-techies.
- Organize the post into 3-5 engaging, descriptive sections or paragraphs, each exploring different aspects, tips, or angles of the topic. Use natural transitions and only use headings if they fit the story. Do not explicitly label sections as 'introduction', 'conclusion', or use numbered sections.
- End with a memorable takeaway or call to action (if any).

Tone & Style:
- Use storytelling, relatable examples, and vivid language to make the topic enjoyable and easy to understand for all readers.
- Use simple, clear language. Avoid overly AI‑sounding or polished phrases.
- Maintain conversational flow, vary sentence length, sprinkle rhetorical questions or surprises for "burstiness" and engagement.

Mentions:
- You must mention at least 2 influential people (real or hypothetical, relevant to the topic and platform) in the post, and each mention must start with '@' (e.g., @elonmusk, @sundarpichai, @tim_cook, etc). More than 2 mentions are allowed if relevant.
- Choose the most relevant influential people for the topic (e.g., Sundar Pichai, Elon Musk, Tim Cook, Larry Page, Satya Nadella, Sheryl Sandberg, Mark Zuckerberg, etc).

Hashtags:
- All hashtags must be placed together at the end of the post, not within the content.
- Hashtags must be highly relevant to the topic only (not the platform or generic tags).
- You must include hashtags as instructed. Do not skip this step.

Constraints:
- Each section ≈ 80–120 words
- Don't use jargon unless you define it
- Avoid vague statements; be specific
- IMPORTANT: The entire post, including headings, content, and hashtags, must be no longer than {char_limit} characters. Do not exceed this limit. Finish your story or post naturally within this space.

After the content, add a line starting with 'Hashtags:' followed by hashtags that are highly relevant to the topic only, with #, space-separated. For Twitter, use only 3-4 hashtags. For other platforms, use up to 10 hashtags. Do not repeat hashtags from previous posts in the series.
'''

    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY and AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_API_VERSION:
        url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_KEY
        }
        body = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.9
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            if response.status_code == 200:
                data = response.json()
                fullText = data["choices"][0]["message"]["content"].strip()
                
                # Parse content and hashtags
                content = fullText
                hashtags = ''
                hashtagMatch = re.search(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', fullText, re.IGNORECASE)
                if hashtagMatch:
                    hashtags = hashtagMatch.group(1).strip()
                    content = re.sub(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', '', content, flags=re.IGNORECASE).strip()
                else:
                    lines = fullText.split('\n')
                    lastLine = lines[-1]
                    if lastLine.count('#') >= 2:
                        hashtags = lastLine.strip()
                        content = '\n'.join(lines[:-1]).strip()
                
                # Remove markdown
                content = content.replace('**', '').replace('*', '')
                
                # Check total length
                combined = (content + ' ' + hashtags).strip()
                
                return {
                    'platform': platform,
                    'char_limit': char_limit,
                    'content': content,
                    'hashtags': hashtags,
                    'total_chars': len(combined),
                    'within_limit': len(combined) <= char_limit
                }
            else:
                return None
        except Exception as e:
            print(f"Error generating content for {platform}: {e}")
            return None
    else:
        print("API credentials not found. Please check your .env file.")
        return None

def generate_all_platform_samples():
    topic = "Artificial Intelligence"
    tone = "professional"
    
    platforms = ['instagram', 'twitter', 'linkedin', 'facebook', 'tiktok', 'general']
    
    print("🚀 GENERATING SAMPLE CONTENT FOR ALL PLATFORMS")
    print("=" * 80)
    print(f"Topic: {topic}")
    print(f"Tone: {tone}")
    print("=" * 80)
    
    for platform in platforms:
        print(f"\n📱 {platform.upper()}")
        print("-" * 40)
        
        result = generate_platform_content(topic, platform, tone)
        
        if result:
            print(f"Character Limit: {result['char_limit']}")
            print(f"Total Characters: {result['total_chars']}")
            print(f"Within Limit: {'✅' if result['within_limit'] else '❌'}")
            print(f"\n📝 CONTENT:")
            print(result['content'])
            print(f"\n🏷️  HASHTAGS:")
            print(result['hashtags'])
            print(f"\n📊 STATS:")
            print(f"Content chars: {len(result['content'])}")
            print(f"Hashtags chars: {len(result['hashtags'])}")
            print(f"Combined chars: {result['total_chars']}")
            print(f"Remaining: {result['char_limit'] - result['total_chars']}")
        else:
            print("❌ Failed to generate content")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    generate_all_platform_samples() 