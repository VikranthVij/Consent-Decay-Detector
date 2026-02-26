# 📄 README.md

```markdown
# Consent Decay Detector  
### Policy Drift Intelligence Platform  
Developed for AMD Hackathon (Slingshot Challenge)

---

## 📌 Overview

Consent Decay Detector is an automated policy monitoring system that tracks changes in privacy policies and terms of service over time.

The system scrapes public policy pages, stores historical versions, and detects updates using cryptographic hashing.  

It forms the foundation of a larger Policy Drift Intelligence Platform aimed at quantifying semantic expansion of user consent over time.

---

## 🎯 Problem Statement

Digital platforms frequently update their:

- Privacy Policies  
- Terms of Service  
- Data Usage Policies  

Users provide consent once, but policies evolve silently.

Existing tools:
- Highlight textual changes
- Show redline diffs
- Send alerts

They do **not**:
- Track structured historical versions automatically
- Store policy evolution in a database
- Prepare data for semantic drift analysis

This project builds the automated monitoring backbone required for policy drift intelligence.

---

## 🚀 What Has Been Implemented

### ✅ 1. Automated Policy Crawler

- Supports static HTML pages
- Supports JavaScript-rendered pages (via Playwright)
- Extracts readable policy text
- Cleans and processes content

---

### ✅ 2. SQLite Database Integration

The system stores data in a structured SQLite database.

#### Database: `policies.db`

Tables:

**companies**
| id | name | url |

**policy_versions**
| id | company_id | timestamp | hash | content |

Features:
- Foreign key relationships
- Timestamped version storage
- Efficient historical tracking

---

### ✅ 3. Hash-Based Change Detection

Each fetched policy is processed as follows:

1. Extract full text
2. Generate SHA256 hash
3. Compare against latest stored hash
4. If unchanged → skip
5. If changed → store new version

This ensures:
- No duplicate entries
- Efficient monitoring
- Accurate version tracking

---

### ✅ 4. Version Retrieval Module

`versioning.py` enables retrieval of:

- Earliest stored version
- Latest stored version

This prepares the system for future semantic comparison between baseline and current policies.

---

## 🏗 Project Structure

```

consent_decay_detector/
│
├── backend/
│   ├── __init__.py
│   ├── crawler.py
│   ├── database.py
│   ├── versioning.py
│   ├── registry.json
│   └── policies.db
│
├── requirements.txt
└── README.md

````

---

## ⚙️ How It Works

1. `registry.json` defines companies and policy URLs.
2. `crawler.py` fetches policy content.
3. Text is cleaned and hashed.
4. Database is queried for latest stored hash.
5. If new → insert new version.
6. If same → skip.

---

## 🧩 Core Modules Used

- Python 3.9+
- sqlite3
- requests
- trafilatura
- playwright
- hashlib
- json
- datetime

---

## ▶️ How To Run

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/consent-decay-detector.git
cd consent-decay-detector
````

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install
```

### 4. Run Crawler

```bash
python3 -m backend.crawler
```

The system will:

* Fetch policies
* Compare hash
* Store new versions if changes detected

---

## 📈 Current Status

✔ Automated scraping (static + JS-rendered pages)
✔ Structured SQLite integration
✔ Version storage
✔ Hash-based change detection
✔ Baseline & latest version retrieval

---

## 🔜 Upcoming Development

Next phase will implement:

* Policy chunking
* Embedding generation
* Semantic similarity computation
* Drift magnitude scoring
* Risk-weighted expansion detection

This will evolve the system into a full Policy Drift Intelligence Platform.

---

## 🏁 Hackathon Context

This project is being developed for the **AMD Hackathon (Slingshot Challenge)** and demonstrates:

* Applied NLP infrastructure
* Automated monitoring systems
* Structured database design
* Scalable AI-ready architecture

---

## ⚖️ Ethical Note

* Only publicly available policy documents are processed.
* No private user data is collected.
* No invasive system monitoring is performed.


