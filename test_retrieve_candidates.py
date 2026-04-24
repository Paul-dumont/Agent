#!/usr/bin/env python3
"""
Test script pour vérifier si retrieve_candidates supprime le tool prévu.
Lit les JSON depuis Param_and_cli/queries et teste chaque query.
"""

import re
import json
import os
from difflib import SequenceMatcher
import yaml

def _tokenize(text: str):
    if not text:
        return []
    return re.findall(r"[a-z0-9_]+", text.lower())

def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def retrieve_candidates(manifest: dict, user_text: str, k: int = 5):
    """
    Retourne top-k scripts candidats (dicts du manifest) via scoring local.
    """
    scripts = manifest.get("scripts", [])
    t = user_text.lower()
    toks = set(_tokenize(user_text))

    scored = []
    for s in scripts:
        name = s.get("name", "")
        desc = s.get("description", "")
        tags = [str(x).lower() for x in (s.get("tags") or [])]

        score = 0.0

        # Match nom direct
        if name and name.lower() in t:
            score += 10.0

        # Tags
        for tag in tags:
            if tag in toks:
                score += 3.0
            elif tag in t:  # match substring
                score += 1.5

        # Desc tokens (léger)
        desc_toks = set(_tokenize(desc))
        score += 0.25 * len(desc_toks.intersection(toks))

        # Similarité "fuzzy" entre requête et nom/desc (petit bonus)
        score += 2.0 * _sim(user_text, name)
        score += 1.0 * _sim(user_text, desc[:120])

        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:k]]
    return top

def load_manifest(path: str):
    """Charge le manifest YAML."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # Chemins
    base_dir = "/home/luciacev/Documents/AlexCodes/Agent"
    manifest_path = os.path.join(base_dir, "AI_Agent/Agent_CLI/manifest.yaml")
    queries_dir = os.path.join(base_dir, "Param_and_cli/queries")
    
    # Charger le manifest
    manifest = load_manifest(manifest_path)
    
    # Résultats
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "failed_cases": []
    }
    
    # Parcourir tous les fichiers JSON
    json_files = [f for f in os.listdir(queries_dir) if f.endswith('.json')]
    
    print(f"📊 Analysing {len(json_files)} query files...\n")
    
    for json_file in sorted(json_files):
        json_path = os.path.join(queries_dir, json_file)
        
        with open(json_path, 'r') as f:
            queries = json.load(f)
        
        print(f"\n{'='*80}")
        print(f"📄 File: {json_file} ({len(queries)} queries)")
        print(f"{'='*80}")
        
        for idx, query_obj in enumerate(queries, 1):
            query_text = query_obj.get("query", "")
            expected_tool = query_obj.get("expected_tool", "")
            
            if not query_text or not expected_tool:
                continue
            
            results["total"] += 1
            
            # Obtenir les candidats
            candidates = retrieve_candidates(manifest, query_text, k=5)
            candidate_names = [c.get("name", "") for c in candidates]
            
            # Vérifier si le tool attendu est dans les candidats
            is_present = expected_tool in candidate_names
            rank = candidate_names.index(expected_tool) + 1 if is_present else -1
            
            # Score du tool attendu
            tool_def = None
            for t in manifest.get("scripts", []):
                if t.get("name") == expected_tool:
                    tool_def = t
                    break
            
            # Calculer le score manuellement pour debug
            if tool_def:
                name = tool_def.get("name", "")
                desc = tool_def.get("description", "")
                tags = [str(x).lower() for x in (tool_def.get("tags") or [])]
                t = query_text.lower()
                toks = set(_tokenize(query_text))
                
                score = 0.0
                if name and name.lower() in t:
                    score += 10.0
                
                for tag in tags:
                    if tag in toks:
                        score += 3.0
                    elif tag in t:
                        score += 1.5
                
                desc_toks = set(_tokenize(desc))
                score += 0.25 * len(desc_toks.intersection(toks))
                score += 2.0 * _sim(query_text, name)
                score += 1.0 * _sim(query_text, desc[:120])
            else:
                score = 0.0
            
            status = "✅ PASS" if is_present else "❌ FAIL"
            
            if is_present:
                results["passed"] += 1
                print(f"\n  [{idx:2d}] {status} | Query {idx}")
                print(f"       Expected: {expected_tool}")
                print(f"       Rank: #{rank} / Score: {score:.2f}")
                print(f"       Candidates: {', '.join(candidate_names[:3])}")
            else:
                results["failed"] += 1
                results["failed_cases"].append({
                    "file": json_file,
                    "query_idx": idx,
                    "query": query_text[:100] + "...",
                    "expected": expected_tool,
                    "candidates": candidate_names[:5],
                    "score": score
                })
                print(f"\n  [{idx:2d}] {status} | Query {idx}")
                print(f"       Expected: {expected_tool}")
                print(f"       Score: {score:.2f}")
                print(f"       Top candidates: {', '.join(candidate_names[:5])}")
                print(f"       Query: {query_text[:80]}...")
    
    # Rapport final
    print(f"\n\n{'='*80}")
    print(f"📈 FINAL REPORT")
    print(f"{'='*80}")
    print(f"Total queries tested: {results['total']}")
    print(f"✅ Passed: {results['passed']} ({100*results['passed']/max(1, results['total']):.1f}%)")
    print(f"❌ Failed: {results['failed']} ({100*results['failed']/max(1, results['total']):.1f}%)")
    
    if results["failed"] > 0:
        print(f"\n{'='*80}")
        print(f"🔴 FAILED CASES DETAILS")
        print(f"{'='*80}")
        for case in results["failed_cases"][:10]:  # Afficher les 10 premiers
            print(f"\n📌 File: {case['file']}, Query #{case['query_idx']}")
            print(f"   Expected tool: {case['expected']}")
            print(f"   Tool score: {case['score']:.2f}")
            print(f"   Top 5 candidates: {', '.join(case['candidates'])}")
            print(f"   Query: {case['query']}")
        
        if len(results["failed_cases"]) > 10:
            print(f"\n... and {len(results['failed_cases']) - 10} more failures")
    
    print(f"\n")

if __name__ == "__main__":
    main()
