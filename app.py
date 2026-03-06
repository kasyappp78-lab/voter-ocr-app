import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.title("🗳️ Booth Analytics - Trikaripur")

uploaded_file = st.file_uploader("Upload Scanned PDF", type="pdf")

if uploaded_file:
    with st.status("AI is reading the Malayalam text...") as status:
        voter_records = []
        # Convert PDF to images
        images = convert_from_bytes(uploaded_file.read())
        
        for i, image in enumerate(images):
            if i < 2: continue # Skip maps
            # OCR using Malayalam pack
            text = pytesseract.image_to_string(image, lang='mal')
            
            # Extract data
            names = re.findall(r"പേര്[:\s]+([^\n]+)", text)
            ages = re.findall(r"വയസ്സ്[:\s]+(\d+)", text)
            houses = re.findall(r"വീട്ടു നമ്പർ[:\s]+([^\n]+)", text)
            
            for n, a, h in zip(names, ages, houses):
                voter_records.append({"Name": n.strip(), "Age": int(a), "House": h.strip()})
        status.update(label="Scanning Complete!", state="complete")

    if voter_records:
        df = pd.DataFrame(voter_records)
        st.dataframe(df.sort_values(by="Age"))
