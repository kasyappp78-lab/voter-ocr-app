import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

# --- IMPROVED EXTRACTION LOGIC ---
def extract_flexible_data(text):
    records = []
    # Split text into voter blocks (each voter usually starts with a serial number or Name)
    # We look for the patterns specifically used in Kerala Voter Lists
    
    # regex explanation: 
    # 'പേര്' followed by anything that isn't a newline
    # 'വയസ്സ്' followed by optional spaces/colon and then digits
    names = re.findall(r"പേര്[\s:]+([^\n#]+)", text)
    ages = re.findall(r"വയസ്സ്[\s:]+(\d+)", text)
    # Some lists use 'വീട്ടു നമ്പർ', others use 'വീട്ടുനമ്പർ'
    houses = re.findall(r"വീട്ടു[\s]*നമ്പർ[\s:]+([^\n]+)", text)
    
    # Zip them together based on the shortest list found to avoid index errors
    for n, a, h in zip(names, ages, houses):
        records.append({
            "Name": n.strip(),
            "Age": int(a),
            "House Number": h.strip()
        })
    return records

# --- UPDATED APP LOGIC ---
st.title("🗳️ Trikaripur Voter Data Tool")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    # Adding a 'Debug' view to see what the AI actually sees
    show_raw = st.checkbox("Show AI Raw Text (For Troubleshooting)")

    with st.spinner("AI is reading..."):
        images = convert_from_bytes(uploaded_file.read())
        all_data = []
        
        for i, img in enumerate(images):
            if i < 2: continue # Skip index
            
            # Use '--oem 3 --psm 6' for better table/block reading
            raw_text = pytesseract.image_to_string(img, lang='mal', config='--oem 3 --psm 6')
            
            if show_raw:
                st.text_area(f"Raw Data Page {i+1}", raw_text, height=100)
            
            page_records = extract_flexible_data(raw_text)
            all_data.extend(page_records)

    if all_data:
        df = pd.DataFrame(all_data)
        st.success(f"Found {len(df)} voters!")
        
        # Sorting
        df = df.sort_values(by="Age")
        st.dataframe(df)
        
        # Export
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download Excel", output.getvalue(), "Booth_List.xlsx")
    else:
        st.error("AI read the page but couldn't find the specific words 'പേര്' or 'വയസ്സ്'.")
        st.info("Try checking the 'Show AI Raw Text' box above to see what the AI is actually reading.")
