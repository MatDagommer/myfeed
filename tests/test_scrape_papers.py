import pytest
from unittest.mock import Mock, patch
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
def mock_openalex_response():
    """Mock JSON response from OpenAlex API."""
    return {
        "meta": {
            "count": 1000,
            "per_page": 10,
            "page": 1
        },
        "results": [
            {
                "id": "https://openalex.org/W1234567890",
                "doi": "https://doi.org/10.1234/example.2023.001",
                "title": "Artificial Intelligence in Drug Discovery",
                "display_name": "Artificial Intelligence in Drug Discovery",
                "publication_year": 2023,
                "cited_by_count": 45,
                "authorships": [
                    {
                        "author_position": "first",
                        "author": {
                            "id": "https://openalex.org/A1111111111",
                            "display_name": "John Doe"
                        }
                    },
                    {
                        "author_position": "middle",
                        "author": {
                            "id": "https://openalex.org/A2222222222",
                            "display_name": "Jane Smith"
                        }
                    }
                ],
                "abstract_inverted_index": {
                    "This": [0],
                    "paper": [1],
                    "discusses": [2],
                    "the": [3, 8],
                    "application": [4],
                    "of": [5],
                    "AI": [6],
                    "in": [7],
                    "pharmaceutical": [9],
                    "research.": [10]
                },
                "primary_location": {
                    "source": {
                        "id": "https://openalex.org/S1234567890",
                        "display_name": "Nature"
                    },
                    "landing_page_url": "https://example.com/paper1"
                }
            },
            {
                "id": "https://openalex.org/W0987654321",
                "doi": "https://doi.org/10.1234/example.2023.002",
                "title": "ADME Properties Prediction Using Machine Learning",
                "display_name": "ADME Properties Prediction Using Machine Learning",
                "publication_year": 2023,
                "cited_by_count": 23,
                "authorships": [
                    {
                        "author_position": "first",
                        "author": {
                            "id": "https://openalex.org/A3333333333",
                            "display_name": "Alice Johnson"
                        }
                    },
                    {
                        "author_position": "last",
                        "author": {
                            "id": "https://openalex.org/A4444444444",
                            "display_name": "Bob Wilson"
                        }
                    }
                ],
                "abstract_inverted_index": {
                    "Machine": [0],
                    "learning": [1],
                    "approaches": [2],
                    "for": [3],
                    "predicting": [4],
                    "ADME": [5],
                    "properties.": [6]
                },
                "primary_location": {
                    "source": {
                        "id": "https://openalex.org/S0987654321",
                        "display_name": "Journal of Medicinal Chemistry"
                    },
                    "landing_page_url": "https://example.com/paper2"
                }
            }
        ]
    }


def test_scrape_papers_success(news_agent, newsletter_state, mock_openalex_response):
    """Test successful paper scraping from OpenAlex API for AI and ADME topics."""

    with patch('requests.get') as mock_get:
        # Mock the requests.get response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the _scrape_papers method
        result_state = news_agent._scrape_papers(newsletter_state)

        # Verify that requests.get was called for each topic
        assert mock_get.call_count == len(newsletter_state.topics)

        # Check that the URLs contain the expected API endpoint
        calls = mock_get.call_args_list
        for call in calls:
            url = call[0][0]
            assert "api.openalex.org/works" in url

        # Verify that papers were extracted and stored
        assert len(result_state.raw_papers) > 0

        # Check the structure of extracted papers
        for paper in result_state.raw_papers:
            assert "title" in paper
            assert "url" in paper
            assert "authors" in paper
            assert "citations" in paper

        # Verify specific paper content
        paper_titles = [paper["title"] for paper in result_state.raw_papers]
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


def test_scrape_papers_with_empty_response(news_agent, newsletter_state):
    """Test paper scraping handles empty API response gracefully."""

    with patch('requests.get') as mock_get:
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"meta": {}, "results": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the _scrape_papers method
        result_state = news_agent._scrape_papers(newsletter_state)

        # Should handle empty response and return empty papers list
        assert isinstance(result_state.raw_papers, list)
        assert len(result_state.raw_papers) == 0


def test_scrape_papers_extracts_authors_correctly(news_agent, newsletter_state, mock_openalex_response):
    """Test that authors are extracted and formatted correctly."""

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result_state = news_agent._scrape_papers(newsletter_state)

        # Find the AI paper and check authors
        ai_paper = next(
            (p for p in result_state.raw_papers if "Artificial Intelligence" in p["title"]),
            None
        )
        assert ai_paper is not None
        assert "John Doe" in ai_paper["authors"]
        assert "Jane Smith" in ai_paper["authors"]


def test_scrape_papers_extracts_citations(news_agent, newsletter_state, mock_openalex_response):
    """Test that citation counts are extracted correctly."""

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result_state = news_agent._scrape_papers(newsletter_state)

        # Check that citations are extracted as strings
        for paper in result_state.raw_papers:
            assert "citations" in paper
            assert isinstance(paper["citations"], str)


def test_reconstruct_abstract(news_agent):
    """Test that abstract reconstruction from inverted index works correctly."""

    inverted_index = {
        "Hello": [0],
        "world": [1],
        "this": [2],
        "is": [3],
        "a": [4],
        "test.": [5]
    }

    result = news_agent._reconstruct_abstract(inverted_index)
    assert result == "Hello world this is a test."


def test_reconstruct_abstract_empty(news_agent):
    """Test that empty inverted index returns empty string."""

    result = news_agent._reconstruct_abstract(None)
    assert result == ""

    result = news_agent._reconstruct_abstract({})
    assert result == ""


def test_scrape_papers_filters_empty_values(news_agent, newsletter_state):
    """Test that empty values are filtered out from paper data."""

    response_with_missing_data = {
        "meta": {},
        "results": [
            {
                "id": "https://openalex.org/W1234567890",
                "title": "Test Paper",
                "publication_year": 2023,
                "cited_by_count": 10,
                "authorships": [],
                "abstract_inverted_index": None,
                "primary_location": None
            }
        ]
    }

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_with_missing_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result_state = news_agent._scrape_papers(newsletter_state)

        # Verify that empty values are filtered out
        for paper in result_state.raw_papers:
            for key, value in paper.items():
                assert value != ""
                assert value is not None


def test_scrape_papers_uses_polite_pool(news_agent, newsletter_state, mock_openalex_response):
    """Test that requests include mailto parameter for polite pool."""

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        news_agent._scrape_papers(newsletter_state)

        # Check that mailto parameter is included
        calls = mock_get.call_args_list
        for call in calls:
            params = call[1].get('params', {})
            assert 'mailto' in params


if __name__ == "__main__":
    pytest.main([__file__])
