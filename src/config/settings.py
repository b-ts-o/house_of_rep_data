import os
from dotenv import load_dotenv

load_dotenv()

# Congress API configurations
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = os.getenv("BASE_URL")
VER = os.getenv("SERVER")
FORMAT = os.getenv("FORMAT")
CONGRESS = os.getenv("DEFAULT_CONGRESS")
SESSION = os.getenv("DEFAULT_SESSION")