"""
LLM Client for story generation
Supports ZhipuAI GLM-4.7 and other OpenAI-compatible APIs
"""

import os
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    Client for interacting with LLM APIs
    Currently supports ZhipuAI GLM-4.7
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "glm-4"
    ):
        """
        Initialize LLM Client
        
        Args:
            api_key: API key for the LLM service
            base_url: Base URL for the API
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY must be set in environment or passed as parameter")
        
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    def generate_story(
        self,
        prompt: str,
        genre: str = "Fantasy",
        length: str = "medium",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a story based on the given prompt
        
        Args:
            prompt: Story prompt or idea
            genre: Story genre
            length: Story length (short, medium, long)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated story text
        """
        # Adjust max_tokens based on length
        length_tokens = {
            "short": 500,
            "medium": 1500,
            "long": 3000
        }
        max_tokens = length_tokens.get(length.lower(), max_tokens)
        
        # Build the prompt with genre context
        system_prompt = self._build_system_prompt(genre)
        
        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract the generated story
            story = data["choices"][0]["message"]["content"]
            return story.strip()
            
        except httpx.HTTPError as e:
            raise Exception(f"LLM API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {e}")
        except Exception as e:
            raise Exception(f"Story generation failed: {e}")
    
    def _build_system_prompt(self, genre: str) -> str:
        """
        Build system prompt based on genre
        
        Args:
            genre: Story genre
            
        Returns:
            System prompt string
        """
        genre_instructions = {
            "Fantasy": "Create a magical fantasy world with wizards, dragons, or mythical creatures.",
            "Sci-Fi": "Write a science fiction story with futuristic technology, space exploration, or AI.",
            "Romance": "Create a heartwarming romance story with emotional depth and character development.",
            "Mystery": "Craft a suspenseful mystery with clues, twists, and an engaging plot.",
            "Horror": "Write a chilling horror story with suspense and supernatural elements.",
            "Adventure": "Create an exciting adventure with action, exploration, and discovery.",
            "Drama": "Write a compelling drama with realistic characters and emotional conflicts.",
            "Comedy": "Create a humorous and entertaining story with witty dialogue.",
            "Thriller": "Craft a fast-paced thriller with tension and excitement."
        }
        
        instruction = genre_instructions.get(genre, "Create an engaging story.")
        
        return f"""You are a creative writer specializing in {genre} stories. {instruction}

Write a compelling story with:
- Well-developed characters
- Clear plot progression
- Vivid descriptions
- Appropriate pacing
- Satisfying conclusion

Focus on creating an immersive reading experience that captures the essence of the {genre} genre."""
    
    def generate_title(self, story_content: str) -> str:
        """
        Generate a title for a story
        
        Args:
            story_content: The story text
            
        Returns:
            Generated title
        """
        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Generate a catchy, creative title for the given story. Return only the title, no additional text."
                        },
                        {
                            "role": "user",
                            "content": f"Generate a title for this story:\n\n{story_content[:500]}..."
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 50
                }
            )
            
            response.raise_for_status()
            data = response.json()
            title = data["choices"][0]["message"]["content"]
            
            # Clean up the title
            title = title.strip()
            # Remove quotes if present
            title = title.strip('"\'')
            
            return title
            
        except Exception as e:
            # Fallback to a generic title if generation fails
            return "Untitled Story"
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()