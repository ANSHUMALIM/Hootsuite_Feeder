# Hootsuite_Feeder
# Social Media Post Generator & Scheduler

Generate and schedule optimized social media posts for platforms like Facebook, Instagram, and Twitter, and export them as CSV for seamless publishing.

---

##  Features

-  **Platform-Specific Post Generation** — Tailors content to each social media algorithm.
-  **Scheduling Flexibility** — Set custom date and time for each post.
-  **CSV Export** — Download generated posts in CSV format; each row contains:
  - **Cell 1**: Date and time (formatted as `YYYY-MM-DD HH:MM`)  
  - **Cell 2**: The post content

---

##  Getting Started

### Prerequisites

- Ensure you have **Python** installed (recommended: Python 3.7+).
- Optionally, set up a virtual environment to isolate dependencies.

### Sample Output
2025-08-22 14:30,Check out our new blog post!
2025-08-23 09:00,Don’t miss today’s updates!

### How It Works

Capture Input: Topic, desired platform(s), and schedule.
Generate Content: AI-driven or templated generation tailored to each platform’s algorithm.
Schedule Assignment: Posts are paired with the user-specified date/time.
CSV Export: Outputs an easily importable file where each line contains scheduling and content in two columns.


### Installation & Run


Clone the repository:  
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo

    pip install -r requirements.txt
    python api_html.py


