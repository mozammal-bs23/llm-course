#!/usr/bin/env python3
"""
AI Tutoring Assistant
An interactive AI-powered tutoring system using LangGraph and LangChain
"""

import os
import json
from pathlib import Path
from typing import TypedDict, List, Dict, Optional, Literal
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from openai import RateLimitError, APIError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("💡 Tip: Install python-dotenv to use .env files: pip install python-dotenv")

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class TutoringState(TypedDict):
    """State management for the tutoring workflow"""
    student_id: str
    current_topic: str
    conversation_history: List[Dict[str, str]]  # List of {"role": "user/assistant", "content": "..."}
    current_question: str
    student_answer: str
    answer_evaluation: Dict[str, any]  # {"correct": bool, "feedback": str, "score": float}
    explanation_provided: bool
    questions_asked: int
    correct_answers: int
    topics_covered: List[str]
    understanding_level: str  # "beginner", "intermediate", "advanced"
    next_action: str  # "ask_question", "provide_explanation", "end_session", "follow_up"
    session_active: bool

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

class TutoringPrompts:
    """Prompt templates for different tutoring interactions"""
    
    @staticmethod
    def get_question_prompt(topic: str, understanding_level: str, previous_questions: List[str]) -> str:
        """Generate a question based on topic and student level"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\nPrevious questions asked: {', '.join(previous_questions[-3:])}"
        
        return f"""You are an expert tutor helping a student learn about {topic}.
The student's current understanding level is: {understanding_level}.

Generate a single, clear question that:
1. Is appropriate for the {understanding_level} level
2. Tests understanding of key concepts in {topic}
3. Is different from previous questions{previous_context}
4. Can be answered in 1-3 sentences

Format your response as just the question, nothing else."""

    @staticmethod
    def get_evaluation_prompt(question: str, correct_answer: str, student_answer: str, topic: str) -> str:
        """Evaluate student's answer"""
        return f"""You are a tutor evaluating a student's answer.

Topic: {topic}
Question: {question}
Expected answer (key concepts): {correct_answer}
Student's answer: {student_answer}

Evaluate the student's answer and provide:
1. A score from 0.0 to 1.0 (where 1.0 is fully correct)
2. Brief feedback (1-2 sentences) explaining what was correct or incorrect
3. Whether the answer demonstrates understanding (correct: true/false)

Respond in JSON format:
{{
    "score": 0.0-1.0,
    "correct": true/false,
    "feedback": "your feedback here"
}}"""

    @staticmethod
    def get_explanation_prompt(topic: str, understanding_level: str, question: str, student_answer: str) -> str:
        """Generate an explanation based on student's answer"""
        return f"""You are a tutor explaining a concept to a student.

Topic: {topic}
Student's understanding level: {understanding_level}
Question asked: {question}
Student's answer: {student_answer}

Provide a clear, engaging explanation that:
1. Addresses the question directly
2. Uses examples and analogies appropriate for {understanding_level} level
3. Builds on what the student already knows
4. Is 2-4 sentences long

Format your response as just the explanation, nothing else."""

    @staticmethod
    def get_follow_up_decision_prompt(
        topic: str, 
        questions_asked: int, 
        correct_answers: int,
        last_answer_correct: bool,
        understanding_level: str
    ) -> str:
        """Decide next action based on student progress"""
        accuracy = (correct_answers / questions_asked * 100) if questions_asked > 0 else 0
        
        return f"""As a tutor, decide the next action for this student:

Topic: {topic}
Questions asked: {questions_asked}
Correct answers: {correct_answers}
Accuracy: {accuracy:.1f}%
Last answer was correct: {last_answer_correct}
Understanding level: {understanding_level}

Decide the next action:
- "ask_question": Ask another question to continue learning
- "provide_explanation": Provide explanation if student struggled
- "follow_up": Ask a follow-up question on the same concept
- "end_session": End the session if student has mastered the topic

Respond with ONLY one of: ask_question, provide_explanation, follow_up, end_session"""

# ============================================================================
# LANGCHAIN COMPONENTS
# ============================================================================

class TutoringLLM:
    """LangChain components for LLM interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required! Set OPENAI_API_KEY environment variable.")
        
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=self.api_key
        )
        self.output_parser = StrOutputParser()
    
    def generate_question(self, topic: str, understanding_level: str, previous_questions: List[str]) -> str:
        """Generate a question using LLM"""
        prompt = TutoringPrompts.get_question_prompt(topic, understanding_level, previous_questions)
        
        chain = ChatPromptTemplate.from_template("{prompt}") | self.llm | self.output_parser
        
        try:
            question = chain.invoke({"prompt": prompt})
            return question.strip()
        except RateLimitError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                raise ValueError(
                    "❌ OpenAI API Quota Exceeded\n"
                    "Your OpenAI account has insufficient quota or credits.\n"
                    "Please:\n"
                    "1. Check your billing at https://platform.openai.com/account/billing\n"
                    "2. Add credits to your account\n"
                    "3. Verify your API key is valid and active\n\n"
                    f"Error details: {error_msg}"
                )
            else:
                raise ValueError(
                    f"❌ OpenAI API Rate Limit Error\n"
                    f"Please wait a moment and try again.\n"
                    f"Error: {error_msg}"
                )
        except APIError as e:
            raise ValueError(
                f"❌ OpenAI API Error\n"
                f"Please check your API key and account status.\n"
                f"Error: {str(e)}"
            )
        except Exception as e:
            raise ValueError(
                f"❌ Error generating question\n"
                f"Unexpected error: {str(e)}"
            )
    
    def evaluate_answer(self, question: str, correct_answer: str, student_answer: str, topic: str) -> Dict:
        """Evaluate student's answer"""
        prompt = TutoringPrompts.get_evaluation_prompt(question, correct_answer, student_answer, topic)
        
        chain = ChatPromptTemplate.from_template("{prompt}") | self.llm | self.output_parser
        
        try:
            response = chain.invoke({"prompt": prompt})
        except RateLimitError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                raise ValueError(
                    "❌ OpenAI API Quota Exceeded\n"
                    "Your OpenAI account has insufficient quota or credits.\n"
                    "Please check your billing at https://platform.openai.com/account/billing"
                )
            else:
                raise ValueError(f"❌ OpenAI API Rate Limit Error: {error_msg}")
        except APIError as e:
            raise ValueError(f"❌ OpenAI API Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"❌ Error evaluating answer: {str(e)}")
        
        # Parse JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                # Fallback parsing
                evaluation = {
                    "score": 0.5,
                    "correct": "correct" in response.lower() or "right" in response.lower(),
                    "feedback": response
                }
        except:
            # Fallback if JSON parsing fails
            evaluation = {
                "score": 0.5,
                "correct": "correct" in response.lower() or "right" in response.lower(),
                "feedback": response
            }
        
        # Ensure correct types
        evaluation["score"] = float(evaluation.get("score", 0.5))
        evaluation["correct"] = bool(evaluation.get("correct", False))
        
        return evaluation
    
    def generate_explanation(self, topic: str, understanding_level: str, question: str, student_answer: str) -> str:
        """Generate explanation using LLM"""
        prompt = TutoringPrompts.get_explanation_prompt(topic, understanding_level, question, student_answer)
        
        chain = ChatPromptTemplate.from_template("{prompt}") | self.llm | self.output_parser
        
        try:
            explanation = chain.invoke({"prompt": prompt})
            return explanation.strip()
        except RateLimitError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                raise ValueError(
                    "❌ OpenAI API Quota Exceeded\n"
                    "Your OpenAI account has insufficient quota or credits.\n"
                    "Please check your billing at https://platform.openai.com/account/billing"
                )
            else:
                raise ValueError(f"❌ OpenAI API Rate Limit Error: {error_msg}")
        except APIError as e:
            raise ValueError(f"❌ OpenAI API Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"❌ Error generating explanation: {str(e)}")
    
    def decide_next_action(
        self, 
        topic: str, 
        questions_asked: int, 
        correct_answers: int,
        last_answer_correct: bool,
        understanding_level: str
    ) -> str:
        """Decide next action using LLM"""
        prompt = TutoringPrompts.get_follow_up_decision_prompt(
            topic, questions_asked, correct_answers, last_answer_correct, understanding_level
        )
        
        chain = ChatPromptTemplate.from_template("{prompt}") | self.llm | self.output_parser
        
        try:
            action = chain.invoke({"prompt": prompt}).strip().lower()
        except RateLimitError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                raise ValueError(
                    "❌ OpenAI API Quota Exceeded\n"
                    "Your OpenAI account has insufficient quota or credits.\n"
                    "Please check your billing at https://platform.openai.com/account/billing"
                )
            else:
                raise ValueError(f"❌ OpenAI API Rate Limit Error: {error_msg}")
        except APIError as e:
            raise ValueError(f"❌ OpenAI API Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"❌ Error deciding next action: {str(e)}")
        
        # Normalize action
        valid_actions = ["ask_question", "provide_explanation", "follow_up", "end_session"]
        for valid_action in valid_actions:
            if valid_action in action:
                return valid_action
        
        # Default decision based on accuracy
        accuracy = (correct_answers / questions_asked * 100) if questions_asked > 0 else 0
        if accuracy >= 80 and questions_asked >= 3:
            return "end_session"
        elif not last_answer_correct:
            return "provide_explanation"
        else:
            return "ask_question"

# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Track and persist student progress"""
    
    def __init__(self, progress_file: str = "student_progress.json"):
        self.progress_file = Path(progress_file)
        self.progress_data = self.load_progress()
    
    def load_progress(self) -> Dict:
        """Load progress from JSON file"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_progress(self):
        """Save progress to JSON file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress_data, f, indent=2)
    
    def get_student_progress(self, student_id: str) -> Dict:
        """Get progress for a specific student"""
        if student_id not in self.progress_data:
            self.progress_data[student_id] = {
                "sessions": [],
                "topics_covered": [],
                "total_questions": 0,
                "total_correct": 0,
                "understanding_levels": {}
            }
        return self.progress_data[student_id]
    
    def update_progress(self, state: TutoringState):
        """Update progress from current state"""
        student_id = state["student_id"]
        student_progress = self.get_student_progress(student_id)
        
        # Update session data
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "topic": state["current_topic"],
            "questions_asked": state["questions_asked"],
            "correct_answers": state["correct_answers"],
            "accuracy": (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
        }
        student_progress["sessions"].append(session_data)
        
        # Update topics covered
        for topic in state["topics_covered"]:
            if topic not in student_progress["topics_covered"]:
                student_progress["topics_covered"].append(topic)
        
        # Update totals
        student_progress["total_questions"] += state["questions_asked"]
        student_progress["total_correct"] += state["correct_answers"]
        
        # Update understanding level for topic
        student_progress["understanding_levels"][state["current_topic"]] = state["understanding_level"]
        
        self.save_progress()
    
    def get_progress_summary(self, student_id: str) -> str:
        """Get a summary of student progress"""
        student_progress = self.get_student_progress(student_id)
        
        if not student_progress["sessions"]:
            return "No previous sessions found."
        
        total_sessions = len(student_progress["sessions"])
        total_questions = student_progress["total_questions"]
        total_correct = student_progress["total_correct"]
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        summary = f"""
Progress Summary for Student: {student_id}
========================================
Total Sessions: {total_sessions}
Total Questions: {total_questions}
Correct Answers: {total_correct}
Overall Accuracy: {overall_accuracy:.1f}%
Topics Covered: {', '.join(student_progress['topics_covered']) if student_progress['topics_covered'] else 'None'}
"""
        return summary

# ============================================================================
# LANGGRAPH WORKFLOW NODES
# ============================================================================

class TutoringWorkflow:
    """LangGraph workflow for tutoring interactions"""
    
    def __init__(self, llm_component: TutoringLLM, progress_tracker: ProgressTracker):
        self.llm = llm_component
        self.progress = progress_tracker
        self.graph = self._build_graph()
    
    def initialize_session(self, state: TutoringState) -> TutoringState:
        """Initialize a new tutoring session"""
        print(f"\n📚 Starting tutoring session for student: {state['student_id']}")
        print(f"📖 Topic: {state['current_topic']}")
        print(f"🎯 Understanding Level: {state['understanding_level']}")
        
        # Load previous progress
        student_progress = self.progress.get_student_progress(state["student_id"])
        
        # Update understanding level if we have history
        if state["current_topic"] in student_progress.get("understanding_levels", {}):
            state["understanding_level"] = student_progress["understanding_levels"][state["current_topic"]]
        
        # Add topic to covered topics
        if state["current_topic"] not in state["topics_covered"]:
            state["topics_covered"].append(state["current_topic"])
        
        state["session_active"] = True
        state["next_action"] = "ask_question"
        
        return state
    
    def generate_question(self, state: TutoringState) -> TutoringState:
        """Generate a question for the student"""
        print("\n🤔 Generating question...")
        
        # Get previous questions from conversation history
        previous_questions = [
            msg["content"] for msg in state["conversation_history"] 
            if msg["role"] == "assistant" and "?" in msg["content"]
        ]
        
        question = self.llm.generate_question(
            state["current_topic"],
            state["understanding_level"],
            previous_questions
        )
        
        state["current_question"] = question
        state["conversation_history"].append({
            "role": "assistant",
            "content": question
        })
        
        print(f"❓ Question: {question}")
        
        return state
    
    def evaluate_answer(self, state: TutoringState) -> TutoringState:
        """Evaluate the student's answer"""
        print("\n📝 Evaluating answer...")
        
        # For simplicity, we'll use the question as the "correct answer" reference
        # In a real system, you'd have a knowledge base with correct answers
        correct_answer = f"Key concepts related to {state['current_topic']}"
        
        evaluation = self.llm.evaluate_answer(
            state["current_question"],
            correct_answer,
            state["student_answer"],
            state["current_topic"]
        )
        
        state["answer_evaluation"] = evaluation
        state["questions_asked"] += 1
        
        if evaluation["correct"]:
            state["correct_answers"] += 1
            print(f"✅ Correct! Score: {evaluation['score']:.2f}")
        else:
            print(f"❌ Incorrect. Score: {evaluation['score']:.2f}")
        
        print(f"💬 Feedback: {evaluation['feedback']}")
        
        # Add feedback to conversation
        state["conversation_history"].append({
            "role": "assistant",
            "content": evaluation["feedback"]
        })
        
        return state
    
    def provide_explanation(self, state: TutoringState) -> TutoringState:
        """Provide explanation of the concept"""
        print("\n📚 Generating explanation...")
        
        explanation = self.llm.generate_explanation(
            state["current_topic"],
            state["understanding_level"],
            state["current_question"],
            state["student_answer"]
        )
        
        state["explanation_provided"] = True
        state["conversation_history"].append({
            "role": "assistant",
            "content": f"Explanation: {explanation}"
        })
        
        print(f"💡 {explanation}")
        
        return state
    
    def update_progress(self, state: TutoringState) -> TutoringState:
        """Update and save student progress"""
        print("\n💾 Updating progress...")
        
        self.progress.update_progress(state)
        
        # Update understanding level based on performance
        accuracy = (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
        
        if accuracy >= 80 and state["questions_asked"] >= 3:
            if state["understanding_level"] == "beginner":
                state["understanding_level"] = "intermediate"
            elif state["understanding_level"] == "intermediate":
                state["understanding_level"] = "advanced"
        elif accuracy < 50:
            if state["understanding_level"] == "advanced":
                state["understanding_level"] = "intermediate"
            elif state["understanding_level"] == "intermediate":
                state["understanding_level"] = "beginner"
        
        return state
    
    def decide_next_action(self, state: TutoringState) -> TutoringState:
        """Decide the next action based on student progress"""
        print("\n🤔 Deciding next action...")
        
        last_correct = state["answer_evaluation"].get("correct", False) if state.get("answer_evaluation") else True
        
        next_action = self.llm.decide_next_action(
            state["current_topic"],
            state["questions_asked"],
            state["correct_answers"],
            last_correct,
            state["understanding_level"]
        )
        
        state["next_action"] = next_action
        
        # End session if decided
        if next_action == "end_session":
            state["session_active"] = False
            print("\n🎉 Session complete! Great job!")
        
        return state
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(TutoringState)
        
        # Add nodes
        workflow.add_node("initialize", self.initialize_session)
        workflow.add_node("generate_question", self.generate_question)
        workflow.add_node("evaluate_answer", self.evaluate_answer)
        workflow.add_node("provide_explanation", self.provide_explanation)
        workflow.add_node("update_progress", self.update_progress)
        workflow.add_node("decide_action", self.decide_next_action)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Define flow
        workflow.add_edge("initialize", "generate_question")
        workflow.add_edge("generate_question", "evaluate_answer")
        workflow.add_edge("evaluate_answer", "update_progress")
        workflow.add_edge("update_progress", "decide_action")
        
        # Conditional routing based on next_action
        def route_after_decision(state: TutoringState) -> str:
            if not state["session_active"]:
                return "end"
            elif state["next_action"] == "provide_explanation":
                return "provide_explanation"
            elif state["next_action"] == "follow_up":
                return "generate_question"
            elif state["next_action"] == "ask_question":
                return "generate_question"
            else:
                return "end"
        
        workflow.add_conditional_edges(
            "decide_action",
            route_after_decision,
            {
                "provide_explanation": "provide_explanation",
                "generate_question": "generate_question",
                "end": END
            }
        )
        
        workflow.add_edge("provide_explanation", "decide_action")
        
        return workflow.compile()
    
    def create_initial_state(self, student_id: str, topic: str, understanding_level: str = "beginner") -> TutoringState:
        """Create initial state for a tutoring session"""
        return {
            "student_id": student_id,
            "current_topic": topic,
            "conversation_history": [],
            "current_question": "",
            "student_answer": "",
            "answer_evaluation": {},
            "explanation_provided": False,
            "questions_asked": 0,
            "correct_answers": 0,
            "topics_covered": [],
            "understanding_level": understanding_level,
            "next_action": "ask_question",
            "session_active": True
        }
    
    def run_workflow_step(self, state: TutoringState) -> TutoringState:
        """Run one step of the workflow from current state"""
        # Determine current node based on state
        if state["next_action"] == "ask_question" and not state.get("current_question"):
            # Start with question generation
            state = self.generate_question(state)
            return state
        elif state.get("student_answer") and not state.get("answer_evaluation"):
            # Evaluate answer
            state = self.evaluate_answer(state)
            state = self.update_progress(state)
            state = self.decide_next_action(state)
            return state
        elif state["next_action"] == "provide_explanation":
            state = self.provide_explanation(state)
            state = self.decide_next_action(state)
            return state
        else:
            # Default: generate question
            state = self.generate_question(state)
            return state

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    print("=" * 60)
    print("🤖 AI TUTORING ASSISTANT")
    print("=" * 60)
    print("An interactive AI-powered tutoring system")
    print("Using LangGraph for workflows and LangChain for LLM interactions\n")
    
    try:
        # Initialize components
        llm = TutoringLLM()
        progress_tracker = ProgressTracker("student_progress.json")
        workflow = TutoringWorkflow(llm, progress_tracker)
        
        # Get student information
        student_id = input("Enter your student ID (or press Enter for 'student_001'): ").strip() or "student_001"
        topic = input("What topic would you like to learn about? ").strip()
        
        if not topic:
            print("❌ Topic is required!")
            return
        
        understanding_level = input("Your understanding level (beginner/intermediate/advanced, default: beginner): ").strip().lower()
        if understanding_level not in ["beginner", "intermediate", "advanced"]:
            understanding_level = "beginner"
        
        # Show progress summary if available
        summary = progress_tracker.get_progress_summary(student_id)
        if "No previous sessions" not in summary:
            print(summary)
        
        print("\n" + "=" * 60)
        print("Starting tutoring session...")
        print("=" * 60)
        
        # Create initial state
        state = workflow.create_initial_state(student_id, topic, understanding_level)
        
        # Initialize session
        state = workflow.initialize_session(state)
        
        # Interactive loop
        while state["session_active"]:
            # Generate question if needed
            if not state.get("current_question") or state["next_action"] in ["ask_question", "follow_up"]:
                state = workflow.generate_question(state)
            
            # Get student answer
            print("\n" + "-" * 60)
            student_answer = input("Your answer (or 'quit' to end): ").strip()
            
            if not student_answer:
                print("Please provide an answer!")
                continue
            
            if student_answer.lower() in ["quit", "exit", "end"]:
                state["session_active"] = False
                break
            
            # Update state with answer
            state["student_answer"] = student_answer
            state["conversation_history"].append({
                "role": "user",
                "content": student_answer
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
            
            # Clear student answer for next iteration
            state["student_answer"] = ""
            state["current_question"] = ""  # Will generate new question next iteration
        
        # Final progress update
        progress_tracker.update_progress(state)
        
        # Show final summary
        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Topic: {state['current_topic']}")
        print(f"Questions Asked: {state['questions_asked']}")
        print(f"Correct Answers: {state['correct_answers']}")
        accuracy = (state["correct_answers"] / state["questions_asked"] * 100) if state["questions_asked"] > 0 else 0
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"Final Understanding Level: {state['understanding_level']}")
        print("=" * 60)
        
    except ValueError as e:
        # Handle API quota/rate limit errors with user-friendly messages
        print(f"\n{e}")
        print("\n💡 Troubleshooting Tips:")
        print("1. Verify your OpenAI API key is set: echo $OPENAI_API_KEY")
        print("2. Check your OpenAI account billing: https://platform.openai.com/account/billing")
        print("3. Ensure you have sufficient credits/quota in your account")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

