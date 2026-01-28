# Story Agent - Debugging Guide

## 422 Error Analysis and Resolution

### Problem Summary
When attempting to generate a story, the API returned a `422 Unprocessable Content` error:
```
INFO:     127.0.0.1:51790 - "POST /api/stories/generate HTTP/1.1" 422 Unprocessable Content
```

### Root Cause
The 422 error was caused by a **genre value mismatch** between the frontend and backend:

**Frontend (HTML/JS):**
- Used `"SciFi"` (no hyphen)

**Backend (Pydantic Enum):**
- Expected `"Sci-Fi"` (with hyphen)

This mismatch caused Pydantic validation to fail, returning a 422 error before the request even reached the LLM generation logic.

### Changes Made

#### 1. Fixed Genre Value Mismatch
**Files Modified:**
- `frontend/index.html` - Changed `value="SciFi"` to `value="Sci-Fi"`
- `frontend/app.js` - Updated `genreNames` mapping from `'SciFi'` to `'Sci-Fi'`

**Impact:** All genre selections now properly match the backend enum values.

#### 2. Enhanced Backend Logging
**File Modified:** `backend/api/stories.py`

**Additions:**
- Comprehensive request logging with unique request IDs
- Detailed validation logging for all parameters
- Step-by-step progress tracking through the generation process
- Enhanced error messages with specific field information
- Full stack trace logging for debugging

**Example Log Output:**
```
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Story generation request received
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Request details - Genre: Fantasy, Length: medium
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Prompt length: 50 characters
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Validating request parameters...
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Valid genre: Fantasy
2026-01-28 18:15:00 - backend.api.stories - INFO - [20260128181500] Starting LLM story generation...
```

#### 3. Enhanced Frontend Debugging
**File Modified:** `frontend/app.js`

**Additions:**
- Detailed console logging before and after API calls
- Request body inspection
- Response status and body logging
- Enhanced error parsing and display
- Stack trace logging for JavaScript errors

**Example Console Output:**
```javascript
=== Story Generation Request ===
Genre: Fantasy
Genre type: string
Length: medium
Length type: string
Prompt length: 50
Prompt preview: 一只勇敢的小猫在森林里...
Request body: {
  "prompt": "一只勇敢的小猫在森林里...",
  "genre": "Fantasy",
  "length": "medium"
}
Sending request to: http://localhost:8000/api/stories/generate
```

## How to Troubleshoot 422 Errors

### Step 1: Check Frontend Console
1. Open browser DevTools (F12)
2. Go to the Console tab
3. Look for the `=== Story Generation Request ===` section
4. Verify the values being sent:
   - Genre should match one of: Fantasy, Sci-Fi, Mystery, Romance, Adventure, Horror, Drama, Comedy, Thriller, Other
   - Length should be: short, medium, or long
   - Prompt should be non-empty and at least 5 characters

### Step 2: Check Network Tab
1. In DevTools, go to the Network tab
2. Click on the failed `/api/stories/generate` request
3. Check the Request Payload tab to see exact data sent
4. Check the Response tab for error details:
   ```json
   {
     "detail": [
       {
         "loc": ["body", "genre"],
         "msg": "value is not a valid enumeration member",
         "type": "type_error.enum"
       }
     ]
   }
   ```

### Step 3: Check Backend Logs
1. Check the terminal where the backend is running
2. Look for the request ID (timestamp format: YYYYMMDDHHMMSS)
3. Review the validation errors logged
4. Check for any `KeyError` or other exceptions

### Step 4: Verify Data Types
Ensure all values match the expected types:

**Genre (Enum):**
```python
class Genre(str, Enum):
    FANTASY = "Fantasy"
    SCIFI = "Sci-Fi"      # Note: with hyphen
    ROMANCE = "Romance"
    MYSTERY = "Mystery"
    HORROR = "Horror"
    ADVENTURE = "Adventure"
    DRAMA = "Drama"
    COMEDY = "Comedy"
    THRILLER = "Thriller"
    OTHER = "Other"
```

**Length (String):**
- `"short"` - ~500 words
- `"medium"` - ~1500 words
- `"long"` - ~3000 words

**Prompt (String):**
- Minimum 5 characters
- No special format requirements

## Common 422 Error Scenarios

### Scenario 1: Invalid Genre Value
**Error Message:**
```
value is not a valid enumeration member; permitted: 'Fantasy', 'Sci-Fi', 'Romance', ...
```

**Solution:**
- Check HTML `value` attributes for genre radio buttons
- Verify they match the backend enum exactly (case-sensitive)

### Scenario 2: Invalid Length Value
**Error Message:**
```
value is not a valid enumeration member; permitted: 'short', 'medium', 'long'
```

**Solution:**
- Check HTML `value` attributes for length radio buttons
- Ensure they are exactly 'short', 'medium', or 'long'

### Scenario 3: Empty or Short Prompt
**Error Message:**
```
Validation error: Prompt must be at least 5 characters long
```

**Solution:**
- Ensure prompt textarea has content
- Minimum 5 characters required

### Scenario 4: Missing Required Fields
**Error Message:**
```
field required
```

**Solution:**
- Ensure all required fields are present in request body
- Check that radio buttons have default checked values

## Is This Related to LLM Token Limits?

**NO** - The 422 error is not related to LLM token limits because:

1. **Timing:** 422 errors occur during request validation, before any LLM API calls
2. **Location:** FastAPI validates the request before it reaches the LLM generation logic
3. **Error Type:** Token limit errors would typically be:
   - Timeout errors (504)
   - LLM API errors (500)
   - Content too large (413)

**If you encounter actual LLM token limit issues:**
- The error would be caught in `backend/core/llm/client.py`
- Logs would show "LLM API request failed" or similar
- Response would be 500 Internal Server Error, not 422

## Testing the Fixes

### Test 1: Generate a Story with Each Genre
```bash
# Open frontend in browser
# Try generating stories with different genres
# Check console logs for correct values
# Verify successful generation
```

### Test 2: Check Backend Logs
```bash
# Monitor backend terminal while generating
# Verify all steps complete successfully
# Check for detailed request information
```

### Test 3: Verify Error Handling
```bash
# Try with invalid genre (e.g., "InvalidGenre")
# Check for proper 422 error with clear message
# Verify logs show validation failure
```

## Additional Debugging Tips

### Enable Debug Logging
To enable more verbose logging, modify `backend/api/stories.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Test API Directly
Use `test_api.py` to test the API independently:
```bash
python test_api.py
```

### Check Environment Variables
Ensure required environment variables are set:
```bash
ZHIPUAI_API_KEY=your_api_key
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id
```

## Summary

The 422 error was resolved by:
1. ✅ Fixed genre value mismatch (SciFi → Sci-Fi)
2. ✅ Added comprehensive logging to both frontend and backend
3. ✅ Enhanced error messages for better debugging
4. ✅ Added validation checks with detailed error reporting

The application now has robust debugging capabilities that will help quickly identify any future 422 or other validation errors.