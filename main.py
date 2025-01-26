import requests
import pandas as pd

#Define JAO API URLs
BASE_URL = 'https://publicationtool.jao.eu/coreID/api'
FINAL_DOMAIN_URL = f"{BASE_URL}/IDCCB_finalComputation"
IDCCA_URL = f"{BASE_URL}/IDCCA_intracdayAtc"



def fetch_data(api_rul, params=None):
    """Fetch JSON data from the JAO API."""
    try:
        response = requests.get(api_rul, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"Error fetching data: {err}")
        return None
    

def parse_final_domain(data):
    """Parse the Final Domain data into a structured DataFrame."""
    cnec_list = []

    for cnec in data.get("cnecs", []):
        cnec_list.append({
            "id":cnec["id"],
            "RAM":cnec["RAM"],
            "PTDF": cnec["PTDF"],
            "presolved":cnec.get("presolved", False),
        })
    return pd.DataFrame(cnec_list)


def calculate_atc(final_domain_df, idcca_df):
    """Calculate ATC based on RAM and PTDF values."""
    atc_results = []
    for _, cnec in final_domain_df.iterrows():
        if not cnec["presolved"]:
            continue
        if cnec["RAM"] <= 0:
            atc_value = 0
        else:
            atc_value = cnec["PTDF"] / cnec["RAM"]
        atc_results.append({
            "CNEC_ID": cnec["id"],
            "ATC_PreFinal": atc_value,
            "ATC_Final": atc_value,
        })

    return  pd.DataFrame(atc_results)


def add_idcca_capacity(atc_df, idcca_df):
    """Add unused capacity from IDCCa results to finalize ATC."""
    for _, idcca in idcca_df.iterrows():
        matching_rows = atc_df["CNEC_ID"] == idcca["CNEC_ID"]
        atc_df.loc[matching_rows, "ATC_Final"] += idcca["Unused_Capacity"]
    return atc_df

def main():
    # Fetch data
    print("Fetching Final Domain data...")
    final_domain_data = fetch_data(FINAL_DOMAIN_URL)
    print("Fetching IDCCA data...")
    idcca_data = fetch_data(IDCCA_URL)  

    if not final_domain_data or not idcca_data:
        print("Error fetching data. Exiting...")
        return
    
    # Parse data
    print("Parsing Final Domain data...")
    final_domain_df = parse_final_domain(final_domain_data)
    print("Parsing IDCCa data...")
    idcca_df = pd.DataFrame(idcca_data)  # Adjust as per the API structure

    # Perform ATC calculation
    print("Calculating ATC values...")
    atc_df = calculate_atc(final_domain_df, idcca_df)

    # Add IDCCa unused capacity
    print("Adjusting ATC with IDCCa unused capacity...")
    atc_final_df = add_idcca_capacity(atc_df, idcca_df)

    # Output results
    print("Calculation complete. Final ATC values:")
    print(atc_final_df)
    atc_final_df.to_csv("final_atc_values.csv", index=False)
    print("Results saved to 'final_atc_values.csv'.")

if __name__ == "__main__":
    main()