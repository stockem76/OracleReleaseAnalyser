"""
Fetch all 26C features from the live Oracle Readiness MCP server.
Queries each pillar's module breakdown and drills into each module for feature details.

Usage
-----
    ORACLE_MCP_TOKEN=<bearer-token> python get_26c_features.py
"""
import os
import urllib.request
import urllib.parse
import json

BASE  = "https://oraclereadinesssrc-dzxnqq.fly.dev"
TOKEN = os.environ.get("ORACLE_MCP_TOKEN", "")
if not TOKEN:
    raise SystemExit(
        "ERROR: ORACLE_MCP_TOKEN environment variable not set.\n"
        "Export your Bearer token before running:\n"
        "  $env:ORACLE_MCP_TOKEN='<your-token>'"
    )
HDRS  = {"Authorization": f"Bearer {TOKEN}"}

def fetch(path):
    req = urllib.request.Request(BASE + path, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

all_features = []
pillar_stats  = {}

# The server has both lowercase and uppercase product_family entries.
# The uppercase ones (ERP=27, HCM=47, SCM=55) have the real detail.
# But the /api/releases/{release}/{pillar} route is CASE-INSENSITIVE so we
# need to look at both to find all unique modules.
# 
# Better approach: use /api/releases JSON which already totals by product_family.
# Let's enumerate all unique product_families and modules from the releases endpoint,
# then drill into each module.

releases = fetch("/api/releases")
r26 = next(r for r in releases["releases"] if r["release"] == "26C")

print("=== 26C Summary ===")
print(f"Total features: {r26['totals']['features']}")
print(f"Setup required: {r26['totals']['setup_required']}")
print(f"Opt-in: {r26['totals']['opt_in']}")
print(f"AI features: {r26['totals']['ai']}")
print(f"Redwood: {r26['totals']['redwood']}")
print(f"Large scale: {r26['totals']['large_scale']}")
print()
print("By product family:")
for pf, s in r26["pillars"].items():
    print(f"  {pf}: features={s.get('features',0)}, setup={s.get('setup_required',0)}, "
          f"opt_in={s.get('opt_in',0)}, ai={s.get('ai',0)}, "
          f"redwood={s.get('redwood',0)}, large={s.get('large_scale',0)}")
    pillar_stats[pf] = s

print()

# Drill into modules for each pillar (only non-lowercase ones that have real detail)
# The uppercase pillars (ERP, HCM, SCM) with high feature counts are the real ones
detail_pillars = [
    ("ERP",     "Enterprise Resource Planning"),
    ("HCM",     "Human Capital Management"),
    ("SCM",     "Supply Chain & Manufacturing"),
]

for pillar, label in detail_pillars:
    pdata = fetch(f"/api/releases/26C/{pillar}")
    print(f"=== {label} ({pillar}) — {pdata['totals']['features']} features ===")
    for m in pdata.get("modules", []):
        mname = m["module"]
        mn_enc = urllib.parse.quote(mname)
        mdata = fetch(f"/api/releases/26C/{pillar}/{mn_enc}")
        feats = mdata.get("features", [])
        print(f"  [{mname}] — {len(feats)} features, setup={m.get('setup_required',0)}, "
              f"opt_in={m.get('opt_in',0)}, ai={m.get('ai',0)}, redwood={m.get('redwood',0)}")
        for feat in feats:
            feat["pillar"]      = pillar
            feat["pillar_label"]= label
            feat["module"]      = mname
            all_features.append(feat)
            flags = []
            if feat.get("setup_required"):  flags.append("SETUP")
            if feat.get("opt_in_required"): flags.append("OPT-IN")
            if feat.get("is_ai"):           flags.append("AI")
            if feat.get("is_redwood"):      flags.append("REDWOOD")
            impact = feat.get("impact") or ""
            if "Large" in impact:           flags.append("LARGE")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            print(f"    • {feat['feature_name']}{flag_str}")
            if feat.get("description") and feat["description"] != feat["feature_name"]:
                desc = feat["description"][:120] + "..." if len(feat["description"]) > 120 else feat["description"]
                print(f"      {desc}")

print(f"\nTotal features extracted: {len(all_features)}")

with open("dfl_26c_features.json", "w", encoding="utf-8") as f:
    json.dump({"summary": r26["totals"], "pillars": pillar_stats, "features": all_features}, f, indent=2)
print("Saved to dfl_26c_features.json")
