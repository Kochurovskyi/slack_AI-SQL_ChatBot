"""LangSmith experiment for intent classification.

This experiment evaluates the Router Agent's ability to correctly
classify user intent (SQL_QUERY, CSV_EXPORT, SQL_RETRIEVAL, OFF_TOPIC).
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env", override=False)

from langsmith import evaluate
from langsmith.schemas import Example, Run

from ai.agents.router_agent import get_router_agent


# Ground truth dataset: 15 examples
GROUND_TRUTH_DATASET = [
    {
        "input": "How many apps do we have?",
        "expected_output": "SQL_QUERY",
        "metadata": {"intent_type": "database_query"}
    },
    {
        "input": "Export the results to CSV",
        "expected_output": "CSV_EXPORT",
        "metadata": {"intent_type": "export_request"}
    },
    {
        "input": "Show me the SQL query you used",
        "expected_output": "SQL_RETRIEVAL",
        "metadata": {"intent_type": "sql_retrieval"}
    },
    {
        "input": "What is the weather today?",
        "expected_output": "OFF_TOPIC",
        "metadata": {"intent_type": "off_topic"}
    },
    {
        "input": "Download the data as CSV file",
        "expected_output": "CSV_EXPORT",
        "metadata": {"intent_type": "export_request"}
    },
    {
        "input": "How many Android apps are there?",
        "expected_output": "SQL_QUERY",
        "metadata": {"intent_type": "database_query"}
    },
    {
        "input": "What SQL did you run?",
        "expected_output": "SQL_RETRIEVAL",
        "metadata": {"intent_type": "sql_retrieval"}
    },
    {
        "input": "Hello, how are you?",
        "expected_output": "OFF_TOPIC",
        "metadata": {"intent_type": "off_topic"}
    },
    {
        "input": "What is the total revenue?",
        "expected_output": "SQL_QUERY",
        "metadata": {"intent_type": "database_query"}
    },
    {
        "input": "Save results as CSV",
        "expected_output": "CSV_EXPORT",
        "metadata": {"intent_type": "export_request"}
    },
    {
        "input": "Show me the query",
        "expected_output": "SQL_RETRIEVAL",
        "metadata": {"intent_type": "sql_retrieval"}
    },
    {
        "input": "Tell me a joke",
        "expected_output": "OFF_TOPIC",
        "metadata": {"intent_type": "off_topic"}
    },
    {
        "input": "List all iOS apps",
        "expected_output": "SQL_QUERY",
        "metadata": {"intent_type": "database_query"}
    },
    {
        "input": "I want to download the data",
        "expected_output": "CSV_EXPORT",
        "metadata": {"intent_type": "export_request"}
    },
    {
        "input": "Display the SQL statement",
        "expected_output": "SQL_RETRIEVAL",
        "metadata": {"intent_type": "sql_retrieval"}
    }
]


def intent_classification_target_function(example: Example) -> Dict[str, Any]:
    """Target function that classifies user intent.
    
    Args:
        example: Dictionary with 'input' key containing the user message
        
    Returns:
        Dictionary with 'output' key containing the classified intent
    """
    try:
        router = get_router_agent()
        thread_ts = "experiment_test_thread"
        
        # Classify intent
        input_text = example.inputs.get("input", "")
        result = router.classify_intent(
            user_message=input_text,
            thread_ts=thread_ts
        )
        
        intent = result.get("intent", "SQL_QUERY")
        
        return {
            "output": intent,
            "metadata": {
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", "")
            }
        }
    except Exception as e:
        return {
            "output": "ERROR",
            "metadata": {"error": str(e)}
        }


def intent_accuracy_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluator that checks if classified intent matches expected intent.
    
    Args:
        run: The run containing the classified intent
        example: The example with expected intent
        
    Returns:
        Dictionary with score and feedback
    """
    predicted_intent = run.outputs.get("output", "").strip()
    expected_intent = example.outputs.get("expected_output", "").strip()
    
    is_correct = predicted_intent == expected_intent
    
    confidence = run.outputs.get("metadata", {}).get("confidence", 0.0)
    
    return {
        "key": "intent_accuracy",
        "score": 1.0 if is_correct else 0.0,
        "feedback": f"Expected: {expected_intent}, Predicted: {predicted_intent}, Confidence: {confidence:.2f}"
    }


def run_experiment():
    """Run the intent classification experiment."""
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
            dataset_name = "intent_classification_experiment"
            
            # Try to get existing dataset or create new one
            try:
                dataset = client.read_dataset(dataset_name=dataset_name)
                print(f"Using existing dataset: {dataset_name}")
            except Exception:
                # Create new dataset
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description="Intent classification experiment with 15 examples"
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
                intent_classification_target_function,
                data=dataset_name,  # Use dataset name instead of examples list
                evaluators=[intent_accuracy_evaluator],
                experiment_prefix="intent_classification_experiment",
                max_concurrency=1,
            )
            print(f"\n{'='*60}")
            print(f"Intent Classification Experiment Results (LangSmith)")
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
                output = intent_classification_target_function(example)
                run = Run(
                    id=str(uuid.uuid4()),
                    name="intent_classification",
                    start_time=datetime.now(),
                    run_type="chain",
                    trace_id=str(uuid.uuid4()),
                    outputs=output,
                    inputs=example.inputs
                )
                eval_result = intent_accuracy_evaluator(run, example)
                results.append({
                    "example": example.inputs.get("input", ""),
                    "expected": example.outputs.get("expected_output", ""),
                    "predicted": output.get("output", ""),
                    "score": eval_result.get("score", 0.0),
                    "feedback": eval_result.get("feedback", "")
                })
                scores.append(eval_result.get("score", 0.0))
            except Exception as e:
                results.append({
                    "example": example.inputs.get("input", ""),
                    "error": str(e),
                    "score": 0.0
                })
                scores.append(0.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        print(f"\n{'='*60}")
        print(f"Intent Classification Experiment Results (Local)")
        print(f"{'='*60}")
        print(f"Total examples: {len(examples)}")
        print(f"Average score: {avg_score:.2%}")
        print(f"Correct: {sum(scores)}/{len(scores)}")
        print(f"\nDetailed Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Input: {result.get('example', 'N/A')}")
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

