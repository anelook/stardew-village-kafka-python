
import os
from dotenv import load_dotenv
import openai
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException

load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure OpenSearch client
OPENSEARCH_NODE_URL = os.getenv("OPENSEARCH_NODE_URL")  # e.g., "https://localhost:9200"
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
OPENSEARCH_INDEX_PREFIX = os.getenv("OPENSEARCH_INDEX")  # e.g., "long_term_memory"

os_client = OpenSearch(
    hosts=[OPENSEARCH_NODE_URL],
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=False,
    connection_class=RequestsHttpConnection
)


def search_long_term_memory(query: str, name: str, k: int = 5) -> str:
    """
    Search long-term memory by embedding similarity.

    :param query: the query text (must be non-empty)
    :param name:  the namespace/index suffix (will be lowercased)
    :param k:     how many top hits to retrieve (default: 5)
    :return:      semicolon-joined summaries, or '' on error
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    # 1) Get embedding for the query
    try:
        embedding_res = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=query
        )
        embedding = embedding_res["data"][0]["embedding"]
    except Exception as e:
        print(f"Error obtaining embedding from OpenAI: {e}")
        return ""

    # 2) Build the index name
    index_name = f"{OPENSEARCH_INDEX_PREFIX}_{name.lower()}"

    # 3) Perform kNN search via script_score + cosineSimilarity
    body = {
        "size": k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, doc['embedding']) + 1.0",
                    "params": {"query_vector": embedding}
                }
            }
        },
        "_source": ["summary"]
    }

    try:
        resp = os_client.search(index=index_name, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        summaries = [hit["_source"].get("summary", "") for hit in hits]
        result = ";".join(summaries)
        print(f"{name.upper()}: RELEVANT MEMORIES ---- {result}")
        return result
    except OpenSearchException as e:
        print(f'Error searching OpenSearch index "{index_name}": {e}')
        print(f"{name.upper()}: NO RELEVANT MEMORIES")
        return ""
    except Exception as e:
        print(f"Unexpected error during OpenSearch search: {e}")
        print(f"{name.upper()}: NO RELEVANT MEMORIES")
        return ""
