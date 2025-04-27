import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

# Base URL for NCBI E-utilities
EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def search_pubmed(query: str, max_results: int = 10) -> List[Dict[str, Optional[str]]]:
    """
    Searches PubMed for articles matching the query using NCBI E-utilities.

    Args:
        query: The search term(s).
        max_results: The maximum number of results to return.

    Returns:
        A list of dictionaries, each containing 'pmid', 'title', and 'abstract'.
        Returns an empty list if the search fails or no results are found.
    """
    search_url = f"{EUTILS_BASE_URL}esearch.fcgi"
    fetch_url = f"{EUTILS_BASE_URL}efetch.fcgi"
    results = []

    try:
        # 1. Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "usehistory": "y",  # Use history server for larger requests
        }
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        search_root = ET.fromstring(search_response.content)
        id_list = [
            id_elem.text
            for id_elem in search_root.findall(".//IdList/Id")
            if id_elem.text
        ]

        if not id_list:
            print(f"No PubMed IDs found for query: {query}")
            return []

        # Get history server info (if available)
        web_env = search_root.findtext(".//WebEnv")
        query_key = search_root.findtext(".//QueryKey")

        # 2. Fetch article details using PMIDs or history server
        fetch_params = {
            "db": "pubmed",
            "rettype": "abstract",  # Get abstract text
            "retmode": "xml",
        }
        if web_env and query_key:
            fetch_params["WebEnv"] = web_env
            fetch_params["query_key"] = query_key
            # Use retmax from esearch result count if needed, esearch retmax limits the *IDs* returned
            # fetch_params["retmax"] = len(id_list) # Or use the count from esearch if available
        else:
            # Fallback to using comma-separated IDs if history fails
            fetch_params["id"] = ",".join(id_list)

        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()

        # 3. Parse fetched XML details
        fetch_root = ET.fromstring(fetch_response.content)
        for article in fetch_root.findall(".//PubmedArticle"):
            pmid_elem = article.find(".//PMID")
            title_elem = article.find(".//ArticleTitle")
            abstract_elem = article.find(
                ".//Abstract/AbstractText"
            )  # Simple case, might need more robust parsing for structured abstracts

            pmid = pmid_elem.text if pmid_elem is not None else None
            # Handle potential missing titles or titles split across elements
            title = (
                "".join(title_elem.itertext()).strip()
                if title_elem is not None
                else "No title available"
            )
            abstract = abstract_elem.text if abstract_elem is not None else None

            if pmid:
                results.append({"pmid": pmid, "title": title, "abstract": abstract})

    except requests.exceptions.RequestException as e:
        print(f"Error querying PubMed API: {e}")
        # Optionally, re-raise or handle specific HTTP errors
    except ET.ParseError as e:
        print(f"Error parsing PubMed XML response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during PubMed search: {e}")

    return results


# Example Usage (can be run standalone for testing)
if __name__ == "__main__":
    test_query = "diabetes management type 2"
    print(f"Searching PubMed for: '{test_query}'")
    articles = search_pubmed(test_query, max_results=5)
    if articles:
        print(f"Found {len(articles)} articles:")
        for i, article in enumerate(articles):
            print(f"--- Result {i + 1} ---")
            print(f"  PMID: {article['pmid']}")
            print(f"  Title: {article['title']}")
            print(
                f"  Abstract: {article['abstract'][:200] if article['abstract'] else 'N/A'}..."
            )
    else:
        print("No articles found or error occurred.")
