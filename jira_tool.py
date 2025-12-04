import json
from datetime import datetime
from atlassian import Jira
from config import JIRA_URL, CUSTOM_FIELDS

def extract_description(description_field):
    """Extract readable description from Jira's various formats (plain text, ADF, etc)."""
    if not description_field:
        return ""

    # If it's a string, return as-is
    if isinstance(description_field, str):
        return description_field

    # Handle Atlassian Document Format (ADF)
    if isinstance(description_field, dict) and description_field.get("type") == "doc":
        text_parts = []
        for content in description_field.get("content", []):
            if content.get("type") == "paragraph":
                for text_node in content.get("content", []):
                    if text_node.get("type") == "text":
                        text_parts.append(text_node.get("text", ""))
            elif content.get("type") == "codeBlock":
                code_text = ""
                for text_node in content.get("content", []):
                    if text_node.get("type") == "text":
                        code_text += text_node.get("text", "")
                if code_text:
                    text_parts.append(f"```\n{code_text}\n```")
        return "\n".join(text_parts)

    return str(description_field)

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
        return [extract_issue_info(issue, JIRA_URL) for issue in data]
    else:
        return extract_issue_info(data, JIRA_URL)

def extract_issue_info(issue, jira_url):
    """Extract key information from a Jira issue that's relevant for management."""
    result = {}
    fields = issue.get("fields", {})

    # Basic information
    result["key"] = issue.get("key", "")
    result["url"] = f"{jira_url.rstrip('/')}/browse/{issue.get('key', '')}"
    result["summary"] = fields.get("summary", "")
    result["description"] = extract_description(fields.get("description"))

    # Labels
    labels = fields.get("labels", [])
    result["labels"] = labels if labels else []
    
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

    # Resolved date
    resolved_date = parse_date(fields.get("resolutiondate", ""))
    result["resolved"] = resolved_date.strftime("%Y-%m-%d") if resolved_date else "Not resolved"
    
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

    # Issue links (blockers, dependencies, etc.)
    issue_links = fields.get("issuelinks", [])
    blockers = []
    blocked_by = []
    relates_to = []

    for link in issue_links:
        link_type = link.get("type", {}).get("name", "").lower()

        if "outwardIssue" in link:
            linked_issue = link["outwardIssue"]
            if "blocks" in link_type:
                blockers.append({
                    "key": linked_issue.get("key"),
                    "summary": linked_issue.get("fields", {}).get("summary", ""),
                    "status": linked_issue.get("fields", {}).get("status", {}).get("name", "")
                })
            else:
                relates_to.append(linked_issue.get("key"))

        if "inwardIssue" in link:
            linked_issue = link["inwardIssue"]
            if "blocked" in link_type:
                blocked_by.append({
                    "key": linked_issue.get("key"),
                    "summary": linked_issue.get("fields", {}).get("summary", ""),
                    "status": linked_issue.get("fields", {}).get("status", {}).get("name", "")
                })

    result["is_blocked"] = len(blocked_by) > 0
    result["blocked_by"] = blocked_by
    result["blocks"] = blockers

    # Epic link (using custom field from config)
    epic_link_field = CUSTOM_FIELDS.get("epic_link")
    epic_link = fields.get(epic_link_field)
    if epic_link:
        result["epic_link"] = epic_link

    # Story points (using custom field from config)
    story_points_field = CUSTOM_FIELDS.get("story_points")
    story_points = fields.get(story_points_field)
    result["story_points"] = story_points if story_points else None

    # Sprint information (using custom field from config)
    sprint_field = CUSTOM_FIELDS.get("sprint")
    sprint_info = fields.get(sprint_field)
    if sprint_info:
        if isinstance(sprint_info, list) and sprint_info:
            # Get the most recent sprint (last item)
            latest_sprint = sprint_info[-1]
            if isinstance(latest_sprint, str):
                result["sprint"] = latest_sprint
            elif isinstance(latest_sprint, dict):
                result["sprint"] = latest_sprint.get("name", "No sprint")
        elif isinstance(sprint_info, dict):
            result["sprint"] = sprint_info.get("name", "No sprint")
        else:
            result["sprint"] = str(sprint_info)
    else:
        result["sprint"] = None

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