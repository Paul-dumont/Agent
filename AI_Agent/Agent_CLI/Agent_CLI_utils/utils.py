import json
import subprocess
import os
import time
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from Agent_CLI_utils.parameter_extraction_improved import ImprovedParameterExtractor
from Agent_CLI_utils.parameter_validator import ParameterValidator,ValidationReport
import yaml


def load_manifest(manifest_path):
    """Load the manifest with all tool descriptions."""
    with open(manifest_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

def build_tool_spec(manifest):
    """Build tool specifications with memoization support."""
    tools = []
    for s in manifest.get("scripts", []):
        # Extract parameters from "parameters" (new structure)
        params = set()
        required_params = set()
        
        # Support old structure (patterns) and new (parameters)
        if "patterns" in s:
            # Old structure
            for p in s.get("patterns", []) or []:
                for g, flag in (p.get("args") or {}).items():
                    params.add(g)
        
        if "parameters" in s:
            # New structure
            for param in s.get("parameters", []):
                param_name = param.get("name", "")
                if param_name:
                    params.add(param_name)
                    if param.get("required", False):
                        required_params.add(param_name)
        
        # Support old structure defaults
        if "defaults" in s:
            params.update(s["defaults"].keys())

        tools.append({
            "name": s["name"],
            "description": s.get("description",""),
            "params": sorted(list(params)),           # logical names (not "--flag")
            "required_params": sorted(list(required_params)),
            "path": s["path"],
            "tags": s.get("tags", []),
            "priority": s.get("priority", 0),
        })
    return tools

def extract_parameters(manifest: Dict, tool_name: str, user_text: str,improved_extractor:ImprovedParameterExtractor,parameter_validator:ParameterValidator,model) -> Tuple[Dict[str, Any], float, List[str]]:
    
    # Get tool spec
    scripts = {s["name"]: s for s in manifest.get("scripts", [])}
    tool_spec = scripts.get(tool_name)
    if not tool_spec:
        print(f"Tool {tool_name} not found in manifest")
        return {}, 0.0, []
    
    try:
        # Créer le prompt avec few-shot examples
        prompt = improved_extractor.build_prompt(tool_name, user_text)
        payload =f"""system prompt: You are a parameter extraction expert. Output ONLY valid JSON on one line.
                    user prompt: {prompt}"""
        try:
            # Appel subprocess → ollama CLI
            result = subprocess.run(
                ["ollama", "run", model],
                input=payload,
                text=True,
                capture_output=True
            )
            response = result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError("Ollama CLI introuvable. Installez-le et assurez-vous que `ollama` est dans le PATH.")
        
        # Parser JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                raise json.JSONDecodeError("No JSON found", response, 0)
        
        extracted_raw = data.get("extracted", {})
        confidence = float(data.get("confidence", 0.0))
        
        # ÉTAPE 1.5: Conversion de types
        extracted_converted, conversion_errors = improved_extractor.convert_types(
            extracted_raw, tool_spec
        )
        if conversion_errors:
            print(f"Conversion errors: {conversion_errors}")
        
        # ÉTAPE 2: Validation
        validation_result = parameter_validator.validate(tool_name, extracted_converted)
        
        if validation_result["valid"]:
            report = ValidationReport.generate_report(tool_name, validation_result)
            print(report, file=sys.stderr)
        
        # Retourner les paramètres validés
        final_params = validation_result["params"]
        final_confidence = confidence if validation_result["valid"] else confidence * 0.6
        missing_required = validation_result["missing_required"]
        
        return final_params, final_confidence, missing_required
    
    except Exception as e:
        print(f"IMPROVED extraction failed, falling back to simple: {e}")
        # Fall back to simple extraction

def build_cli_args(tool_name: str, params: Dict[str, Any], manifest: Dict) -> List[str]:
    """Construit les arguments CLI."""
    
    scripts = {s["name"]: s for s in manifest.get("scripts", [])}
    spec = scripts[tool_name]
    
    # Fusionner avec les défauts
    defaults = {
        p["name"]: p["default"]
        for p in spec.get("parameters", [])
        if "default" in p
    }
    merged = dict(defaults)
    merged.update({k: v for k, v in (params or {}).items() if v is not None})
    cli_style = spec.get("cli_style", "positional")
    
    if cli_style == "positional":
        # Arguments positionnels
        param_list = spec.get("parameters", [])
        positional_order = spec.get("positional_order", [])
        
        cli = []
        if positional_order:
            for param_name in positional_order:
                if param_name in merged:
                    cli.append(str(merged[param_name]))
        else:
            for param in param_list:
                param_name = param.get("name", "")
                if param_name in merged:
                    cli.append(str(merged[param_name]))
        
        return [sys.executable, spec["path"]] + cli
    else:
        # Arguments nommés (--flag style)
        param2flag = {}
        for p in spec.get("parameters", []):
            param_name = p.get("name", "")
            if param_name:
                flag = p.get("flag", f"--{param_name}")
                param2flag[param_name] = flag
        
        cli = []
        for k, v in merged.items():
            flag = param2flag.get(k, f"--{k}")
            cli += [flag, str(v)]
        
        return [sys.executable, spec["path"]] + cli