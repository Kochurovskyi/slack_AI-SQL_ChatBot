"""Run all LangSmith experiments and evaluate results.

This script runs all three experiments and provides a comprehensive analysis.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env", override=False)

from tests.langsmith.experiment_sql_generation import (
    run_experiment as run_sql_experiment,
    GROUND_TRUTH_DATASET as SQL_DATASET,
    sql_generation_target_function,
    sql_correctness_evaluator
)
from tests.langsmith.experiment_intent_classification import (
    run_experiment as run_intent_experiment,
    GROUND_TRUTH_DATASET as INTENT_DATASET,
    intent_classification_target_function,
    intent_accuracy_evaluator
)
from tests.langsmith.experiment_result_formatting import (
    run_experiment as run_formatting_experiment,
    GROUND_TRUTH_DATASET as FORMATTING_DATASET,
    formatting_target_function,
    format_accuracy_evaluator
)
from langsmith.schemas import Example, Run
import uuid
from datetime import datetime


def run_local_evaluation(dataset, target_func, evaluator, experiment_name):
    """Run local evaluation to get detailed scores."""
    print(f"  Running local evaluation for detailed scores...")
    
    # Convert to Example objects
    examples = [
        Example(
            id=str(uuid.uuid4()),
            inputs={"input": item["input"]} if "input" in item else {"input": item},
            outputs={"expected_output": item["expected_output"]} if "expected_output" in item else item.get("outputs", {}),
            metadata=item.get("metadata", {})
        )
        for item in dataset
    ]
    
    scores = []
    detailed_results = []
    
    for i, example in enumerate(examples, 1):
        try:
            output = target_func(example)
            run = Run(
                id=str(uuid.uuid4()),
                name=experiment_name.lower().replace(" ", "_"),
                start_time=datetime.now(),
                run_type="chain",
                trace_id=str(uuid.uuid4()),
                outputs=output,
                inputs=example.inputs
            )
            eval_result = evaluator(run, example)
            score = eval_result.get("score", 0.0)
            scores.append(score)
            
            detailed_results.append({
                "example": i,
                "input": list(example.inputs.values())[0] if example.inputs else "N/A",
                "score": score,
                "feedback": eval_result.get("feedback", "")[:100]  # Truncate long feedback
            })
        except Exception as e:
            scores.append(0.0)
            detailed_results.append({
                "example": i,
                "input": "N/A",
                "score": 0.0,
                "error": str(e)
            })
    
    return scores, detailed_results


def analyze_results(results, experiment_name, dataset, target_func, evaluator):
    """Analyze experiment results and return summary."""
    # Always run local evaluation for detailed scores
    scores, detailed_results = run_local_evaluation(dataset, target_func, evaluator, experiment_name)
    
    if not scores:
        return {
            "experiment": experiment_name,
            "status": "error",
            "error": "No scores generated"
        }
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    # Use threshold: 0.7 for SQL (semantic), 1.0 for others (exact match)
    threshold = 0.7 if "SQL" in experiment_name else 1.0
    passed = sum(1 for s in scores if s >= threshold)
    
    return {
        "experiment": experiment_name,
        "status": "completed",
        "total": len(scores),
        "average_score": f"{avg_score:.2%}",
        "passed": f"{passed}/{len(scores)}",
        "pass_rate": f"{passed/len(scores)*100:.1f}%",
        "scores": scores,
        "detailed_results": detailed_results
    }


def main():
    """Run all experiments and display results."""
    print("="*70)
    print("Running All LangSmith Experiments")
    print("="*70)
    print()
    
    results_summary = []
    
    # Run SQL Generation Experiment
    print("1. Running SQL Generation Experiment...")
    print("-" * 70)
    try:
        sql_results = run_sql_experiment()
        sql_summary = analyze_results(
            sql_results, 
            "SQL Generation",
            SQL_DATASET,
            sql_generation_target_function,
            sql_correctness_evaluator
        )
        results_summary.append(sql_summary)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        results_summary.append({
            "experiment": "SQL Generation",
            "status": "error",
            "error": str(e)
        })
    print()
    
    # Run Intent Classification Experiment
    print("2. Running Intent Classification Experiment...")
    print("-" * 70)
    try:
        intent_results = run_intent_experiment()
        intent_summary = analyze_results(
            intent_results,
            "Intent Classification",
            INTENT_DATASET,
            intent_classification_target_function,
            intent_accuracy_evaluator
        )
        results_summary.append(intent_summary)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        results_summary.append({
            "experiment": "Intent Classification",
            "status": "error",
            "error": str(e)
        })
    print()
    
    # Run Result Formatting Experiment
    print("3. Running Result Formatting Experiment...")
    print("-" * 70)
    try:
        formatting_results = run_formatting_experiment()
        formatting_summary = analyze_results(
            formatting_results,
            "Result Formatting",
            FORMATTING_DATASET,
            formatting_target_function,
            format_accuracy_evaluator
        )
        results_summary.append(formatting_summary)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        results_summary.append({
            "experiment": "Result Formatting",
            "status": "error",
            "error": str(e)
        })
    print()
    
    # Display Summary
    print("="*70)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*70)
    print()
    
    for summary in results_summary:
        print(f"Experiment: {summary.get('experiment', 'Unknown')}")
        print(f"  Status: {summary.get('status', 'unknown')}")
        if 'error' in summary:
            print(f"  Error: {summary['error']}")
        else:
            print(f"  Total Examples: {summary.get('total', 'N/A')}")
            print(f"  Average Score: {summary.get('average_score', 'N/A')}")
            print(f"  Passed: {summary.get('passed', 'N/A')}")
            print(f"  Pass Rate: {summary.get('pass_rate', 'N/A')}")
            
            # Show score distribution
            if 'scores' in summary:
                scores = summary['scores']
                perfect = sum(1 for s in scores if s >= 1.0)
                good = sum(1 for s in scores if 0.7 <= s < 1.0)
                poor = sum(1 for s in scores if s < 0.7)
                print(f"  Score Distribution:")
                print(f"    Perfect (1.0): {perfect}/{len(scores)}")
                print(f"    Good (0.7-1.0): {good}/{len(scores)}")
                print(f"    Poor (<0.7): {poor}/{len(scores)}")
            
            # Show failed examples if any
            if 'detailed_results' in summary:
                failed = [r for r in summary['detailed_results'] if r.get('score', 0) < 0.7]
                if failed:
                    print(f"  Failed Examples ({len(failed)}):")
                    for fail in failed[:5]:  # Show first 5 failures
                        input_str = str(fail.get('input', 'N/A'))
                        if len(input_str) > 60:
                            input_str = input_str[:60] + "..."
                        print(f"    - Example {fail['example']}: {input_str} (score: {fail['score']:.2f})")
        print()
    
    # Overall Statistics
    completed = [s for s in results_summary if s.get('status') == 'completed']
    if completed:
        total_examples = sum(int(s.get('total', 0)) for s in completed if isinstance(s.get('total'), int))
        print(f"Total Examples Tested: {total_examples}")
        print(f"Experiments Completed: {len(completed)}/3")
    
    print("="*70)
    print("View detailed results in LangSmith:")
    print("  - SQL Generation: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/4760a03d-d423-4c5b-89e7-4c2f7bf58f7d")
    print("  - Intent Classification: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/2a6af4e8-c655-4b7f-a621-c0d9d475edd2")
    print("  - Result Formatting: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/480e202f-b3ff-408a-a80b-1729909b8e09")
    print("="*70)


if __name__ == "__main__":
    main()

