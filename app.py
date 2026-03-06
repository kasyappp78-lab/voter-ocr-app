import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Trikaripur Voter Sorter", layout="wide")
st.title("🗳️ Booth Analytics: Trikaripur")

uploaded_file = st.file_uploader("Upload Scanned PDF", type="pdf")

if uploaded_file:
    # We use st.cache_data so it doesn't re-scan every time you change a sort option
    @st.cache_data
    def process_pdf(file_bytes):
        voter_records = []
        images = convert_from_bytes(file_bytes)
        for i, image in enumerate(images):
            if i < 2: continue # Skip first 2 pages
            text = pytesseract.image_to_string(image, lang='mal')
            
            # Extracting Name, Age, and House Number
            names = re.findall(r"പേര്[:\s]+([^\n]+)", text)
            ages = re.findall(r"വയസ്സ്[:\s]+(\d+)", text)
            houses = re.findall(r"വീട്ടു നമ്പർ[:\s]+([^\n]+)", text)
            
            for n, a, h in zip(names, ages, houses):
                voter_records.append({
                    "Name": n.strip(),
                    "Age": int(a),
                    "House Number": h.strip()
                })
        return voter_records

    # 1. Run the scanning
    with st.spinner("AI is reading Malayalam... This takes 1-2 minutes."):
        data = process_pdf(uploaded_file.read())
    
    if data:
        st.success(f"✅ Scanning Complete! Found {len(data)} voters.")
        df = pd.DataFrame(data)

        # --- THIS PART ADDS THE OPTIONS ---
        st.divider()
        st.header("🔍 Sort and Filter List")
        
        col1, col2 = st.columns(2)
        with col1:
            sort_order = st.selectbox("Sort Age Order", ["Youngest First", "Oldest First"])
        with col2:
            filter_org = st.radio("Quick Filter", ["None", "Balasangham (<18)", "SFI (18-25)", "Seniors (80+)"])

        # Apply Sorting
        is_ascending = True if sort_order == "Youngest First" else False
        df = df.sort_values(by="Age", ascending=is_ascending)

        # Apply Quick Filters
        if filter_org == "Balasangham (<18)":
            df = df[df['Age'] < 18]
        elif filter_org == "SFI (18-25)":
            df = df[(df['Age'] >= 18) & (df['Age'] <= 25)]
        elif filter_org == "Seniors (80+)":
            df = df[df['Age'] >= 80]

        # --- SHOW THE FINAL TABLE ---
        st.dataframe(df, use_container_width=True)

        # --- DOWNLOAD OPTION ---
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            label="📥 Download this sorted list (Excel)",
            data=output.getvalue(),
            file_name="Sorted_Booth_List.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No data found. Try a different page or check the PDF quality.")
