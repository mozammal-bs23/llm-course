#!/usr/bin/env python3
"""
FastAPI Backend for AI Tutoring Assistant
Provides REST API endpoints for the web frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
from pathlib import Path

from ai_tutoring_assistant import TutoringLLM, ProgressTracker, TutoringWorkflow, TutoringState

# Initialize FastAPI app
app = FastAPI(title="AI Tutoring Assistant API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management (in production, use Redis or database)
active_sessions: Dict[str, TutoringState] = {}
workflows: Dict[str, TutoringWorkflow] = {}

# Initialize components
try:
    llm = TutoringLLM()
    progress_tracker = ProgressTracker("student_progress.json")
except Exception as e:
    print(f"Warning: Could not initialize LLM: {e}")
    llm = None
    progress_tracker = None

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SessionRequest(BaseModel):
    student_id: str
    topic: str
    understanding_level: str = "beginner"

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class SessionResponse(BaseModel):
    session_id: str
    message: str
    question: Optional[str] = None
    state: Optional[Dict] = None

class ProgressResponse(BaseModel):
    student_id: str
    summary: str
    progress_data: Dict

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def read_root():
    """Serve the frontend HTML file"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "AI Tutoring Assistant API", "status": "running", "frontend": "Navigate to /api/health to check API status"}

@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(request: SessionRequest):
    """Start a new tutoring session"""
    if not llm or not progress_tracker:
        raise HTTPException(status_code=500, detail="LLM not initialized. Check API key.")
    
    try:
        # Create workflow for this session
        workflow = TutoringWorkflow(llm, progress_tracker)
        
        # Create initial state
        state = workflow.create_initial_state(
            student_id=request.student_id,
            topic=request.topic,
            understanding_level=request.understanding_level
        )
        
        # Initialize session
        state = workflow.initialize_session(state)
        
        # Generate first question
        state = workflow.generate_question(state)
        
        # Store session
        session_id = f"{request.student_id}_{state['current_topic']}_{len(active_sessions)}"
        active_sessions[session_id] = state
        workflows[session_id] = workflow
        
        return SessionResponse(
            session_id=session_id,
            message="Session started successfully",
            question=state.get("current_question", ""),
            state={
                "topic": state["current_topic"],
                "understanding_level": state["understanding_level"],
                "questions_asked": state["questions_asked"],
                "correct_answers": state["correct_answers"],
                "session_active": state["session_active"]
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

@app.post("/api/session/answer", response_model=SessionResponse)
async def submit_answer(request: AnswerRequest):
    """Submit an answer and get feedback"""
    if not llm or not progress_tracker:
        raise HTTPException(status_code=500, detail="LLM not initialized. Check API key.")
    
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        state = active_sessions[request.session_id]
        workflow = workflows[request.session_id]
        
        if not state["session_active"]:
            raise HTTPException(status_code=400, detail="Session is no longer active")
        
        # Update state with answer
        state["student_answer"] = request.answer
        state["conversation_history"].append({
            "role": "user",
            "content": request.answer
        })
        
        # Clear previous evaluation
        state["answer_evaluation"] = {}
        
        # Run workflow steps
        state = workflow.evaluate_answer(state)
        state = workflow.update_progress(state)
        state = workflow.decide_next_action(state)
        
        # Handle explanation if needed
        if state["next_action"] == "provide_explanation":
            state = workflow.provide_explanation(state)
            state = workflow.decide_next_action(state)
        
        # Generate next question if needed
        next_question = None
        if state["session_active"] and state["next_action"] in ["ask_question", "follow_up"]:
            state = workflow.generate_question(state)
            next_question = state.get("current_question", "")
            state["student_answer"] = ""  # Clear for next iteration
            state["current_question"] = ""  # Will be set by generate_question
        
        # Update stored state
        active_sessions[request.session_id] = state
        
        # Prepare response
        evaluation = state.get("answer_evaluation", {})
        feedback = evaluation.get("feedback", "")
        is_correct = evaluation.get("correct", False)
        score = evaluation.get("score", 0.0)
        
        # Get explanation if provided
        explanation = None
        if state.get("explanation_provided"):
            # Find explanation in conversation history
            for msg in reversed(state["conversation_history"]):
                if msg["role"] == "assistant" and "Explanation:" in msg["content"]:
                    explanation = msg["content"].replace("Explanation: ", "")
                    break
        
        return SessionResponse(
            session_id=request.session_id,
            message=feedback,
            question=next_question,
            state={
                "topic": state["current_topic"],
                "understanding_level": state["understanding_level"],
                "questions_asked": state["questions_asked"],
                "correct_answers": state["correct_answers"],
                "session_active": state["session_active"],
                "is_correct": is_correct,
                "score": score,
                "explanation": explanation,
                "accuracy": (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")

@app.get("/api/session/{session_id}/progress")
async def get_session_progress(session_id: str):
    """Get current session progress"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    accuracy = (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
    
    return {
        "session_id": session_id,
        "topic": state["current_topic"],
        "understanding_level": state["understanding_level"],
        "questions_asked": state["questions_asked"],
        "correct_answers": state["correct_answers"],
        "accuracy": accuracy,
        "session_active": state["session_active"]
    }

@app.get("/api/progress/{student_id}", response_model=ProgressResponse)
async def get_student_progress(student_id: str):
    """Get overall progress for a student"""
    if not progress_tracker:
        raise HTTPException(status_code=500, detail="Progress tracker not initialized")
    
    try:
        summary = progress_tracker.get_progress_summary(student_id)
        progress_data = progress_tracker.get_student_progress(student_id)
        
        return ProgressResponse(
            student_id=student_id,
            summary=summary,
            progress_data=progress_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting progress: {str(e)}")

@app.post("/api/session/{session_id}/end")
async def end_session(session_id: str):
    """End a tutoring session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    workflow = workflows[session_id]
    
    # Update progress one final time
    if progress_tracker:
        progress_tracker.update_progress(state)
    
    # Mark session as inactive
    state["session_active"] = False
    
    # Calculate final stats
    accuracy = (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
    
    return {
        "session_id": session_id,
        "message": "Session ended",
        "summary": {
            "topic": state["current_topic"],
            "questions_asked": state["questions_asked"],
            "correct_answers": state["correct_answers"],
            "accuracy": accuracy,
            "final_understanding_level": state["understanding_level"]
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_initialized": llm is not None,
        "progress_tracker_initialized": progress_tracker is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

