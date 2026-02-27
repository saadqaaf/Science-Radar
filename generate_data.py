import requests
import json
import datetime
import re
import os
import nltk
from nltk.corpus import stopwords
from collections import Counter

# --- CONFIGURATION ---
ISSNS = ["2058-7546","2520-8136","2542-4351","1748-3395","1754-5706","1614-6840","2637-9368",
        "2589-7780","2405-8297","2380-8195","2211-2855","2692-7640","2095-4956","2575-0356","2768-1696","2352-152X",
        "2211-467X"] # Nature Energy, Joule
EMAIL = "s_g555@yahoo.com"
STATE_FILE = "word_state.json"
DASHBOARD_DATA = "dashboard_data.json"
SEEN_DOIS_FILE = "seen_dois.json" # Our new memory bank for papers

# Setup stopwords
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))
stop_words.update(['using', 'based', 'study', 'effect', 'effects', 'analysis', 'new', 'two', 'via', 'high'])

def clean_and_tokenize(text):
    """Removes punctuation (except hyphens), stop words, and standalone numbers but keeps chemical formulas."""
    text = re.sub(r'[^\w\s\-]', '', text).lower()
    words = text.split()
    cleaned_words = []
    
    for w in words:
        w = w.strip('-')
        if w not in stop_words and len(w) > 1 and not w.isnumeric():
            cleaned_words.append(w)
            
    return cleaned_words

def fetch_new_papers(seen_dois):
    """Fetches the 100 most recent papers and filters out ones we've already seen."""
    papers = []
    headers = {"User-Agent": f"DailyTrendTracker/1.0 (mailto:{EMAIL})"}
    
    for issn in ISSNS:
        # Sort by creation date descending, grab top 100
        url = f"https://api.crossref.org/journals/{issn}/works?sort=created&order=desc&rows=100&select=title,DOI"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                items = response.json().get('message', {}).get('items', [])
                for item in items:
                    doi = item.get('DOI')
                    title_list = item.get('title', [])
                    
                    # If it has a title, a DOI, and we haven't processed it before
                    if title_list and doi and doi not in seen_dois:
                        papers.append({
                            "title": title_list[0],
                            "doi": doi
                        })
                        seen_dois.add(doi) # Add to our memory bank
        except Exception as e:
            print(f"Error fetching ISSN {issn}: {e}")
            
    return papers

def main():
    # 1. Load historical word state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            cumulative_counts = json.load(f)
    else:
        cumulative_counts = {}

    # 2. Load seen DOIs memory bank
    if os.path.exists(SEEN_DOIS_FILE):
        with open(SEEN_DOIS_FILE, 'r') as f:
            seen_dois = set(json.load(f))
    else:
        seen_dois = set()

    # 3. Fetch only truly new papers
    papers = fetch_new_papers(seen_dois)
    if not papers:
        print("No new papers published since last run. Exiting.")
        return

    today_counts = Counter()
    new_words_data = {} 

    # 4. Process papers
    for paper in papers:
        words = clean_and_tokenize(paper["title"])
        for word in words:
            today_counts[word] += 1
            if word not in cumulative_counts:
                if word not in new_words_data:
                    new_words_data[word] = {"count": 0, "dois": []}
                new_words_data[word]["count"] += 1
                if paper["doi"] not in new_words_data[word]["dois"]:
                    new_words_data[word]["dois"].append(paper["doi"])

    # 5. Update the accumulative state
    for word, count in today_counts.items():
        cumulative_counts[word] = cumulative_counts.get(word, 0) + count

    # 6. Save internal states
    with open(STATE_FILE, 'w') as f:
        json.dump(cumulative_counts, f)
        
    with open(SEEN_DOIS_FILE, 'w') as f:
        json.dump(list(seen_dois), f) # Save updated DOI memory bank

    # 7. Save frontend dashboard data
    sorted_cumulative = dict(sorted(cumulative_counts.items(), key=lambda item: item[1], reverse=True)[:300])
    dashboard_payload = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "cumulative": sorted_cumulative,
        "new_words": new_words_data
    }
    
    with open(DASHBOARD_DATA, 'w') as f:
        json.dump(dashboard_payload, f)
    print(f"Processed {len(papers)} new papers. Dashboard updated.")

if __name__ == "__main__":
    main()


