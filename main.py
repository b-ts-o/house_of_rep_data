import json, logging
from pathlib import Path
from src.api.congress_client import CongressAPIClient
from src.extract.initial_extract import InitialExtractor

log_dir = Path("logs")
log_dir.mkdir(exist_ok = True)

def setup_logging():
    formatter = logging.Formatter(
        fmt = "%(asctime)s [%(levelname)s] %(message)s",
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Extraction logger setup
    extraction_logger = logging.getLogger("extraction")
    extraction_logger.setLevel(logging.INFO)
    extraction_logger.propagate = False

    extraction_file = logging.FileHandler(log_dir / "extraction.log", encoding="utf-8")
    extraction_file.setFormatter(formatter)
    extraction_logger.addHandler(extraction_file)

    # CongressAPIClient logger setup
    api_client_logger = logging.getLogger("api_client")
    api_client_logger.setLevel(logging.INFO)
    api_client_logger.propagate = False

    api_client_file = logging.FileHandler(log_dir / "api_client.log", encoding="utf-8")
    api_client_file.setFormatter(formatter)
    api_client_logger.addHandler(api_client_file)

setup_logging()

client = CongressAPIClient()
initial_extractor = InitialExtractor()
initial_data = initial_extractor.run()

# with open('bills_demo.json', 'w', encoding = 'utf-8') as json_file:
#     json.dump(initial_data.get('bills'), json_file, indent=4)


