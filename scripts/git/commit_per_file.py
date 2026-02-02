#!/usr/bin/env python3
"""
Per-file git commit script with logging
"""
import subprocess
import csv
import os
from pathlib import Path
from datetime import datetime

def run_cmd(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    # Get repo root
    repo_root, _, code = run_cmd("git rev-parse --show-toplevel")
    if code != 0:
        print("ERROR: Not in git repository")
        return 1
    
    os.chdir(repo_root)
    print(f"Working in: {repo_root}")
    
    # Setup output dirs
    log_dir = "docs/git_commits"
    diff_dir = os.path.join(log_dir, "diffs")
    log_file = os.path.join(log_dir, "git_commit_log.csv")
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    Path(diff_dir).mkdir(parents=True, exist_ok=True)
    
    # Get staged files
    stdout, _, _ = run_cmd("git diff --name-only --cached")
    files = [f for f in stdout.split('\n') if f.strip()]
    
    if not files:
        print("No staged files found.")
        return 0
    
    print(f"\nFound {len(files)} staged files\n")
    
    # Setup CSV
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['CommitSHA', 'File', 'DateISO', 'Message'])
    
    committed = 0
    errors = []
    
    for idx, file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {file}", end=" ... ")
        
        # Get diff
        diff_output, _, _ = run_cmd(f'git diff --cached -- "{file}"')
        stats_output, _, _ = run_cmd(f'git diff --cached --numstat -- "{file}"')
        
        # Save diff
        safe_name = file.replace('/', '_').replace('\\', '_').replace(':', '_')
        diff_path = os.path.join(diff_dir, f"{safe_name}.diff")
        with open(diff_path, 'w', encoding='utf-8') as f:
            f.write(diff_output)
        
        # Generate commit message
        prefix = 'chore'
        if file.endswith('.md') or file.startswith('docs/'):
            prefix = 'docs'
        elif file.startswith('tests/'):
            prefix = 'test'
        elif file.startswith('app/') and file.endswith('.py'):
            prefix = 'feat'
        elif file.startswith('scripts/'):
            prefix = 'chore'
        
        # Parse stats
        if stats_output:
            parts = stats_output.split()
            if len(parts) >= 2:
                adds, dels = parts[0], parts[1]
                summary = f"{adds} additions, {dels} deletions"
            else:
                summary = "file update"
        else:
            summary = "file update"
        
        msg = f"{prefix}: update {file} ({summary})"
        
        # Commit
        commit_cmd = f'git commit -m "{msg}" -- "{file}"'
        out, err, code = run_cmd(commit_cmd)
        
        if code == 0:
            # Get commit SHA
            sha, _, _ = run_cmd("git rev-parse --short HEAD")
            date_iso = datetime.now().isoformat()
            
            # Log
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow([sha, file, date_iso, msg])
            
            print(f"✓ {sha}")
            committed += 1
        else:
            print(f"✗ FAILED")
            errors.append({'file': file, 'error': err})
    
    print(f"\n=== Summary ===")
    print(f"Committed: {committed} / {len(files)}")
    if errors:
        print(f"Errors: {len(errors)}")
        with open(os.path.join(log_dir, "errors.json"), 'w') as f:
            import json
            json.dump(errors, f, indent=2)
    
    print(f"Log: {log_file}")
    print(f"Diffs: {diff_dir}")
    
    return 0 if len(errors) == 0 else 1

if __name__ == '__main__':
    exit(main())
