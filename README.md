# Jira JQL Tool for Claude

A tool that enables Claude to interact with Jira through JQL queries using the Model Control Protocol (MCP).

## Setup Instructions

### 1. Project Setup

Create and set up your project environment:

```bash
# Create project directory
git clone git@github.com:amiralamox/mcp-servers.git && cd jira_tool

# Create Python virtual environment (Python 3.12)
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Test server (optional)
python server.py  # Run briefly to verify it works, then stop
```

### 2. Claude Desktop Configuration

Configure Claude Desktop to connect to your JQL tool:

1. Open Claude desktop configuration file:
  ```bash
  vim ~/Library/Application\ Support/Claude/claude_desktop_config.json
  ```

2. Add the following configuration (replace `[path_to_project]` with your actual project path):
  ```json
  {
    "mcpServers": {
     "jira-jql-tool": {
      "command": "[path_to_project]/.venv/bin/python",
      "args": [
        "[path_to_project]/server.py"
      ]
     }
    }
  }
  ```

3. Save the file and restart Claude Desktop

## Usage

[Add usage instructions here]