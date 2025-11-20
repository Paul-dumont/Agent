#!/usr/bin/env python3
"""
Test rapide d'un modèle
Permet de tester n'importe quel modèle avec le routeur
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def test_model(model: str, queries: list = None):
    """Test un modèle avec des queries"""
    
    if not queries:
        queries = [
            "segment dental teeth",
            "register CBCT images",
            "detect landmarks",
            "crop volume",
            "analyze 3D structure"
        ]
    
    print_header(f"🧪 Test du Modèle: {model}")
    
    # Vérifier que le modèle existe
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if model not in result.stdout:
            print(f"❌ Modèle '{model}' non installé")
            print(f"\n📥 Installer avec: ollama pull {model}")
            return False
    except subprocess.CalledProcessError:
        print("❌ Impossible de vérifier les modèles")
        return False
    
    print(f"✓ Modèle '{model}' trouvé\n")
    
    # Changer de répertoire
    work_dir = Path("/home/luciacev/Documents/AlexCodes/Agent")
    os.chdir(work_dir)
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: {query}")
        print("-" * 70)
        
        start_time = time.time()
        
        try:
            # Exécuter le routeur
            result = subprocess.run(
                ["python", "router.py", query, "--dry-run"],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "ROUTER_MODEL": model}
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # Parser la sortie JSON
                try:
                    output = result.stdout
                    # Chercher le JSON dans la sortie
                    json_start = output.find('{')
                    json_end = output.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = output[json_start:json_end]
                        data = json.loads(json_str)
                        
                        tool = data.get("tool", "unknown")
                        confidence = data.get("confidence", 0)
                        
                        status = "✓" if data.get("success") else "✗"
                        print(f"{status} Tool: {tool}")
                        print(f"  Confidence: {confidence:.2%}")
                        print(f"  Time: {elapsed:.1f}s")
                        
                        results.append({
                            "query": query,
                            "tool": tool,
                            "confidence": confidence,
                            "time": elapsed,
                            "success": True
                        })
                    else:
                        print(f"⚠ Could not parse JSON response")
                        print(f"  Time: {elapsed:.1f}s")
                        print(f"\n  Output:\n{result.stdout}")
                        
                        results.append({
                            "query": query,
                            "time": elapsed,
                            "success": False
                        })
                
                except json.JSONDecodeError:
                    print(f"⚠ Error parsing JSON response")
                    print(f"  Time: {elapsed:.1f}s")
                    
                    results.append({
                        "query": query,
                        "time": elapsed,
                        "success": False
                    })
            else:
                print(f"✗ Error: {result.stderr}")
                results.append({
                    "query": query,
                    "time": elapsed,
                    "success": False
                })
        
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout (> 120s)")
            results.append({
                "query": query,
                "time": 120,
                "success": False,
                "error": "timeout"
            })
        
        except Exception as e:
            print(f"✗ Exception: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Résumé
    print_header("📊 Résumé du Test")
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    if successful:
        avg_time = sum(r["time"] for r in successful) / len(successful)
        avg_conf = sum(r["confidence"] for r in successful) / len(successful)
        
        print(f"✓ Requêtes réussies: {len(successful)}/{len(results)}")
        print(f"  Temps moyen: {avg_time:.1f}s")
        print(f"  Confiance moyenne: {avg_conf:.2%}")
    
    if failed:
        print(f"✗ Requêtes échouées: {len(failed)}/{len(results)}")
    
    # Détails
    print(f"\nDétails:")
    for i, r in enumerate(results, 1):
        if r.get("success"):
            print(f"  {i}. {r['query'][:30]:30s} → {r['tool']:15s} ({r['time']:5.1f}s)")
        else:
            error = r.get("error", "unknown")
            print(f"  {i}. {r['query'][:30]:30s} → ERROR ({error})")
    
    # Sauvegarder les résultats
    output_file = work_dir / f"test_{model.replace(':', '_')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "model": model,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "queries_count": len(queries),
            "successful": len(successful),
            "failed": len(failed),
            "average_time": sum(r["time"] for r in successful) / len(successful) if successful else 0,
            "results": results
        }, f, indent=2)
    
    print(f"\n✓ Résultats sauvegardés: {output_file}")
    
    return len(failed) == 0

def main():
    """Point d'entrée"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_model.py <model> [query1] [query2] ...")
        print("\nExemples:")
        print("  python test_model.py mistral")
        print("  python test_model.py phi3 'segment teeth' 'register images'")
        print("\nModèles disponibles:")
        print("  tinyllama, mistral, neural-chat, phi3, llama2:13b")
        print("  openhermes, dolphin-mixtral, llama2:70b")
        return 1
    
    model = sys.argv[1]
    queries = sys.argv[2:] if len(sys.argv) > 2 else None
    
    success = test_model(model, queries)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
