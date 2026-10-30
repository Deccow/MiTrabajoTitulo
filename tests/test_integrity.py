"""
Pruebas de integridad del grafo.

1. TestChecksDetectSeededDefects: valida las propias consultas. Sobre una base en memoria
   limpia, ninguna invariante falla; luego se siembra un defecto de cada tipo y se verifica
   que la invariante correspondiente (y solo esa) lo detecta.
2. TestRealDatabases: ejecuta todas las invariantes sobre el 100 % de las bases reales.

Ejecutar desde new_app/:
    python -m unittest discover -s tests -v
Para elegir otras bases:  INTEGRITY_DBS="a.db;b.db" python -m unittest discover -s tests -v
"""
import os
import sqlite3
import unittest

from integrity_checks import CHECKS, connect_read_only, count_violations, sample_violations

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DBS = ["database.db", "api_database.db"]

# Mismo esquema que las bases reales, pero sin los índices UNIQUE ni las FOREIGN KEY
# para poder sembrar los defectos que esas restricciones evitarían.
SCHEMA = """
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    language TEXT NOT NULL,
    concept TEXT,
    scrapped BOOLEAN DEFAULT FALSE,
    translated BOOLEAN DEFAULT FALSE
);
CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word1_id INTEGER NOT NULL,
    word2_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL
);
"""

CLEAN_WORDS = [
    (1, "action", "EN", "bn:00001127n"),
    (2, "acción", "ES", "bn:00001127n"),
    (3, "act", "EN", None),
    (4, "hecho", "ES", None),
]
CLEAN_RELATIONS = [
    (1, 3, "definition"),   # action -> act
    (2, 4, "definition"),   # acción -> hecho
    (1, 2, "translation"),  # action <-> acción, mismo concepto
]

# Cada defecto: (invariante que debe detectarlo, palabras extra, relaciones extra)
SEEDED_DEFECTS = {
    "definition_same_language": ([], [(1, 4, "definition")]),
    "translation_well_formed": ([], [(1, 4, "translation")]),
    "no_duplicate_null_concept": ([(5, "act", "EN", None)], []),
    "no_duplicate_concept": ([(5, "action", "EN", "bn:00001127n")], []),
    "no_orphan_relations": ([], [(1, 999, "definition")]),
    "known_relation_types": ([], [(3, 1, "synonym")]),
    "known_languages": ([(5, "Aktion", "DE", None)], []),
    "words_trimmed": ([(5, " act", "EN", None)], []),
}


def build_db(extra_words=(), extra_relations=()):
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO words (id, word, language, concept) VALUES (?, ?, ?, ?)",
                     [*CLEAN_WORDS, *extra_words])
    conn.executemany("INSERT INTO relations (word1_id, word2_id, relation_type) VALUES (?, ?, ?)",
                     [*CLEAN_RELATIONS, *extra_relations])
    return conn


class TestChecksDetectSeededDefects(unittest.TestCase):

    def test_every_check_has_a_seeded_defect(self):
        self.assertEqual({c.name for c in CHECKS}, set(SEEDED_DEFECTS))

    def test_clean_db_passes_every_check(self):
        conn = build_db()
        for check in CHECKS:
            with self.subTest(check=check.name):
                self.assertEqual(count_violations(conn, check), 0)

    def test_each_defect_is_detected_only_by_its_check(self):
        for expected, (words, relations) in SEEDED_DEFECTS.items():
            conn = build_db(words, relations)
            for check in CHECKS:
                with self.subTest(defect=expected, check=check.name):
                    n = count_violations(conn, check)
                    if check.name == expected:
                        self.assertGreater(n, 0, "la invariante no detectó su defecto")
                    else:
                        self.assertEqual(n, 0, "falso positivo en otra invariante")


class TestRealDatabases(unittest.TestCase):

    def test_invariants_hold(self):
        paths = os.environ.get("INTEGRITY_DBS", ";".join(DEFAULT_DBS)).split(";")
        for path in paths:
            full_path = path if os.path.isabs(path) else os.path.join(APP_DIR, path)
            if not os.path.exists(full_path):
                with self.subTest(db=path):
                    self.skipTest(f"{path} no existe")
                continue
            conn = connect_read_only(full_path)
            self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")
            for check in CHECKS:
                with self.subTest(db=path, check=check.name):
                    n = count_violations(conn, check)
                    self.assertEqual(
                        n, 0,
                        f"{check.description}: {n} violaciones, "
                        f"ej. {sample_violations(conn, check, 3)}",
                    )
            conn.close()


if __name__ == "__main__":
    unittest.main()
