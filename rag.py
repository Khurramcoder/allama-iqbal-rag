import os
import json
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Path to your assets
BASE_DIR = r"E:\allama-iqbal.com-main\allama-iqbal.com-main\src\assets\content"

def build_rag():
    documents = []
    print("Starting data ingestion...")
    
    # Walk through all directories
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                
                # Identify the book name from the folder path
                # Example: content/zarb-e-kaleem/01/01.json -> book = zarb-e-kaleem
                parts = os.path.relpath(file_path, BASE_DIR).split(os.sep)
                book_name = parts[0]

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Logic to extract text based on Iqbal dataset structure
                        # It looks for a 'text' key, or joins list items if it's an array
                        if isinstance(data, dict):
                            content = data.get("text") or data.get("content") or json.dumps(data, ensure_ascii=False)
                        elif isinstance(data, list):
                            content = " ".join([str(x) for x in data])
                        else:
                            content = str(data)
                            
                        documents.append(Document(
                            page_content=content,
                            metadata={"book": book_name, "file": file}
                        ))
                except Exception as e:
                    print(f"  Skipping {file} due to error: {e}")

    print(f"Successfully loaded {len(documents)} documents.")

    # Multilingual model is essential for Urdu/Persian poetry
    # We use 'cuda' to leverage your RTX 4060 Ti
    print("Initializing embeddings on GPU...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cuda'}
    )

    # Build the FAISS index
    print("Building vector index (FAISS)...")
    vector_db = FAISS.from_documents(documents, embeddings)
    
    # Save the index locally
    vector_db.save_local("iqbal_index")
    print("\nSUCCESS: Index created and saved to 'iqbal_index' folder.")

if __name__ == "__main__":
    build_rag()