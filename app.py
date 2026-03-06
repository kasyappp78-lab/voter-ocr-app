import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO
from PIL import ImageOps, ImageFilter

# SETPAGE CONFIG
st.set_page_config(page_title="Trikaripur Voter Sorter", layout="wide")

st.title("🗳️ Booth Analytics: Trikaripur (Scanned PDF Mode)")
st.info("This app uses OCR to read scanned Malayalam text. Processing may take 5-10 seconds per page.")

# --- STEP 1: FLEXIBLE EXTRACTION FUNCTION ---
def extract_voter_data_flexible(text):
    voters = []
    lines = text.split('\n')
    
    current_name = None
    current_house = None

    for line in lines:
        # Look for Name (Flexible for OCR errors in 'പേര്')
        name_match = re.search(r"[പവേ]\s*[രർ]\s*്\s*[:\s]+([^\n#]+)", line)
        if name_match:
            current_name = name_match.group(1).strip()

        # Look for House Number (Flexible for 'വീട്ടു നമ്പർ')
        house_match = re.search(r"വീ\s*ട\s*്\s*ട\s*ു\s*ന\s*ം\s*പ\s*ർ\s*[:\s]+([^\n]+)", line)
        if house_match:
            current_house = house_match.group(1).strip()

        # Look for Age (The anchor for a complete record)
        age_match = re.search(r"വയ\s*[സശ]\s*്\s*[സശ]\s*്\s*[:\s]+(\d+)", line)
        if age_match:
            age_val = int(age_match.group(1))
            if current_name:
                voters.append({
                    "Name": current_name,
                    "Age": age_val,
                    "House": current_house if current_house else "Not Found"
                })
                # Reset for next voter box
                current_name, current_house = None, None
    return voters

# --- STEP 2: UI & UPLOAD ---
uploaded_file = st.file_uploader("Upload the Scanned Booth PDF", type="pdf")

if uploaded_file:
    # Option to see what the AI is "seeing"
    debug_mode = st.checkbox("Show AI Raw Text (Use this if no data is found)")

    if st.button("Start AI Scanning"):
        with st.status("AI is processing pages... This will take a moment.") as status:
            all_voters = []
            
            # Convert PDF to Images
            # Note: poppler_path is not needed on Streamlit Cloud
            images = convert_from_bytes(uploaded_file.read())
            
            for i, image in enumerate(images):
                if i < 2: continue # Skip cover and map pages
                
                # --- IMAGE PRE-PROCESSING (Crucial for Scans) ---
                # Convert to Grayscale
                image = image.convert('L') 
                # Increase contrast to make text pop
                image = ImageOps.autocontrast(image)
                
                # Run OCR with Malayalam Language
                # psm 6 assumes a uniform block of text (voter boxes)
                raw_text = pytesseract.image_to_string(image, lang='mal', config='--psm 6')
                
                if debug_mode:
                    st.text_area(f"Raw Text Page {i+1}", raw_text, height=150)
                
                # Extract structured data
                page_data = extract_voter_data_flexible(raw_text)
                all_data_len = len(page_data)
                all_voters.extend(page_data)
                
                st.write(f"✅ Page {i+1}: Found {all_data_len} voters")
            
            status.update(label="Scanning Complete!", state="complete")

        # --- STEP 3: DISPLAY & SORT ---
        if all_voters:
            df = pd.DataFrame(all_voters)
            st.divider()
            
            # Interactive Sorting
            col1, col2 = st.columns(2)
            with col1:
                sort_val = st.radio("Age Sorting", ["Youngest to Oldest", "Oldest to Youngest"])
            with col2:
                search = st.text_input("Search Name/House Number")

            # Apply Logic
            df = df.sort_values(by="Age", ascending=(sort_val == "Youngest to Oldest"))
            if search:
                df = df[df['Name'].str.contains(search, case=False) | df['House'].str.contains(search, case=False)]

            st.success(f"Successfully compiled {len(df)} voters.")
            st.dataframe(df, use_container_width=True)

            # Export to Excel
            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button(
                label="📥 Download Sorted Excel",
                data=output.getvalue(),
                file_name="Trikaripur_Sorted_List.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No voter data could be identified. Check 'Show AI Raw Text' to see if OCR is failing.")
