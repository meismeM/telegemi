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
'''import PyPDF2
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
    return concept_pages'''


# api/textbook_processor.py
import json
import os

TEXTBOOK_INDEX_DIR = "api/textbook_index" # Directory where index files are stored
TEXTBOOK_CACHE = {}  # Dictionary to cache loaded textbook indices in memory

def load_textbook_index(textbook_id):
    """Loads textbook index from JSON file and caches it."""
    index_filepath = os.path.join(TEXTBOOK_INDEX_DIR, f"{textbook_id}_index.json")
    print(f"Loading index for textbook '{textbook_id}' from '{index_filepath}'...") # Log loading start
    try:
        with open(index_filepath, 'r') as infile:
            index_data = json.load(infile)
            TEXTBOOK_CACHE[textbook_id] = index_data # Cache index data
            print(f"Index for textbook '{textbook_id}' loaded and cached successfully.") # Log loading success
            return index_data
    except FileNotFoundError:
        print(f"Error: Index file not found for textbook '{textbook_id}' at '{index_filepath}'") # Log file not found error
        return None
    except json.JSONDecodeError as e:
        print(f"Error: JSONDecodeError loading index for '{textbook_id}' from '{index_filepath}': {e}") # Log JSON decode error
        return None
    except Exception as e:
        print(f"Error loading index for textbook '{textbook_id}': {e}") # General error log
        return None


def get_textbook_content(textbook_id):
    """Returns textbook content (index data) from cache or loads it if not cached."""
    if textbook_id in TEXTBOOK_CACHE:
        print(f"Index for textbook '{textbook_id}' found in cache.") # Log cache hit
        return TEXTBOOK_CACHE[textbook_id] # Return from cache
    else:
        print(f"Index for textbook '{textbook_id}' not in cache. Loading from file...") # Log cache miss
        return load_textbook_index(textbook_id) # Load from file


def get_text_from_pages(textbook_id, page_numbers):
    """Retrieves combined text from specified pages using the loaded index."""
    textbook_index = get_textbook_content(textbook_id) # Get index data from cache or load
    if not textbook_index:
        return ""
    combined_text = ""
    for page_data in textbook_index["chunks"]: # Access 'chunks' from index data
        if page_data["page_number"] in page_numbers:
            combined_text += page_data["text"] + "\n\n"
    return combined_text


def search_concept_pages(textbook_id, concept):
    """Searches for a concept in the textbook index and returns page numbers."""
    textbook_index = get_textbook_content(textbook_id) # Get index data from cache or load
    if not textbook_index:
        return []

    concept_pages = []
    for page_data in textbook_index["chunks"]: # Access 'chunks' from index data
        if concept.lower() in page_data["text"].lower():
            concept_pages.append(page_data["page_number"])
    return concept_pages
