"""Evaluate LangSmith experiment results by querying the API.

This script fetches results from LangSmith and provides detailed analysis.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env", override=False)

from langsmith import Client


def get_experiment_results(dataset_name: str, experiment_prefix: str):
    """Get results from LangSmith for a specific experiment."""
    client = Client()
    
    try:
        # Get dataset
        dataset = client.read_dataset(dataset_name=dataset_name)
        
        # Get recent experiments
        experiments = client.list_experiments(
            dataset_id=dataset.id,
            limit=1
        )
        
        if not experiments:
            return None
        
        latest_experiment = experiments[0]
        
        # Get experiment results
        results = client.get_experiment_results(latest_experiment.id)
        
        return {
            "experiment_id": latest_experiment.id,
            "dataset_id": dataset.id,
            "results": results,
            "experiment_name": latest_experiment.name
        }
    except Exception as e:
        print(f"Error fetching results: {e}")
        return None


def analyze_experiment(experiment_info):
    """Analyze experiment results."""
    if not experiment_info:
        return None
    
    # Extract scores from results
    scores = []
    total_examples = 0
    
    try:
        results = experiment_info.get('results', [])
        total_examples = len(results)
        
        for result in results:
            # Try to get evaluation score
            if hasattr(result, 'evaluation_results') and result.evaluation_results:
                for eval_result in result.evaluation_results:
                    if hasattr(eval_result, 'score'):
                        scores.append(eval_result.score)
                    elif isinstance(eval_result, dict):
                        scores.append(eval_result.get('score', 0.0))
    except Exception as e:
        print(f"Error analyzing results: {e}")
    
    if not scores:
        return {
            "experiment": experiment_info.get('experiment_name', 'Unknown'),
            "total": total_examples,
            "status": "completed",
            "note": "Scores not available in API response - check LangSmith UI"
        }
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    passed = sum(1 for s in scores if s >= 0.7)
    
    return {
        "experiment": experiment_info.get('experiment_name', 'Unknown'),
        "total": len(scores),
        "average_score": f"{avg_score:.2%}",
        "passed": f"{passed}/{len(scores)}",
        "pass_rate": f"{passed/len(scores)*100:.1f}%",
        "min_score": f"{min(scores):.2%}",
        "max_score": f"{max(scores):.2%}"
    }


def main():
    """Fetch and analyze all experiment results."""
    print("="*70)
    print("LangSmith Experiment Results Analysis")
    print("="*70)
    print()
    
    experiments = [
        ("sql_generation_experiment", "SQL Generation"),
        ("intent_classification_experiment", "Intent Classification"),
        ("result_formatting_experiment", "Result Formatting")
    ]
    
    all_results = []
    
    for dataset_name, display_name in experiments:
        print(f"Fetching results for {display_name}...")
        experiment_info = get_experiment_results(dataset_name, dataset_name)
        if experiment_info:
            analysis = analyze_experiment(experiment_info)
            if analysis:
                analysis["experiment"] = display_name
                all_results.append(analysis)
        print()
    
    # Display Summary
    print("="*70)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*70)
    print()
    
    for result in all_results:
        print(f"Experiment: {result.get('experiment', 'Unknown')}")
        print(f"  Total Examples: {result.get('total', 'N/A')}")
        if 'average_score' in result:
            print(f"  Average Score: {result['average_score']}")
            print(f"  Passed: {result.get('passed', 'N/A')}")
            print(f"  Pass Rate: {result.get('pass_rate', 'N/A')}")
            print(f"  Score Range: {result.get('min_score', 'N/A')} - {result.get('max_score', 'N/A')}")
        else:
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Note: {result.get('note', 'N/A')}")
        print()
    
    print("="*70)
    print("View detailed results in LangSmith:")
    print("  - SQL Generation: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/4760a03d-d423-4c5b-89e7-4c2f7bf58f7d")
    print("  - Intent Classification: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/2a6af4e8-c655-4b7f-a621-c0d9d475edd2")
    print("  - Result Formatting: https://smith.langchain.com/o/00e6c5f8-89a3-4061-bdd8-ce97966a1d7a/datasets/480e202f-b3ff-408a-a80b-1729909b8e09")
    print("="*70)


if __name__ == "__main__":
    main()

