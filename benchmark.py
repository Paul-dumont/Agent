#!/usr/bin/env python3
"""
Performance benchmark suite for the router agent.
Measures routing accuracy, latency, and resource usage.
"""

import json
import subprocess
import time
import statistics
from pathlib import Path
from typing import List, Dict, Tuple

class BenchmarkSuite:
    def __init__(self, router_script="router.py"):
        self.router_script = router_script
        self.results = []
        self.metrics = {
            "latencies": [],
            "accuracies": [],
            "confidences": [],
            "llm_times": []
        }
    
    def run_single_query(self, query: str, expected_tool: str = None) -> Dict:
        """Run a single query and measure performance."""
        t0 = time.time()
        
        try:
            result = subprocess.run(
                ["python", self.router_script, query, "--benchmark", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            elapsed = time.time() - t0
            
            if result.returncode not in [0, 2]:
                return {
                    "query": query,
                    "status": "error",
                    "latency": elapsed,
                    "error": result.stderr
                }
            
            output = json.loads(result.stdout)
            
            metric_data = {
                "query": query,
                "status": output.get("status"),
                "latency": elapsed,
                "chosen": output.get("chosen"),
                "confidence": output.get("confidence", 0),
                "expected": expected_tool,
                "correct": output.get("chosen") == expected_tool if expected_tool else None
            }
            
            if "metrics" in output:
                metric_data.update(output["metrics"])
            
            return metric_data
            
        except subprocess.TimeoutExpired:
            return {
                "query": query,
                "status": "timeout",
                "latency": time.time() - t0,
                "error": "Query exceeded 60s timeout"
            }
        except Exception as e:
            return {
                "query": query,
                "status": "exception",
                "latency": time.time() - t0,
                "error": str(e)
            }
    
    def run_benchmark_suite(self, queries: List[Tuple[str, str]] = None) -> None:
        """Run a suite of test queries."""
        
        if queries is None:
            # Default test queries
            queries = [
                ("identify landmarks on CBCT scans", "ali_cbct"),
                ("register my ios files", "areg_ios"),
                ("segment dental structures from CBCT", "amasss_cli"),
                ("crop a region of interest", "autocrop3d"),
                ("analyze tooth shape", "docshapeaxi"),
                ("preprocess CBCT for segmentation", "pre_aso_cbct"),
                ("automatically segment mandible and maxilla", "amasss_cli"),
                ("register intraoral surfaces", "areg_ios"),
                ("create a dental dashboard", "medx_dashboard"),
                ("summarize patient notes", "medx_summarize"),
            ]
        
        print(f"Running {len(queries)} benchmark queries...")
        print("=" * 80)
        
        for query, expected_tool in queries:
            print(f"[{len(self.results)+1}/{len(queries)}] {query[:60]}...", end=" ", flush=True)
            result = self.run_single_query(query, expected_tool)
            self.results.append(result)
            
            status = result.get("status", "unknown")
            latency = result.get("latency", 0)
            correct = result.get("correct")
            
            status_str = "✓" if correct else "✗" if correct is False else "?"
            print(f"{status_str} ({latency:.2f}s)")
            
            # Collect metrics
            if latency > 0:
                self.metrics["latencies"].append(latency)
            if "llm_time" in result:
                self.metrics["llm_times"].append(result["llm_time"])
            if "confidence" in result:
                self.metrics["confidences"].append(result["confidence"])
            if correct is not None:
                self.metrics["accuracies"].append(1 if correct else 0)
    
    def print_summary(self) -> None:
        """Print performance summary."""
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        
        total_queries = len(self.results)
        successful = sum(1 for r in self.results if r.get("status") in ["dry_run", "running"])
        errors = total_queries - successful
        
        print(f"\nQueries Run: {total_queries}")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {errors}")
        
        if self.metrics["latencies"]:
            latencies = self.metrics["latencies"]
            print(f"\nLatency Metrics (seconds):")
            print(f"  Min:     {min(latencies):.3f}s")
            print(f"  Max:     {max(latencies):.3f}s")
            print(f"  Mean:    {statistics.mean(latencies):.3f}s")
            print(f"  Median:  {statistics.median(latencies):.3f}s")
            print(f"  StdDev:  {statistics.stdev(latencies):.3f}s" if len(latencies) > 1 else "")
        
        if self.metrics["llm_times"]:
            llm_times = self.metrics["llm_times"]
            print(f"\nLLM Response Time (seconds):")
            print(f"  Min:     {min(llm_times):.3f}s")
            print(f"  Max:     {max(llm_times):.3f}s")
            print(f"  Mean:    {statistics.mean(llm_times):.3f}s")
            print(f"  Median:  {statistics.median(llm_times):.3f}s")
            llm_pct = (statistics.mean(llm_times) / statistics.mean(self.metrics["latencies"]) * 100) if self.metrics["latencies"] else 0
            print(f"  % of Total: {llm_pct:.1f}%")
        
        if self.metrics["confidences"]:
            confidences = self.metrics["confidences"]
            print(f"\nConfidence Metrics:")
            print(f"  Min:     {min(confidences):.3f}")
            print(f"  Max:     {max(confidences):.3f}")
            print(f"  Mean:    {statistics.mean(confidences):.3f}")
            print(f"  Median:  {statistics.median(confidences):.3f}")
        
        if self.metrics["accuracies"]:
            accuracy = statistics.mean(self.metrics["accuracies"])
            print(f"\nRouting Accuracy: {accuracy*100:.1f}%")
        
        print("\n" + "=" * 80)
    
    def save_results(self, filename="benchmark_results.json") -> None:
        """Save detailed results to JSON."""
        output = {
            "summary": {
                "total_queries": len(self.results),
                "successful": sum(1 for r in self.results if r.get("status") in ["dry_run", "running"]),
                "errors": sum(1 for r in self.results if r.get("status") in ["error", "timeout", "exception"])
            },
            "metrics": {
                "latencies": {
                    "min": min(self.metrics["latencies"]) if self.metrics["latencies"] else None,
                    "max": max(self.metrics["latencies"]) if self.metrics["latencies"] else None,
                    "mean": statistics.mean(self.metrics["latencies"]) if self.metrics["latencies"] else None,
                    "median": statistics.median(self.metrics["latencies"]) if self.metrics["latencies"] else None,
                },
                "llm_times": {
                    "mean": statistics.mean(self.metrics["llm_times"]) if self.metrics["llm_times"] else None,
                    "median": statistics.median(self.metrics["llm_times"]) if self.metrics["llm_times"] else None,
                },
                "confidences": {
                    "mean": statistics.mean(self.metrics["confidences"]) if self.metrics["confidences"] else None,
                    "median": statistics.median(self.metrics["confidences"]) if self.metrics["confidences"] else None,
                },
                "accuracy": statistics.mean(self.metrics["accuracies"]) if self.metrics["accuracies"] else None,
            },
            "detailed_results": self.results
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to {filename}")


if __name__ == "__main__":
    import sys
    
    suite = BenchmarkSuite()
    
    # Allow custom query file
    if len(sys.argv) > 1:
        query_file = sys.argv[1]
        if Path(query_file).exists():
            with open(query_file, "r") as f:
                queries = json.load(f)
            suite.run_benchmark_suite(queries)
        else:
            print(f"Query file {query_file} not found")
            sys.exit(1)
    else:
        suite.run_benchmark_suite()
    
    suite.print_summary()
    suite.save_results()
