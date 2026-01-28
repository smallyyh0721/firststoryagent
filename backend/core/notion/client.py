"""
Notion Client for story management
Handles all interactions with Notion API
Adapted to work with existing database structure
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from notion_client import APIResponseError
from backend.models.story import Story, Genre, Status
from backend.core.notion.manager import notion_manager


class NotionClient:
    """
    Client for interacting with Notion API
    Manages stories in a Notion database
    """
    
    # Property names in Notion database
    PROPERTY_TITLE = "Title"
    PROPERTY_GENRE = "Genre"
    PROPERTY_STATUS = "Status"
    PROPERTY_CREATED_AT = "CreatedAt"
    PROPERTY_WORD_COUNT = "WordCount"
    PROPERTY_CONTENT = "Content"
    
    def __init__(
        self,
        database_id: Optional[str] = None
    ):
        """
        Initialize Notion Client
        
        Args:
            database_id: Notion Database ID
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID must be set in environment or passed as parameter")
        
        # Use singleton client from manager
        self.client = notion_manager.client
    
    def create_story(
        self,
        title: str,
        genre: Genre,
        status: Optional[Status] = None,
        content: str = ""
    ) -> Story:
        """
        Create a new story in Notion
        
        Args:
            title: Story title
            genre: Story genre
            status: Story status (optional, may not exist in database)
            content: Story content
            
        Returns:
            Created story object
        """
        try:
            # Calculate word count
            word_count = len(content.split())
            
            # Build properties - only include ones that exist in database
            properties = {
                self.PROPERTY_TITLE: {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                self.PROPERTY_GENRE: {
                    "multi_select": [
                        {
                            "name": genre.value
                        }
                    ]
                }
            }
            
            # Only add optional properties if they should exist
            # We'll try to add them, if they don't exist, API will error
            # and we'll retry without them
            if status is not None:
                properties[self.PROPERTY_STATUS] = {
                    "select": {
                        "name": status.value
                    }
                }
            
            properties[self.PROPERTY_CREATED_AT] = {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
            
            properties[self.PROPERTY_WORD_COUNT] = {
                "number": word_count
            }
            
            # Try to create with all properties first
            try:
                page = notion_manager.retry_request(lambda: self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                ))
            except APIResponseError as e:
                # If properties don't exist, try without them
                if "is not a property that exists" in str(e):
                    # Remove properties that don't exist
                    properties_to_remove = []
                    for prop_name in [self.PROPERTY_STATUS, self.PROPERTY_CREATED_AT, self.PROPERTY_WORD_COUNT]:
                        if prop_name in properties:
                            error_msg = str(e)
                            if prop_name.replace("PROPERTY_", "").lower() in error_msg.lower():
                                properties_to_remove.append(prop_name)
                    
                    for prop in properties_to_remove:
                        del properties[prop]
                    
                    # Retry without those properties
                    page = notion_manager.retry_request(lambda: self.client.pages.create(
                        parent={"database_id": self.database_id},
                        properties=properties,
                        children=[
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": content
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    ))
                else:
                    raise
            
            return self._parse_page_to_story(page)
            
        except APIResponseError as e:
            # Extract error message from body
            if hasattr(e, 'body'):
                if isinstance(e.body, dict):
                    error_msg = e.body.get("message", "Unknown error")
                else:
                    error_msg = str(e.body)
            else:
                error_msg = str(e)
            raise Exception(f"Notion API error: {e.code} - {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to create story: {e}")
    
    def get_story(self, page_id: str) -> Optional[Story]:
        """
        Retrieve a specific story by page ID
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Story object or None if not found
        """
        try:
            page = notion_manager.retry_request(lambda: self.client.pages.retrieve(page_id))
            return self._parse_page_to_story(page)
        except APIResponseError as e:
            if e.code == "object_not_found":
                return None
            if hasattr(e, 'body'):
                if isinstance(e.body, dict):
                    error_msg = e.body.get("message", "Unknown error")
                else:
                    error_msg = str(e.body)
            else:
                error_msg = str(e)
            raise Exception(f"Notion API error: {e.code} - {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to retrieve story: {e}")
    
    def list_stories(
        self,
        genre: Optional[Genre] = None,
        status: Optional[Status] = None,
        limit: int = 100
    ) -> List[Story]:
        """
        List all stories, optionally filtered by genre and/or status
        
        Args:
            genre: Filter by genre
            status: Filter by status (optional, may not work if property doesn't exist)
            limit: Maximum number of stories to return
            
        Returns:
            List of story objects
        """
        try:
            # Build filter - only include filters for properties that exist
            filters = []
            
            if genre:
                filters.append({
                    "property": self.PROPERTY_GENRE,
                    "multi_select": {
                        "contains": genre.value
                    }
                })
            
            # Only add status filter if parameter is provided
            # (may fail if property doesn't exist, but we'll handle it)
            if status:
                filters.append({
                    "property": self.PROPERTY_STATUS,
                    "select": {
                        "equals": status.value
                    }
                })
            
            # Query database
            query_params = {
                "database_id": self.database_id,
                "page_size": limit
            }
            
            # Try to add filter
            if filters:
                try:
                    if len(filters) == 1:
                        query_params["filter"] = filters[0]
                    else:
                        query_params["filter"] = {
                            "and": filters
                        }
                except Exception as e:
                    # If filter fails, query without it
                    print(f"Warning: Could not apply filter: {e}")
            
            response = notion_manager.retry_request(lambda: self.client.databases.query(**query_params))
            
            # Parse results
            stories = []
            for page in response["results"]:
                stories.append(self._parse_page_to_story(page))
            
            return stories
            
        except APIResponseError as e:
            if hasattr(e, 'body'):
                if isinstance(e.body, dict):
                    error_msg = e.body.get("message", "Unknown error")
                else:
                    error_msg = str(e.body)
            else:
                error_msg = str(e)
            raise Exception(f"Notion API error: {e.code} - {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to list stories: {e}")
    
    def update_story(
        self,
        page_id: str,
        title: Optional[str] = None,
        genre: Optional[Genre] = None,
        status: Optional[Status] = None,
        content: Optional[str] = None
    ) -> Story:
        """
        Update an existing story
        
        Args:
            page_id: Notion page ID
            title: New title
            genre: New genre
            status: New status (optional)
            content: New content
            
        Returns:
            Updated story object
        """
        try:
            # Build properties to update
            properties = {}
            
            if title is not None:
                properties[self.PROPERTY_TITLE] = {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            
            if genre is not None:
                properties[self.PROPERTY_GENRE] = {
                    "multi_select": [
                        {
                            "name": genre.value
                        }
                    ]
                }
            
            if status is not None:
                properties[self.PROPERTY_STATUS] = {
                    "select": {
                        "name": status.value
                    }
                }
            
            if content is not None:
                # Try to update word count if property exists
                word_count = len(content.split())
                properties[self.PROPERTY_WORD_COUNT] = {
                    "number": word_count
                }
            
            # Try to update with all properties
            try:
                page = notion_manager.retry_request(lambda: self.client.pages.update(
                    page_id=page_id,
                    properties=properties
                ))
            except APIResponseError as e:
                # If properties don't exist, try without them
                if "is not a property that exists" in str(e):
                    # Remove properties that don't exist
                    properties_to_remove = []
                    for prop_name in [self.PROPERTY_STATUS, self.PROPERTY_WORD_COUNT]:
                        if prop_name in properties:
                            error_msg = str(e)
                            if prop_name.replace("PROPERTY_", "").lower() in error_msg.lower():
                                properties_to_remove.append(prop_name)
                    
                    for prop in properties_to_remove:
                        del properties[prop]
                    
                    # Retry without those properties
                    page = notion_manager.retry_request(lambda: self.client.pages.update(
                        page_id=page_id,
                        properties=properties
                    ))
                else:
                    raise
            
            # If content was updated, we need to clear and re-add blocks
            if content is not None:
                # Get all blocks with retry logic
                blocks = notion_manager.retry_request(lambda: self.client.blocks.children.list(block_id=page_id))
                
                # Delete existing content blocks
                for block in blocks["results"]:
                    if block["type"] == "paragraph":
                        try:
                            self.client.blocks.delete(block["id"])
                        except:
                            pass
                
                # Add new content
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                )
                
                # Re-fetch to get updated page with retry logic
                page = notion_manager.retry_request(lambda: self.client.pages.retrieve(page_id))
            
            return self._parse_page_to_story(page)
            
        except APIResponseError as e:
            if hasattr(e, 'body'):
                if isinstance(e.body, dict):
                    error_msg = e.body.get("message", "Unknown error")
                else:
                    error_msg = str(e.body)
            else:
                error_msg = str(e)
            raise Exception(f"Notion API error: {e.code} - {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to update story: {e}")
    
    def delete_story(self, page_id: str) -> bool:
        """
        Delete a story (archive the page)
        
        Args:
            page_id: Notion page ID
            
        Returns:
            True if successful
        """
        try:
            notion_manager.retry_request(lambda: self.client.pages.update(
                page_id=page_id,
                archived=True
            ))
            return True
        except APIResponseError as e:
            if hasattr(e, 'body'):
                if isinstance(e.body, dict):
                    error_msg = e.body.get("message", "Unknown error")
                else:
                    error_msg = str(e.body)
            else:
                error_msg = str(e)
            raise Exception(f"Notion API error: {e.code} - {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to delete story: {e}")
    
    def _parse_page_to_story(self, page: Dict[str, Any]) -> Story:
        """
        Parse Notion page to Story object
        Handles missing properties gracefully
        
        Args:
            page: Notion page object
            
        Returns:
            Story object
        """
        properties = page["properties"]
        
        # Extract title - handle missing or empty title
        title_obj = properties.get(self.PROPERTY_TITLE, {}).get("title", [])
        if title_obj and len(title_obj) > 0:
            title = title_obj[0].get("text", {}).get("content", "Untitled")
        else:
            title = "Untitled"
        
        # Extract genre - handle both multi_select and select
        genre = Genre.FANTASY  # default
        genre_prop = properties.get(self.PROPERTY_GENRE, {})
        
        if "multi_select" in genre_prop:
            # Handle multi_select
            genres = genre_prop.get("multi_select", [])
            if genres:
                genre_value = genres[0].get("name", "Fantasy")
                try:
                    genre = Genre(genre_value)
                except ValueError:
                    genre = Genre.FANTASY
        elif "select" in genre_prop:
            # Handle single select (fallback)
            genre_value = genre_prop.get("select", {}).get("name", "Fantasy")
            try:
                genre = Genre(genre_value)
            except ValueError:
                genre = Genre.FANTASY
        
        # Extract status - optional
        status = Status.DRAFT  # default
        status_prop = properties.get(self.PROPERTY_STATUS, {})
        
        if "select" in status_prop:
            status_value = status_prop.get("select", {}).get("name", "Draft")
            try:
                status = Status(status_value)
            except ValueError:
                status = Status.DRAFT
        
        # Extract word count - optional
        word_count = properties.get(self.PROPERTY_WORD_COUNT, {}).get("number", 0)
        
        # Extract created date - optional
        created_at = datetime.now()  # default
        created_at_prop = properties.get(self.PROPERTY_CREATED_AT, {})
        
        if "date" in created_at_prop:
            created_at_str = created_at_prop.get("date", {}).get("start")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except:
                    created_at = datetime.now()
        
        # Extract content from blocks
        content = ""
        try:
            blocks = notion_manager.retry_request(lambda: self.client.blocks.children.list(block_id=page["id"]))
            for block in blocks["results"]:
                if block["type"] == "paragraph":
                    text_list = block["paragraph"].get("rich_text", [])
                    for text_obj in text_list:
                        if text_obj.get("type") == "text":
                            content += text_obj["text"].get("content", "") + "\n"
            content = content.strip()
        except:
            content = ""
        
        # Build URL
        url = f"https://www.notion.so/{page['id'].replace('-', '')}"
        
        return Story(
            id=page["id"],
            title=title,
            genre=genre,
            status=status,
            content=content,
            word_count=word_count,
            created_at=created_at,
            updated_at=datetime.now(),
            url=url
        )