import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
from myfeed.agent import NewsAgent, NewsletterState


@pytest.fixture
def news_agent():
    """Create a NewsAgent instance for testing."""
    # Use a dummy API key for testing
    return NewsAgent(openai_api_key="test-api-key")


@pytest.fixture
def newsletter_state():
    """Create a NewsletterState with AI and ADME topics."""
    return NewsletterState(topics=["AI", "ADME"])


@pytest.fixture
def mock_scholar_html():
    """Mock HTML response from Google Scholar."""
    return """
    <div class="gs_r">
        <h3 class="gs_rt">
            <a href="https://example.com/paper1" id="paper1">
                Artificial Intelligence in Drug Discovery
            </a>
        </h3>
        <div class="gs_a">John Doe, Jane Smith - Nature, 2023</div>
        <div class="gs_rs">This paper discusses the application of AI in pharmaceutical research and drug discovery processes.</div>
        <div class="gs_fl">
            <span class="gs_nph"></span>
            <a href="/scholar?cites=123">Cited by 45</a>
            <a href="/scholar?cluster=456" style="margin-left:16px">Related articles</a>
            <a href="/scholar?versions=456" class="gs_nph">All 3 versions</a>
        </div>
    </div>
    <div class="gs_r">
        <h3 class="gs_rt">
            <a href="https://example.com/paper2" id="paper2">
                ADME Properties Prediction Using Machine Learning
            </a>
        </h3>
        <div class="gs_a">Alice Johnson, Bob Wilson - Journal of Medicinal Chemistry, 2023</div>
        <div class="gs_rs">Machine learning approaches for predicting absorption, distribution, metabolism, and excretion properties of compounds.</div>
        <div class="gs_fl">
            <span class="gs_nph"></span>
            <a href="/scholar?cites=789">Cited by 23</a>
            <a href="/scholar?cluster=101" style="margin-left:16px">Related articles</a>
            <a href="/scholar?versions=101" class="gs_nph">All 2 versions</a>
        </div>
    </div>
    """


def test_scrape_papers_success(news_agent, newsletter_state, mock_scholar_html):
    """Test successful paper scraping for AI and ADME topics."""
    
    with patch('requests.get') as mock_get:
        # Mock the requests.get response
        mock_response = Mock()
        mock_response.content = mock_scholar_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Call the _scrape_papers method
        result_state = news_agent._scrape_papers(newsletter_state)
        
        # Verify that requests.get was called for each topic
        assert mock_get.call_count == len(newsletter_state.topics)
        
        # Check that the URLs contain the expected search terms
        calls = mock_get.call_args_list
        ai_call = calls[0]
        adme_call = calls[1]
        
        # Verify AI search URL
        ai_url = ai_call[0][0]
        assert "q=AI" in ai_url
        assert "scholar.google.com" in ai_url
        
        # Verify ADME search URL  
        adme_url = adme_call[0][0]
        assert "q=ADME" in adme_url
        assert "scholar.google.com" in adme_url
        
        # Verify that papers were extracted and stored
        assert len(result_state.raw_papers) > 0
        
        # Check the structure of extracted papers
        for paper in result_state.raw_papers:
            assert "title" in paper
            assert "title_link" in paper
            assert "id" in paper
            assert "displayed_link" in paper
            assert "snippet" in paper
            
        # Verify specific paper content (titles may contain whitespace)
        paper_titles = [paper["title"].strip() for paper in result_state.raw_papers]
        assert "Artificial Intelligence in Drug Discovery" in paper_titles
        assert "ADME Properties Prediction Using Machine Learning" in paper_titles


def test_scrape_papers_with_network_error(news_agent, newsletter_state):
    """Test paper scraping handles network errors gracefully."""
    
    with patch('requests.get') as mock_get:
        # Simulate a network error
        mock_get.side_effect = Exception("Network timeout")
        
        # Call the _scrape_papers method
        result_state = news_agent._scrape_papers(newsletter_state)
        
        # Should handle error gracefully and return empty papers list
        assert result_state.raw_papers == []


def test_scrape_papers_with_malformed_html(news_agent, newsletter_state):
    """Test paper scraping handles malformed HTML gracefully."""
    
    with patch('requests.get') as mock_get:
        # Mock response with malformed HTML
        mock_response = Mock()
        mock_response.content = b"<html><body>No valid scholar results</body></html>"
        mock_get.return_value = mock_response
        
        # Call the _scrape_papers method
        result_state = news_agent._scrape_papers(newsletter_state)
        
        # Should handle malformed HTML and return empty or minimal papers
        assert isinstance(result_state.raw_papers, list)
        # The actual behavior may vary depending on how BeautifulSoup parses the HTML


def test_scrape_papers_filters_empty_values(news_agent, newsletter_state):
    """Test that empty values are filtered out from paper data."""
    
    html_with_empty_values = """
    <div class="gs_r">
        <h3 class="gs_rt">
            <a href="https://example.com/paper1" id="paper1">Test Paper</a>
        </h3>
        <div class="gs_a">Author Info</div>
        <div class="gs_rs">Paper abstract</div>
        <div>
            <a href="/scholar?cites=" class="gs_nph"></a>
            <a href="" class="gs_nph"></a>
        </div>
    </div>
    """
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.content = html_with_empty_values.encode('utf-8')
        mock_get.return_value = mock_response
        
        result_state = news_agent._scrape_papers(newsletter_state)
        
        # Verify that empty values are filtered out
        for paper in result_state.raw_papers:
            for key, value in paper.items():
                assert value != ""
                assert value is not None


if __name__ == "__main__":
    pytest.main([__file__])