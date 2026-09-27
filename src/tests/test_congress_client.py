from unittest.mock import Mock
import pytest
from src.api.congress_client import CongressAPIClient
import requests

class MockResponse:
    def __init__(self):
        self.status_code = 200

    def raise_for_status(self):
        return None

# Test client._get_root()
def test_get_root_returns_expected_value():
    client = CongressAPIClient()
    response = Mock()
    response.json.return_value = {"bill": {"number": "123"}}

    result = client._get_root(response, "bill")

    assert result == {"number": "123"}

def test_get_root_missing_key():
    client = CongressAPIClient()
    response = Mock()
    response.json.return_value = {}

    result = client._get_root(response, "bill")

    assert result is None

def test_request_successful(monkeypatch):
    client = CongressAPIClient()
    client.api_key = "DEMO_KEY"
    client.format = "json"
    
    captured_args = {}
    expected_response = MockResponse()

    def mock_get(url, **kwargs):
        assert url == "https://www.example.com"
        captured_args.update(kwargs)
        return expected_response

    monkeypatch.setattr("src.api.congress_client.requests.get", mock_get)

    result = client._request("https://www.example.com")

    assert result is expected_response
    assert result.status_code == 200
    assert captured_args.get("params") == {"format": "json", "api_key": "DEMO_KEY"}
    assert captured_args.get("timeout") == 30

def test_request_timeout(monkeypatch):
    client = CongressAPIClient()
    try_count = [0]
    sleep_calls = []

    def mock_get_timeout(url, **kwargs):
        try_count[0] += 1
        raise requests.exceptions.Timeout("Timeout error")

    def mock_sleep(seconds):
        sleep_calls.append(seconds)
    
    monkeypatch.setattr("src.api.congress_client.requests.get", mock_get_timeout)
    monkeypatch.setattr("src.api.congress_client.time.sleep", mock_sleep)

    with pytest.raises(RuntimeError, match = r"Failed to fetch data after 3 attempts\."):
        client._request("https://www.example.com")

    assert try_count[0] == 3
    assert sleep_calls == [1, 2, 4]

def test_request_connection_error(monkeypatch):
    client = CongressAPIClient()
    try_count = [0]
    sleep_calls = []

    def mock_get_timeout(url, **kwargs):
        try_count[0] += 1
        raise requests.exceptions.ConnectionError("Connection Error")

    def mock_sleep(seconds):
        sleep_calls.append(seconds)
    
    monkeypatch.setattr("src.api.congress_client.requests.get", mock_get_timeout)
    monkeypatch.setattr("src.api.congress_client.time.sleep", mock_sleep)

    with pytest.raises(RuntimeError, match = r"Failed to fetch data after 3 attempts\."):
        client._request("https://www.example.com")

    assert try_count[0] == 3
    assert sleep_calls == [1, 2, 4]

def test_request_http_error(monkeypatch):
    client = CongressAPIClient()

    expected_response = MockResponse()
    expected_response.status_code = 500
    expected_response.raise_for_status = Mock(
        side_effect = requests.exceptions.HTTPError("500 Server Error")
    )

    def mock_get_http(url, **kwargs):
        return expected_response

    monkeypatch.setattr("src.api.congress_client.requests.get", mock_get_http)

    with pytest.raises(RuntimeError, match = r"HTTP error occurred"):
        client._request("https://www.example.com")

    expected_response.raise_for_status.assert_called_once_with()

def test_request_exception(monkeypatch):
    client = CongressAPIClient()

    expected_response = MockResponse()
    expected_response.status_code = 500
    expected_response.raise_for_status = Mock(
        side_effect = requests.exceptions.RequestException("Request exception occurred")
    )
    
    def mock_get_request_exception(url, **kwargs):
        return expected_response
    
    monkeypatch.setattr("src.api.congress_client.requests.get", mock_get_request_exception)
    
    with pytest.raises(RuntimeError, match = r"Request exception occurred"):
        client._request("https://www.example.com")
    
    expected_response.raise_for_status.assert_called_once_with()

