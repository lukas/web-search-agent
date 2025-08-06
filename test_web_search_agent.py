import pytest
from unittest.mock import Mock, patch
from web_search_agent import WebSearchAgent


class TestWebSearchAgent:
    """Test suite for WebSearchAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WebSearchAgent()
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly"""
        assert self.agent.conversation_history == []
    
    @patch('web_search_agent.requests.get')
    def test_search_web_success(self, mock_get):
        """Test successful web search"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'Abstract': 'Python is a programming language',
            'AbstractText': 'Python Programming',
            'AbstractURL': 'https://python.org',
            'RelatedTopics': [
                {'Text': 'Python is easy to learn', 'FirstURL': 'https://example.com'}
            ]
        }
        mock_get.return_value = mock_response
        
        results = self.agent.search_web("What is Python?")
        
        assert len(results) >= 1
        assert results[0]['content'] == 'Python is a programming language'
        assert results[0]['source'] == 'https://python.org'
    
    @patch('web_search_agent.requests.get')
    def test_search_web_error_handling(self, mock_get):
        """Test web search error handling"""
        # Mock API error
        mock_get.side_effect = Exception("Network error")
        
        results = self.agent.search_web("test query")
        
        assert len(results) == 1
        assert 'error' in results[0]['content'].lower()
    
    @patch('web_search_agent.requests.get')
    def test_process_question(self, mock_get):
        """Test question processing with mocked search"""
        # Mock successful search response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'Abstract': 'Machine learning is a subset of AI',
            'AbstractText': 'ML Overview',
            'AbstractURL': 'https://ml.org'
        }
        mock_get.return_value = mock_response
        
        question = "What is machine learning?"
        response = self.agent.process_question(question)
        
        # Check conversation history is updated
        assert len(self.agent.conversation_history) == 2
        assert self.agent.conversation_history[0]['role'] == 'user'
        assert self.agent.conversation_history[0]['content'] == question
        assert self.agent.conversation_history[1]['role'] == 'assistant'
        
        # Check response contains search results
        assert 'machine learning' in response.lower()
    
    def test_generate_response(self):
        """Test response generation from search results"""
        search_results = [
            {
                'title': 'Test Result',
                'content': 'This is a test result',
                'source': 'https://test.com'
            }
        ]
        
        response = self.agent.generate_response("test question", search_results)
        
        assert "Based on my web search for 'test question'" in response
        assert "This is a test result" in response
        assert "https://test.com" in response
    
    def test_generate_response_empty_results(self):
        """Test response generation with empty results"""
        response = self.agent.generate_response("test", [])
        
        assert "Unfortunately, I couldn't find detailed information" in response
    
    @patch('web_search_agent.requests.get')
    def test_conversation_history_tracking(self, mock_get):
        """Test that conversation history is properly tracked"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'Abstract': 'Test response'}
        mock_get.return_value = mock_response
        
        # Ask multiple questions
        self.agent.process_question("Question 1")
        self.agent.process_question("Question 2")
        
        # Should have 4 entries: user1, assistant1, user2, assistant2
        assert len(self.agent.conversation_history) == 4
        assert self.agent.conversation_history[0]['content'] == "Question 1"
        assert self.agent.conversation_history[2]['content'] == "Question 2"


# Integration tests with actual API calls (fast, limited scope)
class TestWebSearchAgentIntegration:
    """Integration tests with real API calls"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WebSearchAgent()
    
    @pytest.mark.timeout(3)
    def test_real_search_python(self):
        """Test real search for Python - should complete under 3 seconds"""
        results = self.agent.search_web("Python programming language")
        
        # Should get some results
        assert len(results) >= 1
        
        # Results should have expected structure
        for result in results:
            assert 'title' in result
            assert 'content' in result
            assert 'source' in result
    
    @pytest.mark.timeout(3) 
    def test_real_process_question(self):
        """Test real question processing - should complete under 3 seconds"""
        response = self.agent.process_question("What is Git?")
        
        # Should get a response
        assert len(response) > 0
        assert isinstance(response, str)
        
        # History should be updated
        assert len(self.agent.conversation_history) == 2