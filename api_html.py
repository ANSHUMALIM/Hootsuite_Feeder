from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
import os
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import csv
import io

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Social Media Post Generator</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #fffbe6 0%, #fffde4 100%);
            padding: 40px;
            min-height: 100vh;
        }
        .container {
            background: #fffbe6;
            border-radius: 18px;
            padding: 36px 32px 32px 32px;
            max-width: 800px;
            margin: 40px auto 0 auto;
            box-shadow: 0 4px 32px #ffe06699, 0 1.5px 8px #fffde4;
        }
        h2 {
            text-align: center;
            color: #ffb300;
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: 1px;
            margin-bottom: 28px;
            text-shadow: 0 2px 8px #fffde4;
        }
        .form-group { margin-bottom: 22px; }
        label { font-weight: 600; color: #b38f00; }
        input, select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1.5px solid #ffe066;
            background: #fffde4;
            font-size: 1em;
            margin-top: 4px;
            margin-bottom: 2px;
            transition: border 0.2s, box-shadow 0.2s;
        }
        input:focus, select:focus {
            border: 1.5px solid #ffd600;
            outline: none;
            box-shadow: 0 0 0 2px #fffde4;
        }
        .btn {
            background: linear-gradient(90deg, #ffd600 0%, #fff176 100%);
            color: #b38f00;
            border: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px #ffe06699;
            transition: background 0.2s, box-shadow 0.2s;
            margin-top: 8px;
        }
        .btn:hover {
            background: linear-gradient(90deg, #fff176 0%, #ffd600 100%);
            box-shadow: 0 4px 16px #ffe066cc;
        }
        .csv-btn {
            margin-top: 15px;
            background: linear-gradient(90deg, #fffde4 0%, #ffe066 100%);
            color: #b38f00;
            border: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px #ffe06699;
            transition: background 0.2s, box-shadow 0.2s;
        }
        .csv-btn:hover {
            background: linear-gradient(90deg, #ffe066 0%, #fffde4 100%);
            box-shadow: 0 4px 16px #ffe066cc;
        }
        .posts {
            margin-top: 36px;
        }
        .table-container {
            overflow-x: auto;
            border-radius: 14px;
            box-shadow: 0 2px 12px #ffe06655;
            background: #fffde4;
            margin-bottom: 10px;
        }
        .styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 14px;
            overflow: hidden;
        }
        .styled-table th, .styled-table td {
            padding: 12px 10px;
            border-bottom: 1px solid #ffe066;
        }
        .styled-table th {
            background: #fff9c4;
            color: #b38f00;
            font-weight: 700;
        }
        .styled-table tr:nth-child(even) {
            background: #fffde4;
        }
        .styled-table tr:hover {
            background: #fff9c4;
            transition: background 0.2s;
        }
        .edit-input, .edit-textarea {
            background: #fffbe6;
            border: 1.5px solid #ffe066;
            border-radius: 6px;
            padding: 4px 6px;
            font-size: 1em;
            width: 100%;
            box-sizing: border-box;
            margin: 0;
            resize: vertical;
            min-height: 32px;
            max-height: 120px;
            transition: border 0.2s, box-shadow 0.2s;
            vertical-align: middle;
            display: block;
            color: #b38f00;
        }
        .edit-input:focus, .edit-textarea:focus {
            border: 1.5px solid #ffd600;
            box-shadow: 0 0 0 2px #fffde4;
            outline: none;
        }
        .hashtags { color: #ffb300; font-weight: 600; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .results-list {
            display: flex;
            flex-direction: column;
            gap: 24px;
            margin-bottom: 10px;
        }
        .result-card {
            background: #fffde4;
            border-radius: 14px;
            box-shadow: 0 2px 12px #ffe06655;
            padding: 20px 18px 16px 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            border: 1.5px solid #ffe066;
        }
        .result-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .result-content label, .result-hashtags label {
            font-weight: 600;
            color: #b38f00;
            margin-bottom: 4px;
            display: block;
        }
        .result-content textarea {
            min-height: 120px !important;
        }
        .result-hashtags textarea {
            margin-top: 2px;
        }
        .post-number {
            font-weight: 700;
            color: #ffb300;
            font-size: 1.1em;
            margin-bottom: 6px;
            letter-spacing: 1px;
        }
        .poll-question {
            background: linear-gradient(135deg, #fff9c4 0%, #fffde4 100%);
            border: 2px solid #ffe066;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            position: relative;
            overflow: hidden;
            animation: pollSlideIn 0.6s ease-out;
        }
        .poll-question::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 214, 0, 0.3), transparent);
            animation: pollShine 2s infinite;
        }
        .poll-option {
            background: #fffbe6;
            border: 1.5px solid #ffe066;
            border-radius: 8px;
            padding: 10px 14px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .poll-option:hover {
            background: #fff9c4;
            border-color: #ffd600;
            transform: translateX(8px);
            box-shadow: 0 4px 12px #ffe06699;
        }
        .poll-option::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 214, 0, 0.2);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.3s, height 0.3s;
        }
        .poll-option:hover::after {
            width: 100%;
            height: 100%;
        }
        @keyframes pollSlideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes pollShine {
            0% { left: -100%; }
            50% { left: 100%; }
            100% { left: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Social Media Post Generator</h2>
        <form method="post">
            <div class="form-group">
                <label>Topic:</label>
                <input type="text" name="topic" required>
            </div>
            <div class="form-group">
                <label>Platform:</label>
                <select name="platform">
                    <option value="general">General</option>
                    <option value="instagram">Instagram</option>
                    <option value="twitter">Twitter/X</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="facebook">Facebook</option>
                    <option value="tiktok">TikTok</option>
                </select>
            </div>
            <div class="form-group">
                <label>Tone:</label>
                <select name="tone">
                    <option value="professional">Professional</option>
                    <option value="casual">Casual & Friendly</option>
                    <option value="educational">Educational</option>
                    <option value="inspirational">Inspirational</option>
                    <option value="humorous">Humorous</option>
                </select>
            </div>
            <div class="form-group">
                <label>Number of Posts:</label>
                <input type="number" name="postCount" min="1" max="50" value="3" required>
            </div>
            <div class="form-group">
                <label>Base Date:</label>
                <input type="date" name="baseDate" required value="{{ base_date|default('') }}">
            </div>
            <div class="form-group">
                <label>Base Time:</label>
                <input type="time" name="baseTime" required value="{{ base_time|default('09:00') }}">
            </div>
            <div class="form-group">
                <label>Time Distribution:</label>
                <select name="timeOption" id="timeOption" onchange="document.getElementById('intervalGroup').style.display = this.value === 'different' ? 'block' : 'none';">
                    <option value="same">Same time for all posts</option>
                    <option value="different">Different times (daily intervals)</option>
                </select>
            </div>
            <div class="form-group" id="intervalGroup" style="display: none;">
                <label>Interval between posts:</label>
                <select name="interval">
                    <option value="1">Daily (1 day apart)</option>
                    <option value="2">Every 2 days</option>
                    <option value="3">Every 3 days</option>
                    <option value="7">Weekly (7 days apart)</option>
                </select>
            </div>
            <button class="btn" id="generateBtn" type="submit">
                <span id="spinner" style="display:none;vertical-align:middle;margin-right:8px;width:18px;height:18px;border:3px solid #fff;border-radius:50%;border-top:3px solid #ffd600;animation:spin 1s linear infinite;"></span>
                <span id="btnText">Generate Posts</span>
            </button>
        </form>
        {% if posts %}
        <div class="posts">
            <h3>Generated Posts</h3>
            <form method="post">
                <input type="hidden" name="edit" value="1">
                <div class="results-list">
                    {% for post in posts %}
                    <div class="result-card">
                        <div class="post-number">Post {{ loop.index }}</div>
                        <div class="result-row">
                            <label>Date:</label>
                            <input type="date" name="date_{{ loop.index0 }}" value="{{ post.date }}" required class="edit-input" style="max-width: 140px;">
                            <label style="margin-left:16px;">Time:</label>
                            <input type="time" name="time_{{ loop.index0 }}" value="{{ post.time }}" required class="edit-input" style="max-width: 100px;">
                        </div>
                        <div class="result-content">
                            <label>Content:</label>
                            <textarea name="content_{{ loop.index0 }}" class="edit-textarea" style="min-height:60px;white-space:pre-line;">{{ post.content }}</textarea>
                        </div>
                        <div class="result-hashtags">
                            <label>Hashtags:</label>
                            <textarea name="hashtags_{{ loop.index0 }}" class="edit-textarea" style="min-height:30px;">{{ post.hashtags }}</textarea>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <button class="btn" type="submit" style="margin-top:16px;">Save Changes</button>
            </form>
            <form method="get" action="{{ url_for('download_csv') }}" style="margin-top:24px;">
                <button class="csv-btn" type="submit" title="Download as CSV">
                    <span style="vertical-align:middle;margin-right:8px;">&#128190;</span> Download CSV
                </button>
            </form>
        </div>
        {% endif %}
    </div>
    <script>
        // Set interval group visibility on page load
        window.onload = function() {
            var timeOption = document.getElementById('timeOption');
            var intervalGroup = document.getElementById('intervalGroup');
            if (timeOption.value === 'different') intervalGroup.style.display = 'block';
        };
        
        // Spinner and disable logic
        document.querySelector('form').addEventListener('submit', function(e) {
            var btn = document.getElementById('generateBtn');
            var spinner = document.getElementById('spinner');
            var btnText = document.getElementById('btnText');
            if (btn && spinner && btnText) {
                btn.disabled = true;
                spinner.style.display = 'inline-block';
                btnText.textContent = 'Generating...';
            }
        });
    </script>
</body>
</html>
"""

PLATFORM_ALGORITHMS = {
    "instagram": "Instagram Algorithm: Prioritize visually engaging content, use relevant hashtags, encourage saves and shares, post at optimal times, and interact with followers. Stories, Reels, and carousels get more reach. Content length: up to 800 characters.",
    "twitter": "Twitter/X Algorithm: Focus on concise, timely, and engaging tweets. Use trending hashtags, encourage retweets and replies, and post threads for deeper topics. Engage with trending topics and communities. Content length: up to 280 characters.",
    "linkedin": "LinkedIn Algorithm: Share professional, value-driven content. Use industry hashtags, encourage comments and shares, and tag relevant people or companies. Consistency and engagement boost reach. Content length: up to 1,200 characters.",
    "facebook": "Facebook Algorithm: Prioritize meaningful interactions, use groups and events, encourage comments and shares, and post a mix of media types. Stories and live videos get more visibility. Content length: up to 1,000 characters.",
    "tiktok": "TikTok Algorithm: Create short, entertaining, and trend-driven videos. Use trending sounds and hashtags, encourage likes and shares, and post consistently. Early engagement boosts reach. Content length: up to 150 characters.",
    "general": "General Social Media Algorithm: Post engaging, relevant content with appropriate hashtags. Encourage interaction, post consistently, and use a mix of content types for best results. Content length: up to 800 characters."
}

def generate_post_llm(topic, platform, tone, index, algorithm):
    PLATFORM_CHAR_LIMITS = {
        'instagram': 800,
        'twitter': 280,
        'linkedin': 1200,
        'facebook': 1000,
        'tiktok': 150,
        'general': 800
    }
    char_limit = PLATFORM_CHAR_LIMITS.get(platform, PLATFORM_CHAR_LIMITS['general'])
    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY and AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_API_VERSION:
        print(f"Generating content for {platform} with topic: {topic}")
        print(f"API Endpoint: {AZURE_OPENAI_ENDPOINT}")
        print(f"Deployment: {AZURE_OPENAI_DEPLOYMENT}")
        print(f"API Version: {AZURE_OPENAI_API_VERSION}")
        print(f"API Key: {'Set' if AZURE_OPENAI_KEY else 'Not set'}")
        prompt = f'''
You are an expert content creator or copywriter. Generate an engaging article/post on "{topic}".

Context:
- Target audience: {platform}
- Purpose: educate, inform, and engage
- Style: {tone}

Tone Guidelines:
- Professional: Use formal language, industry insights, and authoritative tone. Include data, statistics, and expert opinions.
- Casual & Friendly: Use conversational language, personal anecdotes, and relatable examples. Be warm and approachable.
- Educational: Use clear explanations, step-by-step breakdowns, and teaching moments. Include "did you know" facts and learning points.
- Inspirational: Use motivational language, success stories, and uplifting messages. Include quotes, achievements, and positive energy.
- Humorous: Use wit, clever analogies, and light-hearted approach. Include puns, funny observations, and entertaining angles.

Structure:
- Start with a compelling hook that immediately explains what the topic is and why it matters to the reader.
- Use a comprehensive, story-like narrative that thoroughly explores the topic with detailed explanations, real-world examples, and practical applications.
- Organize the post into 2-3 engaging, descriptive sections or paragraphs for shorter platforms (Instagram, Facebook, General), or 3-4 sections for longer platforms (LinkedIn). Each section should deeply explore different aspects, provide detailed explanations, and include practical examples that help readers truly understand the topic.
- Use tone-appropriate formatting: Professional (clean, structured), Casual (emojis, friendly), Educational (bullet points, examples), Inspirational (bold statements, quotes), Humorous (clever formatting, puns).
- Include comprehensive examples: Professional (detailed industry cases), Casual (relatable personal stories), Educational (step-by-step learning moments), Inspirational (detailed success stories), Humorous (entertaining analogies with explanations).
- Provide detailed explanations that break down complex concepts into simple, understandable parts.
- End with a comprehensive summary that reinforces understanding and provides actionable insights.

Tone & Style:
- Use storytelling, relatable examples, and vivid language to make the topic enjoyable and easy to understand for all readers.
- Use simple, clear language. Avoid overly AI‑sounding or polished phrases.
- Maintain conversational flow, vary sentence length, sprinkle rhetorical questions or surprises for “burstiness” and engagement.

Mentions:
- You must mention at least 2 influential people (real or hypothetical, relevant to the topic and platform) in the post, and each mention must start with '@' (e.g., @sundarpichai, @tim_cook, @satyanadella, @larrypage, @sherylsandberg, @markzuckerberg, etc). More than 2 mentions are allowed if relevant.
- Choose the most relevant influential people for the topic (e.g., Sundar Pichai, Tim Cook, Satya Nadella, Larry Page, Sheryl Sandberg, Mark Zuckerberg, etc).

Hashtags:
- All hashtags must be placed together at the end of the post, not within the content.
- Hashtags must be highly relevant to the topic only (not the platform or generic tags).
- You must include hashtags as instructed. Do not skip this step.

Constraints:
- Each section ≈ 80–120 words
- Don’t use jargon unless you define it
- Avoid vague statements; be specific
- IMPORTANT: The entire post, including headings, content, and hashtags, must be no longer than {char_limit} characters. Do not exceed this limit. Finish your story or post naturally within this space. Do not cut off mid-sentence or mid-thought - ensure complete, coherent endings.

Engagement Tips:
- Professional: Use industry statistics, expert quotes, and authoritative language. Include detailed data-driven insights, comprehensive case studies, and professional achievements with thorough explanations.
- Casual & Friendly: Use emojis, personal stories, and conversational language. Include relatable examples, detailed personal anecdotes, and warm interactions that help readers connect with the topic.
- Educational: Use "did you know" facts, step-by-step explanations, and detailed learning moments. Include comprehensive examples, teaching points, and thorough breakdowns of complex concepts.
- Inspirational: Use motivational quotes, success stories, and uplifting language. Include detailed achievement stories, comprehensive success examples, and positive energy that motivates learning.
- Humorous: Use clever puns, witty observations, and entertaining angles. Include funny analogies with detailed explanations and light-hearted humor that makes learning enjoyable.
- Provide comprehensive explanations that break down complex topics into simple, understandable parts
- Include practical applications and real-world examples that help readers truly understand and apply the knowledge
- Use detailed analogies and metaphors that make abstract concepts concrete and relatable

After the content, add a line starting with 'Hashtags:' followed by hashtags that are highly relevant to the topic only, with #, space-separated. For Twitter, use only 2-3 hashtags. For other platforms, use up to 10 hashtags. Do not repeat hashtags from previous posts in the series.
'''
        
        # Special handling for Twitter to ensure concise content
        if platform == 'twitter':
            prompt = f'''
You are an expert Twitter content creator. Generate a concise, engaging tweet about "{topic}".

Requirements:
- Maximum 240 characters for content (leaving 40 for hashtags and mentions)
- Include 1 mention starting with '@' (e.g., @sundarpichai, @tim_cook, @satyanadella)
- Use only 2-3 relevant hashtags at the end
- Make it viral-worthy and shareable
- Use trending language and emojis where appropriate
- Include surprising facts or statistics
- Create FOMO (fear of missing out) or curiosity
- Use power words and emotional triggers
- Ensure the tweet has a natural, complete ending - do not cut off mid-sentence

Format: Content with mention + hashtags
Example: "🚀 AI is changing healthcare FOREVER! @sundarpichai just revealed Google's AI can diagnose diseases 10x faster than doctors. This is INSANE! The future is NOW! 🔥 #AI #Healthcare #Tech"

Generate the tweet within the 280 character limit.
'''
        
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
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code}")
                return None, None
            data = response.json()
            if "choices" not in data or len(data["choices"]) == 0:
                print(f"API Error: No choices in response")
                return None, None
            fullText = data["choices"][0]["message"]["content"].strip()
            if not fullText:
                print(f"API Error: Empty response content")
                return None, None
            content = fullText
            hashtags = ''
            
            # Special handling for Twitter - parse hashtags from the same line
            if platform == 'twitter':
                # Look for hashtags at the end of the content
                hashtag_pattern = r'(\s+#\w+(?:\s+#\w+)*)$'
                hashtag_match = re.search(hashtag_pattern, fullText)
                if hashtag_match:
                    hashtags = hashtag_match.group(1).strip()
                    content = re.sub(hashtag_pattern, '', fullText).strip()
                else:
                    # If no hashtags found, treat entire content as content
                    content = fullText.strip()
                    hashtags = ''
            else:
                # For other platforms, use the original parsing logic
                hashtagMatch = re.search(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', fullText, re.IGNORECASE)
                if hashtagMatch:
                    hashtags = hashtagMatch.group(1).strip()
                    content = re.sub(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', '', content, flags=re.IGNORECASE).strip()
                else:
                    # Look for hashtags at the end of the content (similar to Twitter but for multi-line)
                    lines = fullText.split('\n')
                    content_lines = []
                    hashtags = ''
                    
                    for line in lines:
                        # Check if line contains mostly hashtags
                        hashtag_count = line.count('#')
                        word_count = len(line.split())
                        
                        if hashtag_count >= 2 and hashtag_count >= word_count * 0.5:  # If more than 50% are hashtags
                            hashtags = line.strip()
                        else:
                            content_lines.append(line)
                    
                    content = '\n'.join(content_lines).strip()
            # Remove all '**' and '*' from content
            content = content.replace('**', '').replace('*', '')
            # Check if total length exceeds limit and regenerate if needed
            combined = (content + ' ' + hashtags).strip()
            if len(combined) > char_limit:
                # For Twitter, be extra strict about character limits
                if platform == 'twitter' and len(combined) > 280:
                    # Truncate content to fit within 280 characters
                    available_chars = 280 - len(hashtags) - 1  # -1 for space
                    if available_chars > 0:
                        content = content[:available_chars].rsplit(' ', 1)[0] + '...'
                        combined = (content + ' ' + hashtags).strip()
                # If content is too long, try to regenerate with a more restrictive prompt
                # Special regeneration prompt for Twitter
                if platform == 'twitter':
                    shorter_prompt = f'''
You are an expert Twitter content creator. Generate a concise tweet about "{topic}".

Requirements:
- Maximum 240 characters for content
- Include 1 mention starting with '@'
- Use only 2-3 relevant hashtags
- Make it viral-worthy and shareable
- Use trending language and emojis where appropriate
- Include surprising facts or statistics
- Create FOMO or curiosity
- Use power words and emotional triggers
- Do not exceed 280 characters total
- Ensure natural, complete endings - do not cut off mid-sentence

Generate a tweet within the strict limit.
'''
                else:
                    shorter_prompt = f'''
You are an expert content creator. Generate a concise, engaging post on "{topic}" for {platform} in a {tone} tone.

Requirements:
- Maximum {char_limit} characters total (including hashtags)
- Include at least 2 mentions starting with '@'
- Add relevant hashtags at the end
- For Twitter: use only 3-4 hashtags
- For other platforms: use up to 10 hashtags
- Make it engaging and complete within the limit
- Match the {tone} tone: Professional (authoritative), Casual (friendly), Educational (instructive), Inspirational (uplifting), Humorous (entertaining)
- Use tone-appropriate language and examples
- Include tone-specific engagement elements
- Provide comprehensive explanations that help readers truly understand the topic
- Include detailed examples and practical applications
- Break down complex concepts into simple, digestible parts
- Make complex topics simple and accessible
- Do not exceed {char_limit} characters under any circumstances
- Ensure natural, complete endings - do not cut off mid-sentence or mid-thought

Generate the content and hashtags within this strict limit.
'''
                try:
                    body["messages"][0]["content"] = shorter_prompt
                    response = requests.post(url, headers=headers, json=body, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        fullText = data["choices"][0]["message"]["content"].strip()
                        content = fullText
                        hashtags = ''
                        
                        # Special handling for Twitter - parse hashtags from the same line
                        if platform == 'twitter':
                            # Look for hashtags at the end of the content
                            hashtag_pattern = r'(\s+#\w+(?:\s+#\w+)*)$'
                            hashtag_match = re.search(hashtag_pattern, fullText)
                            if hashtag_match:
                                hashtags = hashtag_match.group(1).strip()
                                content = re.sub(hashtag_pattern, '', fullText).strip()
                            else:
                                # If no hashtags found, treat entire content as content
                                content = fullText.strip()
                                hashtags = ''
                        else:
                            # For other platforms, use the original parsing logic
                            hashtagMatch = re.search(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', fullText, re.IGNORECASE)
                            if hashtagMatch:
                                hashtags = hashtagMatch.group(1).strip()
                                content = re.sub(r'(?:^|\n)hashtags:\s*([#\w\s-]+)', '', content, flags=re.IGNORECASE).strip()
                            else:
                                # Look for hashtags at the end of the content (similar to Twitter but for multi-line)
                                lines = fullText.split('\n')
                                content_lines = []
                                hashtags = ''
                                
                                for line in lines:
                                    # Check if line contains mostly hashtags
                                    hashtag_count = line.count('#')
                                    word_count = len(line.split())
                                    
                                    if hashtag_count >= 2 and hashtag_count >= word_count * 0.5:  # If more than 50% are hashtags
                                        hashtags = line.strip()
                                    else:
                                        content_lines.append(line)
                                
                                content = '\n'.join(content_lines).strip()
                        content = content.replace('**', '').replace('*', '')
                except Exception:
                    pass  # Keep original content if regeneration fails
            
            return content, hashtags
        except Exception:
            return None, None
    else:
        print("API credentials not found. Please check your .env file.")
        print(f"Missing: AZURE_OPENAI_ENDPOINT={bool(AZURE_OPENAI_ENDPOINT)}, AZURE_OPENAI_KEY={bool(AZURE_OPENAI_KEY)}, AZURE_OPENAI_DEPLOYMENT={bool(AZURE_OPENAI_DEPLOYMENT)}, AZURE_OPENAI_API_VERSION={bool(AZURE_OPENAI_API_VERSION)}")
        return None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    posts = []
    now = datetime.now()
    base_date = ''
    base_time = ''
    if request.method == 'POST':
        if request.form.get('edit') == '1':
            # Save edits to posts
            posts = session.get('posts', [])
            for i in range(len(posts)):
                posts[i]['date'] = request.form.get(f'date_{i}', posts[i]['date'])
                posts[i]['time'] = request.form.get(f'time_{i}', posts[i]['time'])
                posts[i]['content'] = request.form.get(f'content_{i}', posts[i]['content'])
                posts[i]['hashtags'] = request.form.get(f'hashtags_{i}', posts[i]['hashtags'])
            session['posts'] = posts
        else:
            topic = request.form.get('topic')
            platform = request.form.get('platform')
            tone = request.form.get('tone')
            postCount = int(request.form.get('postCount', 1))
            base_date = request.form.get('baseDate')
            base_time = request.form.get('baseTime')
            time_option = request.form.get('timeOption', 'same')
            interval = int(request.form.get('interval', 1))
            algo = PLATFORM_ALGORITHMS.get(platform, PLATFORM_ALGORITHMS['general'])
            try:
                post_base_date = datetime.strptime(base_date, '%Y-%m-%d')
            except Exception:
                post_base_date = now
            try:
                base_hour, base_minute = map(int, base_time.split(':'))
            except Exception:
                base_hour, base_minute = now.hour, (now.minute // 5) * 5
            posts = []
            for i in range(1, postCount + 1):
                if time_option == 'different':
                    post_date = post_base_date + timedelta(days=(i - 1) * interval)
                else:
                    post_date = post_base_date
                post_datetime = post_date.replace(hour=base_hour, minute=base_minute)
                date_str = post_datetime.strftime('%Y-%m-%d')
                time_str = post_datetime.strftime('%H:%M')
                
                content, hashtags = generate_post_llm(topic, platform, tone, i, algo)
                posts.append({
                    'date': date_str,
                    'time': time_str,
                    'content': content,
                    'hashtags': hashtags
                })
            session['posts'] = posts
    else:
        posts = session.get('posts', [])
        # Set default base_date and base_time if not set
        base_date = now.strftime('%Y-%m-%d')
        base_time = f"{now.hour:02d}:{(now.minute // 5) * 5:02d}"
    return render_template_string(HTML_TEMPLATE, posts=posts, base_date=base_date, base_time=base_time)

@app.route('/download-csv', methods=['GET'])
def download_csv():
    posts = session.get('posts', [])
    if not posts:
        return redirect(url_for('index'))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date & Time', 'Content'])
    for post in posts:
        # Remove HTML tags from content for CSV
        content = re.sub('<[^<]+?>', '', post['content'])
        # After extracting 'content' from the LLM response, remove all '**' from content before saving to posts.
        # Also apply this cleaning in the CSV export.
        content = content.replace('**', '')
        hashtags = post['hashtags']
        date_time = f"{post['date']} {post['time']}"
        content_hashtags = f"{content} {hashtags}".strip()
        writer.writerow([date_time, content_hashtags])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'social_media_posts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True) 