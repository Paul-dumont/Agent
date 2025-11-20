#!/usr/bin/env python3
"""
Agent Status Dashboard
Shows current status of all components
"""

import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if file exists"""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description:<40} {path}")
    return exists

def check_dir(path, description):
    """Check if directory exists"""
    exists = Path(path).is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description:<40} {path}")
    return exists

def main():
    print("=" * 80)
    print(" 🚀 AGENT LLM ROUTER - STATUS DASHBOARD")
    print("=" * 80)
    print()
    
    os.chdir(Path(__file__).parent)
    
    # Documentation files
    print("📖 DOCUMENTATION FILES:")
    print("-" * 80)
    doc_files = [
        ("README.md", "Project overview"),
        ("QUICKSTART.md", "3-step launch guide"),
        ("SETUP.md", "Detailed installation"),
        ("TODO.md", "Implementation checklist"),
        ("FLOWCHART.md", "Visual diagrams"),
        ("REPORT.md", "Completion report"),
        ("EXECUTIVE_SUMMARY.md", "Executive brief"),
        ("FILES_CREATED.md", "Files summary"),
    ]
    doc_ok = sum(check_file(f, d) for f, d in doc_files)
    print()
    
    # Configuration files
    print("⚙️  CONFIGURATION FILES:")
    print("-" * 80)
    config_files = [
        ("manifest.yaml", "Tool definitions (23)"),
        ("router.py", "LLM dispatcher"),
        ("requirements.txt", "Python dependencies"),
        ("setup.sh", "Auto-install script"),
        ("quick_launch.sh", "Quick setup launcher"),
        (".env.example", "Config template"),
    ]
    config_ok = sum(check_file(f, d) for f, d in config_files)
    print()
    
    # Utility files
    print("🧪 UTILITY FILES:")
    print("-" * 80)
    util_files = [
        ("test_config.py", "Configuration validator"),
        ("examples.sh", "Example commands"),
    ]
    util_ok = sum(check_file(f, d) for f, d in util_files)
    print()
    
    # CLI Scripts
    print("🔧 CLI SCRIPTS:")
    print("-" * 80)
    cli_dir = "CLI files"
    cli_exists = check_dir(cli_dir, "CLI scripts folder")
    if cli_exists:
        cli_files = list(Path(cli_dir).glob("*.py"))
        print(f"   📦 {len(cli_files)} Python scripts present")
    print()
    
    # Utility packages
    print("📦 UTILITY PACKAGES:")
    print("-" * 80)
    utils = [
        "ALI_CBCT_utils",
        "ALI_IOS_utils",
        "AREG_CBCT_utils",
        "AREG_IOS_utils",
        "ASO_CBCT_utils",
        "ASO_IOS_utils",
        "BATCHDENTALSEGLib",
        "Crop_Volumes_utils",
        "FlexReg_Method",
        "MedX_CLI_utils",
        "MRI2CBCT_CLI_utils",
        "runner",
    ]
    utils_ok = sum(check_dir(u, f"Utility package: {u}") for u in utils)
    print()
    
    # Summary
    print("=" * 80)
    print(" 📊 SUMMARY")
    print("=" * 80)
    
    total_checks = doc_ok + config_ok + util_ok + (1 if cli_exists else 0) + utils_ok
    expected = len(doc_files) + len(config_files) + len(util_files) + 1 + len(utils)
    
    print()
    print(f"Documentation:  {doc_ok}/{len(doc_files)} files ✓")
    print(f"Configuration:  {config_ok}/{len(config_files)} files ✓")
    print(f"Utilities:      {util_ok}/{len(util_files)} files ✓")
    print(f"CLI Scripts:    {1 if cli_exists else 0}/1 folder ✓ ({len(cli_files)} scripts)")
    print(f"Util Packages:  {utils_ok}/{len(utils)} folders ✓")
    print()
    print(f"TOTAL: {total_checks}/{expected} components ready ✓")
    print()
    
    if total_checks == expected:
        print("✅ ALL SYSTEMS READY!")
        print()
        print("Next steps:")
        print("  1. pip install -r requirements.txt")
        print("  2. ollama serve (in new terminal)")
        print("  3. python router.py 'your command'")
        print()
        return 0
    else:
        print("⚠️  Some components missing. Check above.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
