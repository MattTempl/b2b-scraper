
import os
import json
import gspread

def test_sheet_write():
    print("Testing sheet write on Render...")
    try:
        # Load creds from env
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            print("Error: GOOGLE_CREDENTIALS missing")
            return
            
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)
        
        # Open sheet
        sheet_name = "B2B Scraper Results"
        print(f"Opening sheet: {sheet_name}")
        sh = gc.open(sheet_name)
        ws = sh.sheet1
        
        # Write dummy data
        print("Writing to A1...")
        ws.update([['Timestamp', 'Status'], ['Test', 'Hello from Render!']], 'A1')
        print("Success! Check your sheet.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sheet_write()
