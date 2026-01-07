"""Formatting Guidelines for Query Results.

Guidelines for formatting SQL query results for Slack display.
"""

FORMATTING_GUIDELINES = """Formatting Guidelines for SQL Query Results

**Format Selection**:

1. **Simple Text Format** (use for):
   - Single value results (COUNT queries)
   - Single row aggregations with 1-2 columns
   - Results with ≤5 rows and ≤3 columns
   - Examples: "50", "iOS: 21", "Netherlands: 67125.31"

2. **Table Format** (use for):
   - Multiple rows (>5 rows)
   - Multiple columns (>3 columns)
   - Complex aggregations with grouping
   - Top-N lists
   - Examples: Country revenue tables, platform breakdowns

**Slack Markdown Guidelines**:

- Use markdown tables for multi-row results:
  ```
  column1 | column2 | column3
  --- | --- | ---
  value1 | value2 | value3
  ```

- Use simple text for single values:
  ```
  50
  ```

- Format numbers appropriately:
  - Integers: Display as-is (50, 1000)
  - Decimals: 2 decimal places (1234.56)
  - Large numbers: Keep readable (no commas needed in Slack)

- Filter out 'id' column from display (internal use only)

**Assumptions and Context**:

- For complex queries, include assumptions/notes:
  - Timeframe assumptions (e.g., "All available data", "Last 12 months")
  - Aggregation explanations (e.g., "Total values calculated across all matching records")
  - Sorting notes (e.g., "Results sorted in descending order")
  - Top-N notes (e.g., "Showing top 5 results")
  - Popularity metrics (e.g., "Popularity defined by number of installs")

- Format assumptions as italicized notes:
  ```
  *Note: Total values calculated across all matching records; Results sorted in descending order*
  ```

**Error Messages**:

- Format errors clearly:
  - "Error: [clear explanation]"
  - Provide helpful guidance when possible
  - Suggest alternatives if query fails

**Empty Results**:

- Display: "No results found."
- Provide context if helpful (e.g., "No apps found matching your criteria")

**Best Practices**:

- Keep responses concise but informative
- Use appropriate format for data complexity
- Include assumptions for complex queries
- Maintain readability in Slack
- Filter unnecessary columns (like 'id')
"""

