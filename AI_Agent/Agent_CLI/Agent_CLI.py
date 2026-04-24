#!/usr/bin/env python-real

import re
from difflib import SequenceMatcher
import json
import subprocess
import os
import argparse
import logging
import ollama
from Agent_CLI_utils.utils import (load_manifest,build_tool_spec,extract_parameters,build_cli_args)
from Agent_CLI_utils.parameter_extraction_improved import ImprovedParameterExtractor
from Agent_CLI_utils.parameter_validator import ParameterValidator,ValidationReport


logger = logging.getLogger(__name__)

def get_tool_def(manifest, tool_name: str):
    for tool in manifest.get("scripts", []):
        if tool.get("name") == tool_name:
            return tool
    return None

def complete_with_defaults(manifest, tool_name: str,params:dict):
    tool = get_tool_def(manifest, tool_name)
    if not tool:
        return []
    defaults = {p.get("name",""):p.get("default","") for p in tool.get("parameters", []) if not p.get("required", False) and "default" in p}
    for name,default in defaults.items():
        if name not in params:
            params[name]= default
    
    return params

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

        # Similarité “fuzzy” entre requête et nom/desc (petit bonus)
        score += 2.0 * _sim(user_text, name)
        score += 1.0 * _sim(user_text, desc[:120])

        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:k]]
    return top

def build_candidates_block(candidates):
    """
    Construit un bloc compact (5 lignes) pour le routeur.
    """
    lines = []
    for i, s in enumerate(candidates, 1):
        name = s.get("name", "")
        desc = (s.get("description", "") or "").strip()
        desc = re.sub(r"\s+", " ", desc)
        desc = desc[:140]  # TRÈS important: court
        tags = s.get("tags") or []
        tags = [str(x) for x in tags[:8]]  # max 8 tags
        tag_str = ", ".join(tags)
        lines.append(f"{i}) {name} — {desc} | tags: {tag_str}")
    return "\n".join(lines)

def build_candidates_block_ask(candidates):
    """
    Construit un bloc compact (5 lignes) pour le routeur.
    """
    lines = []
    for i, s in enumerate(candidates, 1):
        name = s.get("name", "")
        desc = (s.get("description", "") or "").strip()
        desc = re.sub(r"\s+", " ", desc)
        desc = desc[:140]  # TRÈS important: court
        tags = s.get("tags") or []
        tags = [str(x) for x in tags[:8]]  # max 8 tags
        tag_str = ", ".join(tags)
        params = s.get("parameters","")
        lines.append(f"{i}) {name} — {desc} | tags: {tag_str}| parameters:{params}")
    return "\n".join(lines)


def main(input):
    module_dir = os.path.dirname(__file__)

    manifest_path = os.path.join(module_dir,"manifest.yaml")
    manifest = load_manifest(manifest_path)
    tools = build_tool_spec(manifest)
    improved_extractor = ImprovedParameterExtractor(manifest_path)
    parameter_validator = ParameterValidator(manifest_path)

    if input.modeagent == "Agent (Automated)":

        folder_list_str = "\n".join(input.folders.split(","))

        folders_context = f"""
        FOLDERS_CONTEXT:
        {folder_list_str}

        Rules:
        - Treat FOLDERS_CONTEXT as the source of truth for paths.
        - If a required path parameter is missing, try to infer it from FOLDERS_CONTEXT.
        - If multiple candidates exist, pick the most specific match and explain briefly in 'reason'.
        """.strip()

        modele = os.environ.get("ROUTER_MODEL", "gemma2:latest")

        candidates = retrieve_candidates(manifest, input.prompt, k=3)
        candidates_block = build_candidates_block(candidates)

        router_system = """
You are a tool router. Output ONLY one JSON object.
Schema:
{"tool": string|null, "confidence": number, "reason": string}

Rules:
- Choose tool ONLY from the candidate list provided by the user message.
- If none match, set tool = null and confidence <= 0.4.
- Do not invent tool names.
- Keep reason short (max 1 sentence).
""".strip()

        router_user = f"""
USER_REQUEST:
{input.prompt}

CANDIDATES (choose exactly one name from this list):
{candidates_block}
""".strip()

        try:
            response = ollama.chat(
                model=modele,
                messages=[
                    {"role": "system", "content": router_system},
                    {"role": "user", "content": router_user}
                ],
                format="json"
            )
        except Exception as e:
            raise RuntimeError(f"Router error: {e}")

        data = json.loads(response["message"]["content"])
        selected_tool = data.get("tool")
        confidence = float(data.get("confidence", 0.0))

        if selected_tool and selected_tool!="null" and selected_tool!="None":
            new_prompt = f"""{input.prompt}\n\n{folders_context}"""

            params, param_conf, missing_required,removed = extract_parameters(manifest, selected_tool, new_prompt,improved_extractor,parameter_validator,modele)

            params = complete_with_defaults(manifest,selected_tool,params)

            if removed:
                params[removed[0]] = input.temp_folder
                missing_required.remove(removed[0])

            cli_args = build_cli_args(selected_tool, params, manifest)
            
            output = {
                "tool": selected_tool,
                "tool_confidence": round(confidence, 3),
                "parameters_confidence": round(param_conf, 3) if params else 0.0,
                "parameters": params,
                "missing_required": missing_required,
                "command": cli_args,
            }
            print(json.dumps(output))

        else:

            output = {
                "tool": None,
                "tool_confidence": None,
                "parameters_confidence": None,
                "parameters": None,
                "missing_required": None,
                "command": None,
            }
            print(json.dumps(output))

    else:
        candidates = retrieve_candidates(manifest, input.prompt, k=3)
        candidates_block = build_candidates_block_ask(candidates)
        modele = os.environ.get("ROUTER_MODEL", "gemma:latest")

        system_prompt = f"""You are an expert medical image analysis consultant specializing in dental and orthodontic imaging.

Your role is to provide methodology advice and workflow recommendations for image analysis projects.

Available Tools and their purposes:
{candidates_block}

When answering questions:
1. Recommend the most appropriate tools from the available set
2. Explain the recommended workflow order
3. Provide reasoning for your recommendations
4. Consider preprocessing requirements
5. Mention any important parameters or settings

Keep your response focused and practical."""
        
        try:
            response = ollama.chat(
                model=modele,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input.prompt}
                ]
            )
        except Exception as e:
            raise RuntimeError(f"Router error: {e}")

        output = response["message"]["content"].strip()
        output = output.replace("*","")
        output = output.replace("#","")
        print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('prompt',type=str)
    parser.add_argument('folders',type=str)
    parser.add_argument('modeagent',type=str)
    parser.add_argument('temp_folder',type=str)

    try:
        args = parser.parse_args()
    except SystemExit:
        print("Erreur de parsing : Vérifiez le nombre d'arguments envoyés !")
        raise
    main(args)
