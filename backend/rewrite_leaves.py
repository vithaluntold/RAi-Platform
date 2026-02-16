"""
Rewrite decision tree leaf nodes from old inverted format to direct COMPLIANT: format.

Mapping:
  "Raises compliance issue: YES" → "COMPLIANT: NO"   (was non-compliant)
  "Raises compliance issue: NO"  → "COMPLIANT: YES"  (was compliant)
  "Not Applicable"               → "COMPLIANT: N/A"

Only rewrites string leaves in yes_case/no_case fields of decision trees.
"""
import json
import glob
import os
import sys

TREE_DIR = os.path.join(os.path.dirname(__file__), "IFRS_decisiontree")

LEAF_MAP = {
    "Raises compliance issue: YES": "COMPLIANT: NO",
    "Raises compliance issue: NO": "COMPLIANT: YES",
    "Not Applicable": "COMPLIANT: N/A",
}


def rewrite_tree(node):
    """Recursively rewrite leaf node strings in a decision tree."""
    if isinstance(node, str):
        return LEAF_MAP.get(node, node)
    if isinstance(node, dict):
        result = dict(node)
        if "yes_case" in result:
            result["yes_case"] = rewrite_tree(result["yes_case"])
        if "no_case" in result:
            result["no_case"] = rewrite_tree(result["no_case"])
        return result
    return node


def main():
    dry_run = "--dry-run" in sys.argv
    files = sorted(glob.glob(os.path.join(TREE_DIR, "*.json")))

    total_rewrites = 0
    files_changed = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        original = json.dumps(data)
        file_rewrites = 0

        for section in data.get("sections", []):
            for item in section.get("items", []):
                tree = item.get("decision_tree")
                if tree:
                    rewritten = rewrite_tree(tree)
                    if json.dumps(rewritten) != json.dumps(tree):
                        item["decision_tree"] = rewritten
                        file_rewrites += 1

        if file_rewrites > 0:
            files_changed += 1
            total_rewrites += file_rewrites
            if not dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
            print(f"  {'[DRY] ' if dry_run else ''}Rewrote {file_rewrites} trees in {filename}")
        else:
            print(f"  No changes in {filename}")

    print(f"\nTotal: {total_rewrites} trees in {files_changed} files {'(dry run)' if dry_run else 'rewritten'}")


if __name__ == "__main__":
    main()
