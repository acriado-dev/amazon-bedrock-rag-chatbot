import chromadb
import logging


print("Hello, world!")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection")
# Add logging to print the input data
documents = ["This is a document about pineapple", "This is a document about oranges"]
logging.debug(f"Documents to be added: {documents}")

try:
    collection.add(documents=documents, ids=["id1", "id2"])
except Exception as e:
    logging.error(f"Error adding documents to collection: {e}")

results = collection.query(
    query_texts=[
        "This is a query document about hawaii"
    ],  # Chroma will embed this for you
    n_results=2,  # how many results to return
)
print(results)
