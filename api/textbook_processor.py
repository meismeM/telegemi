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
        with open(filepath, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content = page.extract_text()
                pages_content.append({"page_number": page_num + 1, "text": text_content})
            TEXTBOOKS[textbook_id] = pages_content
            print(f"Textbook '{textbook_id}' loaded successfully from '{filepath}' with page-wise content.")
    except Exception as e:
        print(f"Error loading textbook '{textbook_id}': {e}")

def get_textbook_content(textbook_id):
    return TEXTBOOKS.get(textbook_id)

def get_text_from_pages(textbook_id, page_numbers): # Helper function to get combined text from specific pages
    textbook_pages = get_textbook_content(textbook_id)
    if not textbook_pages:
        return ""
    combined_text = ""
    for page_data in textbook_pages:
        if page_data["page_number"] in page_numbers:
            combined_text += page_data["text"] + "\n\n"
    return combined_text

def search_concept_pages(textbook_id, concept): # Helper function to find pages containing a concept
    textbook_pages = get_textbook_content(textbook_id)
    if not textbook_pages:
        return []

    concept_pages = []
    for page_data in textbook_pages:
        if concept.lower() in page_data["text"].lower():
            concept_pages.append(page_data["page_number"])
    return concept_pages
