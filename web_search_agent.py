import asyncio
import requests
import json
from typing import List, Dict


class WebSearchAgent:
    def __init__(self):
        self.conversation_history = []
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo's instant answer API
        """
        try:
            # Using DuckDuckGo instant answer API (no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('AbstractText', 'Summary'),
                    'content': data['Abstract'],
                    'source': data.get('AbstractURL', '')
                })
            
            # Get related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '')[:100] + '...' if len(topic.get('Text', '')) > 100 else topic.get('Text', ''),
                        'content': topic.get('Text', ''),
                        'source': topic.get('FirstURL', '')
                    })
            
            # If no results, try a different approach with web scraping
            if not results:
                results.append({
                    'title': 'Search Result',
                    'content': f'I searched for "{query}" but could not find specific results. Let me provide what I know about this topic.',
                    'source': 'General knowledge'
                })
            
            return results
            
        except Exception as e:
            return [{
                'title': 'Search Error',
                'content': f'I encountered an error while searching: {str(e)}. Let me provide what I know about "{query}".',
                'source': 'Error'
            }]
    
    def process_question(self, question: str) -> str:
        """
        Process a user question by searching the web and generating an answer
        """
        # Search the web for information
        search_results = self.search_web(question)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Generate response based on search results
        if search_results and not search_results[0]['content'].startswith('I searched for'):
            response = self.generate_response(question, search_results)
        else:
            response = f"I searched for information about '{question}' but could not find specific current results. This could be due to the search API limitations or the specific nature of your question."
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def generate_response(self, question: str, search_results: List[Dict[str, str]]) -> str:
        """
        Generate a response based on search results
        """
        response_parts = []
        
        response_parts.append(f"Based on my web search for '{question}', here's what I found:\n")
        
        for i, result in enumerate(search_results[:3], 1):  # Use top 3 results
            if result['content'] and not result['content'].startswith('I searched for'):
                response_parts.append(f"{i}. {result['content']}")
                if result['source']:
                    response_parts.append(f"   (Source: {result['source']})")
                response_parts.append("")
        
        if len(response_parts) == 1:  # Only the intro was added
            response_parts.append("Unfortunately, I could not find detailed information about this topic from the web search.")
        
        return "\n".join(response_parts)
    
    def chat_loop(self):
        """
        Main chat loop for interactive conversation
        """
        print("🔍 Web Search Agent initialized!")
        print("Ask me any question and I'll search the web to find you accurate, up-to-date information.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye! 👋")
                    break
                
                if not user_input:
                    continue
                
                print("🔍 Searching...")
                response = self.process_question(user_input)
                print(f"\nAgent: {response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {str(e)}")


def main():
    agent = WebSearchAgent()
    agent.chat_loop()


if __name__ == "__main__":
    main()