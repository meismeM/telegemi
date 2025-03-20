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

TEXTBOOK_CACHE = {}  # Dictionary to cache loaded textbooks in memory (using textbook_id as key)

def load_textbook(textbook_id, filename):
    """Loads textbook content from PDF and caches it."""
    filepath = f"api/{filename}" # Assuming PDFs are still in api/

    print(f"Loading textbook '{textbook_id}' from '{filepath}'...") # Log loading start
    try:
        with open(filepath, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content = page.extract_text()
                pages_content.append({"page_number": page_num + 1, "text": text_content})
            TEXTBOOK_CACHE[textbook_id] = pages_content # Cache in global dictionary
            print(f"Textbook '{textbook_id}' loaded and cached successfully.") # Log loading success
            return pages_content # Return the content
    except Exception as e:
        print(f"Error loading textbook '{textbook_id}': {e}")
        return None # Return None on error


def get_textbook_content(textbook_id):
    """Returns textbook content from cache or loads it if not cached."""
    if textbook_id in TEXTBOOK_CACHE:
        print(f"Textbook '{textbook_id}' found in cache.") # Log cache hit
        return TEXTBOOK_CACHE[textbook_id] # Return from cache
    else:
        print(f"Textbook '{textbook_id}' not in cache. Loading from file...") # Log cache miss
        if textbook_id == "economics9": # Load based on textbook_id
            return load_textbook(textbook_id, "economics9.pdf") # Load economics textbook
        elif textbook_id == "history9":
            return load_textbook(textbook_id, "history9.pdf") # Load history textbook
        else:
            print(f"Error: Unknown textbook_id: '{textbook_id}'") # Log unknown textbook ID
            return None


def get_text_from_pages(textbook_id, page_numbers):
    # ... (rest of your get_text_from_pages function - no changes needed) ...
    pass # Placeholder - keep your existing function

def search_concept_pages(textbook_id, concept):
    # ... (rest of your search_concept_pages function - no changes needed) ...
    pass # Placeholder - keep your existing function
