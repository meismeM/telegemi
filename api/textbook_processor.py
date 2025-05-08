# api/textbook_processor.py
import json
import os
from typing import List, Dict, Optional, Any

TEXTBOOK_INDEX_DIR = "api/textbook_index" # Directory where index files are stored
TEXTBOOK_CACHE: Dict[str, Dict[str, Any]] = {}  # Cache for loaded textbook indices

def load_textbook_index(textbook_id: str) -> Optional[Dict[str, Any]]:
    """Loads a textbook index from a JSON file and caches it."""
    if not os.path.exists(TEXTBOOK_INDEX_DIR):
        print(f"Error: Textbook index directory '{TEXTBOOK_INDEX_DIR}' does not exist.")
        return None

    index_filename = f"{textbook_id}_index.json"
    index_filepath = os.path.join(TEXTBOOK_INDEX_DIR, index_filename)
    
    # print(f"Attempting to load index for textbook '{textbook_id}' from '{index_filepath}'...")
    try:
        with open(index_filepath, 'r', encoding='utf-8') as infile:
            index_data = json.load(infile)
            TEXTBOOK_CACHE[textbook_id] = index_data # Cache the loaded index
            # print(f"Index for textbook '{textbook_id}' loaded and cached successfully.")
            return index_data
    except FileNotFoundError:
        print(f"Error: Index file not found for textbook '{textbook_id}' at '{index_filepath}'. "
              f"Run preprocess_textbooks.py if you haven't.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: JSONDecodeError loading index for '{textbook_id}' from '{index_filepath}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading index for textbook '{textbook_id}': {e}")
        return None


def get_textbook_data(textbook_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns textbook index data (which includes chunks of text).
    Loads from file and caches if not already in memory.
    """
    if textbook_id in TEXTBOOK_CACHE:
        # print(f"Index for textbook '{textbook_id}' found in cache.")
        return TEXTBOOK_CACHE[textbook_id]
    else:
        # print(f"Index for textbook '{textbook_id}' not in cache. Loading from file...")
        return load_textbook_index(textbook_id)


def get_text_from_pages(textbook_id: str, page_numbers: List[int]) -> str:
    """Retrieves combined text from specified pages using the loaded/cached index."""
    textbook_index_data = get_textbook_data(textbook_id)
    if not textbook_index_data or "chunks" not in textbook_index_data:
        print(f"No index data or chunks found for textbook '{textbook_id}'.")
        return ""
        
    combined_text = ""
    # Ensure page_numbers are unique and sorted for consistent output if needed
    unique_page_numbers = sorted(list(set(page_numbers)))

    for page_data in textbook_index_data["chunks"]:
        if "page_number" in page_data and page_data["page_number"] in unique_page_numbers:
            combined_text += page_data.get("text", "") + "\n\n" # Add two newlines for separation
            
    return combined_text.strip()


def search_concept_pages(textbook_id: str, concept: str, max_pages: int = 5) -> List[int]:
    """
    Searches for a concept in the textbook index (page texts) and returns page numbers.
    Limits the number of returned pages to max_pages.
    """
    textbook_index_data = get_textbook_data(textbook_id)
    if not textbook_index_data or "chunks" not in textbook_index_data:
        print(f"No index data or chunks for searching in textbook '{textbook_id}'.")
        return []

    concept_pages_found: List[int] = []
    concept_lower = concept.lower()

    for page_data in textbook_index_data["chunks"]:
        page_text = page_data.get("text", "")
        page_num = page_data.get("page_number")
        if page_text and page_num is not None:
            if concept_lower in page_text.lower():
                concept_pages_found.append(page_num)
                if len(concept_pages_found) >= max_pages:
                    break # Stop if we've found enough relevant pages
                    
    return sorted(list(set(concept_pages_found))) # Return unique, sorted page numbers

# --- Example usage (for testing - can be commented out) ---
# if __name__ == "__main__":
#     # Ensure you have run preprocess_textbooks.py and have an index file
#     # e.g., api/textbook_index/economics9_index.json
#     test_tb_id = "economics9"
#     load_textbook_index(test_tb_id) # Load it into cache first

#     pages = search_concept_pages(test_tb_id, "market equilibrium")
#     if pages:
#         print(f"Concept 'market equilibrium' found on pages: {pages} in '{test_tb_id}'")
#         text_content = get_text_from_pages(test_tb_id, pages)
#         print(f"\nText from these pages (first 300 chars):\n{text_content[:300]}...")
#     else:
#         print(f"Concept 'market equilibrium' not found in '{test_tb_id}'.")

#     # Test getting full textbook content (all chunks)
#     # full_content_data = get_textbook_data(test_tb_id)
#     # if full_content_data and "chunks" in full_content_data:
#     #     print(f"\nTotal pages/chunks in '{test_tb_id}': {len(full_content_data['chunks'])}")