from src.config import settings
import requests, json, time, logging
from requests.exceptions import HTTPError, RequestException, Timeout, ConnectionError

class CongressAPIClient:
    def __init__(self, congress = settings.CONGRESS, session = settings.SESSION):
        # Can i make these private?
        self.logger = logging.getLogger("api_client")
        self.congress = congress
        self.session = session
        self.api_key = settings.CONGRESS_API_KEY
        self.base_url = settings.BASE_URL
        self.ver = settings.VER
        self.format = settings.FORMAT

    def _request(self, url):
        # Set up query parameters for URL
        query_params = {
            "format": self.format,
            "api_key": self.api_key
        }

        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(url, params = query_params, timeout = 30)
                response.raise_for_status()
                self.logger.info(f"{response.status_code} GET {url}")
                return response
            except (Timeout, ConnectionError) as e:
                self.logger.warning(f"Request failed: {type(e).__name__} Re-try {attempt + 1}/{3}")
                self.logger.warning(f"GET {url}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except HTTPError as e:
                self.logger.error(f"HTTP Error")
                self.logger.error(f"{response.status_code} GET {url}")
                raise RuntimeError(f"HTTP error occurred: {e}")
            except RequestException as e:
                self.logger.error(f"Request Exception")
                self.logger.error(f"GET {url}")
                raise RuntimeError(f"Request exception occurred: {e}")
        self.logger.error(f"Request failed after 3 attempts")
        self.logger.error(f"GET {url}")
        raise RuntimeError("Failed to fetch data after 3 attempts.")

    def _request_all_pages(self, url, data_key, limit = 250):
        url += f"?limit={limit}"
        roll_call_records = []
        current_url = url
        
        while current_url:
            # How to pass 'offset' and 'limit'
            response = self._request(current_url)
            # Add entries from response into 'data'
            data = response.json()
            roll_call_records.extend(data[data_key])
            # Set up next url
            current_url = data['pagination'].get('next')

        return roll_call_records

    # Gets all roll call records
    def fetch_house_roll_call(self):
        # /house-vote/{congress}/{session} | primary key: 'houseRollCallVotes'
        url = f"{self.base_url}/{self.ver}/house-vote/{self.congress}/{self.session}"
        return self._request_all_pages(url, "houseRollCallVotes")
    
    # Gets roll call votes for a specifiec roll call vote | roll_call_id required
    def fetch_house_roll_call_votes(self, roll_call_id):
        # /house-vote/{congress}/{session}/{voteNumber} | primary key: 'houseRollCallVote'
        url = f"{self.base_url}/{self.ver}/house-vote/{self.congress}/{self.session}/{roll_call_id}"
        response = self._request(url)
        # Root/Key = 'houseRollCallVote'
        return self._get_root(response, "houseRollCallVote")

    # Gets roll call votes for each member for a specified roll call vote | required: roll_call_id
    def fetch_house_roll_call_member_votes(self, roll_call_id):
        # /house-vote/{congress}/{session}/{voteNumber}/members | primary key: 'houseRollCallVoteMemberVotes'
        url = f"{self.base_url}/{self.ver}/house-vote/{self.congress}/{self.session}/{roll_call_id}/members"
        response = self._request(url)
        # Root/Key = 'houseRollCallVoteMemberVotes'
        return self._get_root(response, "houseRollCallVoteMemberVotes")

    # Gets general information for a specified legislate voted bill and congress | required: bill_type, bill_number
    def fetch_bill(self, bill_type, bill_number):
        # /bill/{congress}/{billType}/{billNumber} | primary key: 'bill'
        url = f"{self.base_url}/{self.ver}/bill/{self.congress}/{bill_type}/{bill_number}"
        response = self._request(url)
        # Root/Key = 'bill'
        return self._get_root(response, "bill")

    # Gets bill text link for a specified legislate voted bill and congress | required: bill_type, bill_number
    def fetch_bill_text(self, bill_type, bill_number):
        # /bill/{congress}/{billType}/{billNumber}/text | primary key: 'textVersions'
        url = f"{self.base_url}/{self.ver}/bill/{self.congress}/{bill_type}/{bill_number}/text"
        response = self._request(url)
        # Root/Key = 'textVersions'
        return self._get_root(response, "textVersions")

    # Gets member information | required: bioguide_id
    def fetch_member(self, bioguide_id):
        # /member/{bioguideId} | primary key: 'member'
        url = f"{self.base_url}/{self.ver}/member/{bioguide_id}"
        response = self._request(url)
        # Root/Key = 'member'
        return self._get_root(response, "member")

    # Error catch function, checks if our API response root key is present, otherwise make it 'None'
    # CURRENTLY: only works on dicts, will break otherwise. Need to fix
    def _get_root(self, response, key):
        data = response.json()

        if key not in data:
            self.logger.warning(
                f"Expected root key '{key}' not found in API response"
            )

            return None

        return data[key]