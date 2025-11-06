# AI Tutoring Assistant - Web Frontend

A modern, interactive web interface for the AI Tutoring Assistant built with FastAPI and vanilla JavaScript.

## Features

- 🎨 **Modern UI**: Beautiful, responsive design with gradient backgrounds and smooth animations
- 📊 **Real-time Progress Tracking**: Live updates of questions asked, correct answers, and accuracy
- 💬 **Interactive Q&A**: Seamless question-answer flow with instant feedback
- 💡 **Smart Explanations**: Contextual explanations based on student responses
- 📈 **Progress Visualization**: Visual progress bars and statistics
- 🔄 **Session Management**: Start, manage, and end tutoring sessions

## Architecture

### Backend (FastAPI)
- **`api.py`**: RESTful API server that wraps the tutoring assistant functionality
- Provides endpoints for:
  - Starting sessions
  - Submitting answers
  - Getting progress
  - Ending sessions

### Frontend (HTML/CSS/JavaScript)
- **`frontend/index.html`**: Single-page application with embedded CSS and JavaScript
- No build process required - just open in browser or serve via FastAPI

## Installation

1. **Install dependencies** (if not already installed):
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GOOGLE_API_KEY=your-api-key-here
```

## Running the Application

### Quick Start (Recommended)

**On macOS/Linux:**
```bash
./start_server.sh
```

**On Windows:**
```cmd
start_server.bat
```

The startup script will:
- Activate the virtual environment (if present)
- Check for API key
- Install dependencies if needed
- Start the server on `http://localhost:8000`

### Manual Start Options

**Option 1: Run FastAPI server directly**
```bash
python api.py
```

The server will start on `http://localhost:8000`

**Option 2: Run with uvicorn**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Option 3: Access frontend directly**
Open `frontend/index.html` in your browser (note: API calls will fail unless you configure CORS or run the server)

## Usage

1. **Start the server**:
   ```bash
   python api.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

3. **Start a session**:
   - Enter your Student ID (or use default)
   - Enter a topic you want to learn about
   - Select your understanding level (beginner/intermediate/advanced)
   - Click "Start Learning Session"

4. **Answer questions**:
   - Read the question displayed
   - Type your answer in the text area
   - Click "Submit Answer" or press Enter
   - View feedback and explanations

5. **Track progress**:
   - Monitor your stats in real-time
   - See your accuracy percentage
   - Track your understanding level progression

6. **End session**:
   - Click "End Session" when finished
   - View your session summary

## API Endpoints

### `POST /api/session/start`
Start a new tutoring session.

**Request:**
```json
{
  "student_id": "student_001",
  "topic": "Python programming",
  "understanding_level": "beginner"
}
```

**Response:**
```json
{
  "session_id": "student_001_Python programming_0",
  "message": "Session started successfully",
  "question": "What is a variable in Python?",
  "state": {
    "topic": "Python programming",
    "understanding_level": "beginner",
    "questions_asked": 0,
    "correct_answers": 0,
    "session_active": true
  }
}
```

### `POST /api/session/answer`
Submit an answer to the current question.

**Request:**
```json
{
  "session_id": "student_001_Python programming_0",
  "answer": "A variable is a container that stores data"
}
```

**Response:**
```json
{
  "session_id": "student_001_Python programming_0",
  "message": "Excellent! You correctly identified...",
  "question": "What is the difference between a list and a tuple?",
  "state": {
    "topic": "Python programming",
    "understanding_level": "beginner",
    "questions_asked": 1,
    "correct_answers": 1,
    "session_active": true,
    "is_correct": true,
    "score": 0.95,
    "explanation": null,
    "accuracy": 100.0
  }
}
```

### `GET /api/session/{session_id}/progress`
Get current session progress.

### `GET /api/progress/{student_id}`
Get overall progress for a student across all sessions.

### `POST /api/session/{session_id}/end`
End a tutoring session and get final summary.

### `GET /api/health`
Health check endpoint.

## Frontend Features

### Responsive Design
- Works on desktop, tablet, and mobile devices
- Adaptive layout that adjusts to screen size

### Real-time Updates
- Progress bars update automatically
- Statistics refresh after each answer
- Smooth animations for feedback

### User Experience
- Loading indicators during API calls
- Error messages for failed requests
- Keyboard shortcuts (Enter to submit)
- Clear visual feedback for correct/incorrect answers

## Customization

### Styling
Edit the `<style>` section in `frontend/index.html` to customize:
- Colors and gradients
- Fonts and typography
- Spacing and layout
- Animations

### API Configuration
If running frontend separately, update `API_BASE` in the JavaScript:
```javascript
const API_BASE = 'http://localhost:8000';
```

## Troubleshooting

### API Key Issues
- Ensure `GOOGLE_API_KEY` is set in your environment
- Check that your API key is valid and has sufficient quota

### CORS Errors
- The API includes CORS middleware allowing all origins
- For production, restrict `allow_origins` in `api.py`

### Session Not Found
- Sessions are stored in memory (not persistent)
- Restarting the server clears all sessions
- For production, use Redis or a database for session storage

### Port Already in Use
- Change the port in `api.py` or use uvicorn with `--port` flag
- Update frontend `API_BASE` if using a different port

## Production Deployment

For production deployment:

1. **Use a production ASGI server**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
   ```

2. **Configure CORS properly**:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

3. **Add session persistence**:
   - Use Redis for session storage
   - Or implement database-backed sessions

4. **Add authentication**:
   - Implement user authentication
   - Secure API endpoints

5. **Environment variables**:
   - Use secure secret management
   - Never commit API keys

## License

This project is part of an LLM course curriculum.

