Here is your **clean, polished Markdown README**, formatted professionally and ready to copy-paste directly into GitHub:

---

# Consent Decay Detector (CDD)

## Policy Drift Intelligence & Consent Erosion Modeling Platform

Developed for AMD Slingshot Hackathon

---

## 📌 Overview

Consent Decay Detector (CDD) is a privacy-preserving, AI-powered policy intelligence platform that tracks, analyzes, and quantifies how corporate data rights expand over time.

Unlike traditional diff tools that only highlight textual edits, CDD models the evolution of consent power using structural drift detection, LLM-based semantic risk analysis, escalation tracking, and cumulative risk scoring.

It introduces a novel metric called the **Consent Decay Index (CDI)** — a quantitative measure of how user consent scope expands across policy versions.

---

## 🎯 Problem Statement

Digital platforms frequently update:

* Privacy Policies
* Terms of Service
* Data Usage Agreements

Users consent once, but policies evolve silently.

Existing tools:

* Show redline differences
* Highlight textual edits
* Send alerts

They do **not**:

* Store structured historical versions automatically
* Detect semantic expansion beyond wording
* Track escalation of data-processing categories
* Identify irreversible data power shifts
* Quantify cumulative consent erosion

CDD transforms policy evolution into measurable intelligence.

---

## 🚀 Core Capabilities

### 1️⃣ Structural Drift Detection

* Clause-level comparison using sentence embeddings
* Cosine similarity matrix computation
* Classification into unchanged, modified, removed, added
* Structural drift percentage calculation

### 2️⃣ LLM-Based Semantic Risk Analysis

* Ollama-hosted LLM (Mistral / LLaMA)
* Risk scoring (0–10)
* Controlled ontology classification:

  * AI training
  * Retention expansion
  * Cross-platform sharing
  * Profiling
  * Automated decision-making
* Strict category constraints to prevent hallucination

### 3️⃣ Category Escalation Tracking

* Version-level category severity maps
* Escalation intensity computation across versions

### 4️⃣ Irreversibility Detection

Flags permanent shifts such as:

* AI model training on user data
* Historical data reclassification
* Automated decision systems

### 5️⃣ Consent Decay Index (CDI)

Cumulative metric combining:

* Structural Drift
* Semantic Expansion
* Escalation Intensity
* Irreversible Expansion

CDI models consent momentum on a 0–100 scale.

---

## 🏗 System Workflow

### Step 1: Policy Crawling

* Supports static HTML pages
* Supports JavaScript-rendered pages (Playwright)
* Extracts readable policy text
* Cleans and processes content

### Step 2: Hash-Based Change Detection

* Generates SHA256 hash of policy text
* Compares with latest stored hash
* Stores only if content changed
* Prevents duplicate versions

### Step 3: Version Storage (SQLite)

Database: `policies.db`

Tables:

**companies**

* id
* name
* url

**policy_versions**

* id
* company_id
* timestamp
* hash
* content

Enables structured historical tracking.

### Step 4: Text Processing

* Normalization using Python + regex
* Clause-level chunking for semantic precision

### Step 5: Embedding & Similarity Engine

* Sentence embeddings
* Cosine similarity computation
* Structural classification via thresholds

### Step 6: LLM Risk Engine

* On-device inference via Ollama
* Structured JSON output validation
* Controlled ontology enforcement

### Step 7: Timeline Drift Engine

* Version-to-version structural comparison
* Semantic expansion analysis
* Escalation growth modeling
* Irreversibility detection
* CDI accumulation

### Step 8: Interactive Dashboard

Displays:

* Structural Drift (%)
* Semantic Risk (/10)
* Escalation Intensity
* CDI Timeline Visualization

---

## 🧠 Technology Stack

* Python 3.9+
* SQLite
* Playwright
* Sentence Embeddings
* NumPy (Cosine Similarity)
* Ollama (Local LLM Hosting)
* HTML / CSS / JavaScript
* Browser Extension Integration

---

# ⚙ Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/consent-decay-detector.git
cd consent-decay-detector
```

---

## 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Install & Start Ollama

Download Ollama from:
[https://ollama.com](https://ollama.com)

Start server:

```bash
ollama serve
```

Pull model:

```bash
ollama pull mistral:instruct
```

---

## 5️⃣ Install Playwright Browsers

```bash
playwright install
```

---

# ▶ Running the System

## Crawl & Store Policy

```bash
python backend/crawler.py
```

## Run Drift Analysis

```bash
python backend/drift_engine.py
```

## Launch Frontend Dashboard

```bash
python frontend/app.py
```

Open in browser:

```
http://localhost:5000
```

---

## 🌍 Impact

CDD transforms privacy policy evolution from a legal diff process into a quantitative intelligence framework.

Instead of asking:

**“What changed?”**

CDD answers:

**“How much more power did the company gain?”**

---

If you want, I can now give you a **clean badge-style professional GitHub header version** (with shields, architecture diagram section, and demo GIF section).
