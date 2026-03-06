import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO
from PIL import ImageOps, ImageFilter

# Page Configuration
st.set_page_config(page_title="Trikaripur Voter Analytics", layout="wide")

st.title("🗳️ Booth Data Tool: Trikaripur")
st.markdown("---")

# --- STEP 1: FUZZY EXTRACTION LOGIC ---
def extract_voter_data_fuzzy(text):
    voters = []
    lines = text.split('\n')
    
    current_name = None
    current_house = None

    for line in lines:
        # 1. FUZZY NAME: Matches 'പേര്' even if start/end characters are slightly off
        name_match = re.search(r"(?:പേ|വേ|പെ|മേ|ര|ർ)\s*[രർ]\s*്\s*[:\s]+([^\n#]+)", line)
        if name_match:
            current_name = name_match.group(1).strip()

        # 2. FUZZY HOUSE NO: Matches 'വീട്ടു നമ്പർ' with flexible spacing
        house_match = re.search(r"(?:വീ|വി)\s*[ടട്ട]\s*്\s*[ടട്ട]\s*ു\s*ന\s*ം\s*പ\s*ർ\s*[:\s]+([^\n]+)", line)
        if house_match:
            current_house = house_match.group(1).strip()

        # 3. FUZZY AGE (The Anchor): Matches 'വയസ്സ്' or any similar shape followed by digits
        age_match = re.search(r"(?:വയ|ഖയ|വിയ|യ|സ)\s*[സശ]\s*്\s*[സശ]\s*്\s*[:\s]+(\d+)", line)
        if age_match:
            try:
                age_val = int(age_match.group(1))
                # Only add if we at least have a Name to pair it with
                if current_name:
                    voters.append({
                        "Name": current_name,
                        "Age": age_val,
                        "House": current_house if current_house else "Unknown"
                    })
                    # Reset variables to look for the next person
                    current_name, current_house = None, None
            except:
                continue
                
    return voters
    
# --- STEP 2: UPLOAD & PROCESSING ---
uploaded_file = st.file_uploader("Upload Scanned Booth PDF", type="pdf")

if uploaded_file:
    # Sidebar Controls
    st.sidebar.header("Settings")
    debug_mode = st.sidebar.checkbox("Show AI Raw Text")
    
    if st.button("🚀 Start AI Analysis"):
        with st.status("AI is reading the scan... This may take 2-4 minutes.") as status:
            all_voters = []
            # Convert PDF to Images
            images = convert_from_bytes(uploaded_file.read())
            
            for i, image in enumerate(images):
                if i < 2: continue # Skip map pages
                
                # Image Pre-processing for better OCR
                image = image.convert('L') 
                image = ImageOps.autocontrast(image)
                
                # OCR Call - using Malayalam language
                raw_text = pytesseract.image_to_string(image, lang='mal', config='--oem 3 --psm 6')
                
                if debug_mode:
                    st.text_area(f"Page {i+1} Raw Text", raw_text, height=100)
                
                # Extract Data
                page_data = extract_voter_data_fuzzy(raw_text)
                all_voters.extend(page_data)
                st.write(f"Processed Page {i+1}: Found {len(page_data)} records.")
            
            status.update(label="Scanning Complete!", state="complete")

        # --- STEP 3: SORTING & DISPLAY ---
        if all_voters:
            df = pd.DataFrame(all_voters)
            
            st.header("📊 Sorted Voter List")
            
            # Interactive Sorting
            sort_order = st.radio("Order by Age", ["Youngest First", "Oldest First"])
            df = df.sort_values(by="Age", ascending=(sort_order == "Youngest First"))
            
            # Organizational Filters
            st.subheader("Quick Filters")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Balasangham Segment (<18)"):
                    df = df[df['Age'] < 18]
            with col2:
                if st.button("SFI Segment (18-25)"):
                    df = df[(df['Age'] >= 18) & (df['Age'] <= 25)]
            with col3:
                if st.button("Clear Filters"):
                    pass # Reset happens on next rerun

            st.dataframe(df, use_container_width=True)

            # --- STEP 4: EXCEL DOWNLOAD ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Age-Sorted Excel",
                data=output.getvalue(),
                file_name="Trikaripur_Booth_Sorted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("AI couldn't find Name/Age patterns. Check 'Show AI Raw Text' to see if OCR is working.")
