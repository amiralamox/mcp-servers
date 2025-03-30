```bash
➜  projects mkdir jira_tool && cd jira_tool
➜  jira_tool python3.12 -m venv .venv
➜  jira_tool source .venv/bin/activate
(.venv) ➜  jira_tool pip install mcp
(.venv) ➜  python server.py #just to test it's working, no need to leave it on!
```

Then you should open your claude desktop config

```vim ~/Library/Application\ Support/Claude/claude_desktop_config.json```

and add the following json:

```JSON
{
  "mcpServers": {
    "jira-jql-tool": {
      "command": "[path_to_project]/.venv/bin/python", //path to python
      "args": [
        "[path_to_project]/server.py"
      ]
    }
  }
}
```