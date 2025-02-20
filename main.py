import requests
from urllib.parse import urlencode
import logging
import json

# Define constants and configurations
FROM_UTC = "2025-02-20T00:00:00.000Z"
TO_UTC = "2025-02-20T02:00:00.000Z"
FINAL_URL = "https://publicationtool.jao.eu/coreID/api/data/IDCCB_finalComputation"

PARAMS_FINAL = {
    "Filter": '{"Presolved":true}',
    "Skip": 0,
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
    RAM_0 = [item['ram'] for item in cnec_data.values()]

    PTDF_0 = [
        [
            item['ptdf_differences'].get('atcz', 0),
            item['ptdf_differences'].get('atde', 0),
            item['ptdf_differences'].get('athu', 0),
            item['ptdf_differences'].get('atsi', 0),
            item['ptdf_differences'].get('bede', 0),
            item['ptdf_differences'].get('befr', 0),
            item['ptdf_differences'].get('benl', 0),
            item['ptdf_differences'].get('czat', 0),
            item['ptdf_differences'].get('czde', 0),
            item['ptdf_differences'].get('czpl', 0),
            item['ptdf_differences'].get('czsk', 0),
            item['ptdf_differences'].get('deat', 0),
            item['ptdf_differences'].get('debe', 0),
            item['ptdf_differences'].get('decz', 0),
            item['ptdf_differences'].get('defr', 0),
            item['ptdf_differences'].get('denl', 0),
            item['ptdf_differences'].get('depl', 0),
            item['ptdf_differences'].get('frbe', 0),
            item['ptdf_differences'].get('frde', 0),
            item['ptdf_differences'].get('hrhu', 0),
            item['ptdf_differences'].get('hrsi', 0),
            item['ptdf_differences'].get('huat', 0),
            item['ptdf_differences'].get('huhr', 0),
            item['ptdf_differences'].get('huro', 0),
            item['ptdf_differences'].get('husi', 0),
            item['ptdf_differences'].get('husk', 0),
            item['ptdf_differences'].get('nlbe', 0),
            item['ptdf_differences'].get('nlde', 0),
            item['ptdf_differences'].get('plcz', 0),
            item['ptdf_differences'].get('plde', 0),
            item['ptdf_differences'].get('plsk', 0),
            item['ptdf_differences'].get('rohu', 0),
            item['ptdf_differences'].get('siat', 0),
            item['ptdf_differences'].get('sihr', 0),
            item['ptdf_differences'].get('sihu', 0),
            item['ptdf_differences'].get('skcz', 0),
            item['ptdf_differences'].get('skhu', 0),
            item['ptdf_differences'].get('skpl', 0)
        ]
        for item in cnec_data.values()
    ]
    
    # Initialize ATC_0 with the correct size (it should match the length of PTDF_0)
    ATC_0 = [0] 
    difference = 1
    while difference > 0.001:
        # Separate positive and negative RAM and PTDF
        positive_PTDF_final = []
        positive_RAM = []
        negative_RAM = []
        negative_PTDF = []

        for i in range(len(PTDF_0)):
            positive_PTDF = [ptdf for ptdf in PTDF_0[i] if ptdf > 0]
            positive_PTDF_final.append(positive_PTDF)
            if RAM_0[i] > 0:
                positive_RAM.append(RAM_0[i])
           

        # Process Negative RAM and PTDF
        if negative_RAM:
            deno_list = []
            for neg_ptdf in negative_PTDF:
                deno = sum([ptdf ** 2 for ptdf in neg_ptdf])
                deno_list.append(deno)

            neg_ATC = []
            for i in range(len(negative_PTDF)):
                # Check for division by zero
                if deno_list[i] != 0:
                    neg_ATC.append([(negative_RAM[i] * (negative_PTDF[i][j] / deno_list[i])) for j in range(len(negative_PTDF[i]))])
                else:
                    neg_ATC.append([0 for _ in range(len(negative_PTDF[i]))])  # Assign zero if deno is zero

            # Scale negative ATC
            sf_list = []
            for i in range(len(neg_ATC)):
                sf_deno = sum([negative_PTDF[i][j] * neg_ATC[i][j] for j in range(len(negative_PTDF[i]))])
                if sf_deno != 0:
                    sf_list.append(negative_RAM[i] / sf_deno)
                else:
                    sf_list.append(0)  # Prevent division by zero

            final_sf = max(sf_list)
            negative_ATC = [min(neg_ATC[i]) * final_sf for i in range(len(neg_ATC))]

            ATC_0 = negative_ATC

        max_RAM = [max(0, ram) for ram in RAM_0]
        ATC_ini_mul = []
        for i in range(len(RAM_0)):
            calc = sum(PTDF_0[i][j] * ATC_0[i] for j in range(len(PTDF_0[i])))
            ATC_ini_mul.append(calc)

        RAM_ini = [max(0, max_RAM[i] - ATC_ini_mul[i]) for i in range(len(RAM_0))]
        ATC_1d = []
        for i in range(len(positive_PTDF_final)):
            ATC_1d.append([RAM_ini[i] / positive_PTDF_final[i][j] if positive_PTDF_final[i][j] != 0 else 0 for j in range(len(positive_PTDF_final[i]))])

        ATC_min = [min(ATC_1d[i]) for i in range(len(ATC_1d))]
        added_ATC = [ATC_0[i] + ATC_min[i] for i in range(len(ATC_min))]
        max_ATC = 1000
        limited_ATC = [min(max_ATC, added_ATC[i]) for i in range(len(added_ATC))]

        # Calculate the difference to check for convergence
        sum_of_new_ATC = sum(limited_ATC)
        sum_of_old_ATC = sum(ATC_0)
        difference = abs(sum_of_new_ATC - sum_of_old_ATC)

        ATC_0 = limited_ATC
        RAM_0 = RAM_ini

    return ATC_0

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






    