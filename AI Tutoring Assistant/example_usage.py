#!/usr/bin/env python3
"""
Example usage of the AI Tutoring Assistant
This demonstrates how to programmatically use the tutoring system
"""

from ai_tutoring_assistant import TutoringLLM, ProgressTracker, TutoringWorkflow

def example_programmatic_usage():
    """Example of using the tutoring system programmatically"""
    
    print("=" * 60)
    print("Example: Programmatic Usage of AI Tutoring Assistant")
    print("=" * 60)
    
    # Initialize components
    llm = TutoringLLM()
    progress_tracker = ProgressTracker("example_progress.json")
    workflow = TutoringWorkflow(llm, progress_tracker)
    
    # Create initial state
    state = workflow.create_initial_state(
        student_id="example_student",
        topic="Machine Learning",
        understanding_level="beginner"
    )
    
    # Initialize session
    state = workflow.initialize_session(state)
    
    # Simulate a tutoring session with predefined answers
    example_answers = [
        "Machine learning is a subset of AI that enables computers to learn from data without explicit programming.",
        "Supervised learning uses labeled data, unsupervised learning finds patterns in unlabeled data, and reinforcement learning learns through trial and error.",
        "Neural networks are computing systems inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information."
    ]
    
    question_count = 0
    max_questions = 3
    
    while state["session_active"] and question_count < max_questions:
        # Generate question
        if not state.get("current_question") or state["next_action"] in ["ask_question", "follow_up"]:
            state = workflow.generate_question(state)
            question_count += 1
        
        # Use example answer
        if question_count <= len(example_answers):
            student_answer = example_answers[question_count - 1]
            print(f"\n📝 Simulated Student Answer: {student_answer}")
        else:
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
        
        # Clear for next iteration
        state["student_answer"] = ""
        state["current_question"] = ""
    
    # Final progress update
    progress_tracker.update_progress(state)
    
    # Show summary
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
    
    # Show progress summary
    print("\n" + progress_tracker.get_progress_summary("example_student"))

if __name__ == "__main__":
    try:
        example_programmatic_usage()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure to set your GOOGLE_API_KEY environment variable")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")

