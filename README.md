# Story Agent - AI-powered Story Writer with Notion Integration

An intelligent agent that uses LLM to automatically write and manage stories in Notion.

## Features

- 🤖 **AI Story Generation**: Use GLM-4.7 model to generate creative stories
- 📝 **Notion Integration**: Store and manage stories directly in Notion
- 🎨 **Web Interface**: Beautiful frontend for story creation and management
- 🏷️ **Story Organization**: Categorize stories by genre and track status
- 📊 **Analytics**: Track word count and creation dates

## Architecture

Inspired by [moltbot](https://github.com/moltbot/moltbot)'s skill-based architecture, Story Agent uses a modular design:

```
story-agent/
├── backend/              # FastAPI backend
│   ├── api/             # API endpoints
│   ├── core/            # Core business logic
│   │   ├── llm/        # LLM integration (GLM-4.7)
│   │   └── notion/     # Notion client wrapper
│   ├── models/          # Pydantic models
│   └── main.py         # Application entry point
├── frontend/            # Web interface
│   └── ...
└── requirements.txt     # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.8+
- Notion account with Integration setup
- ZhipuAI API key (for GLM-4.7)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd story-agent
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Notion Setup

1. Create a Notion Integration at https://www.notion.so/my-integrations
2. Copy the Integration Token
3. Create a Database in Notion with the following properties:
   - **Title** (Title)
   - **Genre** (Select)
   - **Status** (Select)
   - **CreatedAt** (Date)
   - **WordCount** (Number)

4. Connect your Integration to the Database:
   - Open Database settings (••• menu)
   - Click "Add connections"
   - Select your Integration

### Verify Notion Connection

Run the verification script to ensure your Notion setup is correct:

```bash
python verify_notion.py
```

This will test:
- Token validity
- Database access
- Query functionality
- Database structure

### Run the Application

Start the FastAPI backend:
```bash
cd backend
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Stories

- `POST /api/stories/generate` - Generate a new story
- `GET /api/stories` - List all stories
- `GET /api/stories/{story_id}` - Get a specific story
- `PUT /api/stories/{story_id}` - Update a story
- `DELETE /api/stories/{story_id}` - Delete a story

## Project Structure

```
story-agent/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── stories.py          # Story-related endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # GLM-4.7 client
│   │   │   └── prompts.py      # Story generation prompts
│   │   └── notion/
│   │       ├── __init__.py
│   │       └── client.py       # Notion API wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   └── story.py            # Story data models
│   └── main.py                 # FastAPI app
├── frontend/                   # Web UI (to be implemented)
├── tests/                      # Test files
├── verify_notion.py           # Notion connection verifier
├── requirements.txt
└── README.md
```

## Development

### Adding New Features

The project follows a modular structure. To add new features:

1. Create models in `backend/models/`
2. Implement business logic in `backend/core/`
3. Add API endpoints in `backend/api/`
4. Update documentation

### Testing

Run tests with:
```bash
pytest tests/
```

## License

MIT License

## Acknowledgments

- Inspired by [moltbot](https://github.com/moltbot/moltbot)'s skill architecture
- Powered by ZhipuAI's GLM-4.7 model
- Integrated with Notion API