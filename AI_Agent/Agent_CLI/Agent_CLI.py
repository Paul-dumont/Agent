#!/usr/bin/env python-real

import json
import subprocess
import os
import argparse
import logging
from Agent_CLI_utils.utils import (load_manifest,build_tool_spec,extract_parameters,build_cli_args)
from Agent_CLI_utils.parameter_extraction_improved import ImprovedParameterExtractor
from Agent_CLI_utils.parameter_validator import ParameterValidator,ValidationReport


logger = logging.getLogger(__name__)

def main(input):
    module_dir = os.path.dirname(__file__)

    manifest_path = os.path.join(module_dir,"manifest.yaml")
    manifest = load_manifest(manifest_path)
    tools = build_tool_spec(manifest)
    improved_extractor = ImprovedParameterExtractor(manifest_path)
    parameter_validator = ParameterValidator(manifest_path)

    if input.modeagent == "Agent (Automated)":

        model = os.environ.get("ROUTER_MODEL", "gemma2:latest")

        few_shots = """
            Example 1 (confident):
            USER: "resize ./in to 800x600 and save to ./out"
            LLM:
            {"tool":"resize_images","confidence":0.78,"reason":"Matches resize and dimensions keywords"}

            Example 2 (partial info):
            USER: "sum the total column from data.csv"
            LLM:
            {"tool":"sum_csv""confidence":0.72,"reason":"CSV summation task"}

            Example 3 (uncertain):
            USER: "create a business report"
            LLM:
            {"tool": null,"confidence": 0.20, "reason":"No tool matches this request","candidates":[{"name":"sum_csv","score":0.22},{"name":"scrape_site","score":0.18}]}
            """.strip()
        
        system_prompt = f"""
You are a tool router. Your only output must be a single JSON object on one line.  

Rules:
- Choose exactly one 'tool' from the provided list that solves the user request.
- Output MUST strictly follow the JSON structure described below.
- If unsure, return "tool": null and suggest up to 3 'candidates' with a 'score'.
- Never output text outside JSON. No comments, no explanations outside fields.

Available Tools and their purposes:
{tools}

Few-shot examples:
{few_shots}

Strict output format (must be followed exactly):
- Always output a single JSON object with keys: "tool", "confidence", "reason".
- Optionally include "candidates" (list of  ["name", "score" ]) when "tool" is null or when you want to suggest alternatives.

"""
        
        payload =f"""system prompt: {system_prompt}
                    user prompt: {input.prompt}"""

        try:
            # Appel subprocess → ollama CLI
            result = subprocess.run(
                ["ollama", "run", model],
                input=payload,
                text=True,
                capture_output=True
            )
        except FileNotFoundError:
            raise RuntimeError("Ollama CLI introuvable. Installez-le et assurez-vous que `ollama` est dans le PATH.")

        # Le contenu retourné par la CLI est déjà du texte généré
        response = result.stdout.strip()
        # STEP 2: Extraire les paramètres

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                logger.warning(f"No JSON in response: {response}")
                return None, 0.0, "No JSON found"
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}, response: {response}")
            return None, 0.0, str(e)
        
        selected_tool = data.get("tool")
        confidence = float(data.get("confidence", 0.0))

        params, param_conf, missing_required = extract_parameters(manifest, selected_tool, input.prompt,improved_extractor,parameter_validator,model)

        list_name = ["output_folder","output_dir","output","output_path"]
        for name in list_name:
            if name in params:
                params[name] = input.outputfolder
            if name in missing_required:
                params[name] = input.outputfolder
                missing_required.remove(name)

        cli_args = build_cli_args(selected_tool, params, manifest)
        
        # Préparer la sortie
        output = {
            "status": "ready",
            "tool": selected_tool,
            "tool_confidence": round(confidence, 3),
            "parameters_confidence": round(param_conf, 3) if params else 0.0,
            "parameters": params,
            "missing_required": missing_required,
            "command": cli_args,
        }
        print(json.dumps(output))

    else:
        model = os.environ.get("ROUTER_MODEL", "gemma:latest")

        system_prompt = f"""You are an expert medical image analysis consultant specializing in dental and orthodontic imaging.

Your role is to provide methodology advice and workflow recommendations for image analysis projects.

Available Tools and their purposes:
{tools}

When answering questions:
1. Recommend the most appropriate tools from the available set
2. Explain the recommended workflow order
3. Provide reasoning for your recommendations
4. Consider preprocessing requirements
5. Mention any important parameters or settings

Keep your response focused and practical."""

        payload =f"""system prompt: {system_prompt}
                    user prompt: {input.prompt}"""

        try:
            # Appel subprocess → ollama CLI
            result = subprocess.run(
                ["ollama", "run", model],
                input=payload,
                text=True,
                capture_output=True
            )
        except FileNotFoundError:
            raise RuntimeError("Ollama CLI introuvable. Installez-le et assurez-vous que `ollama` est dans le PATH.")

        # Le contenu retourné par la CLI est déjà du texte généré
        output = result.stdout.strip()
        print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('prompt',type=str)
    parser.add_argument("inputfolder",type=str)
    parser.add_argument('outputfolder',type=str)
    parser.add_argument('modeagent',type=str)

    args = parser.parse_args()
    main(args)
