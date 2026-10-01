from unittest.mock import Mock, call
import pytest
from src.api.congress_client import CongressAPIClient
import requests

class MockResponse:
    def __init__(self):
        self.status_code = 200
        self.json_data = None

    def raise_for_status(self):
        return None
    
    def json(self):
        return self.json_data

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

def test_get_root_error():
    client = CongressAPIClient()
    response = Mock()
    response.json.side_effect = RuntimeError("Response parsing failed")

    with pytest.raises(RuntimeError, match=r"Response parsing failed"):
        client._get_root(response, "bill")

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

def test_request_all_pages_successful():
    client = CongressAPIClient()
    url = "https://www.example.com/items"
    data_key = "houseExampleRollCallVotes"

    first_response = MockResponse()
    first_response.json_data = {
        "houseExampleRollCallVotes" : [
            {"record_id": 1},
            {"record_id": 2}
        ],
        "pagination": {
            "count": 3,
            "next": "https://www.example.com/items?offset=2&limit=2"
        }
    }

    second_response = MockResponse()
    second_response.json_data = {
            "houseExampleRollCallVotes" : [
                {"record_id": 3}
            ],
            "pagination": {
                "count": 3,
            }
        }

    client._request = Mock(side_effect = [first_response, second_response])

    result = client._request_all_pages(url, data_key, limit = 2)

    assert result == [
        {"record_id": 1},
        {"record_id": 2},
        {"record_id": 3}
    ]

    assert client._request.call_args_list == [
        call("https://www.example.com/items?limit=2"),
        call("https://www.example.com/items?offset=2&limit=2"),
    ]

def test_request_all_pages_no_next_successful():
    client = CongressAPIClient()
    url = "https://www.example.com/items"
    data_key = "houseExampleRollCallVotes"

    response = MockResponse()
    response.json_data = {
        "houseExampleRollCallVotes" : [
            {"record_id": 1},
            {"record_id": 2}
        ],
        "pagination": {
            "count": 2,
        }
    }

    client._request = Mock(return_value = response)

    result = client._request_all_pages(url, data_key, limit = 2)

    assert result == [
        {"record_id": 1},
        {"record_id": 2},
    ]

    client._request.assert_called_once_with(
        "https://www.example.com/items?limit=2"
    )

def test_request_all_pages_empty():
    client = CongressAPIClient()
    url = "https://www.example.com/items"
    data_key = "houseExampleRollCallVotes"

    response = MockResponse()
    response.json_data = {
        "houseExampleRollCallVotes" : [],
        "pagination": {
            "count": 0,
        }
    }

    client._request = Mock(return_value = response)

    result = client._request_all_pages(url, data_key, limit = 2)

    assert result == []

    client._request.assert_called_once_with(
        "https://www.example.com/items?limit=2"
    )

def test_request_all_pages_request_exception():
    client = CongressAPIClient()
    url = "https://www.example.com/items"
    data_key = "houseExampleRollCallVotes"

    client._request = Mock(side_effect = RuntimeError("Request exception occurred"))

    with pytest.raises(RuntimeError, match = r"Request exception occurred"):
        client._request_all_pages(url, data_key, limit = 2)

    client._request.assert_called_once_with(
        "https://www.example.com/items?limit=2"
    )

def test_fetch_house_roll_call():
    client = CongressAPIClient()
    url = "https://api.congress.gov/v3/house-vote/119/2"

    expected_records = [
        {"record_id": 1},
        {"record_id": 2},
        {"record_id": 3},
        {"record_id": 4}
    ]

    client._request_all_pages = Mock(return_value = expected_records)

    result = client.fetch_house_roll_call()

    assert result == expected_records
    client._request_all_pages.assert_called_once_with(
        "https://api.congress.gov/v3/house-vote/119/2", 
        "houseRollCallVotes"
    )

def test_fetch_house_roll_call_votes():
    client = CongressAPIClient()

    roll_call_id = 74
    url = f"https://api.congress.gov/v3/house-vote/119/2/{roll_call_id}"

    expected_record = {
        "rollCallNumber": 74, 
        "result": "Passed"
    }

    client._request = Mock()
    client._get_root = Mock(return_value = expected_record)

    result = client.fetch_house_roll_call_votes(roll_call_id)

    assert result == expected_record
    client._request.assert_called_once_with(url)
    client._get_root.assert_called_once_with(
        client._request.return_value,
        "houseRollCallVote"
    )

def test_fetch_house_roll_call_member_votes():
    client = CongressAPIClient()

    roll_call_id = 74
    url = f"https://api.congress.gov/v3/house-vote/119/2/{roll_call_id}/members"

    expected_records = {
        "rollCallNumber": 74,
        "result": "Passed",
        "results": [
            {"memberId": "A000360", "voteCast": "Yea"},
            {"memberId": "B000574", "voteCast": "Nay"}
        ]
    }

    client._request = Mock()
    client._get_root = Mock(return_value = expected_records)

    result = client.fetch_house_roll_call_member_votes(roll_call_id)

    assert result == expected_records
    client._request.assert_called_once_with(url)
    client._get_root.assert_called_once_with(
        client._request.return_value,
        "houseRollCallVoteMemberVotes"
    )

def test_fetch_bill():
    client = CongressAPIClient()
    url = "https://api.congress.gov/v3/bill/119/hres/1075"

    expected_record = {
        "type": "HRES",
        "number": 1075
    }

    client._request = Mock()
    client._get_root = Mock(return_value = expected_record)

    result = client.fetch_bill("hres", 1075)
    assert result == expected_record

    client._request.assert_called_once_with(url)
    client._get_root.assert_called_once_with(
        client._request.return_value,
        "bill"
    )

def test_fetch_bill_text():
    client = CongressAPIClient()
    url = "https://api.congress.gov/v3/bill/119/hres/1075/text"

    expected_record = [
        {
            "date": "2024-06-01",
            "format": [],
            "version": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "format": [],
            "version": "Engrossed in House"
        }
    ]

    client._request = Mock()
    client._get_root = Mock(return_value = expected_record)

    result = client.fetch_bill_text("hres", 1075)
    assert result == expected_record

    client._request.assert_called_once_with(url)
    client._get_root.assert_called_once_with(
        client._request.return_value,
        "textVersions"
    )

def test_fetch_member():
    client = CongressAPIClient()
    bioguide_id = "O000172"
    url = f"https://api.congress.gov/v3/member/{bioguide_id}"

    expected_record = {
        "bioguideId": "O000172",
        "firstName": "Alexandria",
        "lastName": "Ocasio-Cortez"
    }

    client._request = Mock()
    client._get_root = Mock(return_value = expected_record)

    result = client.fetch_member(bioguide_id)
    assert result == expected_record

    client._request.assert_called_once_with(url)
    client._get_root.assert_called_once_with(
        client._request.return_value,
        "member"
    )
