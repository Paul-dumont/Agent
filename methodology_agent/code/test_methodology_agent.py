#!/usr/bin/env python3
"""
Methodology Agent Tester
Tests all available LLM models on methodology/project design questions using the manifest.
Stores results in JSON for analysis.
"""

import json
import subprocess
import os
import time
import requests
from datetime import datetime
from pathlib import Path


def load_manifest():
    """Load the manifest with all tool descriptions."""
    with open('manifest.yaml', 'r') as f:
        content = f.read()
    return content


def load_methodology_queries():
    """Load methodology queries from JSON."""
    with open('methodology_agent/queries/methodology_agent_queries.json', 'r') as f:
        return json.load(f)


def get_available_models():
    """Get list of available Ollama models."""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        models = []
        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            if line.strip():
                model_name = line.split()[0]
                models.append(model_name)
        return models
    except Exception as e:
        print(f"Error getting models: {e}")
        return []


def build_methodology_prompt(question, manifest_content):
    """Build a prompt for methodology consultation using the manifest."""
    system_prompt = f"""You are an expert medical image analysis consultant specializing in dental and orthodontic imaging.

Your role is to provide methodology advice and workflow recommendations for image analysis projects.

Available Tools and their purposes:
{manifest_content}

When answering questions:
1. Recommend the most appropriate tools from the available set
2. Explain the recommended workflow order
3. Provide reasoning for your recommendations
4. Consider preprocessing requirements
5. Mention any important parameters or settings

Keep your response focused and practical."""

    return system_prompt, question


def query_model(model_name, system_prompt, user_question, timeout=200):
    """Query a model using Ollama REST API."""
    try:
        start_time = time.time()
        
        # Use Ollama REST API
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": f"{system_prompt}\n\nUser: {user_question}",
            "stream": False,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'response': result.get('response', '').strip(),
                'error': None,
                'latency': latency
            }
        else:
            return {
                'success': False,
                'response': None,
                'error': f"HTTP {response.status_code}: {response.text}",
                'latency': latency
            }
    except requests.Timeout:
        return {
            'success': False,
            'response': None,
            'error': f"Timeout after {timeout}s",
            'latency': timeout
        }
    except requests.ConnectionError:
        return {
            'success': False,
            'response': None,
            'error': "Cannot connect to Ollama. Is it running on localhost:11434?",
            'latency': 0
        }
    except Exception as e:
        return {
            'success': False,
            'response': None,
            'error': str(e),
            'latency': 0
        }


def analyze_response(response_text, expected_tools):
    """Analyze response to see if it mentions expected tools."""
    if not response_text:
        return 0.0, []

    mentioned_tools = []
    response_lower = response_text.lower()
    
    for tool in expected_tools:
        tool_lower = tool.lower()
        if tool_lower in response_lower:
            mentioned_tools.append(tool)
    
    # Calculate score based on how many expected tools were mentioned
    if expected_tools:
        score = len(mentioned_tools) / len(expected_tools)
    else:
        score = 0.0
    
    return score, mentioned_tools


def main():
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║                        🤖 METHODOLOGY AGENT TESTER                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝\n")

    # Load resources
    print("📚 Loading manifest and queries...")
    manifest = load_manifest()
    queries = load_methodology_queries()
    
    print("🔍 Detecting available models...")
    models = get_available_models()
    
    if not models:
        print("❌ No Ollama models found. Please install and start Ollama.")
        return
    
    print(f"✅ Found {len(models)} models: {', '.join(models)}\n")

    # Results storage
    all_results = []
    
    # Test each question with each model
    total_tests = len(queries) * len(models)
    test_count = 0
    
    for query_idx, query_data in enumerate(queries):
        query_id = query_data['query_id']
        question = query_data['question']
        category = query_data['category']
        expected_tools = query_data['expected_tools']
        
        print(f"\n{'='*80}")
        print(f"📋 Query {query_id}: {category}")
        print(f"{'='*80}")
        print(f"Question: {question}\n")
        
        system_prompt, _ = build_methodology_prompt(question, manifest)
        query_results = {
            'query_id': query_id,
            'category': category,
            'question': question,
            'expected_tools': expected_tools,
            'model_responses': []
        }
        
        for model_idx, model in enumerate(models):
            test_count += 1
            progress = f"[{test_count}/{total_tests}]"
            print(f"{progress} Testing {model}...", end=" ", flush=True)
            
            # Query the model
            result = query_model(model, system_prompt, question, timeout=200)
            
            if result['success']:
                # Analyze response
                tool_score, mentioned_tools = analyze_response(
                    result['response'], 
                    expected_tools
                )
                
                print(f"✅ {result['latency']:.1f}s (Score: {tool_score*100:.0f}%)")
                
                model_result = {
                    'model': model,
                    'success': True,
                    'response': result['response'],
                    'tool_mention_score': tool_score,
                    'mentioned_tools': mentioned_tools,
                    'expected_tools': expected_tools,
                    'latency': result['latency']
                }
            else:
                print(f"❌ Error: {result['error']}")
                model_result = {
                    'model': model,
                    'success': False,
                    'error': result['error'],
                    'tool_mention_score': 0.0,
                    'mentioned_tools': [],
                    'expected_tools': expected_tools,
                    'latency': result['latency']
                }
            
            query_results['model_responses'].append(model_result)
        
        all_results.append(query_results)
    
    # Calculate summary statistics
    print(f"\n{'='*80}")
    print("📊 SUMMARY STATISTICS")
    print(f"{'='*80}\n")
    
    model_stats = {}
    for model in models:
        model_stats[model] = {
            'total_queries': 0,
            'successful': 0,
            'failed': 0,
            'avg_score': 0.0,
            'avg_latency': 0.0,
            'total_score': 0.0,
            'total_latency': 0.0
        }
    
    for query_result in all_results:
        for model_response in query_result['model_responses']:
            model = model_response['model']
            model_stats[model]['total_queries'] += 1
            
            if model_response['success']:
                model_stats[model]['successful'] += 1
                model_stats[model]['total_score'] += model_response['tool_mention_score']
                model_stats[model]['total_latency'] += model_response['latency']
            else:
                model_stats[model]['failed'] += 1
    
    # Calculate averages
    for model in model_stats:
        if model_stats[model]['successful'] > 0:
            model_stats[model]['avg_score'] = (
                model_stats[model]['total_score'] / model_stats[model]['successful']
            )
            model_stats[model]['avg_latency'] = (
                model_stats[model]['total_latency'] / model_stats[model]['successful']
            )
    
    # Display results
    print(f"{'Model':<25} {'Success':<12} {'Score':<10} {'Latency':<12}")
    print("-" * 80)
    
    sorted_models = sorted(
        model_stats.items(),
        key=lambda x: x[1]['avg_score'],
        reverse=True
    )
    
    for model, stats in sorted_models:
        success_rate = f"{stats['successful']}/{stats['total_queries']}"
        score = f"{stats['avg_score']*100:.1f}%"
        latency = f"{stats['avg_latency']:.1f}s"
        
        print(f"{model:<25} {success_rate:<12} {score:<10} {latency:<12}")
    
    # Save results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"methodology_agent/methodology_agent_results_{timestamp}.json"
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_queries': len(queries),
        'total_models': len(models),
        'models_tested': models,
        'model_statistics': {
            model: {
                'successful': stats['successful'],
                'failed': stats['failed'],
                'avg_tool_mention_score': round(stats['avg_score'], 3),
                'avg_latency': round(stats['avg_latency'], 2)
            }
            for model, stats in model_stats.items()
        },
        'query_results': all_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}\n")


if __name__ == '__main__':
    main()
