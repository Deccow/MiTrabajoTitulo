import requests
import time
from requests import api as requests_api
from languageprocessing import *

_original_get = requests_api.get  # points to the real function, not requests.get

def _get_with_timeout(url, **kwargs):
    kwargs.setdefault("timeout", 30)
    for attempt in range(3):
        try:
            return _original_get(url, **kwargs)
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1} timed out for {url}, retrying...")
            time.sleep(1)
    raise requests.exceptions.Timeout(f"All 3 attempts timed out for {url}")

requests.get = _get_with_timeout

def apply_condition(dict, condition, field: list):
    desired_field = get_field(dict, field)

    if callable(condition):
        return condition(desired_field)
    
    if isinstance(condition, list):
        return desired_field in condition

    return desired_field == condition

def apply_defined_conditions(dict, lang):
    condition_1 = "HIGH_QUALITY"
    condition_2 = lang
    condition_3 = ["WN", "OEWN", "MCR_ES"]

    response = [item for item in dict["senses"] if (apply_condition(item, condition_1, ["properties", "lemma", "type"])) &
                               (apply_condition(item, condition_2, ["properties", "language"])) & (apply_condition(item, condition_3, ["properties", "source"]))]


    return response


def get_field(dict, field: list):
    for item in field:
        if type(item) == int:
            dict = dict[item]
        if item in dict:
            dict = dict[item]
    return dict


KEY = "91849848-0ffa-4c0d-8689-17389aae6042"
URL = f"https://babelnet.io/v9/getVersion?key={KEY}"

def search_word(word, lang):
    url = f"https://babelnet.io/v9/getSynsetIds?lemma={word}&searchLang={lang}&key={KEY}"
    response = requests.get(url)
    return response.json()

def search_spanish(word):
    return search_word(word, lang='ES')

def search_english(word):
    return search_word(word, lang='EN')

def get_synset(synset_id, lang):
    url = f"https://babelnet.io/v9/getSynset?id={synset_id}&targetLang={lang}&key={KEY}"
    response = requests.get(url)
    new_response = response.json()

    condition_1 = "HIGH_QUALITY"
    condition_2 = lang
    condition_3 = ["WN", "OEWN", "MCR_ES"]
    try:
        new_response["senses"] = [item for item in response.json()["senses"] if (apply_condition(item, condition_1, ["properties", "lemma", "type"])) &
                                (apply_condition(item, condition_2, ["properties", "language"])) & (apply_condition(item, condition_3, ["properties", "source"]))]
    except KeyError:
        new_response["senses"] = []
    
    return new_response

def get_senses(word, lang):
    url = f"https://babelnet.io/v9/getSenses?lemma={word}&searchLang={lang}&key={KEY}"
    response = requests.get(url)
    new_response =([item for item in response.json() if (item["properties"]["language"] == lang) & (item["properties"]["lemma"]["type"] == "HIGH_QUALITY")])    
    return new_response

def get_definitions(word, lang='ES'):
    synsets = search_word(word, lang=lang)
    definitions = []
    n = len(synsets)
    for synset in synsets:
        synset_data = get_synset(synset['id'], lang=lang)
        if "NAMED_ENTITY" in synset_data["tags"]:
            continue
        #print(n)
        n -= 1
        senses = synset_data.get('senses', [])
        #for sense in senses:
            #print(sense)
        glosses = synset_data.get('glosses', [])
        for gloss in glosses:
            if gloss['language'] == lang:
                #print(gloss["source"])
                definitions.append(gloss['gloss'])
                break

    #print(definitions)
    return definitions



# get_definitions("gato")
# get_definitions("banco")


def look_for_word_in_english(word):
    synsets = search_spanish(word)
    return get_synset(synsets[0]['id'], lang='EN')

def get_synset_synonyms(synset_id, lang):
    synset_data = get_synset(synset_id, lang=lang)
    #print(synset_data)
    #print(synset_data)
    senses = synset_data.get('senses', [])
    #print(senses[0]["properties"]["fullLemma"])
    synonyms = []
    for sense in senses:
        if "_" not in sense["properties"]["fullLemma"] and sense["properties"]["language"] == lang:
            synonyms.append(sense)

    #display(synonyms)
    synonyms = list(set([s["properties"]["fullLemma"] for s in synonyms]))
    return synonyms

