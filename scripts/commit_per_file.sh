#!/bin/bash
# Per-file git commit script

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    echo "ERROR: Not in git repository"
    exit 1
fi

cd "$REPO_ROOT"
echo "Working in: $REPO_ROOT"

LOG_DIR="docs/git_commits"
DIFF_DIR="$LOG_DIR/diffs"
LOG_FILE="$LOG_DIR/git_commit_log.csv"

# Create directories
mkdir -p "$LOG_DIR" "$DIFF_DIR"

# Initialize CSV
if [ ! -f "$LOG_FILE" ] || [ ! -s "$LOG_FILE" ]; then
    echo "CommitSHA,File,DateISO,Message" > "$LOG_FILE"
fi

# Get staged files
mapfile -t FILES < <(git diff --name-only --cached)
FILE_COUNT=${#FILES[@]}

if [ $FILE_COUNT -eq 0 ]; then
    echo "No staged files found."
    exit 0
fi

echo -e "\nFound $FILE_COUNT staged files\n"

COMMITTED=0
ERRORS=0

for ((i=0; i<FILE_COUNT; i++)); do
    FILE="${FILES[$i]}"
    NUM=$((i + 1))
    
    printf "[$NUM/$FILE_COUNT] $FILE ... "
    
    # Get diff and stats
    DIFF=$(git diff --cached -- "$FILE")
    STATS=$(git diff --cached --numstat -- "$FILE")
    
    # Save diff
    SAFE_NAME=$(echo "$FILE" | tr '/:' '_')
    DIFF_PATH="$DIFF_DIR/${SAFE_NAME}.diff"
    echo "$DIFF" > "$DIFF_PATH"
    
    # Generate commit message
    PREFIX="chore"
    [[ "$FILE" =~ \.md$ ]] && PREFIX="docs"
    [[ "$FILE" =~ ^docs/ ]] && PREFIX="docs"
    [[ "$FILE" =~ ^tests/ ]] && PREFIX="test"
    [[ "$FILE" =~ ^app/.*\.py$ ]] && PREFIX="feat"
    [[ "$FILE" =~ ^scripts/ ]] && PREFIX="chore"
    
    # Parse stats
    if [[ "$STATS" =~ ^([0-9]+)[[:space:]]+([0-9]+) ]]; then
        ADDS="${BASH_REMATCH[1]}"
        DELS="${BASH_REMATCH[2]}"
        SUMMARY="$ADDS additions, $DELS deletions"
    else
        SUMMARY="file update"
    fi
    
    MSG="$PREFIX: update $FILE ($SUMMARY)"
    
    # Commit
    if git commit -m "$MSG" -- "$FILE" >/dev/null 2>&1; then
        SHA=$(git rev-parse --short HEAD)
        DATE_ISO=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")
        echo "\"$SHA\",\"$FILE\",\"$DATE_ISO\",\"$MSG\"" >> "$LOG_FILE"
        echo "✓ $SHA"
        ((COMMITTED++))
    else
        echo "✗ FAILED"
        ((ERRORS++))
    fi
done

echo ""
echo "=== Summary ==="
echo "Committed: $COMMITTED / $FILE_COUNT"
echo "Errors: $ERRORS"
echo "Log: $LOG_FILE"
echo "Diffs: $DIFF_DIR"

[ $ERRORS -eq 0 ] && exit 0 || exit 1
