#!/usr/bin/env python3

from web_search_agent import WebSearchAgent

def test_agent():
    agent = WebSearchAgent()
    
    # Test questions
    test_questions = [
        "What is Python?",
        "What is machine learning?",
        "Current events in technology"
    ]
    
    print("🔍 Testing Web Search Agent\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"Test {i}: {question}")
        print("🔍 Searching...")
        response = agent.process_question(question)
        print(f"Response: {response}\n")
        print("-" * 50)

if __name__ == "__main__":
    test_agent()