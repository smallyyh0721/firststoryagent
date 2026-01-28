"""
Story API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging
from datetime import datetime
from backend.models.story import (
    Story,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryUpdate,
    StoryListResponse,
    Genre,
    Status
)
from backend.core.llm import LLMClient
from backend.core.notion import NotionClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stories", tags=["stories"])


# Dependency injection functions
def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return LLMClient()


def get_notion_client() -> NotionClient:
    """Get Notion client instance"""
    return NotionClient()


@router.post("/generate", response_model=StoryGenerateResponse)
async def generate_story(
    request: StoryGenerateRequest,
    llm: LLMClient = Depends(get_llm_client),
    notion: NotionClient = Depends(get_notion_client)
):
    """
    Generate a new story using AI and save it to Notion
    
    - **prompt**: Story idea or concept
    - **genre**: Desired story genre
    - **length**: Story length (short, medium, long)
    """
    request_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    logger.info(f"[{request_id}] Story generation request received")
    logger.info(f"[{request_id}] Request details - Genre: {request.genre.value}, Length: {request.length}")
    logger.info(f"[{request_id}] Prompt length: {len(request.prompt)} characters")
    logger.info(f"[{request_id}] Prompt preview: {request.prompt[:100]}...")
    
    try:
        # Validate request
        logger.info(f"[{request_id}] Validating request parameters...")
        
        if not request.prompt or len(request.prompt.strip()) < 5:
            logger.error(f"[{request_id}] Invalid prompt: too short or empty")
            raise ValueError("Prompt must be at least 5 characters long")
        
        if request.length not in ["short", "medium", "long"]:
            logger.error(f"[{request_id}] Invalid length parameter: {request.length}")
            raise ValueError(f"Length must be one of: short, medium, long. Got: {request.length}")
        
        # Log genre validation
        logger.info(f"[{request_id}] Valid genre: {request.genre.value}")
        logger.info(f"[{request_id}] Genre enum type: {type(request.genre)}")
        
        # Generate story content using LLM
        logger.info(f"[{request_id}] Starting LLM story generation...")
        story_content = llm.generate_story(
            prompt=request.prompt,
            genre=request.genre.value,
            length=request.length
        )
        logger.info(f"[{request_id}] LLM generation completed. Story length: {len(story_content)} characters")
        
        # Generate a title for the story
        logger.info(f"[{request_id}] Generating title...")
        title = llm.generate_title(story_content)
        logger.info(f"[{request_id}] Title generated: {title}")
        
        # Save to Notion
        logger.info(f"[{request_id}] Saving story to Notion...")
        story = notion.create_story(
            title=title,
            genre=request.genre,
            status=Status.DRAFT,
            content=story_content
        )
        logger.info(f"[{request_id}] Story saved to Notion successfully. Story ID: {story.id}")
        
        logger.info(f"[{request_id}] Story generation completed successfully")
        
        return StoryGenerateResponse(
            story=story,
            message="Story generated successfully"
        )
        
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except KeyError as e:
        logger.error(f"[{request_id}] Data access error - Missing key: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data processing error: Missing expected field {str(e)}"
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error during story generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate story: {str(e)}. Please check the logs for details."
        )


@router.get("", response_model=StoryListResponse)
async def list_stories(
    genre: Optional[Genre] = None,
    status_param: Optional[Status] = None,
    limit: int = 100,
    notion: NotionClient = Depends(get_notion_client)
):
    """
    List all stories with optional filtering
    
    - **genre**: Filter by genre
    - **status**: Filter by status
    - **limit**: Maximum number of stories to return
    """
    logger.info(f"Listing stories - Genre filter: {genre}, Status filter: {status_param}, Limit: {limit}")
    
    try:
        stories = notion.list_stories(
            genre=genre,
            status=status_param,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(stories)} stories")
        
        return StoryListResponse(
            stories=stories,
            total=len(stories)
        )
        
    except Exception as e:
        logger.error(f"Error listing stories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list stories: {str(e)}"
        )


@router.get("/{story_id}", response_model=Story)
async def get_story(
    story_id: str,
    notion: NotionClient = Depends(get_notion_client)
):
    """
    Get a specific story by ID
    
    - **story_id**: Notion page ID
    """
    logger.info(f"Fetching story with ID: {story_id}")
    
    try:
        story = notion.get_story(story_id)
        
        if not story:
            logger.warning(f"Story not found: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        logger.info(f"Successfully retrieved story: {story.title}")
        return story
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching story {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get story: {str(e)}"
        )


@router.put("/{story_id}", response_model=Story)
async def update_story(
    story_id: str,
    update: StoryUpdate,
    notion: NotionClient = Depends(get_notion_client)
):
    """
    Update an existing story
    
    - **story_id**: Notion page ID
    - **title**: New title (optional)
    - **genre**: New genre (optional)
    - **status**: New status (optional)
    - **content**: New content (optional)
    """
    logger.info(f"Updating story {story_id}")
    logger.info(f"Update data - Title: {update.title}, Genre: {update.genre}, Status: {update.status}")
    
    try:
        story = notion.get_story(story_id)
        
        if not story:
            logger.warning(f"Story not found for update: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Update story
        updated_story = notion.update_story(
            page_id=story_id,
            title=update.title,
            genre=update.genre,
            status=update.status,
            content=update.content
        )
        
        logger.info(f"Story {story_id} updated successfully")
        return updated_story
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating story {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update story: {str(e)}"
        )


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    notion: NotionClient = Depends(get_notion_client)
):
    """
    Delete a story (archive the page)
    
    - **story_id**: Notion page ID
    """
    logger.info(f"Deleting story {story_id}")
    
    try:
        story = notion.get_story(story_id)
        
        if not story:
            logger.warning(f"Story not found for deletion: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        notion.delete_story(story_id)
        
        logger.info(f"Story {story_id} deleted successfully")
        return {"message": "Story deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting story {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete story: {str(e)}"
        )
