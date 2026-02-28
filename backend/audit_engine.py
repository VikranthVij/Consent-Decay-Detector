import sys
from backend.drift_engine import compute_policy_drift
from backend.timeline_engine import compute_timeline_drift


# ==========================================
# Unified Consent Audit Engine
# ==========================================

def run_full_audit(company_name):

    print("\n" + "=" * 80)
    print("CONSENT DECAY DETECTOR — FULL AUDIT")
    print("=" * 80)

    # ==========================
    # 1️⃣ BASELINE MODE
    # ==========================
    print("\n\n" + "=" * 80)
    print("BASELINE DRIFT ANALYSIS")
    print("=" * 80)

    compute_policy_drift(company_name, mode="baseline")

    # ==========================
    # 2️⃣ INCREMENTAL MODE
    # ==========================
    print("\n\n" + "=" * 80)
    print("INCREMENTAL DRIFT ANALYSIS")
    print("=" * 80)

    compute_policy_drift(company_name, mode="incremental")

    # ==========================
    # 3️⃣ TIMELINE + ESCALATION
    # ==========================
    print("\n\n" + "=" * 80)
    print("TIMELINE + CATEGORY ESCALATION ANALYSIS")
    print("=" * 80)

    compute_timeline_drift(company_name)

    print("\n" + "=" * 80)
    print("END OF FULL AUDIT")
    print("=" * 80)


# ==========================================
# CLI Entry
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python -m backend.audit_engine <CompanyName>")
    else:
        run_full_audit(sys.argv[1])