#!/bin/bash
# Generate .design/specs/INDEX.md from spec metadata

cd "$(dirname "$0")/.."
SPECS_DIR="specs"
INDEX_FILE="$SPECS_DIR/INDEX.md"

# Count specs
TOTAL=$(ls -1 $SPECS_DIR/*.md 2>/dev/null | grep -v INDEX.md | grep -v TEMPLATE.md | wc -l | tr -d ' ')

# Generate index
cat > "$INDEX_FILE" <<EOF
# Design Specifications

**Last updated**: $(date +"%Y-%m-%d %H:%M")
**Total specs**: $TOTAL

---

## All Specifications

EOF

# List all specs with metadata
for spec in $SPECS_DIR/*.md; do
  if [ "$(basename "$spec")" != "INDEX.md" ] && [ "$(basename "$spec")" != "TEMPLATE.md" ]; then
    filename=$(basename "$spec")
    # Extract title (first # heading)
    title=$(grep -m 1 "^# " "$spec" | sed 's/^# //')
    # Extract status from YAML
    status=$(grep "^status:" "$spec" | sed 's/status: //' | tr -d ' ')
    # Extract date from YAML
    date=$(grep "^date:" "$spec" | sed 's/date: //' | tr -d ' ')
    # Extract tags from YAML
    tags=$(grep "^tags:" "$spec" | sed 's/tags: //' | tr -d ' ')

    echo "### $title" >> "$INDEX_FILE"
    echo "**Status**: $status | **Date**: $date" >> "$INDEX_FILE"
    if [ -n "$tags" ]; then
      echo "**Tags**: $tags" >> "$INDEX_FILE"
    fi
    echo "[View spec](./$filename)" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
  fi
done

echo "Generated $INDEX_FILE"
