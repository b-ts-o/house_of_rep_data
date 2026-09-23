import logging
from src.api.congress_client import CongressAPIClient

class InitialExtractor:
    def __init__(self):
        self.client = CongressAPIClient()
        self.logger = logging.getLogger("extraction")

        self.votes = []
        self.members = []
        self.bills = []

        self.seen_members = set()
        self.seen_bills = set()

    def run(self):
        self.votes = []
        self.members = []
        self.bills = []
        self.seen_members = set()
        self.seen_bills = set()

        self.logger.info("Starting initial extraction...")

        self._process_votes()

        self._process_bills()

        self._process_members()

        self.logger.info("Initial extraction complete")

        return {
            "votes": self.votes,
            "bills": self.bills,
            "members": self.members
        }

    def _process_votes(self):
        self.logger.info(f"Processing votes...")

        try:
            raw_votes = self.client.fetch_house_roll_call()
        except RuntimeError as error:
            self.logger.error(f"Failed to fetch house roll call votes: {error}")
            raw_votes = []
        else:
            if not self._validate_data(
                raw_votes, 
                list, 
                "House roll call votes parent structure"
            ):
                raw_votes = []

        self.logger.info(f"Retrieved {len(raw_votes)} roll call vote records")

        for index, vote in enumerate(raw_votes, start = 1):
            # Include 'rollCallNumber' in description field
            # Should be after we validate 'rollCallNumber' ?
            if not self._validate_data(
                vote, 
                dict, 
                f"Roll Call record {index} of {len(raw_votes)}"
            ):
                continue

            roll_call_number = vote.get('rollCallNumber')

            # If 'rollCallNumber' is not present, we cannot preceed
            if not self._validate_data(
                roll_call_number, 
                int, 
                f"Roll Call record {index} of {len(raw_votes)} 'rollCallNumber' attribute"
            ):
                continue

            # Fetch house_roll_call_vote | /house-vote/{congress}/{session}/{rollCallNumber}
            try:
                house_roll_call_vote = self.client.fetch_house_roll_call_votes(roll_call_number)
            except RuntimeError as error:
                self.logger.error(f"Failed to fetch house roll call votes for roll call #{roll_call_number}: {error}")
                continue

            # Check if house_roll_call_vote is okay to touch
            if not self._validate_data(
                house_roll_call_vote,
                dict,
                f"Roll Call #{roll_call_number} house roll call vote"
            ):
                continue

            vote_question = house_roll_call_vote.get('voteQuestion', '')

            # Validate 'voteQuestion'
            if not self._validate_data(
                vote_question,
                str,
                f"Roll Call #{roll_call_number} 'voteQuestion' attribute"
            ):
                vote_question = ""

            vote_party_total = house_roll_call_vote.get('votePartyTotal', [])

            # Validate 'votePartyTotal'
            if not self._validate_data(
                vote_party_total,
                list,
                f"Roll Call #{roll_call_number} 'votePartyTotal' attribute"
            ):
                vote_party_total = []
            
            # Fetch house_roll_call_member_votes | /house-vote/{congress}/{session}/{rollCallNumber}/members
            try:
                house_roll_call_member_votes = self.client.fetch_house_roll_call_member_votes(roll_call_number)
            except RuntimeError as error:
                self.logger.error(f"Failed to fetch house roll call member votes for roll call #{roll_call_number}: {error}")
                continue

            # Check if house_roll_call_member_votes is okay to touch
            if not self._validate_data(
                house_roll_call_member_votes,
                dict,
                f"Roll Call #{roll_call_number} house roll call member votes"
            ):
                continue

            member_results = house_roll_call_member_votes.get('results', [])

            # Validate 'results'
            if not self._validate_data(
                member_results,
                list,
                f"Roll Call #{roll_call_number} 'results' attribute"
            ):
                continue

            vote.update({
                'voteQuestion': vote_question,
                'votePartyTotal': vote_party_total,
                'results': member_results
            })

            # legislationType and legislationNumber validating section
            if 'legislationType' not in house_roll_call_vote and 'legislationNumber' not in house_roll_call_vote:
                # Neither legislationType and legislationNumber key is present in dict
                self.logger.debug(f"Roll Call #{roll_call_number} has no associated legislation")
            elif 'legislationType' not in house_roll_call_vote or 'legislationNumber' not in house_roll_call_vote:
                # Either legislationType or legislationNumber key is missing in dict
                self.logger.warning(f"Roll Call #{roll_call_number} has incomplete legislation information: missing keys")
            else:
                # Both legislationType and legislationNumber keys are present in dict
                legislation_type = house_roll_call_vote.get('legislationType')
                legislation_number = house_roll_call_vote.get('legislationNumber')

                if (
                    self._validate_data(legislation_type, str, f"Roll Call #{roll_call_number} attribute legislationType")
                    and self._validate_data(legislation_number, str, f"Roll Call #{roll_call_number} attribute legislationNumber")
                    and legislation_type.strip().lower() in {
                        "hr", "s", "hres", "sres",
                        "hconres", "sconres", "hjres", "sjres"
                    }
                    and legislation_number.strip().isdigit()
                ):
                    self.seen_bills.add((
                        legislation_type.strip().lower(),
                        legislation_number.strip()
                    ))
                else:
                    self.logger.warning(
                        f"Roll Call #{roll_call_number} has invalid legislation metadata"
                    )

            # Process results structure to extract bioguideID and add to seen_members set
            for member_vote in member_results:
                # Validate member_vote structure
                if not self._validate_data(
                    member_vote,
                    dict,
                    f"Roll Call #{roll_call_number} member 'results' entry"
                ):
                    continue

                bioguide_id = member_vote.get('bioguideID', '')

                if not self._validate_data(
                    bioguide_id,
                    str,
                    f"Roll Call #{roll_call_number} member 'results' entry 'bioguideID' attribute"
                ):
                    bioguide_id = None

                if bioguide_id:
                    self.seen_members.add(bioguide_id)

            self.votes.append(vote)
            if index % 25 == 0:
                self.logger.info(f"Processing roll call vote {roll_call_number} ( {index} of {len(raw_votes)} )")
        self.logger.info(
            f"Processing votes complete:"
            f"\n{len(self.votes)} votes processed out of {len(raw_votes)}"
            f"\n{len(self.seen_bills)} unique bills"
            f"\n{len(self.seen_members)} unique members"
        )

    def _process_bills(self):
        self.logger.info(f"Processing bills...")
        
        for bill_name in sorted(self.seen_bills):
            bill_type, bill_number = bill_name

            try:
                bill = self.client.fetch_bill(bill_type, bill_number)
            except RuntimeError as error:
                self.logger.error(
                    f"Failed to fetch Bill {bill_type.upper()} {bill_number} general information: {error}"
                )
                continue

            if not self._validate_data(
                bill, 
                dict, 
                f"Bill {bill_type.upper()} {bill_number} general information "
            ):
                continue

            try:
                bill_text = self.client.fetch_bill_text(bill_type, bill_number)
            except RuntimeError as error:
                self.logger.error(
                    f"Failed to fetch Bill {bill_type.upper()} {bill_number} text: {error}"
                )
                bill_text = []
            else:
                if not self._validate_data(
                    bill_text, 
                    list, 
                    f"Bill {bill_type.upper()} {bill_number} text "
                ):
                    bill_text = []

            versions = []

            for text_version in bill_text:
                if not self._validate_data(
                    text_version, 
                    dict, 
                    f"Bill {bill_type.upper()} {bill_number} textVersions dict "
                ):
                    continue

                formats = text_version.get("formats")

                if not self._validate_data(
                    formats, 
                    list, 
                    f"Bill {bill_type.upper()} {bill_number} textVersions 'formats' attribute "
                ):
                    formats = []

                xml_url = ""

                for format_entry in formats:
                    if not self._validate_data(
                        format_entry, 
                        dict, 
                        f"Bill {bill_type.upper()} {bill_number} format entry in 'formats' is invalid: "
                    ):
                        continue

                    format_type = format_entry.get('type', '')

                    if isinstance(format_type, str) and "xml" in format_type.strip().lower():
                        url = format_entry.get('url', '')
                        if self._validate_data(url, str, f"Bill {bill_type.upper()} {bill_number} XML format found but 'url' is invalid: "):
                            xml_url = url
                            break

                date = text_version.get("date", "")
                version_type = text_version.get("type", "")

                if not self._validate_data(
                    date,
                    str,
                    f"Bill {bill_type.upper()} {bill_number} textVersions 'date' attribute "
                ):
                    date = ""

                if not self._validate_data(
                    version_type,
                    str,
                    f"Bill {bill_type.upper()} {bill_number} textVersions 'type' attribute "
                ):
                    version_type = ""

                self._validate_data(xml_url, str, f"Bill {bill_type.upper()} {bill_number} textVersions 'xml_url' attribute ")

                versions.append({
                    "date": date,
                    "url": xml_url,
                    "type": version_type
                })

            bill['textVersions'] = versions
            self.bills.append(bill)

            self.logger.info(f"Processing bill {bill_type} {bill_number}")
        self.logger.info(f"Processing bills complete: {len(self.bills)} of {len(self.seen_bills)} bills processed")
            
    def _process_members(self):
        self.logger.info(f"Processing members...")
        # Process each unique bioguideID in seen_members set, fetching member information and adding them to members structure
        for member_id in sorted(self.seen_members):
            try:
                member = self.client.fetch_member(member_id)
            except RuntimeError as error:
                self.logger.error(
                    f"Failed to fetch Member {member_id} profile: {error}"
                )
                continue

            # Check: member structure is dict && member is not None
            if not self._validate_data(member, dict, f"Member profile"):
                continue

            # Add to members structure
            self.members.append(member)
        self.logger.info(
            f"Processing members complete:"
            f"\n{len(self.members)} of {len(self.seen_members)} member profiles processed"
        )

    # Validation helper function to check correct type (dict, list, str, int) or is None
    # data: from our api call response structure
    # expected_type: either dict list, str, or int
    # description: brief description of the data being validated, used for logging
    def _validate_data(self, data, expected_type, description):
        if not isinstance(data, expected_type):
            self.logger.warning(
                f"{description} could not be extracted: expected {expected_type.__name__} but received {type(data).__name__}"
            )
            return False

        if not data:
            self.logger.warning(
                f"{description} could not be extracted: value is empty"
            )
            return False
        
        return True
