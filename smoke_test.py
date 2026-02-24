#!/usr/bin/env python3
"""API smoke test — run from project root after backend starts."""
import urllib.request, urllib.parse, json, sys

BASE = "http://localhost:8000"

def req(method, path, token=None, form=None):
    url = BASE + path
    data = urllib.parse.urlencode(form).encode() if form else None
    headers = {"Content-Type": "application/x-www-form-urlencoded"} if form else {}
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
    print(f"  {mark}  {label}{('  →  ' + detail) if detail else ''}")
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

r3 = req("POST", "/auth/login", form={"username": "coordinator@psgai.edu.in", "password": "Password@123"})
tok_coord = r3.get("access_token")
all_ok &= check("coordinator login", bool(tok_coord))

r4 = req("POST", "/auth/login", form={"username": "admin@psgai.edu.in", "password": "Password@123"})
tok_admin = r4.get("access_token")
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

props_coord = req("GET", "/proposals", token=tok_coord)
all_ok &= check("coordinator sees proposals", isinstance(props_coord, list), f"{len(props_coord)}")

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
