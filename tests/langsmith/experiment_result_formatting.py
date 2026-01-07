"""LangSmith experiment for result formatting.

This experiment evaluates the Formatting Service's ability to format
query results appropriately (simple text vs. markdown tables).
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env", override=False)

from langsmith import evaluate
from langsmith.schemas import Example, Run

from services.formatting_service import FormattingService


# Ground truth dataset: 15 examples
GROUND_TRUTH_DATASET = [
    {
        "input": {
            "data": [{"count": 49}],
            "query_type": "simple_count"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [{"platform": "iOS", "count": 21}, {"platform": "Android", "count": 29}],
            "query_type": "group_by"
        },
        "expected_output": "table",  # Should use table format
        "metadata": {"rows": 2, "columns": 2}
    },
    {
        "input": {
            "data": [{"total_revenue": 125000.50}],
            "query_type": "aggregation"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [
                {"app_name": "App1", "platform": "iOS", "revenue": 1000},
                {"app_name": "App2", "platform": "Android", "revenue": 2000},
                {"app_name": "App3", "platform": "iOS", "revenue": 1500},
                {"app_name": "App4", "platform": "Android", "revenue": 3000},
                {"app_name": "App5", "platform": "iOS", "revenue": 2500}
            ],
            "query_type": "list"
        },
        "expected_output": "table",  # Should use table format (>5 rows)
        "metadata": {"rows": 5, "columns": 3}
    },
    {
        "input": {
            "data": [{"avg_installs": 50634.84}],
            "query_type": "aggregation"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [
                {"country": "US", "revenue": 10000},
                {"country": "UK", "revenue": 8000},
                {"country": "DE", "revenue": 6000}
            ],
            "query_type": "group_by"
        },
        "expected_output": "simple",  # Should use simple format (≤5 rows, ≤3 columns)
        "metadata": {"rows": 3, "columns": 2}
    },
    {
        "input": {
            "data": [{"count": 0}],
            "query_type": "simple_count"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [
                {"app_name": "App1", "revenue": 1000, "installs": 50000, "country": "US"},
                {"app_name": "App2", "revenue": 2000, "installs": 60000, "country": "UK"},
                {"app_name": "App3", "revenue": 1500, "installs": 55000, "country": "DE"},
                {"app_name": "App4", "revenue": 3000, "installs": 70000, "country": "FR"},
                {"app_name": "App5", "revenue": 2500, "installs": 65000, "country": "IT"},
                {"app_name": "App6", "revenue": 1800, "installs": 58000, "country": "ES"}
            ],
            "query_type": "list"
        },
        "expected_output": "table",  # Should use table format (>5 rows)
        "metadata": {"rows": 6, "columns": 4}
    },
    {
        "input": {
            "data": [{"max_revenue": 50000.00}],
            "query_type": "aggregation"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [
                {"platform": "iOS", "count": 21},
                {"platform": "Android", "count": 29}
            ],
            "query_type": "group_by"
        },
        "expected_output": "simple",  # Should use simple format (≤5 rows, ≤3 columns)
        "metadata": {"rows": 2, "columns": 2}
    },
    {
        "input": {
            "data": [],
            "query_type": "simple_count"
        },
        "expected_output": "simple",  # Empty results should use simple format
        "metadata": {"rows": 0, "columns": 0}
    },
    {
        "input": {
            "data": [
                {"country": "US", "total": 10000},
                {"country": "UK", "total": 8000},
                {"country": "DE", "total": 6000},
                {"country": "FR", "total": 5000},
                {"country": "IT", "total": 4000},
                {"country": "ES", "total": 3000}
            ],
            "query_type": "group_by"
        },
        "expected_output": "table",  # Should use table format (>5 rows)
        "metadata": {"rows": 6, "columns": 2}
    },
    {
        "input": {
            "data": [{"sum": 250000}],
            "query_type": "aggregation"
        },
        "expected_output": "simple",  # Should use simple format
        "metadata": {"rows": 1, "columns": 1}
    },
    {
        "input": {
            "data": [
                {"app_name": "App1", "revenue": 1000},
                {"app_name": "App2", "revenue": 2000},
                {"app_name": "App3", "revenue": 1500}
            ],
            "query_type": "list"
        },
        "expected_output": "simple",  # Should use simple format (≤5 rows, ≤3 columns)
        "metadata": {"rows": 3, "columns": 2}
    },
    {
        "input": {
            "data": [
                {"col1": "A", "col2": "B", "col3": "C", "col4": "D"},
                {"col1": "E", "col2": "F", "col3": "G", "col4": "H"}
            ],
            "query_type": "list"
        },
        "expected_output": "table",  # Should use table format (>3 columns)
        "metadata": {"rows": 2, "columns": 4}
    }
]


def formatting_target_function(example: Example) -> Dict[str, Any]:
    """Target function that formats query results.
    
    Args:
        example: Dictionary with 'input' key containing data and query_type
        
    Returns:
        Dictionary with 'output' key indicating format type used
    """
    try:
        formatting_service = FormattingService()
        
        input_data = example.inputs.get("input", {})
        data = input_data.get("data", [])
        query_type = input_data.get("query_type", "simple_count")
        
        # Format the result
        formatted = formatting_service.format_result(
            data=data,
            query_type=query_type
        )
        
        # Determine format type (simple or table)
        # Check if formatted result contains table markers
        format_type = "table" if "|" in formatted and "---" in formatted else "simple"
        
        return {
            "output": format_type,
            "metadata": {
                "formatted_length": len(formatted),
                "rows": len(data),
                "columns": len(data[0].keys()) if data else 0
            }
        }
    except Exception as e:
        return {
            "output": "ERROR",
            "metadata": {"error": str(e)}
        }


def format_accuracy_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluator that checks if format type matches expected format.
    
    Args:
        run: The run containing the format type used
        example: The example with expected format type
        
    Returns:
        Dictionary with score and feedback
    """
    predicted_format = run.outputs.get("output", "").strip()
    expected_format = example.outputs.get("expected_output", "").strip()
    
    is_correct = predicted_format == expected_format
    
    metadata = run.outputs.get("metadata", {})
    rows = metadata.get("rows", 0)
    columns = metadata.get("columns", 0)
    
    return {
        "key": "format_accuracy",
        "score": 1.0 if is_correct else 0.0,
        "feedback": f"Expected: {expected_format}, Predicted: {predicted_format}, Rows: {rows}, Columns: {columns}"
    }


def run_experiment():
    """Run the result formatting experiment."""
    # Check for LangSmith API key (now loaded from .env)
    langsmith_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    upload_results = bool(langsmith_key)
    
    if not upload_results:
        print("Warning: LANGSMITH_API_KEY not set in .env file.")
        print("Experiment will run locally without uploading to LangSmith.")
    
    # Convert dataset to Example objects
    import uuid
    examples = [
        Example(
            id=str(uuid.uuid4()),
            inputs={"input": item["input"]},
            outputs={"expected_output": item["expected_output"]},
            metadata=item.get("metadata", {})
        )
        for item in GROUND_TRUTH_DATASET
    ]
    
    # Run evaluation with LangSmith if API key is available
    if upload_results:
        try:
            # Create dataset in LangSmith first
            from langsmith import Client
            client = Client()
            dataset_name = "result_formatting_experiment"
            
            # Try to get existing dataset or create new one
            try:
                dataset = client.read_dataset(dataset_name=dataset_name)
                print(f"Using existing dataset: {dataset_name}")
            except Exception:
                # Create new dataset
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description="Result formatting experiment with 15 examples"
                )
                # Add examples to dataset
                client.create_examples(
                    inputs=[{"input": item["input"]} for item in GROUND_TRUTH_DATASET],
                    outputs=[{"expected_output": item["expected_output"]} for item in GROUND_TRUTH_DATASET],
                    dataset_id=dataset.id
                )
                print(f"Created new dataset: {dataset_name} with {len(GROUND_TRUTH_DATASET)} examples")
            
            # Run evaluation using dataset
            results = evaluate(
                formatting_target_function,
                data=dataset_name,  # Use dataset name instead of examples list
                evaluators=[format_accuracy_evaluator],
                experiment_prefix="result_formatting_experiment",
                max_concurrency=1,
            )
            print(f"\n{'='*60}")
            print(f"Result Formatting Experiment Results (LangSmith)")
            print(f"{'='*60}")
            print(f"Total examples: {len(examples)}")
            print(f"Results uploaded to LangSmith")
            print(f"Results: {results}")
            print(f"{'='*60}\n")
            return results
        except Exception as e:
            print(f"Error uploading to LangSmith: {e}")
            print("Falling back to local evaluation...")
            upload_results = False
    
    # Run evaluation locally
    if not upload_results:
        from datetime import datetime
        results = []
        scores = []
        for example in examples:
            try:
                output = formatting_target_function(example)
                run = Run(
                    id=str(uuid.uuid4()),
                    name="result_formatting",
                    start_time=datetime.now(),
                    run_type="chain",
                    trace_id=str(uuid.uuid4()),
                    outputs=output,
                    inputs=example.inputs
                )
                eval_result = format_accuracy_evaluator(run, example)
                results.append({
                    "example": f"{len(example.inputs.get('input', {}).get('data', []))} rows, {len(example.inputs.get('input', {}).get('data', [{}])[0].keys()) if example.inputs.get('input', {}).get('data') else 0} cols",
                    "expected": example.outputs.get("expected_output", ""),
                    "predicted": output.get("output", ""),
                    "score": eval_result.get("score", 0.0),
                    "feedback": eval_result.get("feedback", "")
                })
                scores.append(eval_result.get("score", 0.0))
            except Exception as e:
                results.append({
                    "example": "N/A",
                    "error": str(e),
                    "score": 0.0
                })
                scores.append(0.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        print(f"\n{'='*60}")
        print(f"Result Formatting Experiment Results (Local)")
        print(f"{'='*60}")
        print(f"Total examples: {len(examples)}")
        print(f"Average score: {avg_score:.2%}")
        print(f"Correct: {sum(scores)}/{len(scores)}")
        print(f"\nDetailed Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Example: {result.get('example', 'N/A')}")
            if 'error' in result:
                print(f"   ERROR: {result['error']}")
            else:
                print(f"   Expected: {result.get('expected', 'N/A')}")
                print(f"   Predicted: {result.get('predicted', 'N/A')}")
                print(f"   Score: {result.get('score', 0.0):.1f}")
        print(f"{'='*60}\n")
        return results


if __name__ == "__main__":
    run_experiment()

