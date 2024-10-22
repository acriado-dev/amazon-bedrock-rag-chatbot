import boto3
import json
import chromadb
from chromadb.utils.embedding_functions import AmazonBedrockEmbeddingFunction


def get_text_embeddings_collection(collection_name, path):
    session = boto3.Session()
    embedding_function = AmazonBedrockEmbeddingFunction(
        session=session, model_name="amazon.titan-embed-text-v2:0"
    )

    client = chromadb.PersistentClient(path=path)
    index = client.get_or_create_collection(
        collection_name, embedding_function=embedding_function
    )

    return index


def initialize_collection(collection_name, source_json_file, path):
    collection = get_text_embeddings_collection(collection_name, path)

    if collection.count() == 0:
        row_count = 0

        with open(source_json_file) as json_file:
            source_json = json.load(json_file)

            for item in source_json:
                row_count += 1
                collection.add(
                    ids=[str(item["id"])],
                    documents=[item["document"]],
                    metadatas=[item["metadata"]],
                    embeddings=[item["embedding"]],
                )

        print(f"Added {row_count} rows to collection {collection_name}")

    print(f"Initialized collection {collection_name}")

    return collection


chroma_db_path = "chroma"

# Initialize collections
initialize_collection(
    "services_collection", "services_with_embeddings.json", path=chroma_db_path
)
initialize_collection(
    "bedrock_faqs_collection", "bedrock_faqs_with_embeddings.json", path=chroma_db_path
)
