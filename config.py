import os
from dotenv import load_dotenv

load_dotenv()

# Jira API Configuration
JIRA_URL = os.environ.get("JIRA_URL", 'https://XX.atlassian.net/')
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", 'email')
JIRA_PASSWORD = os.environ.get("JIRA_PASSWORD", 'api_key')

# Custom Field IDs - adjust these for your Jira instance
CUSTOM_FIELDS = {
    "epic_link": os.environ.get("CUSTOM_FIELD_EPIC_LINK", "customfield_10014"),
    "story_points": os.environ.get("CUSTOM_FIELD_STORY_POINTS", "customfield_10016"),
    "sprint": os.environ.get("CUSTOM_FIELD_SPRINT", "customfield_10020"),
}

# Tool Configuration - Default Values
DEFAULT_TEAM_NAME = os.environ.get("DEFAULT_TEAM_NAME", "Data Pod")
DEFAULT_LIMIT_PRIORITY_BACKLOG = int(os.environ.get("DEFAULT_LIMIT_PRIORITY_BACKLOG", "20"))
DEFAULT_LIMIT_ACTIVE_WORK = int(os.environ.get("DEFAULT_LIMIT_ACTIVE_WORK", "20"))
DEFAULT_LIMIT_ACTIVE_EPICS = int(os.environ.get("DEFAULT_LIMIT_ACTIVE_EPICS", "20"))
DEFAULT_LIMIT_RECENT_COMPLETIONS = int(os.environ.get("DEFAULT_LIMIT_RECENT_COMPLETIONS", "20"))
DEFAULT_LIMIT_SEARCH_ISSUES = int(os.environ.get("DEFAULT_LIMIT_SEARCH_ISSUES", "50"))
DEFAULT_LIMIT_TEAM_METRICS = int(os.environ.get("DEFAULT_LIMIT_TEAM_METRICS", "20"))
DEFAULT_LIMIT_BLOCKED_ISSUES = int(os.environ.get("DEFAULT_LIMIT_BLOCKED_ISSUES", "20"))
DEFAULT_LIMIT_STALE_ISSUES = int(os.environ.get("DEFAULT_LIMIT_STALE_ISSUES", "20"))
DEFAULT_DAYS_RECENT_COMPLETIONS = int(os.environ.get("DEFAULT_DAYS_RECENT_COMPLETIONS", "7"))
DEFAULT_DAYS_TEAM_METRICS = int(os.environ.get("DEFAULT_DAYS_TEAM_METRICS", "30"))
DEFAULT_DAYS_STALE_ISSUES = int(os.environ.get("DEFAULT_DAYS_STALE_ISSUES", "14"))
