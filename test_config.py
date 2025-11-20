#!/usr/bin/env python3
"""
Test script for the Agent LLM Router
Vérifie que tout est bien configuré
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Vérifier la version Python"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    return True

def check_manifest():
    """Vérifier que manifest.yaml existe et est valide"""
    manifest_path = Path("manifest.yaml")
    if not manifest_path.exists():
        print(f"❌ manifest.yaml not found at {manifest_path.absolute()}")
        return False
    
    try:
        import yaml
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        
        if "scripts" not in data:
            print("❌ manifest.yaml: missing 'scripts' section")
            return False
        
        num_scripts = len(data["scripts"])
        print(f"✓ manifest.yaml valid ({num_scripts} scripts)")
        return True
    except ImportError:
        print("❌ PyYAML not installed (pip install pyyaml)")
        return False
    except Exception as e:
        print(f"❌ manifest.yaml parsing error: {e}")
        return False

def check_router():
    """Vérifier que router.py existe"""
    router_path = Path("router.py")
    if not router_path.exists():
        print(f"❌ router.py not found at {router_path.absolute()}")
        return False
    
    print(f"✓ router.py found")
    return True

def check_ollama():
    """Vérifier si Ollama est installé et accessible"""
    try:
        import ollama
        print(f"✓ ollama Python package installed")
        
        # Essayer de se connecter
        try:
            models = ollama.list()
            num_models = len(models)
            print(f"✓ Ollama accessible ({num_models} model(s) available)")
            return True
        except Exception as e:
            print(f"⚠️  Ollama not running? (Error: {e})")
            print(f"   Start with: ollama serve")
            return False
    except ImportError:
        print("⚠️  ollama Python package not installed (pip install ollama)")
        return False

def check_cli_files():
    """Vérifier que les fichiers CLI existent"""
    cli_dir = Path("CLI files")
    if not cli_dir.exists():
        print(f"❌ 'CLI files' directory not found")
        return False
    
    py_files = list(cli_dir.glob("*.py"))
    if not py_files:
        print(f"❌ No Python files in 'CLI files' directory")
        return False
    
    print(f"✓ CLI files directory valid ({len(py_files)} scripts)")
    return True

def main():
    print("=" * 50)
    print("Agent LLM Router - Configuration Check")
    print("=" * 50)
    print()
    
    checks = [
        ("Python version", check_python),
        ("manifest.yaml", check_manifest),
        ("router.py", check_router),
        ("CLI files", check_cli_files),
        ("Ollama", check_ollama),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        results[name] = check_func()
        print()
    
    print()
    print("=" * 50)
    
    all_ok = all(results.values())
    required_ok = all([
        results["Python version"],
        results["manifest.yaml"],
        results["router.py"],
        results["CLI files"],
    ])
    
    if required_ok and results["Ollama"]:
        print("✅ All checks passed! You can use: python router.py \"<command>\"")
    elif required_ok:
        print("⚠️  Core checks passed, but Ollama not running")
        print("   Start Ollama: ollama serve")
        print("   Then try: python router.py \"<command>\" --dry-run")
    else:
        print("❌ Some required checks failed. See above for details.")
        return 1
    
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
