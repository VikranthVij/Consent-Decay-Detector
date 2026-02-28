import sys
from backend.drift_engine import compute_policy_drift
from backend.timeline_engine import compute_timeline_drift


def run_full_audit(company_name):

    print("\nFULL CONSENT AUDIT\n")

    compute_policy_drift(company_name, mode="baseline")
    compute_policy_drift(company_name, mode="incremental")
    compute_timeline_drift(company_name)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m backend.audit_engine <CompanyName>")
    else:
        run_full_audit(sys.argv[1])