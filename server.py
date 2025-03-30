from mcp.server.fastmcp import FastMCP
import time
import signal
import sys
import logging
from typing import List, Dict, Any, Union
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


from dotenv import load_dotenv
load_dotenv()

JIRA_URL = os.environ.get("JIRA_URL", 'https://XX.atlassian.net/')
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", 'email')
JIRA_PASSWORD = os.environ.get("JIRA_PASSWORD", 'api_key')

def run_jql_query(query):
    """
    Execute a JQL query and return parsed Jira issues.
    
    Args:
        query (str): JQL query string
        
    Returns:
        list: List of parsed Jira issues
    """
    try:
        from atlassian import Jira 
        from jira_tool import parse_jira_issues
        
        jira = Jira(
            url= JIRA_URL,
            username=JIRA_USERNAME,
            password=JIRA_PASSWORD
        )
        
        # Execute the JQL query
        jira_issues = jira.jql(query)
        
        # Process all issues
        parsed_results = []
        for issue in jira_issues['issues']:
            
            # Parse the formatted issue
            parsed_issue = parse_jira_issues(issue)
            parsed_results.append(parsed_issue)
        
        return parsed_results
        
    except Exception as e:
        logger.error(f"Error in JQL query execution: {str(e)}")
        raise


def signal_handler(sig, frame):
    logger.info("Shutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Create an MCP server with increased timeout
mcp = FastMCP(
    name="jira-jql-tool",
    host="127.0.0.1",
    port=5000,
    timeout=30  # Increase timeout to 30 seconds
)

# Define our tool
@mcp.tool()
def jira_jql_tool(query: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves and parses Jira tasks from the Jira API using JQL.
    
    Args:
        query (str): JQL query string to execute
        
    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: 
            Either a list of parsed Jira issues or an error message
    """
    try:
        logger.info(f"Executing JQL query: {query}")
        result = run_jql_query(query)
        logger.info(f"Retrieved {len(result)} issues")
        return result
    except Exception as e:
        error_msg = f"Error executing JQL query: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server 'jira_jql_tool' on 127.0.0.1:5000")
        # Use this approach to keep the server running
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        # Sleep before exiting to give time for error logs
        time.sleep(5)