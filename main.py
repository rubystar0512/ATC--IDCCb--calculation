import requests
from urllib.parse import urlencode
import logging
import json

# Define constants and configurations
FROM_UTC = "2025-02-20T00:00:00.000Z"
TO_UTC = "2025-02-20T01:00:00.000Z"
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
            item['ptdf_differences'].get('atcz', None),
            item['ptdf_differences'].get('atde', None),
            item['ptdf_differences'].get('athu', None),
            item['ptdf_differences'].get('atsi', None),
            item['ptdf_differences'].get('bede', None),
            item['ptdf_differences'].get('befr', None),
            item['ptdf_differences'].get('benl', None),
            item['ptdf_differences'].get('czat', None),
            item['ptdf_differences'].get('czde', None),
            item['ptdf_differences'].get('czpl', None),
            item['ptdf_differences'].get('czsk', None),
            item['ptdf_differences'].get('deat', None),
            item['ptdf_differences'].get('debe', None),
            item['ptdf_differences'].get('decz', None),
            item['ptdf_differences'].get('defr', None),
            item['ptdf_differences'].get('denl', None),
            item['ptdf_differences'].get('depl', None),
            item['ptdf_differences'].get('frbe', None),
            item['ptdf_differences'].get('frde', None),
            item['ptdf_differences'].get('hrhu', None),
            item['ptdf_differences'].get('hrsi', None),
            item['ptdf_differences'].get('huat', None),
            item['ptdf_differences'].get('huhr', None),
            item['ptdf_differences'].get('huro', None),
            item['ptdf_differences'].get('husi', None),
            item['ptdf_differences'].get('husk', None),
            item['ptdf_differences'].get('nlbe', None),
            item['ptdf_differences'].get('nlde', None),
            item['ptdf_differences'].get('plcz', None),
            item['ptdf_differences'].get('plde', None),
            item['ptdf_differences'].get('plsk', None),
            item['ptdf_differences'].get('rohu', None),
            item['ptdf_differences'].get('siat', None),
            item['ptdf_differences'].get('sihr', None),
            item['ptdf_differences'].get('sihu', None),
            item['ptdf_differences'].get('skcz', None),
            item['ptdf_differences'].get('skhu', None),
            item['ptdf_differences'].get('skpl', None)
        ]
        for item in cnec_data.values()
    ]
    
    ATC_0 = [0] * len(PTDF_0)

    difference = 1
    positive_PTDF = []
    positive_PTDF_final = []
    positive_RAM = []
    negative_RAM = []
    for i in range(0, len(PTDF_0)):
        for j in range(0,  len(PTDF_0[i])):
            if PTDF_0[i][j] > 0:
                positive_PTDF.append(PTDF_0[i][j])
        positive_PTDF_final.append(positive_PTDF)
        positive_PTDF = []

    pos_PTDF = []
    neg_PTDF = []
    pos_ATC = []
    neg_ATC = []
    for i in range(0, len(RAM_0)):
        if RAM_0[i] > 0:
            positive_RAM.append(RAM_0[i])
            pos_PTDF.append(positive_PTDF_final[i])
            pos_ATC.append(ATC_0[i])
        else:
            negative_RAM.append(RAM_0[i])
            neg_PTDF.append(positive_PTDF_final[i])
            neg_ATC.append(ATC_0[i])

    contains_negative_RAM = False
    for i in range(0, len(RAM_0)):
        if RAM_0[i] <  0:
            contains_negative_RAM = True
    if contains_negative_RAM == True:
        deno = 0
        deno_list = []
        for i in range(0, len(neg_PTDF)):
            for j in range(0, len(neg_PTDF[i])):
                deno = deno + neg_PTDF[i][j] ** 2
            deno_list.append(deno)
            deno = 0


        neg_ATC = []
        neg_ATC_final = []
        neg_ATC_final_min = []
        for i in range(0, len(neg_PTDF)):
            for j in range(0, len(neg_PTDF[i])):
                neg_ATC.append((neg_PTDF[i][j] / deno_list[i]) * negative_RAM[i])
            neg_ATC_final.append(neg_ATC)
            neg_ATC_final_min.append(min(neg_ATC))
            neg_ATC = []

        sf_deno = 0
        sf_list = []
        for i in range(0, len(neg_ATC_final)):
            for j in range(0 , len(neg_ATC_final[i])):
                sf_deno = sf_deno +  neg_PTDF[i][j] * neg_ATC_final[i][j]

            sf = negative_RAM[i] / sf_deno
            sf_list.append(sf)
            sf_deno = 0

        final_sf = max(sf_list)

        negative_ATC = []
        for i in range(0 , len(neg_ATC_final_min)):
            negative_ATC.append(neg_ATC_final_min[i] * final_sf)

        final_negative_ATC = round(min(negative_ATC))

    non_negative_ptdf_1d = []
    non_negative_ptdf_2d = []

    for i in range(0, len(PTDF_0)):
        for j in range(0, len(PTDF_0[i])):
            if PTDF_0[i][j] < 0:
                non_negative_ptdf_1d.append(0)
            else:
                non_negative_ptdf_1d.append(PTDF_0[i][j])
        non_negative_ptdf_2d.append(non_negative_ptdf_1d)
        non_negative_ptdf_1d = []


    while difference > 0.001:
        max_RAM = []
        for i in range(0, len(RAM_0)):
            if RAM_0[i] > 0:
                max_RAM.append(RAM_0[i])
            else:
                max_RAM.append(0)

        calc = 0
        ATC_ini_mul = []
        RAM_ini = []

        for i in range(0 , len(non_negative_ptdf_2d)):
            for j in range(0, len(non_negative_ptdf_2d[i])):
                calc = calc + non_negative_ptdf_2d[i][j] * ATC_0[i]
            ATC_ini_mul.append(calc)
            calc = 0

        for i in range(0, len(max_RAM)):
            if max_RAM[i] - ATC_ini_mul[i] < 0 :
                RAM_ini.append(0)

            else:
                RAM_ini.append(max_RAM[i] - ATC_ini_mul[i])
        zero = []

        for i in range(0,len(ATC_0)):
            zero.append(0)
        if RAM_ini == zero:
            break

        ATC_1d = []
        ATC_2d = []
        ATC_min = []
        for i in range(0, len(positive_PTDF_final)):
            for j in range(0, len(positive_PTDF_final[i])):
                if RAM_ini[i] == 0 and positive_PTDF_final[i][j] == 0:
                    ATC_1d.append(0)
                else:
                    ATC_1d.append(RAM_ini[i]/positive_PTDF_final[i][j])
            ATC_2d.append(ATC_1d)
            ATC_1d = []

        for i in range(0, len(ATC_2d)):
            ATC_min.append(min(ATC_2d[i]))

        added_ATC = []

        for i in range(0, len(ATC_min)):
            added_ATC.append(ATC_0[i] + ATC_min[i])

        limited_ATC = []
        if max_ATC != 0:
            for i in range(0, len(added_ATC)):
                if added_ATC[i] > max_ATC:
                    limited_ATC.append(max_ATC)
                else:
                    limited_ATC.append(added_ATC[i])
        else:
            limited_ATC = added_ATC

        sum_of_new_ATC = 0
        sum_of_old_ATC = 0
        for i in range(0, len(limited_ATC)):
            sum_of_new_ATC = sum_of_new_ATC + limited_ATC[i]

        for i in range(0, len(ATC_0)):
            sum_of_new_ATC = sum_of_new_ATC + ATC_0[i]

        difference = sum_of_new_ATC - sum_of_old_ATC
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






    