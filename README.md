# 📊 Energy Research Trend Tracker

A lightweight Python tool that monitors the latest publications across top energy and materials science journals, tracking keyword trends from paper titles over time. Designed to run on a schedule (e.g. daily via cron or GitHub Actions) and produce a JSON dashboard for frontend visualization.

---

## 🔍 What It Does

1. **Fetches recent papers** from a curated list of journal ISSNs via the [Crossref API](https://api.crossref.org/)
2. **Deduplicates** using a persistent DOI memory bank — so each paper is only counted once, no matter how many times the script runs
3. **Tokenizes and cleans** paper titles, stripping HTML tags, stop words, punctuation, and standalone numbers
4. **Accumulates word frequency counts** over time into a running historical state
5. **Exports a dashboard JSON file** with the top 300 cumulative keywords and a list of newly seen words — ready to power a frontend word cloud or chart

---

## 📁 File Structure

| File | Description |
|---|---|
| `tracker.py` | Main script |
| `word_state.json` | Cumulative word frequency counts (auto-generated) |
| `seen_dois.json` | Memory bank of processed DOIs (auto-generated) |
| `dashboard_data.json` | Output consumed by frontend (auto-generated) |

---

## ⚙️ Installation

**Requirements:** Python 3.7+

```bash
pip install requests nltk
```

NLTK stopwords will be downloaded automatically on the first run.

---

## 🚀 Usage

```bash
python tracker.py
```

On each run, the script will:
- Skip papers it has already processed
- Print a summary like `Processed 42 new papers. Dashboard updated.`
- Exit gracefully with `No new papers published since last run.` if nothing is new

---

## 📦 Dashboard Output Format

`dashboard_data.json` is structured as follows:

```json
{
  "last_updated": "2025-01-15 08:30:00 UTC",
  "cumulative": {
    "battery": 412,
    "solar": 389,
    "lithium": 301,
    ...
  },
  "new_words": {
    "perovskite": {
      "count": 3,
      "dois": ["10.1038/...", "10.1016/..."]
    }
  }
}
```

- **`cumulative`** — Top 300 keywords by all-time frequency, sorted descending
- **`new_words`** — Keywords that appeared for the first time in this run, with source DOIs

---

## 📰 Tracked Journals

The script monitors a curated list of high-impact journals in energy, materials, and sustainability research, including publications from Nature Portfolio, Elsevier, and others. ISSNs are configured at the top of `tracker.py` in the `ISSNS` list and can be freely added or removed.

---

## ⏱️ Scheduling

To run daily, add a cron job:

```bash
# Run every day at 6 AM
0 6 * * * /usr/bin/python3 /path/to/tracker.py
```

Or use **GitHub Actions** with a `schedule` trigger to run it serverlessly and auto-commit the updated JSON files.

---

## 🛠️ Configuration

Edit the constants at the top of `tracker.py`:

| Variable | Description |
|---|---|
| `ISSNS` | List of journal ISSNs to monitor |
| `EMAIL` | Your email, included in the API User-Agent header per Crossref's [etiquette guidelines](https://api.crossref.org/swagger-ui/index.html#/Works/get_works) |
| `STATE_FILE` | Path to the cumulative word count state file |
| `SEEN_DOIS_FILE` | Path to the DOI memory bank |
| `DASHBOARD_DATA` | Path to the output dashboard JSON |

---

## 📄 License

MIT License — free to use, modify, and distribute.
