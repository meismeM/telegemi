"""# api/textbook_processor.py
import PyPDF2

TEXTBOOKS = {}

def load_textbook(textbook_id, filename):
    try:
        # [!HIGHLIGHT!] Modified filepath to look in the 'api' folder directly
        filepath = f"api/{filename}"
        with open(filepath, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text()
            TEXTBOOKS[textbook_id] = text_content
            print(f"Textbook '{textbook_id}' loaded successfully from '{filepath}'")
    except Exception as e:
        print(f"Error loading textbook '{textbook_id}': {e}")

def get_textbook_content(textbook_id):
    return TEXTBOOKS.get(textbook_id)

# --- Example usage (for testing - remove or comment out for deployment) ---
# if __name__ == "__main__":
#     load_textbook("math9", "math_grade9.pdf") # Make sure math_grade9.pdf is in api/textbooks/
#     if "math9" in TEXTBOOKS:
#         print(f"Textbook 'math9' loaded. First 100 chars: {TEXTBOOKS['math9'][:100]}")
#     else:
#         print("Textbook 'math9' not loaded.")
"""
import PyPDF2
import os

TEXTBOOKS = {}

def load_textbook(textbook_id, filename):
    try:
        filepath = f"api/{filename}"

        # [!NEW LOGGING!] Check if the file exists before opening
        print(f"Attempting to load textbook '{textbook_id}' from path: '{filepath}'")
        if not os.path.exists(filepath):
            print(f"ERROR: File '{filepath}' does not exist!") # Log if file is not found
            return # Exit function if file not found

        with open(filepath, 'rb') as pdf_file:
            print(f"File '{filepath}' opened successfully.") # Log if file opens

            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_content = [] # List to store page content as dictionaries
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content = page.extract_text()
                pages_content.append({"page_number": page_num + 1, "text": text_content}) # Store page number and text
            TEXTBOOKS[textbook_id] = pages_content # Store list of pages
            print(f"Textbook '{textbook_id}' loaded successfully from '{filepath}' with page-wise content.")
    except Exception as e:
        print(f"Error loading textbook '{textbook_id}': {e}")

def get_textbook_content(textbook_id):
    return TEXTBOOKS.get(textbook_id) # Corrected to return page-wise content
