import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

# Function to tokenize names for matching
def tokenize(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)  # Remove special characters
    return set(name.split())  # Return unique words in a set

# Function for token-based matching
def match_salesperson_codes(operator_name, master_list, threshold=90):
    if pd.isna(operator_name):
        return "APPROACH"

    operator_tokens = tokenize(operator_name)
    matched_codes = set()

    for _, row in master_list.iterrows():
        master_tokens = tokenize(row["Operator"])
        if len(master_tokens) == 0:
            continue
        
        common_words = operator_tokens.intersection(master_tokens)
        match_percentage = (len(common_words) / len(master_tokens)) * 100

        if match_percentage >= threshold:
            matched_codes.add(row["Salesperson Code"])

    return "/".join([code for code in matched_codes if pd.notna(code)]) if matched_codes else "APPROACH"

# Streamlit App
def main():
    st.title("🐐 Mapping Shortcut - LKA")

    # File upload for Vessel Data
    uploaded_vessel = st.file_uploader("Upload Vessel Data File (Excel)", type=["xlsx"])

    # File upload for Master List
    uploaded_master = st.file_uploader("Upload Master List File (Excel)- Database only ", type=["xlsx"])

    # Process data when files are uploaded
    if uploaded_vessel and uploaded_master:
        st.success("✅ Uploaded liao. wait pls...")

        # Load Vessel Data
        df = pd.read_excel(uploaded_vessel, sheet_name="report")

        # Load Master List
        df_master_list = pd.read_excel(uploaded_master, sheet_name="master list", usecols=[0, 1], names=["Operator", "Salesperson Code"])

        # Convert to lowercase for case-insensitive matching
        df["Operator"] = df["Operator"].astype(str).str.lower()
        df_master_list["Operator"] = df_master_list["Operator"].astype(str).str.lower()
        df_master_list["Salesperson Code"] = df_master_list["Salesperson Code"].astype(str)

        # Select required columns
        columns_needed = [
            "ETA", "Vessel Name", "Vessel Type", "Vessel IMO", "Operator", "Group Owner",
            "Registered Owner", "Last Bunkering Start Date", "Last Bunkering Location"
        ]
        filtered_df = df[columns_needed].copy()

        # Convert date columns
        filtered_df["ETA"] = pd.to_datetime(filtered_df["ETA"])
        filtered_df["Last Bunkering Start Date"] = pd.to_datetime(filtered_df["Last Bunkering Start Date"])

        # Filter ETA for vessels arriving in 5-12 days from today
        today = datetime.today()
        start_date = today + timedelta(days=5)
        end_date = today + timedelta(days=12)
        filtered_df = filtered_df[(filtered_df["ETA"] >= start_date) & (filtered_df["ETA"] <= end_date)]

        # Format dates as DD/MM/YY
        filtered_df["ETA"] = filtered_df["ETA"].dt.strftime("%d/%m/%y")
        filtered_df["Last Bunkering Start Date"] = filtered_df["Last Bunkering Start Date"].dt.strftime("%d/%m/%y")

        # Keep only specified vessel types
        vessel_types_to_keep = [
            "Vehicles Carrier", "Products Tanker", "Ore Carrier", "General Cargo Ship (Open Hatch)",
            "General Cargo Ship", "Drilling Rig, jack up", "Crude/Oil Products Tanker", "Crude Oil Tanker",
            "Chemical/Products Tanker", "Chemical Tanker", "Bulk Carrier", "Aggregates Carrier"
        ]
        filtered_df = filtered_df[filtered_df["Vessel Type"].isin(vessel_types_to_keep)].reset_index(drop=True)

        # Apply matching function
        filtered_df["Salesperson Code"] = filtered_df["Operator"].apply(lambda x: match_salesperson_codes(x, df_master_list))

        # Remove duplicate Operator names
        filtered_df = filtered_df.drop_duplicates(subset=["Operator"], keep="first")

        # Save the processed data
        output_file = "Filtered_Vessel_Data.xlsx"
        filtered_df.to_excel(output_file, index=False)

        # Allow the user to download the processed file
        with open(output_file, "rb") as file:
            st.download_button(
                label="📥 Download Processed Data",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success("✅ ok liao! Download your file above.")

if __name__ == "__main__":
    main()
