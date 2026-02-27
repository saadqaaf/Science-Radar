import requests
import json
import datetime
import re
from collections import Counter
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
# Replace with the ISSNs of your target journals (e.g., Nature, Science, etc.)
ISSNS = ["1476-4687", "1095-9203"] 
# Crossref requires an email to put you in the reliable "Polite Pool"
EMAIL = "s_g555@yahoo.com" 
STATE_FILE = "word_state.json"

def clean_and_tokenize(text):
    """Removes punctuation, numbers, and stop words."""
    text = re.sub(r'[^\w\s]', '', text).lower()
    text = re.sub(r'\d+', '', text) # remove numbers
    words = text.split()
    # Remove standard stop words and any single-letter words
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

def fetch_yesterdays_titles():
    """Fetches paper titles added to Crossref yesterday for the specified ISSNs."""
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    titles = []
    headers = {"User-Agent": f"DailyTrendTracker/1.0 (mailto:{EMAIL})"}
    
    for issn in ISSNS:
        url = f"https://api.crossref.org/journals/{issn}/works?filter=from-created-date:{yesterday},until-created-date:{yesterday}&select=title"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('message', {}).get('items', [])
                for item in items:
                    title_list = item.get('title', [])
                    if title_list:
                        titles.append(title_list[0])
        except Exception as e:
            print(f"Error fetching ISSN {issn}: {e}")
            
    return titles

def main():
    # 1. Load historical state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            cumulative_counts = json.load(f)
    else:
        cumulative_counts = {}

    # 2. Fetch and process new titles
    titles = fetch_yesterdays_titles()
    if not titles:
        print("No new papers found for yesterday. Exiting.")
        return

    today_words = []
    for title in titles:
        today_words.extend(clean_and_tokenize(title))
    
    today_counts = Counter(today_words)

    # 3. Identify brand new words (for the new trends cloud)
    new_words_counts = {}
    for word, count in today_counts.items():
        if word not in cumulative_counts:
            new_words_counts[word] = count

    # 4. Update the accumulative state
    for word, count in today_counts.items():
        cumulative_counts[word] = cumulative_counts.get(word, 0) + count

    # 5. Save the updated state
    with open(STATE_FILE, 'w') as f:
        json.dump(cumulative_counts, f)

    # 6. Generate Accumulative Word Cloud
    if cumulative_counts:
        wc_accum = WordCloud(width=800, height=400, background_color='white', colormap='viridis')
        wc_accum.generate_from_frequencies(cumulative_counts)
        wc_accum.to_file("accumulative_cloud.png")
        print("Generated accumulative_cloud.png")

    # 7. Generate "New Words" Word Cloud
    if new_words_counts:
        wc_new = WordCloud(width=800, height=400, background_color='black', colormap='magma')
        wc_new.generate_from_frequencies(new_words_counts)
        wc_new.to_file("new_words_cloud.png")
        print("Generated new_words_cloud.png")
    else:
        print("No entirely new words found today. Skipping new words cloud.")

if __name__ == "__main__":

    main()
