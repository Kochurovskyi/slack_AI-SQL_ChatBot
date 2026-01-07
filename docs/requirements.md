# Requirements Specification
**Source**: AI Engineer Challenge - Test Task  
**Date**: 2026-01-06  
**Project**: Slack Chatbot for Data Analytics and Business Intelligence

## Overview

This document extracts and categorizes the functional and non-functional requirements from the AI Engineer Challenge specification for building an internal Slack chatbot for data analytics and business intelligence.

---

## Functional Requirements

### FR1: Database Integration

**FR1.1**: The system must work with an SQL database containing app portfolio data.

**FR1.2**: The database schema must include the following columns:
- **App Name**: The name of a mobile app (e.g., Paint for Android, Countdown iOS)
- **Platform**: The operating system (iOS or Android)
- **Date**: The specific date for the data being reported
- **Country**: The geographic country where the app metrics were recorded
- **Installs**: The number of times the app was downloaded by users
- **In-App Revenue**: Revenue generated from purchases made within the app (e.g., premium features, virtual goods, subscriptions)
- **Ads Revenue**: Revenue earned from advertisements displayed within the app
- **UA Cost**: User Acquisition Cost – the amount spent on marketing and advertising to acquire new app users

**FR1.3**: The system must support any relational DBMS of choice.

**FR1.4**: The system must include sample data for demonstration purposes.

### FR2: Natural Language to SQL Conversion

**FR2.1**: The system must convert user questions into SQL statements.

**FR2.2**: The system must execute SQL statements against the database.

**FR2.3**: The system must provide users with interpreted, formatted data.

### FR3: Response Formatting

**FR3.1**: The system must determine when to display a simple interpretation of results.

**FR3.2**: The system must determine when to show raw data (tables).

**FR3.3**: Table responses must include:
- Clear descriptions
- Notes about any assumptions made

**FR3.4**: The system must provide responses either in plain text or as detailed tables, depending on query complexity.

### FR4: Conversation Context

**FR4.1**: The system must support follow-up questions.

**FR4.2**: The system must maintain conversation context across multiple messages.

**FR4.3**: The system must intelligently interpret user intent in follow-up questions (e.g., "what about iOS?" after "how many android apps do we have?").

### FR5: CSV Export

**FR5.1**: Users must be able to export query results as CSV files.

**FR5.2**: The system must provide CSV download links or buttons.

**FR5.3**: The system must optimize CSV exports to avoid regenerating SQL or data (cost-effective token usage).

**FR5.4**: CSV export should work for previously executed queries without re-execution.

### FR6: SQL Statement Retrieval

**FR6.1**: Users must be able to request the SQL statement used to answer their questions.

**FR6.2**: The system must retrieve and display the SQL statement for a specific query.

**FR6.3**: The system must optimize SQL retrieval to avoid regenerating SQL (cost-effective token usage).

**FR6.4**: Users must be able to request SQL for previous queries in the conversation.

### FR7: Off-Topic Handling

**FR7.1**: The system must handle off-topic questions.

**FR7.2**: The system must politely decline off-topic questions.

**FR7.3**: The system must maintain conversation focus on app portfolio analytics.

### FR8: Question Types Support

**FR8.1**: The system must process natural language queries related to the app portfolio.

**FR8.2**: The system must handle simple questions (e.g., "how many apps do we have?").

**FR8.3**: The system must handle complex questions (e.g., "which country generates the most revenue?").

**FR8.4**: The system must handle questions requiring aggregations and comparisons (e.g., "Which apps had the biggest change in UA spend comparing Jan 2025 to Dec 2024?").

**FR8.5**: The system must handle questions requiring sorting (e.g., "List all iOS apps sorted by their popularity").

**FR8.6**: The system must provide brief text summaries explaining timeframe assumptions for time-based queries.

**FR8.7**: The system must explain how metrics are defined (e.g., how 'popularity' was defined).

### FR9: Slack Integration

**FR9.1**: The chatbot must run within Slack.

**FR9.2**: The system must support Slack Developer Sandbox for testing.

**FR9.3**: The system should utilize Slack features such as:
- AI Assistants
- Code Snippets

**FR9.4**: The system must provide clear setup and deployment instructions.

**FR9.5**: The system must include instructions for installing the Slack app in a new workspace.

### FR10: Observability and Traceability

**FR10.1**: The system must use LangSmith or other LLM observability platform.

**FR10.2**: The system must enable x-ray visibility into the inner workings of the agent.

**FR10.3**: The system must provide traceability for agent decisions and actions.

---

## Non-Functional Requirements

### NFR1: Reliability and Quality

**NFR1.1**: The system must be functional and free of unexpected bugs.

**NFR1.2**: Production code must be reviewed (not entirely AI-generated without review).

**NFR1.3**: The system must handle errors gracefully.

**NFR1.4**: The system must provide appropriate error messages to users.

### NFR2: Cost Optimization

**NFR2.1**: The chatbot must be optimized for cost-effective token usage.

**NFR2.2**: CSV exports must not regenerate SQL or data (use cached results).

**NFR2.3**: SQL retrieval must not regenerate SQL (use cached queries).

**NFR2.4**: The system should implement smart solutions for CSV exports and SQL requests to minimize token costs.

### NFR3: Scalability

**NFR3.1**: The architecture must be scalable in terms of feature extension.

**NFR3.2**: The system must support adding new features without major architectural changes.

**NFR3.3**: The system must handle increasing numbers of users and queries.

### NFR4: Maintainability

**NFR4.1**: The codebase must be maintainable.

**NFR4.2**: The code must follow best practices and coding standards.

**NFR4.3**: The codebase must be well-documented.

**NFR4.4**: The architecture must support long-term maintenance.

### NFR5: Usability

**NFR5.1**: The chatbot must maintain a natural conversational flow.

**NFR5.2**: Responses must be clear and easy to understand.

**NFR5.3**: The system must provide appropriate level of detail based on query complexity.

**NFR5.4**: Error messages must be user-friendly.

### NFR6: Performance

**NFR6.1**: The system must respond to queries in a reasonable time.

**NFR6.2**: SQL queries must execute efficiently.

**NFR6.3**: CSV generation must be performant.

### NFR7: Security (Future Development)

**NFR7.1**: The system must support user-level access permissions (planned).

**NFR7.2**: Security measures must be implemented before production deployment.

### NFR8: Documentation

**NFR8.1**: The solution must be submitted as a GitHub repository.

**NFR8.2**: The repository must include clear setup instructions.

**NFR8.3**: The repository must include deployment instructions.

**NFR8.4**: The repository must include instructions for installing the Slack app in a new workspace.

### NFR9: Presentation and Planning

**NFR9.1**: The solution must be prepared for a 40-minute presentation session (20 minutes presentation + 20 minutes Q&A).

**NFR9.2**: A plan for further development must be prepared.

**NFR9.3**: The plan must include:
- Security measures (user-level access permissions)
- Upcoming chatbot features
- A prioritized list of improvements required before deploying to production

### NFR10: Technology Selection

**NFR10.1**: The challenge does not specify particular technical requirements.

**NFR10.2**: Suitable technologies must be selected.

**NFR10.3**: Technology choices must be justified during the presentation.

---

## Example Scenarios

### Scenario 1: Simple Questions

**Input**: "how many apps do we have?"

**Expected Output**: Simple answer without a CSV table

### Scenario 2: Follow-up Questions

**Input Sequence**:
1. "how many android apps do we have?"
2. "what about ios?"

**Expected Output**: 
- First response: Answer about Android apps
- Second response: Follow-up answer showing the bot understood the question (iOS apps)

### Scenario 3: Complex Questions with Tables

**Input**: "which country generates the most revenue?"

**Expected Output**: 
- Table with country name, total revenue
- Brief text summary explaining timeframe assumptions

### Scenario 4: Sorting and Definitions

**Input**: "List all iOS apps sorted by their popularity"

**Expected Output**: 
- Table of iOS apps sorted by popularity
- Explanation of how 'popularity' was defined

### Scenario 5: Time-based Comparisons

**Input**: "Which apps had the biggest change in UA spend comparing Jan 2025 to Dec 2024?"

**Expected Output**: 
- Table showing apps with largest UA spend changes
- Optionally with extra columns for added context

### Scenario 6: CSV Export

**Input Sequence**:
1. "how many apps do we have?"
2. "export this as csv"

**Expected Output**: 
- First response: Answer
- Second response: Confirmation message with CSV download link or button

### Scenario 7: SQL Statement Retrieval

**Input Sequence**:
1. "how many apps do we have?"
2. "how many iOS apps do we have?"
3. "show me the SQL you used to retrieve all the apps"

**Expected Output**: 
- First response: Answer (total apps)
- Second response: Answer (iOS apps)
- Third response: SQL used for the first question (total apps)

---

## Evaluation Criteria

The solution will be evaluated based on:

1. **Functionality**: The basic MVP is functional and free of unexpected bugs
2. **Code Quality**: Production code is reviewed (not entirely AI-generated without review)
3. **Cost Optimization**: The chatbot is optimized for cost-effective token usage
4. **Scalability**: The chosen architecture is scalable in terms of feature extension
5. **Maintainability**: The codebase is maintainable
6. **Roadmap**: The roadmap for further development is well-thought-out, innovative, and practical

---

## Requirements Traceability

### Current Implementation Status

Based on the project documentation:

| Requirement ID | Status | Implementation |
|----------------|--------|---------------|
| FR1.1-FR1.4 | ✅ Complete | Database schema implemented in `data/db_manager.py` |
| FR2.1-FR2.3 | ✅ Complete | SQL Query Agent in `ai/agents/sql_query_agent.py` |
| FR3.1-FR3.4 | ✅ Complete | Formatting Service in `services/formatting_service.py` |
| FR4.1-FR4.3 | ✅ Complete | Memory Store in `ai/memory_store.py` |
| FR5.1-FR5.4 | ✅ Complete | CSV Export Agent in `ai/agents/csv_export_agent.py` |
| FR6.1-FR6.4 | ✅ Complete | SQL Retrieval Agent in `ai/agents/sql_retrieval_agent.py` |
| FR7.1-FR7.3 | ✅ Complete | Off-Topic Handler in `ai/agents/off_topic_handler.py` |
| FR8.1-FR8.7 | ✅ Complete | Router Agent + Specialized Agents |
| FR9.1-FR9.5 | ✅ Complete | Slack handlers in `listeners/` |
| FR10.1-FR10.3 | ✅ Complete | LangSmith integration in `tests/langsmith/` |
| NFR1.1-NFR1.4 | ✅ Complete | Comprehensive testing suite |
| NFR2.1-NFR2.4 | ✅ Complete | Memory store caching, no regeneration |
| NFR3.1-NFR3.3 | ✅ Complete | Multi-agent architecture |
| NFR4.1-NFR4.4 | ✅ Complete | Well-documented codebase |
| NFR5.1-NFR5.4 | ✅ Complete | User-friendly responses |
| NFR6.1-NFR6.3 | ✅ Complete | Optimized query execution |
| NFR7.1-NFR7.2 | ⏳ Planned | Future development |
| NFR8.1-NFR8.4 | ✅ Complete | GitHub repository with documentation |
| NFR9.1-NFR9.3 | ⏳ Pending | Presentation preparation |
| NFR10.1-NFR10.3 | ✅ Complete | Technology choices documented |

**Legend**:
- ✅ Complete: Fully implemented and tested
- ⏳ Planned: Identified for future development
- ⏳ Pending: Requires action (presentation, etc.)

---

## Notes

- The challenge does not specify particular technical requirements. Technologies should be selected and justified.
- The primary technical constraint is that the chatbot must run within Slack.
- All functional requirements have been implemented in the current system.
- Non-functional requirements related to security and presentation are pending or planned for future development.

