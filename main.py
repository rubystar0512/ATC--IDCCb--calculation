import requests
from urllib.parse import urlencode
import logging

# Define constants and configurations
FROM_UTC = "2025-01-27T13:00:00.000Z"
TO_UTC = "2025-01-27T14:00:00.000Z"
FINAL_URL = "https://publicationtool.jao.eu/coreID/api/data/IDCCB_finalComputation"

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

PTDF_KEYS = {country: f"ptdf_{country}" for country in BORDER_MAPPING.keys()}

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

def calculate_atc(cnec_data):
    """Calculate ATC for each CNEC using RAM and PTDF differences."""
    atc_results = []

    for cnec_id, cnec_info in cnec_data.items():
        ram = float(cnec_info["ram"]) 
        ptdf_differences = cnec_info["ptdf_differences"]

        # Initialize ATCs
        atc_values = {border: 0.0 for border in ptdf_differences.keys()}  # Use float for ATCs
        negative_atcs = {}

        if ram < 0:
            for border, ptdf_diff in ptdf_differences.items():
                # Ensure PTDF differences are numeric
                ptdf_diff = float(ptdf_diff)  # Convert PTDF difference to float
                if ptdf_diff > 0:
                    negative_atcs[border] = (ptdf_diff * ram) / ptdf_diff

            # Determine the most negative ATC for each border
            for border in negative_atcs:
                atc_values[border] = min(negative_atcs.get(border, 0.0), 0.0)

            # Calculate scaling factor
            scaling_factors = []
            for border, atc in atc_values.items():
                if atc < 0:
                    ptdf_diff = float(ptdf_differences[border])  # Ensure PTDF difference is numeric
                    scaling_factor = ram / (ptdf_diff * atc)
                    scaling_factors.append(scaling_factor)

            if scaling_factors:
                final_scaling_factor = max(scaling_factors)
                for border in atc_values:
                    if atc_values[border] < 0:
                        atc_values[border] *= final_scaling_factor

        # Adjust RAM to be non-negative
        ram = max(0.0, ram)

        # Iterative calculation of positive ATCs
        iteration = 0
        temp_flag = True
        while temp_flag:
            iteration += 1
            previous_atc_sum = sum(atc_values.values())

            # Calculate remaining available margin for each CNEC
            for border, ptdf_diff in ptdf_differences.items():
                ptdf_diff = float(ptdf_diff)  # Ensure PTDF difference is numeric
                if ptdf_diff > 0:
                    ram_share = ram / len(ptdf_differences)
                    max_additional_exchange = ram_share / ptdf_diff
                    atc_values[border] += max_additional_exchange
            # Check for convergence
            current_atc_sum = sum(atc_values.values())
            logger.info(f"Iteration {iteration}: current_atc_sum={current_atc_sum}, previous_atc_sum={previous_atc_sum}")
            if abs(current_atc_sum - previous_atc_sum) > 1000:  # 1 kW threshold
                temp_flag = False
                

        # Round down to integer values
        for border in atc_values:
            atc_values[border] = int(atc_values[border])

        # Determine final ATCs as the minimum of positive and negative ATCs
        final_atcs = {}
        for border in atc_values:
            final_atcs[border] = min(atc_values[border], negative_atcs.get(border, atc_values[border]))

        atc_results.append({
            "CNEC_ID": cnec_id,
            "PreFinal_ATC": atc_values,
            "Final_ATC": final_atcs
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

    logger.info("Calculating ATC values...")
    atc_results = calculate_atc(processed_cnec_data)

    # Save the ATC results to a JSON file
    output_file = "atc_results.json"
    try:
        with open(output_file, "w") as json_file:
            json.dump(atc_results, json_file, indent=4)
        logger.info(f"ATC results saved to {output_file}")
    except IOError as e:
        logger.error(f"Error saving ATC results to file: {e}")

if __name__ == "__main__":
    main()