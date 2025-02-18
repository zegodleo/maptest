import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import time  # Import time module for real-time tracking

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
    start_time = time.time()  # Capture start time dynamically
    progress_bar = st.progress(0)
    time_remaining_text = st.empty()
    status_text = st.empty()

    # Layout for instructions on the right side
    st.sidebar.title("📌 Instructions")
    st.sidebar.write("1️⃣ Upload the **Vessel Data** Excel file (Sheet: report).")
    st.sidebar.write("2️⃣ Upload the **Master List** Excel file (Sheet: master list).")
    st.sidebar.write("3️⃣ Wait for the processing to complete.")
    st.sidebar.write("4️⃣ Click the **Download Processed Data** button.")
    st.sidebar.write("🔹 Ensure files are in the correct format before uploading.")
    st.title("🐐 Mapping Shortcut - LKA")

    # File upload for Vessel Data
    uploaded_vessel = st.file_uploader("Upload Vessel Data File (Excel)", type=["xlsx"])
    uploaded_master = st.file_uploader("Upload Master List File (Excel)- Database only ", type=["xlsx"])

    if uploaded_vessel and uploaded_master:
        st.success("✅ Uploaded liao. wait pls...")
        total_steps = 7  # Total processing steps
        step = 0  # Track current step

        def update_progress(step_desc):
            nonlocal step
            step += 1
            elapsed_time = time.time() - start_time
            avg_time_per_step = elapsed_time / step if step > 0 else 0
            estimated_total_time = avg_time_per_step * total_steps
            time_left = max(0, int(estimated_total_time - elapsed_time))
            progress_bar.progress(int((step / total_steps) * 100))
            time_remaining_text.text(f"⏳ {step_desc} | Estimated Time Left: {time_left} sec")
            status_text.text(step_desc)

        # Load Vessel Data
        df = pd.read_excel(uploaded_vessel, sheet_name="report")
        update_progress("Processing Vessel Data...")

        # Load Master List
        df_master_list = pd.read_excel(uploaded_master, sheet_name="master list", usecols=[0, 1], names=["Operator", "Salesperson Code"])
        update_progress("Processing Master List...")

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
        update_progress("Filtering Data...")

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
        update_progress("Filtering Vessel Types...")

        # Apply matching function
        filtered_df["Salesperson Code"] = filtered_df["Operator"].apply(lambda x: match_salesperson_codes(x, df_master_list))
        update_progress("Matching Salesperson Codes...")

        # Remove duplicate Operator names
        filtered_df = filtered_df.drop_duplicates(subset=["Operator"], keep="first")
        update_progress("Finalizing Data...")

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

        progress_bar.progress(100)
        time_remaining_text.text("✅ Processing Completed!")
        status_text.text("✅ Processing Complete! Ready for Download.")
        st.success("✅ ok liao! Download your file above.")

if __name__ == "__main__":
    main()
