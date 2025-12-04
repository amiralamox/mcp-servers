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

# Jira API Configuration
JIRA_URL = os.environ.get("JIRA_URL", 'https://XX.atlassian.net/')
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", 'email')
JIRA_PASSWORD = os.environ.get("JIRA_PASSWORD", 'api_key')

# Tool Configuration
DEFAULT_TEAM_NAME = os.environ.get("DEFAULT_TEAM_NAME", "Data Pod")
DEFAULT_LIMIT_PRIORITY_BACKLOG = int(os.environ.get("DEFAULT_LIMIT_PRIORITY_BACKLOG", "20"))
DEFAULT_LIMIT_ACTIVE_WORK = int(os.environ.get("DEFAULT_LIMIT_ACTIVE_WORK", "20"))
DEFAULT_LIMIT_ACTIVE_EPICS = int(os.environ.get("DEFAULT_LIMIT_ACTIVE_EPICS", "20"))
DEFAULT_LIMIT_RECENT_COMPLETIONS = int(os.environ.get("DEFAULT_LIMIT_RECENT_COMPLETIONS", "20"))
DEFAULT_LIMIT_SEARCH_ISSUES = int(os.environ.get("DEFAULT_LIMIT_SEARCH_ISSUES", "50"))
DEFAULT_LIMIT_TEAM_METRICS = int(os.environ.get("DEFAULT_LIMIT_TEAM_METRICS", "20"))
DEFAULT_DAYS_RECENT_COMPLETIONS = int(os.environ.get("DEFAULT_DAYS_RECENT_COMPLETIONS", "7"))
DEFAULT_DAYS_TEAM_METRICS = int(os.environ.get("DEFAULT_DAYS_TEAM_METRICS", "30"))

def run_jql_query(query):
    """
    Execute a JQL query and return parsed Jira issues.
    
    Args:
        query (str): JQL query string
        
    Returns:
        list: List of parsed Jira issues
    """
    try:
        import requests
        import base64
        from jira_tool import parse_jira_issues
        
        # Create authentication header
        auth_string = f"{JIRA_USERNAME}:{JIRA_PASSWORD}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_bytes}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Use the new v3 API endpoint
        api_url = f"{JIRA_URL.rstrip('/')}/rest/api/3/search/jql"
        
        params = {
            'jql': query,
            'fields': '*all',
            'maxResults': 100
        }
        
        # Execute the JQL query
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        
        jira_issues = response.json()
        
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

# Dedicated tools for common queries

@mcp.tool()
def get_priority_backlog(team_name: str = None, limit: int = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves high-priority items (Selected for Development, New) from active epics.
    Only returns issues whose parent epic is In Progress or Backlog.
    Perfect for sprint planning and prioritization.

    Args:
        team_name (str): Team name (default: from DEFAULT_TEAM_NAME environment variable)
        limit (int): Maximum number of results (default: from DEFAULT_LIMIT_PRIORITY_BACKLOG environment variable)

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of issues or error message
    """
    try:
        # Use environment variables if parameters not provided
        if team_name is None:
            team_name = DEFAULT_TEAM_NAME
        if limit is None:
            limit = DEFAULT_LIMIT_PRIORITY_BACKLOG

        query = f'status in ("Selected for Development", "New") AND assignee in (membersOf("{team_name}")) AND priority in (Highest, High) AND (parent.status = "In Progress" OR parent.status = "Backlog") ORDER BY priority DESC, created DESC'
        logger.info(f"Executing get_priority_backlog for team: {team_name}")
        result = run_jql_query(query)
        result = result[:limit]
        logger.info(f"Retrieved {len(result)} priority backlog items from active epics")
        return result
    except Exception as e:
        error_msg = f"Error retrieving priority backlog: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def get_active_work(team_name: str = None, limit: int = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves items currently in development (In Progress, Code Review, Testing).
    Shows what the team is actively working on right now.

    Args:
        team_name (str): Team name (default: from DEFAULT_TEAM_NAME environment variable)
        limit (int): Maximum number of results (default: from DEFAULT_LIMIT_ACTIVE_WORK environment variable)

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of issues or error message
    """
    try:
        # Use environment variables if parameters not provided
        if team_name is None:
            team_name = DEFAULT_TEAM_NAME
        if limit is None:
            limit = DEFAULT_LIMIT_ACTIVE_WORK

        query = f'status in ("In Progress", "Code Review", "Testing") AND assignee in (membersOf("{team_name}")) ORDER BY priority DESC, updated DESC'
        logger.info(f"Executing get_active_work for team: {team_name}")
        result = run_jql_query(query)
        result = result[:limit]
        logger.info(f"Retrieved {len(result)} active work items")
        return result
    except Exception as e:
        error_msg = f"Error retrieving active work: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def get_active_epics(assignee: str = None, limit: int = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves active epics (In Progress or Backlog).
    Useful for understanding strategic initiatives and long-term work.

    Args:
        assignee (str): Optional assignee filter (default: None, returns all)
        limit (int): Maximum number of results (default: from DEFAULT_LIMIT_ACTIVE_EPICS environment variable)

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of epics or error message
    """
    try:
        # Use environment variables if parameters not provided
        if limit is None:
            limit = DEFAULT_LIMIT_ACTIVE_EPICS

        if assignee:
            query = f'type = Epic AND status in ("In Progress", "Backlog") AND assignee = "{assignee}" ORDER BY priority DESC, updated DESC'
            logger.info(f"Executing get_active_epics for assignee: {assignee}")
        else:
            query = 'type = Epic AND status in ("In Progress", "Backlog") ORDER BY priority DESC, updated DESC'
            logger.info("Executing get_active_epics")
        result = run_jql_query(query)
        result = result[:limit]
        logger.info(f"Retrieved {len(result)} active epics")
        return result
    except Exception as e:
        error_msg = f"Error retrieving active epics: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def get_recent_completions(team_name: str = None, days: int = None, limit: int = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves completed work from the last N days.
    Helps identify productivity patterns and team capacity.

    Args:
        team_name (str): Team name (default: from DEFAULT_TEAM_NAME environment variable)
        days (int): Number of days to look back (default: from DEFAULT_DAYS_RECENT_COMPLETIONS environment variable)
        limit (int): Maximum number of results (default: from DEFAULT_LIMIT_RECENT_COMPLETIONS environment variable)

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of completed issues or error message
    """
    try:
        # Use environment variables if parameters not provided
        if team_name is None:
            team_name = DEFAULT_TEAM_NAME
        if days is None:
            days = DEFAULT_DAYS_RECENT_COMPLETIONS
        if limit is None:
            limit = DEFAULT_LIMIT_RECENT_COMPLETIONS

        query = f'resolved >= -{days}d AND assignee in (membersOf("{team_name}")) ORDER BY resolved DESC'
        logger.info(f"Executing get_recent_completions for team: {team_name}, last {days} days")
        result = run_jql_query(query)
        result = result[:limit]
        logger.info(f"Retrieved {len(result)} recent completions")
        return result
    except Exception as e:
        error_msg = f"Error retrieving recent completions: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def search_issues(query: str, limit: int = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Generic JQL query executor for ad-hoc searches.
    Fallback for queries beyond common patterns.

    Args:
        query (str): JQL query string to execute
        limit (int): Maximum number of results (default: from DEFAULT_LIMIT_SEARCH_ISSUES environment variable)

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of issues or error message
    """
    try:
        # Use environment variables if parameters not provided
        if limit is None:
            limit = DEFAULT_LIMIT_SEARCH_ISSUES

        logger.info(f"Executing search_issues query: {query}")
        result = run_jql_query(query)
        result = result[:limit]
        logger.info(f"Retrieved {len(result)} issues from custom search")
        return result
    except Exception as e:
        error_msg = f"Error executing custom search: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def get_team_metrics(team_name: str = None, days: int = None) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Aggregated metrics for team health dashboard.
    Shows backlog items, WIP, and recent completions.

    Args:
        team_name (str): Team name (default: from DEFAULT_TEAM_NAME environment variable)
        days (int): Number of days to analyze (default: from DEFAULT_DAYS_TEAM_METRICS environment variable)

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: Team metrics or error message
    """
    try:
        # Use environment variables if parameters not provided
        if team_name is None:
            team_name = DEFAULT_TEAM_NAME
        if days is None:
            days = DEFAULT_DAYS_TEAM_METRICS

        logger.info(f"Executing get_team_metrics for team: {team_name}")

        # Get backlog items (limit to DEFAULT_LIMIT_TEAM_METRICS)
        backlog_query = f'status in ("Selected for Development", "New") AND assignee in (membersOf("{team_name}"))'
        backlog_results = run_jql_query(backlog_query)[:DEFAULT_LIMIT_TEAM_METRICS]

        # Get active work (limit to DEFAULT_LIMIT_TEAM_METRICS)
        active_query = f'status in ("In Progress", "Code Review", "Testing") AND assignee in (membersOf("{team_name}"))'
        active_results = run_jql_query(active_query)[:DEFAULT_LIMIT_TEAM_METRICS]

        # Get recent completions (limit to DEFAULT_LIMIT_TEAM_METRICS)
        completed_query = f'resolved >= -{days}d AND assignee in (membersOf("{team_name}"))'
        completed_results = run_jql_query(completed_query)[:DEFAULT_LIMIT_TEAM_METRICS]

        metrics = {
            "team": team_name,
            "period_days": days,
            "backlog_count": len(backlog_results),
            "backlog_high_priority": sum(1 for issue in backlog_results if issue.get("priority") in ["Highest", "High"]),
            "wip_count": len(active_results),
            "completed_count": len(completed_results),
            "backlog_items": backlog_results,
            "active_items": active_results,
            "completed_items": completed_results
        }

        logger.info(f"Team metrics computed: {len(backlog_results)} backlog, {len(active_results)} WIP, {len(completed_results)} completed")
        return metrics
    except Exception as e:
        error_msg = f"Error computing team metrics: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


# Legacy generic tool - kept for backward compatibility
@mcp.tool()
def jira_jql_tool(query: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves and parses Jira tasks from the Jira API using JQL.
    DEPRECATED: Use specific tools (get_priority_backlog, get_active_work, etc.) instead.

    Args:
        query (str): JQL query string to execute

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]:
            Either a list of parsed Jira issues or an error message
    """
    try:
        logger.info(f"Executing legacy JQL query: {query}")
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