import requests
import json
import datetime
import re
import os
import nltk
from nltk.corpus import stopwords
from collections import Counter

# --- CONFIGURATION ---
ISSNS = ["1476-4687", "1095-9203"] # Nature, Science
EMAIL = "s_g555@yahoo.com"
STATE_FILE = "word_state.json"
DASHBOARD_DATA = "dashboard_data.json"

# Setup stopwords (removes conjunctions, prepositions, etc.)
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))
# Add common academic filler words you want to ignore
stop_words.update(['using', 'based', 'study', 'effect', 'effects', 'analysis', 'new', 'two', 'via', 'high'])

def clean_and_tokenize(text):
    """Removes punctuation, numbers, and grammar/stop words."""
    text = re.sub(r'[^\w\s]', '', text).lower()
    text = re.sub(r'\d+', '', text)
    return [w for w in text.split() if w not in stop_words and len(w) > 2]

def fetch_yesterdays_papers():
    """Fetches titles and DOIs."""
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    papers = []
    headers = {"User-Agent": f"DailyTrendTracker/1.0 (mailto:{EMAIL})"}
    
    for issn in ISSNS:
        url = f"https://api.crossref.org/journals/{issn}/works?filter=from-created-date:{yesterday},until-created-date:{yesterday}&select=title,DOI"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                items = response.json().get('message', {}).get('items', [])
                for item in items:
                    title_list = item.get('title', [])
                    if title_list:
                        papers.append({
                            "title": title_list[0],
                            "doi": item.get('DOI', 'No DOI available')
                        })
        except Exception as e:
            print(f"Error fetching ISSN {issn}: {e}")
            
    return papers

def main():
    # 1. Load historical state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            cumulative_counts = json.load(f)
    else:
        cumulative_counts = {}

    # 2. Fetch new papers
    papers = fetch_yesterdays_papers()
    if not papers:
        print("No new papers found. Exiting.")
        return

    today_counts = Counter()
    new_words_data = {} # Maps new word to {count: X, dois: [DOI1, DOI2]}

    # 3. Process papers
    for paper in papers:
        words = clean_and_tokenize(paper["title"])
        for word in words:
            today_counts[word] += 1
            # Check if it's a completely new word
            if word not in cumulative_counts:
                if word not in new_words_data:
                    new_words_data[word] = {"count": 0, "dois": []}
                new_words_data[word]["count"] += 1
                if paper["doi"] not in new_words_data[word]["dois"]:
                    new_words_data[word]["dois"].append(paper["doi"])

    # 4. Update the accumulative state
    for word, count in today_counts.items():
        cumulative_counts[word] = cumulative_counts.get(word, 0) + count

    # 5. Save internal state
    with open(STATE_FILE, 'w') as f:
        json.dump(cumulative_counts, f)

    # 6. Save frontend dashboard data
    # Sort cumulative for the frontend (top 300 words to avoid overloading browser)
    sorted_cumulative = dict(sorted(cumulative_counts.items(), key=lambda item: item[1], reverse=True)[:300])
    
    dashboard_payload = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "cumulative": sorted_cumulative,
        "new_words": new_words_data
    }
    
    with open(DASHBOARD_DATA, 'w') as f:
        json.dump(dashboard_payload, f)
    print("Data processed and dashboard_data.json updated.")

if __name__ == "__main__":
    main()
