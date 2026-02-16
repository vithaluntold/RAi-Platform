"""Analyze all IFRS decision tree JSON files."""
import json
import os
import glob

stats = {
    "total_items": 0,
    "max_depth": 0,
    "question_types": set(),
    "context_types": set(),
    "standards": [],
    "terminal_outcomes": set(),
}


def measure_depth(node, d=1):
    if isinstance(node, str):
        return d
    mx = d
    for k in ["yes_case", "no_case"]:
        if k in node and isinstance(node[k], dict):
            mx = max(mx, measure_depth(node[k], d + 1))
    return mx


def collect_terminals(node, results):
    if isinstance(node, str):
        results.add(node.strip())
        return
    for k in ["yes_case", "no_case"]:
        if k in node:
            collect_terminals(node[k], results)


os.chdir(os.path.join(os.path.dirname(__file__), "IFRS_decisiontree"))

for f in sorted(glob.glob("*.json")):
    with open(f) as fh:
        data = json.load(fh)
    for sec in data.get("sections", []):
        items = sec.get("items", [])
        stats["total_items"] += len(items)
        stats["standards"].append(f'{sec["section"]} ({len(items)} items)')
        for item in items:
            if item.get("question_type"):
                stats["question_types"].add(item["question_type"])
            if item.get("context_required"):
                stats["context_types"].add(item["context_required"])
            dt = item.get("decision_tree", {})
            stats["max_depth"] = max(stats["max_depth"], measure_depth(dt))
            collect_terminals(dt, stats["terminal_outcomes"])

print(f"Total standards: {len(stats['standards'])}")
print(f"Total items (questions): {stats['total_items']}")
print(f"Max decision tree depth: {stats['max_depth']}")
print(f"Question types: {stats['question_types']}")
print(f"Context types: {stats['context_types']}")
print(f"Terminal outcomes: {stats['terminal_outcomes']}")
print()
for s in stats["standards"]:
    print(f"  {s}")

# Show one deep example
print("\n--- Example of deepest tree ---")
for f in sorted(glob.glob("*.json")):
    with open(f) as fh:
        data = json.load(fh)
    for sec in data.get("sections", []):
        for item in sec.get("items", []):
            dt = item.get("decision_tree", {})
            if measure_depth(dt) == stats["max_depth"]:
                print(f"File: {f}, ID: {item['id']}, Ref: {item.get('reference')}")
                print(json.dumps(dt, indent=2)[:800])
                print("...")
                break
        else:
            continue
        break
    else:
        continue
    break
