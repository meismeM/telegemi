# api/preprocess_textbooks.py
import PyPDF2 # PyPDF2 can be replaced with a more robust library like pdfminer.six or pymupdf if needed
import json
import os

# Define textbooks to pre-process. Assumes PDFs are in a 'textbooks' subdirectory relative to this script.
# The script itself is expected to be in 'api/' directory, so 'textbooks/' is 'api/textbooks/'
TEXTBOOK_SOURCE_DIR = "textbooks" # Subdirectory within 'api/' where source PDFs are located
TEXTBOOK_FILES = { 
    "economics9": "economics9.pdf",
    "history9": "history9.pdf",
    # "math9": "math_grade9.pdf", # Example: add your PDF filenames here
}

# Output directory for indexes, relative to this script's location ('api/')
# So, 'api/textbook_index/'
INDEX_OUTPUT_DIR = "textbook_index"


def load_and_chunk_textbook(textbook_id: str, pdf_filepath: str) -> Optional[List[Dict[str, Any]]]:
    """Loads a textbook PDF, extracts text per page, and returns page-based chunks."""
    pages_content: List[Dict[str, Any]] = []
    print(f"Processing textbook '{textbook_id}' from '{pdf_filepath}'...")
    try:
        with open(pdf_filepath, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            if num_pages == 0:
                print(f"Warning: No pages found in PDF '{pdf_filepath}' for textbook '{textbook_id}'.")
                return None
                
            for page_num in range(num_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    text_content = page.extract_text()
                    if text_content is None or not text_content.strip():
                        # print(f"  Page {page_num + 1}: No text extracted or only whitespace.")
                        text_content = "" # Store as empty string if no text
                    pages_content.append({"page_number": page_num + 1, "text": text_content.strip()})
                except Exception as e:
                    print(f"  Error extracting text from page {page_num + 1} of '{pdf_filepath}': {e}")
                    pages_content.append({"page_number": page_num + 1, "text": ""}) # Store empty on error

            print(f"Textbook '{textbook_id}' processed: {len(pages_content)} pages extracted.")
            return pages_content
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_filepath}' for textbook '{textbook_id}'.")
        return None
    except PyPDF2.errors.PdfReadError as e: # More specific PyPDF2 error
        print(f"Error: PyPDF2 could not read PDF '{pdf_filepath}' (it might be corrupted or password-protected): {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred processing textbook '{textbook_id}' from '{pdf_filepath}': {e}")
        return None

def create_index(textbook_id: str, pages_content: List[Dict[str, Any]], index_dir: str) -> None:
    """Creates and saves a simple JSON index for a textbook."""
    if not os.path.exists(index_dir):
        try:
            os.makedirs(index_dir)
            print(f"Created index directory: '{index_dir}'")
        except OSError as e:
            print(f"Error creating index directory '{index_dir}': {e}")
            return

    index_filename = f"{textbook_id}_index.json"
    index_filepath = os.path.join(index_dir, index_filename)
    
    index_data = {
        "textbook_id": textbook_id,
        "chunks": pages_content # Each "chunk" is currently one page's content
        # Future: Could add metadata, keywords per chunk, etc.
    }

    try:
        with open(index_filepath, 'w', encoding='utf-8') as outfile:
            json.dump(index_data, outfile, indent=4, ensure_ascii=False)
        print(f"Index for textbook '{textbook_id}' saved successfully to '{index_filepath}'")
    except IOError as e:
        print(f"Error writing index file '{index_filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred saving index for '{textbook_id}': {e}")


def preprocess_all_textbooks():
    """Pre-processes all textbooks defined in TEXTBOOK_FILES."""
    script_dir = os.path.dirname(os.path.abspath(__file__)) # Gets 'api/' directory
    source_pdfs_full_dir = os.path.join(script_dir, TEXTBOOK_SOURCE_DIR)
    index_output_full_dir = os.path.join(script_dir, INDEX_OUTPUT_DIR)

    print(f"Source PDF directory: {source_pdfs_full_dir}")
    print(f"Index output directory: {index_output_full_dir}")

    if not os.path.isdir(source_pdfs_full_dir):
        print(f"Error: Source PDF directory '{source_pdfs_full_dir}' not found. Please create it and place PDF files there.")
        return

    for textbook_id, pdf_filename in TEXTBOOK_FILES.items():
        print(f"\n--- Pre-processing textbook '{textbook_id}' ---")
        pdf_full_filepath = os.path.join(source_pdfs_full_dir, pdf_filename)
        
        pages_data = load_and_chunk_textbook(textbook_id, pdf_full_filepath)
        if pages_data:
            create_index(textbook_id, pages_data, index_output_full_dir)
        else:
            print(f"Skipping index creation for '{textbook_id}' due to previous errors.")

if __name__ == "__main__":
    print("Starting textbook pre-processing and indexing...")
    preprocess_all_textbooks()
    print("\nTextbook pre-processing and indexing complete.")
    print(f"Ensure that the '{INDEX_OUTPUT_DIR}' directory (e.g., 'api/textbook_index/') and its JSON files are deployed with your application.")
    