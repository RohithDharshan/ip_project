#!/usr/bin/env python3
"""API smoke test — run from project root after backend starts."""
import urllib.request, urllib.parse, json, sys

BASE = "http://localhost:8000"

def req(method, path, token=None, form=None, json_body=None):
    url = BASE + path
    data = None
    headers = {}
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read()[:200].decode()}
    except Exception as e:
        return {"_exception": str(e)}

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"

def check(label, cond, detail=""):
    mark = PASS if cond else FAIL
    detail_text = str(detail) if detail is not None else ""
    print(f"  {mark}  {label}{('  →  ' + detail_text) if detail_text else ''}")
    return cond

all_ok = True

# ── Login ───────────────────────────────────────────────────────────────────
print("\n[Auth]")
r = req("POST", "/auth/login", form={"username": "faculty@psgai.edu.in", "password": "Password@123"})
tok_fac = r.get("access_token")
all_ok &= check("faculty login", bool(tok_fac), r.get("_error", ""))

r2 = req("POST", "/auth/login", form={"username": "hod@psgai.edu.in", "password": "Password@123"})
tok_hod = r2.get("access_token")
all_ok &= check("hod login", bool(tok_hod))

r3 = req("POST", "/auth/login", form={"username": "deanadmin@psgai.edu.in", "password": "Password@123"})
tok_dean_admin = r3.get("access_token")
all_ok &= check("dean administration login", bool(tok_dean_admin))

r4 = req("POST", "/auth/login", form={"username": "deanautonomous@psgai.edu.in", "password": "Password@123"})
tok_dean_auto = r4.get("access_token")
all_ok &= check("dean autonomous login", bool(tok_dean_auto))

r5 = req("POST", "/auth/login", form={"username": "admin@psgai.edu.in", "password": "Password@123"})
tok_admin = r5.get("access_token")
all_ok &= check("admin login", bool(tok_admin))

# ── /auth/me ────────────────────────────────────────────────────────────────
print("\n[Auth/Me]")
me = req("GET", "/auth/me", token=tok_fac)
all_ok &= check("faculty /me", me.get("role") == "faculty", me.get("name", str(me)))

me2 = req("GET", "/auth/me", token=tok_hod)
all_ok &= check("hod /me", me2.get("role") == "hod", me2.get("name", str(me2)))

# ── Proposals ───────────────────────────────────────────────────────────────
print("\n[Proposals]")
props_fac = req("GET", "/proposals", token=tok_fac)
all_ok &= check("faculty sees proposals", isinstance(props_fac, list), f"{len(props_fac)} proposals")

props_hod = req("GET", "/proposals", token=tok_hod)
all_ok &= check("hod sees all proposals", isinstance(props_hod, list) and len(props_hod) > len(props_fac),
                f"hod={len(props_hod)}, faculty={len(props_fac)}")

if isinstance(props_fac, list) and props_fac:
    all_ok &= check("faculty can see risk in proposals", props_fac[0].get("ai_risk_level") is not None)
if isinstance(props_hod, list) and props_hod:
    all_ok &= check("non-faculty risk hidden in proposals", props_hod[0].get("ai_risk_level") is None)

if isinstance(props_fac, list) and props_fac:
    pid_for_analysis = props_fac[0].get("id")
    fac_analysis = req("GET", f"/proposals/{pid_for_analysis}/analysis", token=tok_fac)
    hod_analysis = req("GET", f"/proposals/{pid_for_analysis}/analysis", token=tok_hod)
    all_ok &= check("faculty can access analysis", isinstance(fac_analysis, dict) and "risk" in fac_analysis)
    all_ok &= check("non-faculty analysis blocked", hod_analysis.get("_error") == 403, str(hod_analysis))

# ── Vendors ─────────────────────────────────────────────────────────────────
print("\n[Vendors]")
vendors = req("GET", "/vendors", token=tok_fac)
all_ok &= check("vendor list", isinstance(vendors, list) and len(vendors) > 0, f"{len(vendors)} vendors")

rec = req("GET", "/vendors/recommend?category=catering", token=tok_fac)
all_ok &= check("vendor recommend", "vendor_id" in rec or "recommendation_reason" in rec or "vendors" in rec,
                str(rec)[:80])

# ── Analytics ───────────────────────────────────────────────────────────────
print("\n[Analytics]")
ov = req("GET", "/analytics/overview", token=tok_fac)
all_ok &= check("overview endpoint", "total_proposals" in ov,
                f"total={ov.get('total_proposals')} approved={ov.get('approved_proposals')}")

audit = req("GET", "/analytics/audit", token=tok_fac)
all_ok &= check("audit log", isinstance(audit, list), f"{len(audit)} entries")

# ── Approvals ───────────────────────────────────────────────────────────────
print("\n[Approvals]")
pending = req("GET", "/approvals/pending", token=tok_hod)
all_ok &= check("hod pending approvals", isinstance(pending, list), f"{len(pending)} items")

if isinstance(props_hod, list) and props_hod:
    pid = props_hod[0].get("id")
    wf = req("GET", f"/proposals/{pid}/workflow", token=tok_hod)
    expected = ["hod", "bursar", "dean_administration", "dean_autonomous", "principal"]
    actual = [s.get("approver_role") for s in wf] if isinstance(wf, list) else []
    all_ok &= check("workflow chain order", actual == expected, f"{actual}")

if isinstance(pending, list) and pending:
    step_id = pending[0].get("id")
    bad_decision = req(
        "POST",
        f"/approvals/{step_id}/decide",
        token=tok_hod,
            json_body={"decision": "clarification_requested", "comments": "not allowed"},
    )
    all_ok &= check("clarify decision blocked", bad_decision.get("_error") == 400, str(bad_decision))

dash = req("GET", "/approvals/dashboard", token=tok_hod)
all_ok &= check("approvals dashboard", isinstance(dash, dict) and "total" in dash,
                f"total={dash.get('total')} pending={dash.get('pending')}")

# ── Bad credentials → 401 (no auto-logout) ──────────────────────────────────
print("\n[Security]")
bad = req("POST", "/auth/login", form={"username": "x@x.com", "password": "wrong"})
all_ok &= check("bad credentials → 401", bad.get("_error") == 401, str(bad.get("_error")))

# ── Summary ─────────────────────────────────────────────────────────────────
print()
if all_ok:
    print("\033[92m✓ All smoke tests passed — backend is public-ready!\033[0m")
else:
    print("\033[91m✗ Some tests failed — see above\033[0m")
    sys.exit(1)
