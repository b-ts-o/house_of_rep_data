from unittest.mock import Mock, call
import pytest
from src.api.congress_client import CongressAPIClient
from src.extract.initial_extract import InitialExtractor
import requests

def test_validate_data_successful():
    extractor = InitialExtractor()

    # Recreate house roll call votes
    expected_data = [
        {
            "rollCallNumber": 74,
            "result": "Passed",
        },
        {
            "rollCallNumber": 72,
            "result": "Failed"
        }
    ]
    expected_type = list
    expected_description = "House Roll call votes example data"

    result = extractor._validate_data(expected_data, expected_type, expected_description)

    assert result == True

def test_validate_data_empty_list():
    extractor = InitialExtractor()

    # Recreate house roll call votes
    expected_data = []
    expected_type = list
    expected_description = "House Roll call votes example data"

    result = extractor._validate_data(expected_data, expected_type, expected_description)

    assert result == False

def test_validate_data_wrong_type():
    extractor = InitialExtractor()

    # Recreate house roll call votes
    expected_data = {}
    expected_type = list
    expected_description = "House Roll call votes example data"

    result = extractor._validate_data(expected_data, expected_type, expected_description)

    assert result == False

def test_run():
    # Mock return dict: votes, bills, members
    extractor = InitialExtractor()

    expected_votes = [
        {"rollCallNumber": 74},
        {"rollCallNumber": 72}
    ]

    expected_bills = [
        {"billId": "hres1075"},
        {"billId": "s2503"}
    ]

    expected_members = [
        {"memberId": "O000172"},
        {"memberId": "C001131"}
    ]

    def process_votes():
        extractor.votes.extend(expected_votes)

    def process_bills():
        extractor.bills.extend(expected_bills)

    def process_members():
        extractor.members.extend(expected_members)

    extractor._process_votes = Mock(side_effect=process_votes)
    extractor._process_bills = Mock(side_effect=process_bills)
    extractor._process_members = Mock(side_effect=process_members)

    result = extractor.run()

    assert result == {
        "votes": expected_votes,
        "bills": expected_bills,
        "members": expected_members
    }

    extractor._process_votes.assert_called_once_with()
    extractor._process_bills.assert_called_once_with()
    extractor._process_members.assert_called_once_with()

def test_run_resets_data_on_second_run():
    extractor = InitialExtractor()

    first_votes = [{"rollCallNumber": 74}]
    first_bills = [{"billId": "hres1075"}]
    first_members = [{"memberId": "O000172"}]

    def process_votes():
        extractor.votes.extend(first_votes)

    def process_bills():
        extractor.bills.extend(first_bills)

    def process_members():
        extractor.members.extend(first_members)

    extractor._process_votes = Mock(side_effect=process_votes)
    extractor._process_bills = Mock(side_effect=process_bills)
    extractor._process_members = Mock(side_effect=process_members)

    first_result = extractor.run()

    assert first_result == {
        "votes": first_votes,
        "bills": first_bills,
        "members": first_members,
    }

    # Make the second run's processing stages do nothing.
    extractor._process_votes = Mock()
    extractor._process_bills = Mock()
    extractor._process_members = Mock()

    second_result = extractor.run()

    assert second_result == {
        "votes": [],
        "bills": [],
        "members": [],
    }

def test_process_members_successful():
    extractor = InitialExtractor()
    extractor.seen_members = {
        "C001131",
        "O000172"
    }

    first_expected_member = {
        "bioguideId": "C001131",
        "birthYear": 1989,
        "firstName": "Greg",
        "lastName": "Casar",
        "state": "Texas",
    }

    second_expected_member = {
        "bioguideId": "O000172",
        "birthYear": 1989,
        "firstName": "Alexandria",
        "lastName": "Ocasio-Cortez",
        "state": "New York",
    }

    # Mock the CongressAPIClient to return a successful response
    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_member.side_effect = [
        first_expected_member,
        second_expected_member
    ]

    extractor.client = mock_client
    extractor._process_members()

    assert extractor.members == [
        first_expected_member, 
        second_expected_member
    ]

    assert mock_client.fetch_member.call_args_list == [
        call("C001131"),
        call("O000172")
    ]

def test_process_members_runtime_error():
    extractor = InitialExtractor()
    extractor.seen_members = {
        "C001131",
        "O000172"
    }

    # Mock the CongressAPIClient to raise an exception for the first member
    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_member.side_effect = [
        RuntimeError("Runtime failure"),
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    extractor.client = mock_client
    extractor._process_members()

    assert extractor.members == [
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    assert mock_client.fetch_member.call_args_list == [
        call("C001131"),
        call("O000172")
    ]

def test_process_members_empty_dict():
    extractor = InitialExtractor()
    extractor.seen_members = {
        "C001131",
        "O000172"
    }

    # Mock the CongressAPIClient to raise an exception for the first member
    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_member.side_effect = [
        {},
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    extractor.client = mock_client
    extractor._process_members()

    assert extractor.members == [
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    assert mock_client.fetch_member.call_args_list == [
        call("C001131"),
        call("O000172")
    ]

def test_process_members_no_dict():
    extractor = InitialExtractor()
    extractor.seen_members = {
        "C001131",
        "O000172"
    }

    # Mock the CongressAPIClient to raise an exception for the first member
    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_member.side_effect = [
        "not a dict",
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    extractor.client = mock_client
    extractor._process_members()

    assert extractor.members == [
        {
            "bioguideId": "O000172",
            "birthYear": 1989,
            "firstName": "Alexandria",
            "lastName": "Ocasio-Cortez",
            "state": "New York",
        }
    ]

    assert mock_client.fetch_member.call_args_list == [
        call("C001131"),
        call("O000172")
    ]

def test_process_bills_successful():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": "2024-06-01",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-01",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_bill_runtime_error():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        RuntimeError("Runtime failure"),
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("s", "2503")
    ])

def test_process_bills_bill_text_runtime_error():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": []
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        RuntimeError("Runtime failure"),
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_bill_empty_dict():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = { }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("s", "2503")
    ])

def test_process_bills_bill_text_empty_list():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = { 
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    first_expected_bill_text = []

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": []
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_text_ver():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        None,
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_formats():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": "2024-06-01",
            "formats": None,
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-01",
            "url": "",
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_format_entry():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": "2024-06-01",
            "formats": [
                [],
                None
            ],
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-01",
            "url": "",
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_url():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": "2024-06-01",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": None}
            ],
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-01",
            "url": "",
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_date():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": 1234,
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in House"
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_bills_invalid_ver_type():
    extractor = InitialExtractor()
    extractor.seen_bills = {
        ("hres", "1075"),
        ("s", "2503")
    }

    first_expected_bill = {
        "congress": 119,
        "number": "1075",
        "originChamber": "house"
    }

    second_expected_bill = {
        "congress": 119,
        "number": "2503",
        "originChamber": "senate"
    }

    first_expected_bill_text = [
        {
            "date": "2024-06-01",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": []
        },
        {
            "date": "2024-06-02",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in House"
        }
    ]

    second_expected_bill_text = [
        {
            "date": "2025-12-17",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "formats": [
                {"type": "Formatted Text", "url": "https://www.congress.gov/bill/text.htm"},
                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/text.xml"}
            ],
            "type": "Reported in Senate"
        }
    ]

    # First version
    first_expected_text_versions = [
        {
            "date": "2024-06-01",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": ""
        },
        {
            "date": "2024-06-02",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in House"
        }
    ]

    second_expected_text_versions = [
        {
            "date": "2025-12-17",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Engrossed in Senate"
        },
        {
            "date": "2025-11-18",
            "url": "https://www.congress.gov/bill/text.xml",
            "type": "Reported in Senate"
        }
    ]

    expected_processed_bills = [
        {
            **first_expected_bill,
            "textVersions": first_expected_text_versions
        },
        {
            **second_expected_bill,
            "textVersions": second_expected_text_versions
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_bill.side_effect = [
        first_expected_bill,
        second_expected_bill
    ]

    mock_client.fetch_bill_text.side_effect = [
        first_expected_bill_text,
        second_expected_bill_text
    ]

    extractor.client = mock_client
    extractor._process_bills()

    assert extractor.bills == expected_processed_bills

    mock_client.fetch_bill.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

    mock_client.fetch_bill_text.assert_has_calls([
        call("hres", "1075"),
        call("s", "2503")
    ])

def test_process_votes_successful():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("hres", "1075"),
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# fetch_house_roll_call runtime error
def test_process_votes_runtime_error_house_roll_call():
    extractor = InitialExtractor()

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        RuntimeError("Runtime failure")
    ]

    extractor.client = mock_client
    extractor._process_votes()

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert extractor.votes == []
    assert extractor.seen_bills == set()
    assert extractor.seen_members == set()

# Invalid type from fetch_house_roll_call
def test_process_votes_invalid_house_roll_call():
    extractor = InitialExtractor()

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        {}
    ]

    extractor.client = mock_client
    extractor._process_votes()

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert extractor.votes == []
    assert extractor.seen_bills == set()
    assert extractor.seen_members == set()

# Invalid 'vote' type: None
def test_process_votes_invalid_vote():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = None
    
    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }
    
    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_member_votes = {
        "rollCallNumber": 72,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }
    
    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(72),
    ]
    
    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(72),
    ]

    assert extractor.votes == expected_processed_votes
    assert extractor.seen_bills == {
        ("s", "2503")
    }
    assert extractor.seen_members == {
        "O000172",
        "C001131" 
    }

def test_process_votes_invalid_roll_call_id():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": "74",
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }
    
    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }
    
    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_member_votes = {
        "rollCallNumber": 72,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }
    
    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(72),
    ]
    
    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(72),
    ]

    assert extractor.votes == expected_processed_votes
    assert extractor.seen_bills == {
        ("s", "2503")
    }
    assert extractor.seen_members == {
        "O000172",
        "C001131" 
    }

# fetch_house_roll_call_votes runtime error
def test_process_votes_runtime_error_house_roll_call_votes():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }
    
    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }
    
    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_member_votes = {
        "rollCallNumber": 72,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }
    
    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        RuntimeError("Runtime failure"),
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]
    
    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(72),
    ]

    assert extractor.votes == expected_processed_votes
    assert extractor.seen_bills == {
        ("s", "2503")
    }
    assert extractor.seen_members == {
        "O000172",
        "C001131" 
    }

# house_roll_call_votes error
def test_process_votes_invalid_roll_call_votes():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes invalid type
    first_expected_total_votes = [{
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }]
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(72)
    ]

# Invalid vote question
def test_process_votes_invalid_vote_question():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": None,
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": "",
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("hres", "1075"),
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# Invalid vote_party_total
def test_process_votes_invalid_vote_party_total():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": None
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": [],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("hres", "1075"),
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# fetch_house_roll_call_member_votes RuntimeError
def test_process_votes_runtime_error_house_roll_call_member_votes():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        RuntimeError("Runtime failure"),
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# invalid house_roll_call_member_votes
def test_process_votes_invalid_house_roll_call_member_votes():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = [{
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }]

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# invalid member_results | results
def test_process_votes_invalid_member_results():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": None
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# checking legislationType and legislationNumber

# Both legislation keys missing
def test_process_votes_legislation_missing_keys():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# missing legislationType
def test_process_votes_legislation_type_missing_key():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

def test_process_votes_legislation_number_missing_key():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# legislationType is invalid | not in selected set, of type None
# Testedted params: None, "", 11, "ab"
def test_process_votes_legislation_type_invalid_type():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "ab"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "ab",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# legislationNumber is of invalid type
# None, "12A", ""
def test_process_votes_legislation_number_invalid_type():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": 1075,
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": 1075,
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# next test
# Invalid 'member_vote' from results list | invalid type: None or list
def test_process_votes_invalid_member_vote_from_results():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes
    # {"bioguideID": "W000832", "firstName": "Aisha", "lastName": "Wahab"},
    # {"bioguideID": "K000389", "firstName": "Ro", "lastName": "Khanna"}
    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            [{"bioguideID": "W000832", "firstName": "Aisha", "lastName": "Wahab"}],
            {"bioguideID": "K000389", "firstName": "Ro", "lastName": "Khanna"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("hres", "1075"),
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131",
        "K000389"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]

# Validate bioguideID
def test_process_votes_invalid_bioguideID_from_results():
    extractor = InitialExtractor()

    # Mock vote
    first_expected_vote = {
        "rollCallNumber": 74,
        "legislationNumber": "1075",
        "legislationType": "HRES"
    }

    second_expected_vote = {
        "rollCallNumber": 72,
        "legislationNumber": "2503",
        "legislationType": "S"
    }

    # Mock Raw Votes
    expected_raw_votes = [
        first_expected_vote,
        second_expected_vote
    ]

    # Mock house_roll_call_votes
    first_expected_total_votes = {
        "voteQuestion": "On agreeing to resolution",
        "legislationNumber": "1075",
        "legislationType": "HRES",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }
    
    second_expected_total_votes = {
        "voteQuestion": "On Motion to Suspend the Rules and Pass",
        "legislationNumber": "2503",
        "legislationType": "S",
        "votePartyTotal": [
            {"voteParty": "R"},
            {"voteParty": "D"},
            {"voteParty": "I"}
        ]
    }

    # Mock house_roll_call_member_votes

    first_expected_member_votes = {
        "rollCallNumber": 74,
        "results": [
            {"firstName": "Aisha", "lastName": "Wahab"},
            {"bioguideID": "K000389", "firstName": "Ro", "lastName": "Khanna"}
        ]
    }

    second_expected_member_votes = {
    "rollCallNumber": 72,
    "results": [
            {"bioguideID": "O000172", "firstName": "Alexandria", "lastName": "Ocasio-Cortez"},
            {"bioguideID": "C001131", "firstName": "Greg", "lastName": "Casar"}
        ]
    }

    expected_processed_votes = [
        {
            **first_expected_vote,
            "voteQuestion": first_expected_total_votes["voteQuestion"],
            "votePartyTotal": first_expected_total_votes["votePartyTotal"],
            "results": first_expected_member_votes["results"]
        },
        {
            **second_expected_vote,
            "voteQuestion": second_expected_total_votes["voteQuestion"],
            "votePartyTotal": second_expected_total_votes["votePartyTotal"],
            "results": second_expected_member_votes["results"]
        }
    ]

    mock_client = Mock(spec=CongressAPIClient)

    mock_client.fetch_house_roll_call.side_effect = [
        expected_raw_votes
    ]

    # params: roll_call_id
    mock_client.fetch_house_roll_call_votes.side_effect = [
        first_expected_total_votes,
        second_expected_total_votes
    ]

    mock_client.fetch_house_roll_call_member_votes.side_effect = [
        first_expected_member_votes,
        second_expected_member_votes
    ]

    extractor.client = mock_client
    extractor._process_votes()

    assert extractor.votes == expected_processed_votes

    assert extractor.seen_bills == {
        ("hres", "1075"),
        ("s", "2503")
    }

    assert extractor.seen_members == {
        "O000172",
        "C001131",
        "K000389"
    }

    mock_client.fetch_house_roll_call.assert_called_once_with()

    assert mock_client.fetch_house_roll_call_votes.call_args_list == [
        call(74),
        call(72),
    ]

    assert mock_client.fetch_house_roll_call_member_votes.call_args_list == [
        call(74),
        call(72),
    ]