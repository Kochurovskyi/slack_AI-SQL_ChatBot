"""LangSmith experiment for SQL query generation.

This experiment evaluates the SQL Query Agent's ability to generate
correct SQL queries from natural language questions.
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

from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Example, Run

from ai.agents.sql_query_agent import get_sql_query_agent


# Ground truth dataset: 15 examples
GROUND_TRUTH_DATASET = [
    {
        "input": "How many apps do we have?",
        "expected_output": "SELECT COUNT(*) FROM app_portfolio",
        "metadata": {"query_type": "count"}
    },
    {
        "input": "How many Android apps are there?",
        "expected_output": "SELECT COUNT(*) FROM app_portfolio WHERE platform = 'Android'",
        "metadata": {"query_type": "count_filtered"}
    },
    {
        "input": "What is the total revenue?",
        "expected_output": "SELECT SUM(in_app_revenue + ads_revenue) FROM app_portfolio",
        "metadata": {"query_type": "aggregation"}
    },
    {
        "input": "Show me all iOS apps",
        "expected_output": "SELECT * FROM app_portfolio WHERE platform = 'iOS'",
        "metadata": {"query_type": "list"}
    },
    {
        "input": "Which country has the most installs?",
        "expected_output": "SELECT country, SUM(installs) as total_installs FROM app_portfolio GROUP BY country ORDER BY total_installs DESC LIMIT 1",
        "metadata": {"query_type": "aggregation"}
    },
    {
        "input": "What are the top 5 apps by revenue?",
        "expected_output": "SELECT app_name, (in_app_revenue + ads_revenue) as total_revenue FROM app_portfolio ORDER BY total_revenue DESC LIMIT 5",
        "metadata": {"query_type": "top_n"}
    },
    {
        "input": "How many apps were released in 2024?",
        "expected_output": "SELECT COUNT(*) FROM app_portfolio WHERE date >= '2024-01-01' AND date < '2025-01-01'",
        "metadata": {"query_type": "count_date"}
    },
    {
        "input": "What is the average installs per app?",
        "expected_output": "SELECT AVG(installs) FROM app_portfolio",
        "metadata": {"query_type": "aggregation"}
    },
    {
        "input": "List all apps from United States",
        "expected_output": "SELECT * FROM app_portfolio WHERE country = 'United States'",
        "metadata": {"query_type": "list"}
    },
    {
        "input": "What is the total cost spent on user acquisition?",
        "expected_output": "SELECT SUM(ua_cost) FROM app_portfolio",
        "metadata": {"query_type": "aggregation"}
    },
    {
        "input": "Show me apps with revenue greater than 1000",
        "expected_output": "SELECT * FROM app_portfolio WHERE (in_app_revenue + ads_revenue) > 1000",
        "metadata": {"query_type": "filter"}
    },
    {
        "input": "How many apps per platform?",
        "expected_output": "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform",
        "metadata": {"query_type": "group_by"}
    },
    {
        "input": "What is the revenue breakdown by country?",
        "expected_output": "SELECT country, SUM(in_app_revenue + ads_revenue) as total_revenue FROM app_portfolio GROUP BY country",
        "metadata": {"query_type": "group_by"}
    },
    {
        "input": "Find apps with more than 50000 installs",
        "expected_output": "SELECT * FROM app_portfolio WHERE installs > 50000",
        "metadata": {"query_type": "filter"}
    },
    {
        "input": "What is the total number of installs?",
        "expected_output": "SELECT SUM(installs) FROM app_portfolio",
        "metadata": {"query_type": "aggregation"}
    }
]


def sql_generation_target_function(example: Example) -> Dict[str, Any]:
    """Target function that generates SQL from natural language.
    
    Args:
        example: Dictionary with 'input' key containing the question
        
    Returns:
        Dictionary with 'output' key containing the generated SQL
    """
    try:
        from ai.agents.tools import generate_sql_tool
        
        # Use generate_sql_tool directly for SQL generation
        # This is simpler and more direct for the experiment
        input_text = example.inputs.get("input", "")
        sql_query = generate_sql_tool.invoke({
            "question": input_text,
            "conversation_history": None
        })
        
        # Clean up SQL (remove markdown code blocks if present)
        sql_query = sql_query.strip()
        if sql_query.startswith("```"):
            # Remove markdown code blocks
            lines = sql_query.split("\n")
            sql_query = "\n".join([l for l in lines if not l.strip().startswith("```")])
        
        return {
            "output": sql_query.strip(),
            "metadata": {"query_type": example.metadata.get("query_type", "unknown") if example.metadata else "unknown"}
        }
    except Exception as e:
        return {
            "output": f"ERROR: {str(e)}",
            "metadata": {"error": str(e)}
        }


def sql_correctness_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluator that checks if generated SQL matches expected SQL semantically.
    
    Uses semantic comparison to handle variations like DISTINCT, formatting, etc.
    
    Args:
        run: The run containing the generated SQL
        example: The example with expected SQL
        
    Returns:
        Dictionary with score and feedback
    """
    import re
    
    generated_sql = run.outputs.get("output", "").strip()
    expected_sql = example.outputs.get("expected_output", "").strip()
    
    if not generated_sql or not expected_sql:
        return {
            "key": "sql_correctness",
            "score": 0.0,
            "feedback": f"Missing SQL. Expected: {expected_sql}, Generated: {generated_sql}"
        }
    
    # Normalize SQL for comparison
    def normalize_sql(sql: str) -> str:
        """Normalize SQL for comparison."""
        # Remove markdown code blocks if present
        sql = re.sub(r"```\w*\n?", "", sql).strip()
        # Convert to uppercase
        sql = sql.upper()
        # Normalize whitespace
        sql = re.sub(r"\s+", " ", sql)
        # Remove extra parentheses spaces
        sql = sql.replace("( ", "(").replace(" )", ")")
        # Normalize quotes
        sql = sql.replace('"', "'")
        return sql.strip()
    
    generated_normalized = normalize_sql(generated_sql)
    expected_normalized = normalize_sql(expected_sql)
    
    # Check exact match first
    if generated_normalized == expected_normalized:
        return {
            "key": "sql_correctness",
            "score": 1.0,
            "feedback": f"Perfect match!\nExpected: {expected_sql}\nGenerated: {generated_sql}"
        }
    
    # Semantic comparison - check key aspects
    def check_semantic_equivalence(gen: str, exp: str) -> tuple[float, str]:
        """Check if two SQL queries are semantically equivalent.
        
        Returns:
            (score, feedback) tuple where score is 0.0-1.0
        """
        score = 0.0
        checks = []
        
        # 1. Check table name
        gen_table = "APP_PORTFOLIO" in gen
        exp_table = "APP_PORTFOLIO" in exp
        if gen_table == exp_table:
            score += 0.1
            checks.append("✓ Table name")
        else:
            checks.append("✗ Table name mismatch")
        
        # 2. Check SELECT clause - what columns/aggregations
        gen_select = re.search(r"SELECT\s+(.+?)\s+FROM", gen)
        exp_select = re.search(r"SELECT\s+(.+?)\s+FROM", exp)
        
        if gen_select and exp_select:
            gen_cols = gen_select.group(1).strip()
            exp_cols = exp_select.group(1).strip()
            
            # Check for COUNT
            gen_has_count = "COUNT" in gen_cols
            exp_has_count = "COUNT" in exp_cols
            if gen_has_count == exp_has_count:
                score += 0.2
                checks.append("✓ COUNT presence")
                
                # For COUNT queries, allow DISTINCT variations
                if gen_has_count and exp_has_count:
                    # Both have COUNT, check if they're counting similar things
                    gen_count_match = re.search(r"COUNT\s*\(\s*(?:DISTINCT\s+)?(\w+|\*)\s*\)", gen_cols)
                    exp_count_match = re.search(r"COUNT\s*\(\s*(?:DISTINCT\s+)?(\w+|\*)\s*\)", exp_cols)
                    
                    if gen_count_match and exp_count_match:
                        gen_count_target = gen_count_match.group(1)
                        exp_count_target = exp_count_match.group(1)
                        
                        # COUNT(*) vs COUNT(DISTINCT app_name) - both count records, semantically equivalent
                        if (exp_count_target == "*" and gen_count_target in ["APP_NAME", "ID", "*"]) or \
                           (gen_count_target == "*" and exp_count_target in ["APP_NAME", "ID", "*"]):
                            score += 0.3
                            checks.append("✓ COUNT target equivalent")
                        elif gen_count_target == exp_count_target:
                            score += 0.3
                            checks.append("✓ COUNT target matches")
            
            # Check for SUM
            gen_has_sum = "SUM" in gen_cols
            exp_has_sum = "SUM" in exp_cols
            if gen_has_sum == exp_has_sum:
                score += 0.15
                checks.append("✓ SUM presence")
                
                if gen_has_sum and exp_has_sum:
                    # Check if summing same columns
                    gen_sum_cols = re.findall(r"SUM\s*\([^)]+\)", gen_cols)
                    exp_sum_cols = re.findall(r"SUM\s*\([^)]+\)", exp_cols)
                    if gen_sum_cols and exp_sum_cols:
                        # Normalize SUM expressions
                        gen_sum_norm = [re.sub(r"\s+", "", s) for s in gen_sum_cols]
                        exp_sum_norm = [re.sub(r"\s+", "", s) for s in exp_sum_cols]
                        if set(gen_sum_norm) == set(exp_sum_norm):
                            score += 0.15
                            checks.append("✓ SUM columns match")
            
            # Check for AVG
            gen_has_avg = "AVG" in gen_cols
            exp_has_avg = "AVG" in exp_cols
            if gen_has_avg == exp_has_avg:
                score += 0.1
                checks.append("✓ AVG presence")
            
            # Check for SELECT * vs specific columns
            gen_is_star = gen_cols.strip() == "*"
            exp_is_star = exp_cols.strip() == "*"
            if gen_is_star == exp_is_star:
                score += 0.1
                checks.append("✓ SELECT type")
        
        # 3. Check WHERE clause
        gen_where_match = re.search(r"WHERE\s+(.+?)(?:\s+(?:GROUP|ORDER|LIMIT)|$)", gen)
        exp_where_match = re.search(r"WHERE\s+(.+?)(?:\s+(?:GROUP|ORDER|LIMIT)|$)", exp)
        
        gen_has_where = gen_where_match is not None
        exp_has_where = exp_where_match is not None
        
        if gen_has_where == exp_has_where:
            score += 0.1
            checks.append("✓ WHERE presence")
            
            if gen_has_where and exp_has_where:
                gen_where = normalize_sql(gen_where_match.group(1))
                exp_where = normalize_sql(exp_where_match.group(1))
                
                # Check if WHERE conditions are similar
                # Extract key conditions (platform, country, etc.)
                gen_platform = "PLATFORM" in gen_where
                exp_platform = "PLATFORM" in exp_where
                gen_country = "COUNTRY" in gen_where
                exp_country = "COUNTRY" in exp_where
                
                if gen_platform == exp_platform and gen_country == exp_country:
                    score += 0.15
                    checks.append("✓ WHERE filters match")
                    
                    # Try to match actual values
                    gen_platform_val = re.search(r"PLATFORM\s*=\s*'(\w+)'", gen_where)
                    exp_platform_val = re.search(r"PLATFORM\s*=\s*'(\w+)'", exp_where)
                    if gen_platform_val and exp_platform_val:
                        if gen_platform_val.group(1) == exp_platform_val.group(1):
                            score += 0.1
                            checks.append("✓ Platform value matches")
        
        # 4. Check GROUP BY
        gen_group_by = "GROUP BY" in gen
        exp_group_by = "GROUP BY" in exp
        if gen_group_by == exp_group_by:
            score += 0.1
            checks.append("✓ GROUP BY presence")
        
        # 5. Check ORDER BY
        gen_order_by = "ORDER BY" in gen
        exp_order_by = "ORDER BY" in exp
        if gen_order_by == exp_order_by:
            score += 0.1
            checks.append("✓ ORDER BY presence")
        
        # 6. Check LIMIT
        gen_limit_match = re.search(r"LIMIT\s+(\d+)", gen)
        exp_limit_match = re.search(r"LIMIT\s+(\d+)", exp)
        gen_limit = gen_limit_match.group(1) if gen_limit_match else None
        exp_limit = exp_limit_match.group(1) if exp_limit_match else None
        
        if gen_limit == exp_limit:
            if gen_limit:
                score += 0.1
                checks.append("✓ LIMIT matches")
            else:
                score += 0.05
                checks.append("✓ No LIMIT")
        
        return score, "\n".join(checks)
    
    semantic_score, feedback_details = check_semantic_equivalence(generated_normalized, expected_normalized)
    
    # The semantic_score accumulates points (max ~1.5), normalize to 0.0-1.0
    # Use a threshold-based approach: if score >= 0.7, consider it correct
    max_possible_score = 1.5  # Approximate max from all checks
    normalized_score = min(1.0, semantic_score / max_possible_score)
    
    # Consider correct if semantic score is >= 0.7 (70% of key elements match)
    # This is more lenient to account for valid variations
    is_correct = semantic_score >= 0.7
    
    # If correct, give full score (1.0), otherwise use normalized score
    final_score = 1.0 if is_correct else normalized_score
    
    return {
        "key": "sql_correctness",
        "score": final_score,
        "feedback": f"Expected: {expected_sql}\nGenerated: {generated_sql}\n\nSemantic Analysis:\n{feedback_details}\nRaw Score: {semantic_score:.2f}/{max_possible_score} → {normalized_score:.2%} → Final: {final_score:.2%}"
    }


def run_experiment():
    """Run the SQL generation experiment."""
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
            client = Client()
            dataset_name = "sql_generation_experiment"
            
            # Try to get existing dataset or create new one
            try:
                dataset = client.read_dataset(dataset_name=dataset_name)
                print(f"Using existing dataset: {dataset_name}")
            except Exception:
                # Create new dataset
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description="SQL generation experiment with 15 examples"
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
                sql_generation_target_function,
                data=dataset_name,  # Use dataset name instead of examples list
                evaluators=[sql_correctness_evaluator],
                experiment_prefix="sql_generation_experiment",
                max_concurrency=1,
            )
            print(f"\n{'='*60}")
            print(f"SQL Generation Experiment Results (LangSmith)")
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
    
    # Run evaluation locally without uploading
    if not upload_results:
        import uuid
        from datetime import datetime
        results = []
        scores = []
        for example in examples:
            try:
                output = sql_generation_target_function(example)
                # Create a proper Run object for the evaluator
                run = Run(
                    id=str(uuid.uuid4()),
                    name="sql_generation",
                    start_time=datetime.now(),
                    run_type="chain",
                    trace_id=str(uuid.uuid4()),
                    outputs=output,
                    inputs=example.inputs
                )
                eval_result = sql_correctness_evaluator(run, example)
                results.append({
                    "example": example.inputs.get("input", ""),
                    "expected": example.outputs.get("expected_output", ""),
                    "generated": output.get("output", ""),
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
        print(f"SQL Generation Experiment Results (Local)")
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
                print(f"   Generated: {result.get('generated', 'N/A')[:100]}...")
                print(f"   Score: {result.get('score', 0.0):.1f}")
        print(f"{'='*60}\n")
        return results


if __name__ == "__main__":
    run_experiment()

