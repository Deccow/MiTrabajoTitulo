import sqlite3
from languageprocessing import *
from babelnet import *
import random


conn = sqlite3.connect("local_database.db")

cursor = conn.cursor()

def create_tables():

    cursor.execute("DROP TABLE IF EXISTS words")
    cursor.execute("DROP TABLE IF EXISTS relations")
    cursor.execute("DROP TABLE IF EXISTS definitions")


    # Create a table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,  
        language TEXT NOT NULL,
        concept TEXT,
        scrapped BOOLEAN DEFAULT FALSE,
        translated BOOLEAN DEFAULT FALSE,
        UNIQUE(word, language, concept)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word1_id INTEGER NOT NULL,  
        word2_id INTEGER NOT NULL,
        relation_type TEXT NOT NULL,
        FOREIGN KEY (word1_id) REFERENCES words(id),
        FOREIGN KEY (word2_id) REFERENCES words(id),
        UNIQUE(word1_id, word2_id, relation_type)
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        definition TEXT NOT NULL,
        FOREIGN KEY (word_id) REFERENCES words(id),
        UNIQUE(word_id, definition)
    )
    """)

    conn.commit()
    print("Table created successfully!")



def insert_word_and_definition(id, word, definition, language, scrapped=False, translated=False):
    definition_words = preprocess_text(definition, language=language)["lemmatized"]
    if word in definition_words:
        definition_words.remove(word)
    cursor.execute(
    """
    INSERT INTO words (word, language, concept) VALUES (?, ?, ?)
    """, (word, language, id))

    word_id = cursor.lastrowid

    cursor.execute("INSERT INTO definitions (word_id, definition) VALUES (?, ?)", (word_id, definition))

    
    definition_word_ids = []

    for def_word in definition_words:
        cursor.execute(
            "INSERT INTO words (word, language, concept, scrapped) VALUES (?, ?, ?, ?)",
            (def_word, language, None, scrapped)
        )
        definition_word_ids.append(cursor.lastrowid)

    relations = [
        (word_id, def_word_id, "definition")
        for def_word_id in definition_word_ids
    ]

    cursor.executemany(
        "INSERT INTO relations (word1_id, word2_id, relation_type) VALUES (?, ?, ?)",
        relations
    )

def get_word_id(word, concept, language):
    cursor.execute("SELECT id FROM words WHERE word = ? AND language = ? AND concept = ?", (word, language, concept))
    result = cursor.fetchone()
    return result[0] if result else None

def scrap_word(word, language):
    """
    Searches all the different concepts for a given word in a given language and stores them in the database, along with the relations between the word and the definition in its definition.

    Parameters:
        word (str): the word to search for
        language (str ["EN", "ES"]): the language of the word

    Returns:
        None
    """
    cursor.execute("SELECT * FROM words WHERE word = ? AND language = ?", (word, language))
    word_exists = cursor.fetchone()
    if word_exists and word_exists[4]: # scrapped == True
        print(f"Word '{word}' in language '{language}' already scrapped, skipping.")
        return
    
    request = search_word(word, lang=language)
    ids = [id["id"] for id in request]
    cursor.execute("SELECT concept FROM words WHERE word = ? AND language = ?", (word, language))
    existing_ids = cursor.fetchall()
    existing_ids = set([id[0] for id in existing_ids])
    number_of_ids = len(ids)
    for existing_id in existing_ids:
        if (existing_id in ids):
            ids.remove(existing_id)
    print(number_of_ids - len(ids), "existing ids removed")
    for id in range(len(ids)):
        print(f"Scrapping {word} {ids[id]} ({language}) {id+1}/{len(ids)}")
        try:
            get_syn = get_synset(ids[id], lang=language)

            if "NAMED_ENTITY" in get_syn.get("tags", []) or not get_syn.get("glosses"):
                continue
            if (get_syn.get("senses") == [] or "NAMED_ENTITY" in get_syn.get("senses", [{}])[0].get("properties", {}).get("tags", [])):
                continue
            if (apply_condition(get_syn, "HIGH_QUALITY", ["senses", 0, "properties", "lemma", "type"]) and apply_condition(get_syn, language, ["senses", 0, "properties", "language"]) and  apply_condition(get_syn, ["WN", "OEWN", "MCR_ES", "OMWIKI"], ["senses", 0, "properties", "source"])):
                #print(get_syn["glosses"])
                for gloss in range(len(get_syn["glosses"])):
                    if get_syn["glosses"][gloss]["language"] == language:
                        if get_syn["glosses"][gloss]["source"] in ["WN", "OEWN", "MCR_ES", "OMWIKI"]:
                            ids_definition = get_syn["glosses"][gloss]["gloss"]
                            insert_word_and_definition(id=ids[id], word=word, definition=ids_definition, language=language, scrapped=False)
                            break

            else:
                print(f"Synset {ids[id]} for word {word} did not meet the conditions and was skipped.")
        except Exception as e:
            print(f"Error occurred while fetching synset for {word}: {e}")
            continue
    cursor.execute("UPDATE words SET scrapped = 1 WHERE word = ? AND language = ?", (word, language))
    conn.commit()

def scrap_translations(synset_id, original_word, language):
    cursor.execute("SELECT * FROM words WHERE word = ? AND language = ?", (original_word, language))
    word_exists = cursor.fetchone()
    if word_exists and word_exists[5]: # translated == True
        print(f"Word '{original_word}' in language '{language}' already translated, skipping.")
        return
    synonyms = get_synset_synonyms(synset_id, lang=language)
    synonyms = list(set(synonyms))
    #print(synonyms)
    for synonym in synonyms:
        synset_data = get_synset(synset_id, lang=language)
        glosses = synset_data.get('glosses', [])
        for gloss in glosses:
            if gloss['language'] == language and apply_condition(gloss, ["WN", "OEWN", "MCR_ES", "OMWIKI", "WIKIDATA"], ["source"]):
                try:
                    #print(gloss)
                    definition = gloss['gloss']
                    #print(synonym, synset_id)
                    insert_word_and_definition(id=synset_id, word=synonym, definition=definition, language=language)
                    original_lang = "EN" if language == "ES" else "ES"
                    original_word_id = get_word_id(original_word, synset_id, original_lang)
                    synonym_id = get_word_id(synonym, synset_id, language)
                    cursor.execute(
                    """
                    INSERT INTO relations (word1_id, word2_id, relation_type) VALUES (?, ?, ?)
                    """, (original_word_id, synonym_id, "translation"))
                    break
                except Exception as e:
                    #print(f"Error occurred while inserting translation for {synonym}: {e}")
                    continue
    cursor.execute("UPDATE words SET translated = 1 WHERE word = ? AND language = ?", (original_word, language))
    conn.commit()

def get_translations():
    cursor.execute("SELECT DISTINCT w.word, w.language, w.concept FROM words w WHERE w.translated IS FALSE AND w.concept IS NOT NULL")
    rows = cursor.fetchall()
    i=1
    for word, language, concept in rows:
        print(f"{i}/{len(rows)}")
        i += 1
        lang = "ES" if language == "EN" else "EN"
        scrap_translations(concept, word, lang)


def recursive_scrap():
    cursor.execute("SELECT word, language FROM words WHERE NOT EXISTS (SELECT 1 FROM words w2 WHERE w2.word = words.word AND w2.language = words.language AND w2.scrapped = 1)")
    rows = cursor.fetchall()
    print(len(rows))
    random.shuffle(rows)
    i = 1
    for word, language in rows:
        print(f"{i}/{len(rows)}")
        scrap_word(word, language)
        i += 1



def view_all_relations():
    cursor.execute("SELECT word, language, concept FROM words")
    rows = cursor.fetchall()
    for word, language, concept in rows:
        print(f"{word} ({language}) - Concept: {concept}")

def view_all_definitions():
    cursor.execute("""
    SELECT w.word, w.language, d.definition
    FROM words w
    JOIN definitions d ON w.id = d.word_id
    """)
    rows = cursor.fetchall()
    for word, language, definition in rows:
        print(f"{word} ({language}): {definition}")
        