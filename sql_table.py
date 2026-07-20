import sqlite3
from languageprocessing import *
from OldApi.babelnet import *
import random


# Create (or connect to) a local database file
conn = sqlite3.connect("local_database.db")

# Create a cursor to execute SQL commands
cursor = conn.cursor()

def create_tables():

    cursor.execute("DROP TABLE IF EXISTS words")
    cursor.execute("DROP TABLE IF EXISTS relations")
    cursor.execute("DROP TABLE IF EXISTS definitions")
    cursor.execute("DROP TABLE IF EXISTS dict")
    cursor.execute("DROP TABLE IF EXISTS gloss")

    # Scrapping
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dict (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        glossId TEXT NOT NULL UNIQUE,
        lemmaLanguage TEXT NOT NULL,
        lemma TEXT NOT NULL,
        synsetId TEXT NOT NULL,

        idSense TEXT,
        lemmaSensekey TEXT,
        lemmaFrequence TEXT,
        category TEXT,
        languageLemma TEXT,
        type TEXT,
        lemmaSource TEXT
    );
    """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS gloss (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   glossId TEXT NOT NULL,
                   glossLanguage TEXT NOT NULL,
                   glossSource TEXT NOT NULL,
                   glossNewId TEXT NOT NULL,
                   gloss TEXT NOT NULL                
                   );
                   """)

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

def transform_doc_to_word(doc):
    word = {}
    word['glossId'] = doc.get('id', None)
    word['lemmaLanguage'] = doc.get('lemmaLanguage', None)
    word['lemma'] = doc.get('lemma', None)
    word['synsetId'] = doc.get('synsetId', None)
    word["idSense"] = doc.get('idSense', None)
    word["lemmaSensekey"] = doc.get('lemmaSensekey', None)
    word["lemmaFrequence"] = doc.get('lemmaFrequence', None)
    word["category"] = doc.get('category', None)
    word["languageLemma"] = doc.get('languageLemma', None)
    word["type"] = doc.get('type', None)
    word["lemmaSource"] = doc.get('lemmaSource', None)
    return word

def insert_word(doc, glosses):

    cursor.execute("""
    INSERT INTO dict (
        glossId,
        lemmaLanguage,
        lemma,
        synsetId,
        idSense,
        lemmaSensekey,
        lemmaFrequence,
        category,
        languageLemma,
        type,
        lemmaSource
    )
    VALUES (
        :glossId,
        :lemmaLanguage,
        :lemma,
        :synsetId,
        :idSense,
        :lemmaSensekey,
        :lemmaFrequence,
        :category,
        :languageLemma,
        :type,
        :lemmaSource
    )
    """, doc)

    for gloss in glosses:
        gloss['glossId'] = doc['glossId']
        cursor.execute("""
        INSERT INTO gloss (
            glossId,
            glossLanguage,
            glossSource,
            glossNewId,
            gloss
        )
        VALUES (
            :glossId,
            :glossLanguage,
            :glossSource,
            :glossNewId,
            :gloss
        )
        """, gloss)

    conn.commit()