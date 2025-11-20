#!/usr/bin/env python3
"""
Performance metrics visualizer for router agent.
Generates human-readable reports from benchmark results.
"""

import json
import statistics
from pathlib import Path
from datetime import datetime

class PerformanceReporter:
    def __init__(self, results_file="benchmark_results.json"):
        self.results_file = results_file
        self.data = self._load_results()
    
    def _load_results(self):
        """Load results from JSON file."""
        if not Path(self.results_file).exists():
            print(f"Error: {self.results_file} not found")
            return None
        
        with open(self.results_file, "r") as f:
            return json.load(f)
    
    def print_executive_summary(self) -> None:
        """Print high-level summary for stakeholders."""
        
        if not self.data:
            return
        
        summary = self.data.get("summary", {})
        metrics = self.data.get("metrics", {})
        
        print("\n" + "=" * 70)
        print("EXECUTIVE SUMMARY")
        print("=" * 70)
        
        total = summary.get("total_queries", 0)
        success = summary.get("successful", 0)
        errors = summary.get("errors", 0)
        
        print(f"\n✓ Success Rate: {success}/{total} ({success/total*100:.1f}%)")
        print(f"✗ Error Rate:  {errors}/{total} ({errors/total*100:.1f}%)")
        
        # Performance Grade
        accuracy = metrics.get("accuracy", 0)
        if accuracy >= 0.90:
            grade = "A+ (Excellent)"
        elif accuracy >= 0.80:
            grade = "A (Very Good)"
        elif accuracy >= 0.70:
            grade = "B (Good)"
        elif accuracy >= 0.60:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
        
        print(f"\n📊 Performance Grade: {grade}")
        print(f"📈 Routing Accuracy:  {accuracy*100:.1f}%")
        
        latency_stats = metrics.get("latencies", {})
        if latency_stats:
            print(f"\n⏱️  Response Time:     {latency_stats.get('mean', 0):.2f}s (avg)")
            print(f"   Min/Max:         {latency_stats.get('min', 0):.2f}s - {latency_stats.get('max', 0):.2f}s")
        
        conf_stats = metrics.get("confidences", {})
        if conf_stats:
            print(f"\n🎯 Confidence Level:  {conf_stats.get('mean', 0):.3f} (avg)")
            print(f"   Range:          {conf_stats.get('median', 0):.3f} (median)")
        
        print("\n" + "=" * 70 + "\n")
    
    def print_detailed_analysis(self) -> None:
        """Print detailed performance analysis."""
        
        if not self.data:
            return
        
        metrics = self.data.get("metrics", {})
        detailed = self.data.get("detailed_results", [])
        
        print("\n" + "=" * 70)
        print("DETAILED PERFORMANCE ANALYSIS")
        print("=" * 70)
        
        # Latency Analysis
        print("\n📊 LATENCY BREAKDOWN")
        print("-" * 70)
        
        latency_stats = metrics.get("latencies", {})
        if latency_stats:
            print(f"Minimum:           {latency_stats['min']:.3f}s  (best case)")
            print(f"Maximum:           {latency_stats['max']:.3f}s  (worst case)")
            print(f"Average (Mean):    {latency_stats['mean']:.3f}s")
            print(f"Median:            {latency_stats['median']:.3f}s")
            
            range_val = latency_stats['max'] - latency_stats['min']
            print(f"Range:             {range_val:.3f}s  (variation)")
            
            if latency_stats['mean'] < 5:
                print("⚡ Performance:     EXCELLENT (sub-5s response)")
            elif latency_stats['mean'] < 10:
                print("✓ Performance:      GOOD (sub-10s response)")
            else:
                print("⚠️  Performance:     SLOW (>10s response)")
        
        # LLM Response Time
        print("\n🤖 LLM RESPONSE TIME")
        print("-" * 70)
        
        llm_times = metrics.get("llm_times", {})
        if llm_times:
            print(f"Average:           {llm_times.get('mean', 0):.3f}s")
            print(f"Median:            {llm_times.get('median', 0):.3f}s")
            
            if latency_stats and latency_stats.get('mean', 0) > 0:
                pct = (llm_times.get('mean', 0) / latency_stats['mean']) * 100
                print(f"% of Total Time:   {pct:.1f}%")
                print("💡 Insight: LLM inference is the primary bottleneck")
        
        # Confidence Analysis
        print("\n🎯 CONFIDENCE METRICS")
        print("-" * 70)
        
        conf_stats = metrics.get("confidences", {})
        if conf_stats:
            mean = conf_stats.get('mean', 0)
            median = conf_stats.get('median', 0)
            print(f"Mean Confidence:   {mean:.3f}")
            print(f"Median Confidence: {median:.3f}")
            
            # Interpret confidence
            if mean >= 0.8:
                print("✓ Interpretation:  HIGH confidence in routing decisions")
            elif mean >= 0.6:
                print("⚠️  Interpretation:  MODERATE confidence")
            else:
                print("✗ Interpretation:  LOW confidence - consider threshold adjustment")
        
        # Routing Accuracy
        print("\n✅ ROUTING ACCURACY")
        print("-" * 70)
        
        accuracy = metrics.get("accuracy", 0)
        print(f"Overall Accuracy:  {accuracy*100:.1f}%")
        
        if accuracy >= 0.9:
            print("✓ Status:          EXCELLENT - highly reliable routing")
        elif accuracy >= 0.8:
            print("✓ Status:          GOOD - reliable routing")
        elif accuracy >= 0.7:
            print("⚠️  Status:          ACCEPTABLE - may need optimization")
        else:
            print("✗ Status:          POOR - significant routing errors detected")
        
        # Error Analysis
        print("\n⚠️  ERROR ANALYSIS")
        print("-" * 70)
        
        total = len(detailed)
        errors = sum(1 for r in detailed if r.get("status") in ["error", "timeout", "exception"])
        misroutes = sum(1 for r in detailed if r.get("correct") is False)
        
        print(f"Total Errors:      {errors}/{total} ({errors/total*100:.1f}%)")
        print(f"Misroutes:         {misroutes}/{total} ({misroutes/total*100:.1f}%)")
        
        if errors > 0:
            print("\n  Error Details:")
            for r in detailed:
                if r.get("status") in ["error", "timeout", "exception"]:
                    print(f"    - {r.get('query', 'unknown')[:40]}")
                    print(f"      {r.get('error', 'unknown error')[:50]}")
        
        print("\n" + "=" * 70 + "\n")
    
    def print_optimization_recommendations(self) -> None:
        """Print recommendations for optimization."""
        
        if not self.data:
            return
        
        metrics = self.data.get("metrics", {})
        accuracy = metrics.get("accuracy", 0)
        latency_stats = metrics.get("latencies", {})
        
        print("\n" + "=" * 70)
        print("OPTIMIZATION RECOMMENDATIONS")
        print("=" * 70)
        
        recommendations = []
        
        # Accuracy recommendations
        if accuracy < 0.70:
            recommendations.append({
                "priority": "🔴 HIGH",
                "category": "ACCURACY",
                "issue": f"Low routing accuracy ({accuracy*100:.1f}%)",
                "actions": [
                    "Increase confidence threshold: export ROUTER_THRESHOLD=\"0.60\"",
                    "Use more capable model: export ROUTER_MODEL=\"mistral:latest\"",
                    "Review tool descriptions in manifest.yaml",
                    "Analyze failed queries for patterns"
                ]
            })
        
        # Latency recommendations
        if latency_stats.get('mean', 0) > 15:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "LATENCY",
                "issue": f"High response time ({latency_stats.get('mean', 0):.1f}s)",
                "actions": [
                    "Switch to faster model: export ROUTER_MODEL=\"tinyllama\"",
                    "Check LLM server status: ps aux | grep ollama",
                    "Monitor system resources: top, free",
                    "Consider using smaller manifest (fewer tools)"
                ]
            })
        
        # LLM Performance
        llm_times = metrics.get("llm_times", {})
        if llm_times and latency_stats.get('mean', 0) > 0:
            pct = (llm_times.get('mean', 0) / latency_stats['mean']) * 100
            if pct > 95:
                recommendations.append({
                    "priority": "🔵 INFO",
                    "category": "LLM",
                    "issue": "LLM is bottleneck (>95% of time)",
                    "actions": [
                        "This is expected - LLM inference dominates latency",
                        "Consider hardware acceleration: GPU support in Ollama",
                        "Or accept latency and optimize accuracy instead"
                    ]
                })
        
        # Confidence recommendations
        conf_stats = metrics.get("confidences", {})
        if conf_stats.get('mean', 0) < 0.5:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "CONFIDENCE",
                "issue": f"Low average confidence ({conf_stats.get('mean', 0):.3f})",
                "actions": [
                    "Increase LLM model capacity",
                    "Improve tool descriptions in manifest",
                    "Add more distinctive tags to tools",
                    "Verify queries match tool capabilities"
                ]
            })
        
        if not recommendations:
            print("\n✓ System is performing well!")
            print("  - Routing accuracy is good")
            print("  - Response times are acceptable")
            print("  - Confidence levels are appropriate")
            print("\n  Continue monitoring performance regularly.")
        else:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['priority']} {rec['category']}")
                print(f"   Issue: {rec['issue']}")
                print(f"   Recommended Actions:")
                for action in rec['actions']:
                    print(f"     • {action}")
        
        print("\n" + "=" * 70 + "\n")
    
    def export_html_report(self, filename="performance_report.html") -> None:
        """Export a formatted HTML report."""
        
        if not self.data:
            return
        
        summary = self.data.get("summary", {})
        metrics = self.data.get("metrics", {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Router Agent Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 20px; border-radius: 5px; }}
        .metric-box {{ background: white; padding: 15px; margin: 10px 0; 
                       border-left: 4px solid #667eea; border-radius: 3px; }}
        .success {{ border-left-color: #4caf50; }}
        .warning {{ border-left-color: #ff9800; }}
        .error {{ border-left-color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; color: #999; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Router Agent Performance Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metric-box success">
        <h2>📊 Summary</h2>
        <table>
            <tr>
                <td>Total Queries:</td>
                <td><strong>{summary.get('total_queries', 0)}</strong></td>
            </tr>
            <tr>
                <td>Successful:</td>
                <td><strong>{summary.get('successful', 0)}</strong></td>
            </tr>
            <tr>
                <td>Success Rate:</td>
                <td><strong>{(summary.get('successful', 0)/max(summary.get('total_queries', 1), 1))*100:.1f}%</strong></td>
            </tr>
        </table>
    </div>
    
    <div class="metric-box">
        <h2>⏱️  Latency Metrics</h2>
        <table>
            <tr>
                <td>Mean Response Time:</td>
                <td><strong>{metrics.get('latencies', {}).get('mean', 0):.3f}s</strong></td>
            </tr>
            <tr>
                <td>Median Response Time:</td>
                <td><strong>{metrics.get('latencies', {}).get('median', 0):.3f}s</strong></td>
            </tr>
            <tr>
                <td>Min/Max:</td>
                <td><strong>{metrics.get('latencies', {}).get('min', 0):.3f}s / {metrics.get('latencies', {}).get('max', 0):.3f}s</strong></td>
            </tr>
        </table>
    </div>
    
    <div class="metric-box">
        <h2>✅ Accuracy Metrics</h2>
        <table>
            <tr>
                <td>Routing Accuracy:</td>
                <td><strong>{metrics.get('accuracy', 0)*100:.1f}%</strong></td>
            </tr>
            <tr>
                <td>Mean Confidence:</td>
                <td><strong>{metrics.get('confidences', {}).get('mean', 0):.3f}</strong></td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Router Agent Performance Monitoring System</p>
    </div>
</body>
</html>
"""
        
        with open(filename, "w") as f:
            f.write(html)
        
        print(f"✓ HTML report saved to {filename}")


if __name__ == "__main__":
    import sys
    
    results_file = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results.json"
    
    reporter = PerformanceReporter(results_file)
    
    if reporter.data:
        reporter.print_executive_summary()
        reporter.print_detailed_analysis()
        reporter.print_optimization_recommendations()
        reporter.export_html_report()
    else:
        print("No results to report. Run benchmark.py first.")
