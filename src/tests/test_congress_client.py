from unittest.mock import Mock
from src.api.congress_client import CongressAPIClient

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

def test_fetch_house_roll_call_votes():
    client = CongressAPIClient(119, 2)

    response = Mock()

    response.json.return_value = {
        "houseRollCallVote": {
            "rollCallNumber": 74
        }
    }

    expected_data = {"rollCallNumber": 74}
    # Build URL
    expected_url = (f"{client.base_url}/{client.ver}/house-vote/{client.congress}/{client.session}/74")

    client._request = Mock(return_value=response)

    result = client.fetch_house_roll_call_votes(74)

    assert result == {
        "rollCallNumber": 74
    }

    client._request.assert_called_once_with(expected_url)

def test_request_successful():
    client = CongressAPIClient()
    response = Mock()
    response.status_code = 200

    expected_url = "https://example.com/test"
