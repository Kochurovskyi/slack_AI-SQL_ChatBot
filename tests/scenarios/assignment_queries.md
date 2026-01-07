# Assignment Query Scenarios

This file contains various query scenarios based on the AI Engineer Test Task requirements.

## Query Categories

### 1. Simple Questions

**Q1.1**: Basic count query
```
User: how many apps do we have?
Expected: Simple answer without CSV table
```

**Q1.2**: Platform-specific count
```
User: how many android apps do we have?
Expected: Simple answer without CSV table
```

**Q1.3**: Follow-up question
```
User: how many android apps do we have?
Bot: [answer]
User: what about ios?
Expected: Follow-up answer showing bot understood the question
```

### 2. Complex Questions

**Q2.1**: Revenue analysis
```
User: which country generates the most revenue?
Expected: Table with country name, total revenue, plus brief text summary explaining timeframe assumptions
```

**Q2.2**: Sorted list with interpretation
```
User: List all ios apps sorted by their popularity
Expected: Table of iOS apps sorted by popularity, plus explanation of how 'popularity' was defined
```

**Q2.3**: Comparative analysis
```
User: Which apps had the biggest change in UA spend comparing Jan 2025 to Dec 2024?
Expected: Table showing apps with largest UA spend changes, optionally with extra columns for added context
```

**Q2.4**: Revenue breakdown
```
User: What is the total revenue by platform?
Expected: Table with platform, total revenue, plus summary
```

**Q2.5**: Top performers
```
User: Show me the top 5 apps by installs
Expected: Table with top 5 apps, installs, plus summary
```

### 3. CSV Export Requests

**Q3.1**: Export after query
```
User: how many apps do we have?
Bot: [answer]
User: export this as csv
Expected: Confirmation message with CSV file path
```

**Q3.2**: Export complex results
```
User: which country generates the most revenue?
Bot: [table answer]
User: export to csv
Expected: CSV file with country revenue data
```

**Q3.3**: Direct export request
```
User: Export all apps to CSV
Expected: CSV file with all app data
```

### 4. SQL Statement Requests

**Q4.1**: SQL retrieval after query
```
User: how many apps do we have?
Bot: [answer]
User: show me the SQL you used to retrieve all the apps
Expected: SQL statement used for the first question
```

**Q4.2**: SQL retrieval after multiple queries
```
User: how many apps do we have?
Bot: [answer]
User: how many iOS apps do we have?
Bot: [answer]
User: show me the SQL you used to retrieve all the apps
Expected: SQL used for the first question (total apps)
```

**Q4.3**: SQL for specific query
```
User: which country generates the most revenue?
Bot: [answer]
User: what SQL did you use?
Expected: SQL statement for revenue query
```

### 5. Follow-up Questions

**Q5.1**: Platform follow-up
```
User: how many android apps do we have?
Bot: [answer]
User: what about ios?
Expected: Follow-up answer maintaining context
```

**Q5.2**: Date range follow-up
```
User: show me apps from 2024
Bot: [answer]
User: what about 2025?
Expected: Follow-up answer with date context
```

**Q5.3**: Country follow-up
```
User: show me revenue by country
Bot: [answer]
User: what about just the US?
Expected: Follow-up answer filtering by country
```

### 6. Off-Topic Questions

**Q6.1**: General greeting
```
User: Hello, how are you?
Expected: Polite decline, redirect to app portfolio questions
```

**Q6.2**: Unrelated question
```
User: What's the weather today?
Expected: Polite decline, suggest app portfolio questions
```

**Q6.3**: General question
```
User: Tell me a joke
Expected: Polite decline, maintain focus on analytics
```

### 7. Edge Cases

**Q7.1**: Empty result query
```
User: show me apps from 2030
Expected: User-friendly message about no results
```

**Q7.2**: Ambiguous query
```
User: show me the best apps
Expected: Query for clarification or make reasonable assumption
```

**Q7.3**: Complex aggregation
```
User: What is the average revenue per install by platform?
Expected: Calculated metric with explanation
```

**Q7.4**: Date comparison
```
User: Compare revenue between iOS and Android in 2024
Expected: Comparative table with analysis
```

### 8. Multi-Step Workflows

**Q8.1**: Query → Export → SQL
```
User: which country generates the most revenue?
Bot: [answer]
User: export this as csv
Bot: [CSV file]
User: show me the SQL
Expected: SQL statement for revenue query
```

**Q8.2**: Multiple queries → Export
```
User: how many apps do we have?
Bot: [answer]
User: how many iOS apps?
Bot: [answer]
User: export the iOS apps to csv
Expected: CSV with iOS apps data
```

## Query Test Matrix

| Query ID | Category | Complexity | Expected Intent | Expected Format |
|----------|----------|------------|-----------------|-----------------|
| Q1.1 | Simple | Low | SQL_QUERY | Simple text |
| Q1.2 | Simple | Low | SQL_QUERY | Simple text |
| Q1.3 | Follow-up | Low | SQL_QUERY | Simple text |
| Q2.1 | Complex | High | SQL_QUERY | Table + text |
| Q2.2 | Complex | High | SQL_QUERY | Table + text |
| Q2.3 | Complex | High | SQL_QUERY | Table + text |
| Q2.4 | Complex | Medium | SQL_QUERY | Table + text |
| Q2.5 | Complex | Medium | SQL_QUERY | Table + text |
| Q3.1 | Export | Low | CSV_EXPORT | CSV file |
| Q3.2 | Export | Medium | CSV_EXPORT | CSV file |
| Q3.3 | Export | Medium | CSV_EXPORT | CSV file |
| Q4.1 | SQL Retrieval | Low | SQL_RETRIEVAL | SQL code block |
| Q4.2 | SQL Retrieval | Low | SQL_RETRIEVAL | SQL code block |
| Q4.3 | SQL Retrieval | Medium | SQL_RETRIEVAL | SQL code block |
| Q5.1 | Follow-up | Low | SQL_QUERY | Simple text |
| Q5.2 | Follow-up | Medium | SQL_QUERY | Table/text |
| Q5.3 | Follow-up | Medium | SQL_QUERY | Table/text |
| Q6.1 | Off-topic | Low | OFF_TOPIC | Polite decline |
| Q6.2 | Off-topic | Low | OFF_TOPIC | Polite decline |
| Q6.3 | Off-topic | Low | OFF_TOPIC | Polite decline |
| Q7.1 | Edge case | Low | SQL_QUERY | Error message |
| Q7.2 | Edge case | Medium | SQL_QUERY | Clarification/assumption |
| Q7.3 | Edge case | High | SQL_QUERY | Calculated metric |
| Q7.4 | Edge case | High | SQL_QUERY | Comparative table |
| Q8.1 | Multi-step | High | Multiple | Multiple formats |
| Q8.2 | Multi-step | Medium | Multiple | Multiple formats |

