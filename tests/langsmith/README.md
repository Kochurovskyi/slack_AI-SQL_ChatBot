# LangSmith Experiments

This directory contains LangSmith experiments for evaluating the SQL chatbot system.

## Overview

Three basic experiments are implemented:

1. **SQL Generation Experiment** (`experiment_sql_generation.py`)
   - Evaluates SQL Query Agent's ability to generate correct SQL from natural language
   - 15 ground truth examples
   - Evaluates SQL correctness (exact match)

2. **Intent Classification Experiment** (`experiment_intent_classification.py`)
   - Evaluates Router Agent's ability to classify user intent
   - 15 ground truth examples
   - Evaluates intent accuracy (SQL_QUERY, CSV_EXPORT, SQL_RETRIEVAL, OFF_TOPIC)

3. **Result Formatting Experiment** (`experiment_result_formatting.py`)
   - Evaluates Formatting Service's ability to choose correct format (simple vs table)
   - 15 ground truth examples
   - Evaluates format accuracy

## Setup

1. **Install LangSmith SDK**:
   ```bash
   pip install langsmith
   ```

2. **Set Environment Variables**:
   ```bash
   export LANGSMITH_API_KEY="your_langsmith_api_key"
   ```

   Note: Experiments will still run without LangSmith API key, but results won't be logged to LangSmith platform.

3. **Run Experiments**:
   ```bash
   # Run SQL generation experiment
   python tests/langsmith/experiment_sql_generation.py

   # Run intent classification experiment
   python tests/langsmith/experiment_intent_classification.py

   # Run result formatting experiment
   python tests/langsmith/result_formatting_experiment.py
   ```

## Dataset Structure

Each experiment uses a ground truth dataset with 15 examples. Each example contains:

- `input`: The input to the target function
- `expected_output`: The expected output
- `metadata`: Additional metadata (optional)

## Evaluators

Each experiment includes a custom evaluator that:
- Compares predicted output with expected output
- Returns a score (0.0 or 1.0 for binary evaluation)
- Provides feedback on the comparison

## Results

Results are printed to console and optionally logged to LangSmith platform if API key is set.

## Notes

- Experiments run sequentially (`max_concurrency=1`) for small datasets
- All experiments use the actual agent/service implementations
- Error handling is included for robustness
- Experiments can be run independently

