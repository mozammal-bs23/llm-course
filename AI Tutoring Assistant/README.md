# AI Tutoring Assistant

An interactive AI-powered tutoring system that combines **LangGraph** and **LangChain** to provide personalized learning experiences through adaptive questioning, topic explanations, and progress tracking.

## Overview

The AI Tutoring Assistant is an intelligent tutoring system that:
- Engages students through interactive questions
- Adapts to individual student needs and understanding levels
- Provides clear, contextual explanations
- Tracks and maintains student progress over time
- Demonstrates integration of LangGraph workflows with LangChain components

## Features

### 1. Interactive Questioning
- Generates questions based on topic and student understanding level
- Creates adaptive follow-up questions based on student responses
- Supports multiple question types (conceptual, application, problem-solving)

### 2. Topic Explanation
- Provides clear, contextual explanations
- Adjusts explanation depth based on student understanding level
- Uses examples and analogies to enhance comprehension

### 3. Progress Tracking
- Tracks student performance across sessions
- Maintains history of topics covered
- Records question accuracy and response patterns
- Identifies areas of strength and weakness
- Generates progress summaries
- Persists data in JSON format

## Technology Stack

- **LangGraph**: For building stateful, multi-step tutoring workflows
  - State management using TypedDict
  - Workflow orchestration with nodes and edges
  - Conditional routing based on student responses

- **LangChain**: For LLM interactions and tooling
  - Chat models for conversation
  - Prompt templates for questions and explanations
  - Output parsers for structured responses

- **OpenAI**: GPT-3.5-turbo for question generation, answer evaluation, and explanations

## Installation

1. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

Run the tutoring assistant:

```bash
python ai_tutoring_assistant.py
```

The system will prompt you for:
- Student ID (defaults to "student_001" if not provided)
- Topic you want to learn about
- Your current understanding level (beginner/intermediate/advanced)

### Example Session

```
🤖 AI TUTORING ASSISTANT
============================================================
Enter your student ID: student_001
What topic would you like to learn about? Python programming
Your understanding level: beginner

📚 Starting tutoring session for student: student_001
📖 Topic: Python programming
🎯 Understanding Level: beginner

🤔 Generating question...
❓ Question: What is a variable in Python and how do you assign a value to it?

Your answer: A variable is a container that stores data, and you assign values using the = operator

📝 Evaluating answer...
✅ Correct! Score: 0.95
💬 Feedback: Excellent! You correctly identified that variables store data and use the = operator for assignment.

💾 Updating progress...
🤔 Deciding next action...

[Continues with more questions...]
```

## Architecture

### State Management
The system uses a `TutoringState` TypedDict to track:
- Student information and current topic
- Conversation history
- Current question and student answer
- Answer evaluation results
- Progress metrics (questions asked, correct answers)
- Understanding level and next action

### Workflow Nodes

1. **Initialize Session**: Sets up student session and loads previous progress
2. **Generate Question**: Creates questions appropriate for student level
3. **Evaluate Answer**: Assesses student responses and provides feedback
4. **Provide Explanation**: Generates contextual explanations when needed
5. **Update Progress**: Saves progress and adjusts understanding level
6. **Decide Next Action**: Determines whether to ask another question, provide explanation, or end session

### Conditional Routing

The workflow uses conditional edges to route based on:
- Student performance (accuracy, number of questions)
- Answer correctness
- Understanding level progression
- Session completion criteria

## Progress Tracking

Student progress is saved to `student_progress.json` with the following structure:

```json
{
  "student_001": {
    "sessions": [
      {
        "timestamp": "2024-01-15T10:30:00",
        "topic": "Python programming",
        "questions_asked": 5,
        "correct_answers": 4,
        "accuracy": 80.0
      }
    ],
    "topics_covered": ["Python programming"],
    "total_questions": 5,
    "total_correct": 4,
    "understanding_levels": {
      "Python programming": "intermediate"
    }
  }
}
```

## Key Workflows

1. **Initialization Flow**: Set up student session, select topic
2. **Question-Answer Flow**: Generate question → Evaluate answer → Provide feedback
3. **Explanation Flow**: Trigger explanation → Adjust depth → Confirm understanding
4. **Progress Update Flow**: Update metrics → Save progress → Determine next steps

## Success Criteria

✅ Successfully integrates LangGraph for workflow management  
✅ Successfully integrates LangChain for LLM interactions  
✅ System asks relevant follow-up questions based on student responses  
✅ System provides clear, helpful explanations  
✅ Progress tracking persists across sessions  
✅ Demonstrates branching logic (conditional routing) in LangGraph  
✅ Code is well-structured and maintainable  

## Project Structure

```
Class 6 - AI Tutoring Assistant/
├── ai_tutoring_assistant.py  # Main application
├── requirements.txt          # Dependencies
├── README.md                  # This file
└── student_progress.json     # Progress data (created at runtime)
```

## Future Enhancements (Out of Scope for MVP)

- Multi-student management interface
- Advanced analytics dashboard
- Integration with external learning management systems
- Voice interaction
- Multi-language support
- Knowledge base integration for more accurate answer evaluation

## License

This project is part of an LLM course curriculum.

