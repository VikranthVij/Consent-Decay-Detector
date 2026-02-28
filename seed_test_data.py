import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "policies.db")
TEST_POLICY = os.path.join(os.path.dirname(__file__), "test_policy.txt")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if already seeded
c.execute("SELECT COUNT(*) FROM companies")
if c.fetchone()[0] > 0:
    print("Database already has data. Skipping seed.")
    conn.close()
    exit()

# Read test policy
with open(TEST_POLICY, "r") as f:
    policy_text = f.read()

# Insert company
c.execute(
    "INSERT INTO companies (name, url) VALUES (?, ?)",
    ("WhatsApp", "https://www.whatsapp.com/legal/privacy-policy"),
)
company_id = c.lastrowid

# Version 1: first half of policy (simulates the "old" version)
lines = policy_text.split("\n")
midpoint = len(lines) // 2
old_text = "\n".join(lines[:midpoint])

# Version 2: full policy with AI/profiling expansion clauses
new_text = policy_text

h1 = hashlib.sha256(old_text.encode()).hexdigest()
h2 = hashlib.sha256(new_text.encode()).hexdigest()

c.execute(
    'INSERT INTO policy_versions (company_id, timestamp, hash, content) VALUES (?, datetime("now", "-30 days"), ?, ?)',
    (company_id, h1, old_text),
)
c.execute(
    'INSERT INTO policy_versions (company_id, timestamp, hash, content) VALUES (?, datetime("now"), ?, ?)',
    (company_id, h2, new_text),
)

conn.commit()
conn.close()
print("Seeded database with 1 company (WhatsApp) and 2 policy versions.")
