# api/preprocess_textbooks.py
import PyPDF2
import json
import os

TEXTBOOK_FILES = { # Define textbooks to pre-process and their filenames
    "economics9": "economics9.pdf",
    "history9": "history9.pdf",
}

def load_and_chunk_textbook(textbook_id, filepath):
    """Loads a textbook, chunks text by page, and returns page-based chunks."""
    try:
        with open(filepath, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content = page.extract_text()
                pages_content.append({"page_number": page_num + 1, "text": text_content})
            print(f"Textbook '{textbook_id}' processed: {len(pages_content)} pages extracted.")
            return pages_content
    except Exception as e:
        print(f"Error processing textbook '{textbook_id}': {e}")
        return None

def create_index(textbook_id, pages_content, index_dir="textbook_index"):
    """Creates and saves a simple JSON index for a textbook."""
    if not os.path.exists(index_dir):
        os.makedirs(index_dir) # Create index directory if it doesn't exist

    index_filepath = os.path.join(index_dir, f"{textbook_id}_index.json")
    index_data = {
        "textbook_id": textbook_id,
        "chunks": pages_content # For now, chunks are just pages
    }

    with open(index_filepath, 'w') as outfile:
        json.dump(index_data, outfile, indent=4) # Save index to JSON file
    print(f"Index for textbook '{textbook_id}' saved to '{index_filepath}'")


def preprocess_all_textbooks():
    """Pre-processes all textbooks defined in TEXTBOOK_FILES."""
    for textbook_id, filename in TEXTBOOK_FILES.items():
        print(f"--- Pre-processing textbook '{textbook_id}' from '{filename}' ---")
        filepath = f"api/{filename}" # Assuming PDFs are in api/ folder
        pages_content = load_and_chunk_textbook(textbook_id, filepath)
        if pages_content:
            create_index(textbook_id, pages_content)
        else:
            print(f"Preprocessing for '{textbook_id}' failed.")

if __name__ == "__main__":
    preprocess_all_textbooks()
    print("Textbook pre-processing and indexing complete.")
