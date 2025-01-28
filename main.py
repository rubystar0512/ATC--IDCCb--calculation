import requests
from urllib.parse import urlencode
import logging

# Define constants and configurations
FROM_UTC = "2025-01-27T13:00:00.000Z"
TO_UTC = "2025-01-27T14:00:00.000Z"
FINAL_URL = "https://publicationtool.jao.eu/coreID/api/data/IDCCB_finalComputation"
IDCCA_URL = "https://publicationtool.jao.eu/coreID/api/data/IDCCA_intradayAtc"

PARAMS_FINAL = {
    "Filter": '{"Presolved":true}',
    "Skip": 0,
    "Take": 1000,
    "FromUtc": FROM_UTC,
    "ToUtc": TO_UTC
}

PARAMS_IDCCA = {
    "FromUtc": FROM_UTC,
    "ToUtc": TO_UTC
}

ENCODED_PARAMS_FINAL = urlencode(PARAMS_FINAL)
FINAL_COMPUTATION_URL = f"{FINAL_URL}?{ENCODED_PARAMS_FINAL}"

ENCODED_PARAMS_IDCCA = urlencode(PARAMS_IDCCA)
IDCCA_URL = f"{IDCCA_URL}?{ENCODED_PARAMS_IDCCA}"

BORDER_MAPPING = {
    "AT": ["CZ", "DE", "HU", "SI"],
    "BE": ["DE", "FR", "NL"],
    "CZ": ["AT", "DE", "PL", "SK"],
    "DE": ["AT", "BE", "CZ", "FR", "NL", "PL"],
    "FR": ["BE", "DE"],
    "HR": ["HU", "SI"],
    "HU": ["AT", "HR", "RO", "SI", "SK"],
    "NL": ["BE", "DE"],
    "PL": ["CZ", "DE", "SK"],
    "RO": ["HU"],
    "SI": ["AT", "HR", "HU"],
    "SK": ["CZ", "HU", "PL"]
}

# Precompute PTDF keys
PTDF_KEYS = {country: f"ptdf_{country}" for country in BORDER_MAPPING.keys()}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_from_jao(url):
    """Fetch data from the JAO  API."""
    try:
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            logger.info(f"JAO request code: {response.status_code}")
            return response.json()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error occurred: {err}")
    except requests.exceptions.ConnectionError as err:
        logger.error(f"Connection error occurred: {err}")
    except requests.exceptions.Timeout as err:
        logger.error(f"Timeout error occurred: {err}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Error fetching data: {err}")
    return None

def process_cnec_data(data):
    """Process CNEC data and calculate border PTDF differences."""
    cnec_data = {}
    
    for idx, cnec in enumerate(data.get("data", [])):
        cnec_data[idx] = {
            "ram": cnec["ram"],
            "ptdf_differences": {
                f"{source.lower()}{target.lower()}": cnec[PTDF_KEYS[source]] - cnec[PTDF_KEYS[target]]
                for source, targets in BORDER_MAPPING.items()
                for target in targets
                if PTDF_KEYS[source] in cnec and PTDF_KEYS[target] in cnec
            }
        }

    return cnec_data


def process_idcca_data(data):
    """Process IDCCA data with border """
    idcca_data = {}
    return idcca_data


def calculate_atc(cnec_data):
    """Calculate ATC for each CNEC using RAM and PTDF differences."""
    atc_results = []

    for idx, cnec in cnec_data.items():
        ram = cnec["ram"]
        ptdf_differences = cnec["ptdf_differences"]
        
        # Calculate Pre-Final ATC
        if ram > 0:
            atc_values = [
                ram / abs(ptdf) if ptdf > 0 else float('inf')  # Avoid division by zero
                for ptdf in ptdf_differences.values()
            ]
            pre_final_atc = min(atc_values) if atc_values else 0
        else:
            pre_final_atc = 0
        
        # # Add leftover capacity from IDCCa
        # leftover = idcca_leftovers.get(idx, 0)
        final_atc = pre_final_atc

        atc_results.append({
            "CNEC_ID": idx,
            "PreFinal_ATC": pre_final_atc,
            "Final_ATC": final_atc
        })
    
    return atc_results

def main():
    """Main function to fetch and process CNEC data."""
    logger.info("Fetching Final Computation data...")
    cnec_raw_data = fetch_data_from_jao(FINAL_COMPUTATION_URL)
    
    if not cnec_raw_data:
        logger.error("Failed to fetch CNEC data . Exiting...")
        return
    
    logger.info("Processing CNEC data...")
    processed_cnec_data = process_cnec_data(cnec_raw_data)

    logger.info(f"CNEC_DATA = {processed_cnec_data}")

    logger.info("Calculating ATC values...")
    atc_results = calculate_atc(processed_cnec_data)

    # # Display results
    # for atc in atc_results:
    #     logger.info(f"CNEC_ID={atc['CNEC_ID']}, PreFinal_ATC={atc['PreFinal_ATC']}, Final_ATC={atc['Final_ATC']}")

if __name__ == "__main__":
    main()