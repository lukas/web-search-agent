# Web Search Agent

A conversational AI agent that can answer questions using real-time web search. The agent searches the web for current information and provides comprehensive, well-sourced answers.

## Features

- 🔍 **Real-time web search** using DuckDuckGo API (no API key required)
- 💬 **Interactive chat interface** with conversation history tracking
- ⚡ **Fast responses** - all operations complete under 3 seconds
- 🛡️ **Error handling** for network issues and API failures
- 📝 **Source attribution** with links to original content
- ✅ **Well-tested** with comprehensive unit and integration tests

## Setup

1. Clone the repository:
```bash
git clone https://github.com/lukas/web-search-agent.git
cd web-search-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Chat
Run the agent for an interactive conversation:
```bash
python web_search_agent.py
```

The agent will start a chat session where you can ask any questions:
```
🔍 Web Search Agent initialized!
Ask me any question and I'll search the web to find you accurate, up-to-date information.
Type 'quit' or 'exit' to stop.

You: What is machine learning?
🔍 Searching...
Agent: Based on my web search for 'What is machine learning?', here's what I found:

1. Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalise to unseen data, and thus perform tasks without explicit instructions...
   (Source: https://en.wikipedia.org/wiki/Machine_learning)
```

### Programmatic Usage
You can also use the agent programmatically:
```python
from web_search_agent import WebSearchAgent

agent = WebSearchAgent()
response = agent.process_question("What is Python programming?")
print(response)
```

### Testing
Run the test suite to verify functionality:
```bash
pytest test_web_search_agent.py -v --timeout=3
```

All tests are designed to complete under 3 seconds, including integration tests with real API calls.

## Architecture

The agent consists of:

- **WebSearchAgent**: Main class that orchestrates search and response generation
- **search_web()**: Interfaces with DuckDuckGo API for web search
- **process_question()**: Handles user questions and maintains conversation history
- **generate_response()**: Formats search results into coherent answers
- **chat_loop()**: Provides interactive command-line interface

## Testing

The project includes comprehensive tests:

- **Unit tests**: Mock external dependencies for fast, reliable testing
- **Integration tests**: Real API calls with timeout constraints
- **Performance tests**: All tests complete under 3 seconds
- **Error handling tests**: Verify graceful handling of network issues

Run tests with:
```bash
pytest test_web_search_agent.py -v
```

## Dependencies

- `requests`: HTTP library for API calls
- `pytest`: Testing framework
- `pytest-timeout`: Ensures tests complete quickly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass under 3 seconds
5. Submit a pull request

## License

MIT License - see LICENSE file for details.