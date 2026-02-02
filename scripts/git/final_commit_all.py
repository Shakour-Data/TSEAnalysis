#!/usr/bin/env python3
"""
Professional per-file and per-category commit script
Groups files by purpose and commits each group with meaningful messages
"""
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json

def run_cmd(cmd, show_output=False):
    """Run git command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if show_output and result.stdout:
        print(result.stdout)
    return result.stdout.strip(), result.returncode

def stage_and_commit(files, message, prefix="feat"):
    """Stage specific files and commit with message"""
    if not files:
        return True
    
    # Stage files
    for f in files:
        run_cmd(f'git add "{f}"')
    
    # Commit
    full_msg = f"{prefix}: {message}"
    _, code = run_cmd(f'git commit -m "{full_msg}"')
    return code == 0

def main():
    repo_root = subprocess.run("git rev-parse --show-toplevel", shell=True, capture_output=True, text=True).stdout.strip()
    if not repo_root:
        print("ERROR: Not in git repo")
        return 1
    
    os.chdir(repo_root)
    
    # Get all untracked and modified files
    untracked_output, _ = run_cmd("git ls-files --others --exclude-standard")
    untracked = [f for f in untracked_output.split('\n') if f.strip()]
    
    modified_output, _ = run_cmd("git diff --name-only")
    modified = [f for f in modified_output.split('\n') if f.strip()]
    
    deleted_output, _ = run_cmd("git diff --name-only --diff-filter=D")
    deleted = [f for f in deleted_output.split('\n') if f.strip()]
    
    all_files = untracked + modified + deleted
    
    if not all_files:
        print("✓ No files to commit")
        return 0
    
    print(f"📦 Total files: {len(all_files)}")
    print(f"  - Untracked: {len(untracked)}")
    print(f"  - Modified: {len(modified)}")
    print(f"  - Deleted: {len(deleted)}\n")
    
    log_file = Path("docs/git_commits/final_commits.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    commits = []
    
    # 1. Project configuration and docs (highest priority)
    config_files = [f for f in all_files if f in [
        "pyproject.toml", "setup.py", ".gitignore", "Makefile", "pytest.ini",
        "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "README.md"
    ]]
    if config_files:
        print(f"1️⃣ Configuration & Documentation ({len(config_files)} files)")
        for f in config_files:
            print(f"   + {f}")
        if stage_and_commit(config_files, "add project configuration, build setup, and documentation", "build"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "build: config & docs", len(config_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 2. Deployment scripts
    deploy_files = [f for f in all_files if f in ["deploy.ps1", "deploy.sh"]]
    if deploy_files:
        print(f"2️⃣ Deployment Scripts ({len(deploy_files)} files)")
        for f in deploy_files:
            print(f"   + {f}")
        if stage_and_commit(deploy_files, "add cross-platform deployment automation", "ci"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "ci: deployment scripts", len(deploy_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 3. Documentation
    docs_files = [f for f in all_files if f.startswith("docs/") and f not in ["docs/TODO.md"]]
    if docs_files:
        print(f"3️⃣ Documentation ({len(docs_files)} files)")
        for f in docs_files:
            print(f"   + {f}")
        if stage_and_commit(docs_files, "add comprehensive system documentation and guides", "docs"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "docs: system documentation", len(docs_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 4. Application services (new)
    service_files = [f for f in all_files if f.startswith("app/services/") and f not in ["app/services/tsetmc.py"]]
    if service_files:
        print(f"4️⃣ Application Services ({len(service_files)} files)")
        for f in service_files:
            print(f"   + {f}")
        if stage_and_commit(service_files, "add new service modules: data refresh, AI assistant, rate limiting", "feat"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "feat: new service modules", len(service_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 5. API routes (new)
    api_files = [f for f in all_files if f.startswith("app/api/") and f != "app/api/routes.py"]
    if api_files:
        print(f"5️⃣ API Endpoints ({len(api_files)} files)")
        for f in api_files:
            print(f"   + {f}")
        if stage_and_commit(api_files, "add update management API endpoints", "feat"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "feat: update API endpoints", len(api_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 6. Utility scripts
    script_files = [f for f in all_files if f.startswith("scripts/") and not f.endswith((".ps1", ".sh"))]
    script_files = [f for f in script_files if "commit" not in f]
    if script_files:
        print(f"6️⃣ Utility Scripts ({len(script_files)} files)")
        for f in script_files:
            print(f"   + {f}")
        if stage_and_commit(script_files, "add utility scripts for database, monitoring, training", "chore"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "chore: utility scripts", len(script_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 7. Models directory
    models_files = [f for f in all_files if f.startswith("models/")]
    if models_files:
        print(f"7️⃣ AI Models ({len(models_files)} files)")
        for f in models_files:
            print(f"   + {f}")
        if stage_and_commit(models_files, "add trained RandomForestClassifier model", "model"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "model: AI classifier", len(models_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 8. Data files (config and progress)
    data_files = [f for f in all_files if f.startswith("data/") and f.endswith((".json", ".db"))]
    if data_files:
        print(f"8️⃣ Configuration Data ({len(data_files)} files)")
        for f in data_files:
            print(f"   + {f}")
        if stage_and_commit(data_files, "add database update configuration and progress tracking", "chore"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "chore: data config", len(data_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 9. Core application changes
    core_files = [f for f in all_files if f in [
        "app/__init__.py", "app/core_utils.py", "app/database.py", "app/api/routes.py",
        "app/services/tsetmc.py", "requirements.txt"
    ]]
    if core_files:
        print(f"9️⃣ Core Application ({len(core_files)} files)")
        for f in core_files:
            print(f"   + {f}")
        if stage_and_commit(core_files, "update core app modules: utils, database, API, dependencies", "refactor"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "refactor: core modules", len(core_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 10. Test files
    test_files = [f for f in all_files if f.startswith("tests/")]
    if test_files:
        print(f"🔟 Tests ({len(test_files)} files)")
        for f in test_files:
            print(f"   + {f}")
        if stage_and_commit(test_files, "update test fixtures and configurations", "test"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "test: fixtures & config", len(test_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 11. Cleanup - deleted and obsolete files
    cleanup_files = [f for f in deleted if f in [".coverage", "TODO.md", "docs/TODO.md", "tmp_type1.json"]]
    if cleanup_files:
        print(f"🗑️  Cleanup ({len(cleanup_files)} files)")
        for f in cleanup_files:
            print(f"   - {f}")
        if stage_and_commit(cleanup_files, "remove obsolete test files and temporary artifacts", "chore"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "chore: cleanup", len(cleanup_files)))
            print(f"   ✓ Committed {sha}\n")
    
    # 12. Database update
    if "data/tse_data.db" in all_files:
        print(f"💾 Database")
        print(f"   ~ data/tse_data.db")
        if stage_and_commit(["data/tse_data.db"], "update TSE market data with latest symbols and prices", "data"):
            sha, _ = run_cmd("git rev-parse --short HEAD")
            commits.append((sha, "data: TSE database", 1))
            print(f"   ✓ Committed {sha}\n")
    
    # Summary
    print("\n" + "="*60)
    print("📋 COMMIT SUMMARY")
    print("="*60)
    total_files = sum(c[2] for c in commits)
    print(f"Total commits: {len(commits)}")
    print(f"Total files committed: {total_files}\n")
    
    for sha, desc, count in commits:
        print(f"  {sha} | {desc} ({count} files)")
    
    # Save log
    with open(log_file, 'w') as f:
        f.write(f"Final Commit Run - {datetime.now().isoformat()}\n")
        f.write(f"Total Commits: {len(commits)}\n")
        f.write(f"Total Files: {total_files}\n\n")
        for sha, desc, count in commits:
            f.write(f"{sha} | {desc} ({count})\n")
    
    print(f"\n✅ All commits completed successfully!")
    print(f"📄 Log saved: {log_file}")
    
    return 0

if __name__ == '__main__':
    exit(main())
