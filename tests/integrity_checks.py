"""
Invariantes de integridad para las bases de datos del grafo (tablas `words` y `relations`).

Cada invariante es una consulta SQL que cuenta las filas que la violan: una base
correcta debe devolver 0 en todas. No requiere BabelNet y recorre el 100 % de los datos.

Uso como script (reporte para todas las bases indicadas):
    python tests/integrity_checks.py database.db api_database.db
"""
import sqlite3
import sys
from dataclasses import dataclass

LANGUAGES = ("EN", "ES")
RELATION_TYPES = ("definition", "translation")


@dataclass(frozen=True)
class Check:
    name: str
    description: str
    # SELECT que devuelve las filas que violan la invariante; se cuenta con COUNT(*)
    violations_sql: str


CHECKS = [
    Check(
        "definition_same_language",
        "Una relación 'definition' une palabras del mismo idioma",
        """
        SELECT r.id, a.word, a.language, b.word, b.language
        FROM relations r
        JOIN words a ON r.word1_id = a.id
        JOIN words b ON r.word2_id = b.id
        WHERE r.relation_type = 'definition' AND a.language <> b.language
        """,
    ),
    Check(
        "translation_well_formed",
        "Una relación 'translation' une idiomas distintos con el mismo concepto",
        """
        SELECT r.id, a.word, a.language, a.concept, b.word, b.language, b.concept
        FROM relations r
        JOIN words a ON r.word1_id = a.id
        JOIN words b ON r.word2_id = b.id
        WHERE r.relation_type = 'translation'
          AND (a.language = b.language OR a.concept IS NOT b.concept)
        """,
    ),
    Check(
        "no_duplicate_null_concept",
        "No hay palabras duplicadas (word, language) con concept NULL",
        """
        SELECT word, language, COUNT(*)
        FROM words
        WHERE concept IS NULL
        GROUP BY word, language
        HAVING COUNT(*) > 1
        """,
    ),
    Check(
        "no_duplicate_concept",
        "No hay palabras duplicadas (word, language, concept) con concept no NULL",
        """
        SELECT word, language, concept, COUNT(*)
        FROM words
        WHERE concept IS NOT NULL
        GROUP BY word, language, concept
        HAVING COUNT(*) > 1
        """,
    ),
    Check(
        "no_orphan_relations",
        "Toda relación apunta a palabras existentes",
        """
        SELECT id, word1_id, word2_id
        FROM relations
        WHERE word1_id NOT IN (SELECT id FROM words)
           OR word2_id NOT IN (SELECT id FROM words)
        """,
    ),
    Check(
        "known_relation_types",
        f"relation_type pertenece a {RELATION_TYPES}",
        f"""
        SELECT id, relation_type
        FROM relations
        WHERE relation_type NOT IN {RELATION_TYPES}
        """,
    ),
    Check(
        "known_languages",
        f"language pertenece a {LANGUAGES}",
        f"""
        SELECT id, word, language
        FROM words
        WHERE language NOT IN {LANGUAGES}
        """,
    ),
    Check(
        "words_trimmed",
        "Ninguna palabra es vacía ni tiene espacios al inicio o al final",
        """
        SELECT id, '[' || word || ']', language
        FROM words
        WHERE TRIM(word) = '' OR word <> TRIM(word)
        """,
    ),
]


def count_violations(conn, check):
    return conn.execute(f"SELECT COUNT(*) FROM ({check.violations_sql})").fetchone()[0]


def sample_violations(conn, check, limit=5):
    return conn.execute(f"SELECT * FROM ({check.violations_sql}) LIMIT ?", (limit,)).fetchall()


def connect_read_only(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def report(path):
    conn = connect_read_only(path)
    words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    relations = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    print(f"\n== {path}  ({words} palabras, {relations} relaciones)")
    failed = 0
    for check in CHECKS:
        n = count_violations(conn, check)
        status = "OK  " if n == 0 else "FAIL"
        failed += n > 0
        print(f"  [{status}] {check.name:<28} {n:>8}  {check.description}")
        for row in sample_violations(conn, check) if n else []:
            print(f"           ej: {row}")
    conn.close()
    return failed


if __name__ == "__main__":
    paths = sys.argv[1:] or ["database.db", "api_database.db"]
    total_failed = sum(report(p) for p in paths)
    sys.exit(1 if total_failed else 0)
