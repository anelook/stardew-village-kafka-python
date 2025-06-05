
import os
from datetime import datetime
from dotenv import load_dotenv
import openai
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException

load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure OpenSearch client
OPENSEARCH_NODE_URL = os.getenv("OPENSEARCH_NODE_URL")       # e.g., "https://localhost:9200"
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
OPENSEARCH_INDEX_PREFIX = os.getenv("OPENSEARCH_INDEX")     # e.g., "long_term_memory"

os_client = OpenSearch(
    hosts=[OPENSEARCH_NODE_URL],
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=False,
    connection_class=RequestsHttpConnection
)


def store_long_term_memory(conversation_summary: str, name: str) -> dict:
    """
    Store a conversation summary in OpenSearch with its embedding.

    :param conversation_summary: non-empty string summary of the conversation
    :param name:               the namespace/index suffix (will be lowercased)
    :return:                   the raw response from OpenSearch's index call
    :raises ValueError:        if conversation_summary is not a non-empty string
    """
    if not isinstance(conversation_summary, str) or not conversation_summary.strip():
        raise ValueError("conversation_summary must be a non-empty string")

    # 1) Get embedding from OpenAI
    try:
        embedding_res = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=conversation_summary
        )
        embedding = embedding_res["data"][0]["embedding"]
    except Exception as e:
        print(f"Error obtaining embedding from OpenAI: {e}")
        raise

    # 2) Prepare the document
    doc = {
        "summary": conversation_summary,
        "embedding": embedding,  # list of floats
        "timestamp": datetime.utcnow().isoformat()
    }

    # 3) Index into OpenSearch
    index_name = f"{OPENSEARCH_INDEX_PREFIX}_{name.lower()}"
    try:
        resp = os_client.index(
            index=index_name,
            body=doc,
            refresh="wait_for"  # wait so it's immediately queryable
        )
        return resp
    except OpenSearchException as e:
        print(f'Error indexing document into "{index_name}": {e}')
        raise
    except Exception as e:
        print(f"Unexpected error during OpenSearch indexing: {e}")
        raise
