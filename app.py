import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

# --- IMPROVED EXTRACTION LOGIC ---
def extract_voter_data_smart(text):
    voters = []
    # Split the text into lines to process voter blocks
    lines = text.split('\n')
    
    current_name = None
    current_age = None
    current_house = None

    for line in lines:
        # 1. Flexible Name Search: Look for 'പേര്' with any symbols/spaces
        name_match = re.search(r"പേ\s*ര\s*്\s*[:\s]+([^\n]+)", line)
        if name_match:
            current_name = name_match.group(1).strip()

        # 2. Flexible House No: Look for 'വീട്ടു' and 'നമ്പർ'
        house_match = re.search(r"വീ\s*ട\s*്\s*ട\s*ു\s*ന\s*ം\s*പ\s*ർ\s*[:\s]+([^\n]+)", line)
        if house_match:
            current_house = house_match.group(1).strip()

        # 3. Flexible Age Search: Look for the number after 'വയസ്സ്' 
        # Even if 'വയസ്സ്' is misread, we look for the pattern 'Age: XX'
        age_match = re.search(r"വയ\s*സ\s*്\s*സ\s*്\s*[:\s]+(\d+)", line)
        if age_match:
            current_age = int(age_match.group(1))
            
            # Once we have an Age, we assume this voter block is complete
            if current_name:
                voters.append({
                    "Name": current_name,
                    "Age": current_age,
                    "House": current_house if current_house else "N/A"
                })
                # Reset for next voter
                current_name, current_age, current_house = None, None, None
                
    return voters
