import json
from datetime import datetime
from atlassian import Jira

def parse_jira_issues(jira_data):
    """
    Parse Jira API response and extract meaningful information for managers.
    
    Args:
        jira_data (str, dict, or list): Jira API response as JSON string, dict, or list
    
    Returns:
        dict or list: Clean dictionary or list of dictionaries with meaningful information
    """
    if isinstance(jira_data, str):
        try:
            data = json.loads(jira_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format"}
    else:
        data = jira_data
    
    # Handles a list of issues
    if isinstance(data, list):
        return [extract_issue_info(issue) for issue in data]
    else:
        return extract_issue_info(data)

def extract_issue_info(issue):
    """Extract key information from a Jira issue that's relevant for management."""
    result = {}
    fields = issue.get("fields", {})
    
    # Basic information
    result["key"] = issue.get("key", "")
    result["summary"] = fields.get("summary", "")
    result["description"] = fields.get("description", "")
    
    # Type, status, priority
    issuetype = fields.get("issuetype", {})
    result["type"] = issuetype.get("name", "") if issuetype else ""
    
    status = fields.get("status", {})
    result["status"] = status.get("name", "") if status else ""
    
    priority = fields.get("priority", {})
    result["priority"] = priority.get("name", "") if priority else ""
    
    # People
    assignee = fields.get("assignee", {})
    result["assignee"] = assignee.get("displayName", "") if assignee else "Unassigned"
    
    reporter = fields.get("reporter", {})
    result["reporter"] = reporter.get("displayName", "") if reporter else ""
    
    # Components
    components = fields.get("components", [])
    result["components"] = [comp.get("name", "") for comp in components if comp]
    
    # Parse dates
    def parse_date(date_str):
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",  # With milliseconds and timezone
            "%Y-%m-%dT%H:%M:%S%z",     # Without milliseconds
            "%Y-%m-%d"                 # Just date
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    created_date = parse_date(fields.get("created", ""))
    updated_date = parse_date(fields.get("updated", ""))
    status_changed_date = parse_date(fields.get("statuscategorychangedate", ""))
    
    result["created"] = created_date.strftime("%Y-%m-%d") if created_date else "Unknown"
    result["updated"] = updated_date.strftime("%Y-%m-%d") if updated_date else "Unknown"
    
    # Calculate work duration
    if created_date and updated_date:
        duration = updated_date - created_date
        result["duration"] = {
            "days": duration.days,
            "formatted": f"{duration.days} days"
        }
        
        # Add hours and minutes for more precision
        if duration.days < 30:  # Only show detailed time for shorter durations
            total_seconds = duration.total_seconds()
            hours = int((total_seconds % (24 * 3600)) // 3600)
            minutes = int((total_seconds % 3600) // 60)
            result["duration"]["formatted"] = f"{duration.days} days, {hours} hours, {minutes} minutes"
    else:
        result["duration"] = {
            "days": None,
            "formatted": "Unknown"
        }
    
    # Time in current status
    if status_changed_date and updated_date:
        status_duration = updated_date - status_changed_date
        result["time_in_current_status"] = {
            "days": status_duration.days,
            "formatted": f"{status_duration.days} days"
        }
        
        if status_duration.days < 30:
            total_seconds = status_duration.total_seconds()
            hours = int((total_seconds % (24 * 3600)) // 3600)
            minutes = int((total_seconds % 3600) // 60)
            result["time_in_current_status"]["formatted"] = f"{status_duration.days} days, {hours} hours, {minutes} minutes"
    
    # Time tracking
    time_spent = fields.get("timespent")
    if time_spent is not None:
        hours = time_spent // 3600
        minutes = (time_spent % 3600) // 60
        result["time_logged"] = {
            "seconds": time_spent,
            "formatted": f"{hours}h {minutes}m"
        }
    else:
        result["time_logged"] = {
            "seconds": None,
            "formatted": "No time logged"
        }
    
    # Original estimate
    estimate = fields.get("timeoriginalestimate")
    if estimate is not None:
        hours = estimate // 3600
        minutes = (estimate % 3600) // 60
        result["estimate"] = {
            "seconds": estimate,
            "formatted": f"{hours}h {minutes}m"
        }
    else:
        result["estimate"] = {
            "seconds": None,
            "formatted": "No estimate provided"
        }
    
    # Parent issue (Epic)
    parent = fields.get("parent", {})
    if parent:
        parent_fields = parent.get("fields", {})
        result["parent"] = {
            "key": parent.get("key", ""),
            "summary": parent_fields.get("summary", ""),
            "status": parent_fields.get("status", {}).get("name", "") if parent_fields.get("status") else ""
        }
    
    # Epic link (common custom field in Jira)
    epic_link = fields.get("customfield_10014")
    if epic_link:
        result["epic_link"] = epic_link
    
    # Due date
    due_date = fields.get("duedate")
    result["due_date"] = due_date if due_date else "No due date"
    
    return result


# if __name__ == "__main__":
#     jira = Jira(
#     url=JIRA_URL,
#     username=JIRA_USERNAME,
#     password=JIRA_PASSWORD)
#     JQL = 'assignee = currentUser() AND updated >= startOfWeek(-1) ORDER BY updated DESC'
#     jira_data = jira.jql(JQL)
#     for j in jira_data['issues']:
#         parsed_issues = parse_jira_issues(j)
        
#         # Print or use the results
#         print(json.dumps(parsed_issues, indent=2))