"""Notion API client integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from notion_client import Client
from loguru import logger
from dateutil import parser as date_parser

from src.utils.config import settings
from src.models.notion import NotionTask, TaskPriority, TaskStatus, NotionTeam, TeamStatus


class NotionClient:
    """Wrapper for Notion API client with enhanced functionality."""

    def __init__(self):
        """Initialize Notion client."""
        if not settings.notion_token:
            raise ValueError("NOTION_TOKEN not configured")
            
        self.client = Client(auth=settings.notion_token)
        self.tasks_database_id = settings.notion_database_tasks
        self.teams_database_id = settings.notion_database_team
        
        if not self.tasks_database_id:
            logger.warning("NOTION_DATABASE_TASKS not configured")
        if not self.teams_database_id:
            logger.warning("NOTION_DATABASE_TEAMS not configured")
    
    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        discord_user_id: str = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new task in Notion database.
        
        Args:
            title: Task title
            description: Task description
            discord_user_id: Discord user ID who created the task
            priority: Task priority level
            start_date: Task start date
            
        Returns:
            Dict containing the created Notion page data
            
        Raises:
            ValueError: If required fields are missing
            Exception: If Notion API call fails
        """
        if not self.tasks_database_id:
            raise ValueError("Tasks database ID not configured")
            
        if not title or not discord_user_id:
            raise ValueError("Title and Discord user ID are required")
        
        # Prepare properties for Notion database
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Priority": {
                "select": {
                    "name": priority.value
                }
            },
            "Discord ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(discord_user_id)
                        }
                    }
                ]
            }
        }
        
        # Add description if provided
        if description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": description
                        }
                    }
                ]
            }
        
        # Add start date if provided
        if start_date:
            properties["Start Date"] = {
                "date": {
                    "start": start_date.date().isoformat()
                }
            }
        
        try:
            # Create page in Notion database
            logger.debug(f"Creating Notion task with properties: {properties}")
            response = self.client.pages.create(
                parent={"database_id": self.tasks_database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion task: {title} for user {discord_user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create Notion task: {e}")
            logger.error(f"Database ID: {self.tasks_database_id}")
            logger.error(f"Properties sent: {properties}")
            raise
    
    async def get_task(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a task from Notion by page ID.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Dict containing the Notion page data
        """
        try:
            response = self.client.pages.retrieve(page_id)
            return response
        except Exception as e:
            logger.error(f"Failed to retrieve Notion task {page_id}: {e}")
            raise
    
    async def update_task_status(
        self, 
        page_id: str, 
        status: TaskStatus
    ) -> Dict[str, Any]:
        """Update task status in Notion.
        
        Args:
            page_id: Notion page ID
            status: New task status
            
        Returns:
            Dict containing the updated Notion page data
        """
        try:
            properties = {
                "Status": {
                    "select": {
                        "name": status.value
                    }
                }
            }
            
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            logger.info(f"Updated Notion task {page_id} status to {status.value}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to update Notion task status: {e}")
            raise
    
    async def query_user_tasks(
        self, 
        discord_user_id: str, 
        status: Optional[TaskStatus] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query tasks for a specific Discord user.
        
        Args:
            discord_user_id: Discord user ID
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of Notion page data matching the query
        """
        if not self.tasks_database_id:
            raise ValueError("Tasks database ID not configured")
        
        try:
            # Build filter
            filter_conditions = [
                {
                    "property": "Discord ID",
                    "rich_text": {
                        "contains": str(discord_user_id)
                    }
                }
            ]
            
            if status:
                filter_conditions.append({
                    "property": "Status",
                    "select": {
                        "equals": status.value
                    }
                })
            
            query_filter = {
                "and": filter_conditions
            } if len(filter_conditions) > 1 else filter_conditions[0]
            
            response = self.client.databases.query(
                database_id=self.tasks_database_id,
                filter=query_filter,
                page_size=limit,
                sorts=[
                    {
                        "property": "Priority",
                        "direction": "descending"
                    },
                    {
                        "timestamp": "created_time",
                        "direction": "descending"
                    }
                ]
            )
            
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Failed to query user tasks: {e}")
            raise
    
    async def get_database_info(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a Notion database.
        
        Args:
            database_id: Database ID (defaults to tasks database)
            
        Returns:
            Dict containing database information
        """
        db_id = database_id or self.tasks_database_id
        if not db_id:
            raise ValueError("Database ID not provided and tasks database not configured")
        
        try:
            response = self.client.databases.retrieve(database_id=db_id)
            return response
        except Exception as e:
            logger.error(f"Failed to retrieve database info: {e}")
            raise
    
    def log_database_schema(self, database_id: Optional[str] = None):
        """Log the database schema for debugging."""
        try:
            db_info = self.client.databases.retrieve(database_id or self.tasks_database_id)
            properties = db_info.get("properties", {})
            
            logger.info("=== Notion Database Schema ===")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                logger.info(f"Property: '{prop_name}' - Type: {prop_type}")
                
                if prop_type == "select":
                    options = prop_info.get("select", {}).get("options", [])
                    option_names = [opt.get("name") for opt in options]
                    logger.info(f"  Select options: {option_names}")
                    
            logger.info("=== End Schema ===")
            
        except Exception as e:
            logger.error(f"Failed to log database schema: {e}")
    
    def extract_page_content(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key content from a Notion page response.
        
        Args:
            page_data: Raw Notion page data
            
        Returns:
            Dict with extracted content
        """
        try:
            properties = page_data.get("properties", {})
            
            # Extract title
            title_prop = properties.get("Title", {})
            title = ""
            if title_prop.get("title"):
                title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
            
            # Extract description
            desc_prop = properties.get("Description", {})
            description = ""
            if desc_prop.get("rich_text"):
                description = "".join([t.get("plain_text", "") for t in desc_prop["rich_text"]])
            
            # Extract status
            status_prop = properties.get("Status", {})
            status = status_prop.get("select", {}).get("name", "Not started")
            
            # Extract priority
            priority_prop = properties.get("Priority", {})
            priority = priority_prop.get("select", {}).get("name", "Medium")
            
            # Extract Discord ID
            discord_prop = properties.get("Discord ID", {})
            discord_id = ""
            if discord_prop.get("rich_text"):
                discord_id = "".join([t.get("plain_text", "") for t in discord_prop["rich_text"]])
            
            # Extract dates
            start_date = None
            start_prop = properties.get("Start Date", {})
            if start_prop.get("date", {}).get("start"):
                start_date = start_prop["date"]["start"]
            
            return {
                "id": page_data.get("id"),
                "url": page_data.get("url"),
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "discord_id": discord_id,
                "start_date": start_date,
                "created_time": page_data.get("created_time"),
                "last_edited_time": page_data.get("last_edited_time")
            }
            
        except Exception as e:
            logger.error(f"Failed to extract page content: {e}")
            return {"error": str(e)}
    
    async def create_team_member(
        self,
        name: str,
        position: str,
        email: str,
        phone_number: str,
        birthday: str,
        discord_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new team member in Notion database.
        
        Args:
            name: Team member name (required)
            position: Team member position (required)
            email: Team member email (required)
            phone_number: Team member phone number (required)
            birthday: Team member birthday (required)
            discord_user_id: Discord user ID who created the record
            
        Returns:
            Dict containing the created Notion page data
            
        Raises:
            ValueError: If required fields are missing
            Exception: If Notion API call fails
        """
        if not self.teams_database_id:
            raise ValueError("Teams database ID not configured")
            
        if not all([name, position, email, phone_number, birthday]):
            raise ValueError("All fields (name, position, email, phone_number, birthday) are required")
        
        # Parse birthday string to datetime
        try:
            birthday_date = date_parser.parse(birthday)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid birthday format: {birthday}. Please use a valid date format like 'MM-DD-YYYY' or 'January 15, 1990'")
        
        # Prepare properties for Notion database
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name
                        }
                    }
                ]
            }
        }
        
        # Add required fields
        properties["Position"] = {
            "rich_text": [
                {
                    "text": {
                        "content": position
                    }
                }
            ]
        }
        
        properties["Email"] = {
            "rich_text": [
                {
                    "text": {
                        "content": email
                    }
                }
            ]
        }
        
        properties["Phone Number"] = {
            "phone_number": phone_number
        }
        
        properties["Birthday"] = {
            "date": {
                "start": birthday_date.date().isoformat()
            }
        }
        
        # Add automatic Status field with default value
        properties["Status"] = {
            "select": {
                "name": TeamStatus.ACTIVE.value
            }
        }
        
        try:
            # Create page in Notion database
            logger.debug(f"Creating Notion team member with properties: {properties}")
            response = self.client.pages.create(
                parent={"database_id": self.teams_database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion team member: {name}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create Notion team member: {e}")
            logger.error(f"Database ID: {self.teams_database_id}")
            logger.error(f"Properties sent: {properties}")
            raise


# Global client instance
notion_client = None

def get_notion_client() -> NotionClient:
    """Get or create global Notion client instance."""
    global notion_client
    if notion_client is None:
        notion_client = NotionClient()
    return notion_client