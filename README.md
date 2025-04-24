# db-query-chatbot-agent

A natural language interface for querying relational databases through conversation. This AI-powered agent enables users to interact with databases using plain English instead of writing SQL queries directly.

Link - [Agent @ OptimalAgents.ai](https://optimalagents.ai/dashboard/agents/agent/f9e8390d-e1ba-4340-bdb8-61d29eda2211)

## Features

- Connects to multiple relational database types (PostgreSQL, MySQL, SQLite, etc.)
- Translates natural language questions into optimized SQL queries
- Maintains secure database connections using provided credentials
- Stores conversation history and query sessions locally
- Returns results in structured, readable formats
- Validates and sanitizes all queries for security

## Usage

### Database Configuration

Click the "Database" button in the top to configure your database connection. This setting will be common across all sessions.

### Sessions Management

- All your sessions are stored locally in your browser's localStorage
- Create a new session using the "New Session" button on the left panel
- Switch between sessions by clicking on them in the sessions list
- Search for specific sessions using the search bar

### Additional Tips

- Sessions are automatically saved as you work
- Each session maintains its own query history
- You can name your sessions for better organization
- Use the search functionality to quickly find past sessions

## Security

- Credentials are stored securely and never logged
- All user input is sanitized before query execution
- Read-only connections by default
- Session tokens for conversation persistence

## Requirements

- Python 3.8+
- Required database drivers
- PostgreSQL, MySQL, SQLite Connection Credentials

## Example

Set the database connection credentials using the Database button .

User: "Show me the top 5 customers by total order value"

Agent: "Here's what I found:
[Results table]
Translated SQL: SELECT c.customer_name, SUM(o.total) as total_value..."

## License

MIT License
