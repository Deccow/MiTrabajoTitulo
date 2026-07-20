"""
Python client for the Lucene Spring Boot REST API.
Make sure the Java server is running on port 8080 before using this.
"""

import requests

BASE_URL = "http://localhost:8080/api"


def dict_search(query: str, max_results: int = 10) -> dict:
    """Search the Lucene index."""
    response = requests.get(f"{BASE_URL}/dict_search", params={"q": query, "max": max_results})
    response.raise_for_status()
    return response.json()

def gloss_search(query: str, max_results: int = 10) -> dict:
    """Search the glossary index."""
    response = requests.get(f"{BASE_URL}/gloss_search", params={"q": query, "max": max_results})
    response.raise_for_status()
    return response.json()


def index_document(id: str, title: str, contents: str) -> dict:
    """Add or update a single document in the index."""
    payload = {"id": id, "title": title, "contents": contents}
    response = requests.post(f"{BASE_URL}/index", json=payload)
    response.raise_for_status()
    return response.json()


def index_batch(documents: list[dict]) -> dict:
    """Add multiple documents at once. Each dict needs id, title, contents."""
    response = requests.post(f"{BASE_URL}/index/batch", json=documents)
    response.raise_for_status()
    return response.json()


def delete_document(id: str) -> dict:
    """Delete a document from the index by id."""
    response = requests.delete(f"{BASE_URL}/index/{id}")
    response.raise_for_status()
    return response.json()


def stats() -> dict:
    """Get index statistics (document count, path)."""
    response = requests.get(f"{BASE_URL}/stats")
    response.raise_for_status()
    return response.json()


def is_int(string) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False

def gloss_parser(doc) -> dict:
    try:
        gloss = doc.get('gloss', '')
    except AttributeError:
        gloss = doc
    lines = gloss.split("\t")
    new_gloss = {}
    if len(lines) != 4:
        lines_to_remove = []
        if len(lines) < 4:
            print(f"Unexpected gloss format: {gloss}")
            return
        for i in range(4, len(lines)):
            if "bn:" in lines[i]:
                lines_to_remove.append(i)
                continue
            if lines[i] == "":
                lines_to_remove.append(i)
                continue
        for line in reversed(lines_to_remove):
            lines.pop(line)
        if len(lines) != 4:
            print(f"Unexpected gloss format after cleaning: {gloss}")
            return
        
    new_gloss['glossLanguage'] = lines[0]
    new_gloss["glossSource"] = lines[1]
    new_gloss["glossNewId"] = lines[2]
    new_gloss["gloss"] = lines[3]
    # Chequear que las son como esperamos las lineas
    try:
        assert new_gloss["glossSource"].startswith("WIK") or new_gloss["glossSource"].startswith("OM")
        assert is_int(new_gloss["glossNewId"])
    except AssertionError as e:
        print(f"Unexpected gloss format: {e}")
        return
    return new_gloss


"""


#print(requests.get("http://localhost:8080/api/dict_fields").json())
#print(requests.get("http://localhost:8080/api/gloss_fields").json())

#print(gloss_search('ID:*', max_results=10))


print(requests.get("http://localhost:8080/api/dict_fields").json())
# 3. Search

results = dict_search('LEMMA_LANGUAGE:EN', max_results=5)    
print(f"\nSearch results ({results['count']} found):")
print(f"Found {results['count']} results:")
for dict_doc in results['results']:
    id = dict_doc['id']
    print(dict_doc)
    print(f"LEMMA {dict_doc.get('lemma', 'N/A')}")
    print(f"TYPE: {dict_doc.get('type', 'N/A')}")
    results = gloss_search(id, max_results=2)
    doc = results['results'][0] if results['count'] > 0 else None
    if not doc:
        continue
    gloss_parser(doc)

#CBS30:RDC55sounwrn
 """