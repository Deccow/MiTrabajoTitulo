To run local scrapper, you need to:

- DOWNLOAD babelnet-ccbysa-5.3 from BabelNet and place on the root folder

- Download Lucene 8.11.4

- Run LuceneReader JavaSpringBoot App

## Integrity tests

`tests/` checks integrity invariants over 100% of the `words` and `relations` tables
(no BabelNet access needed). Each invariant is an SQL query that counts the rows
violating it; a correct database returns 0 for every one:

- `definition` relations link words of the same language
- `translation` relations link different languages with the same concept
- no duplicated `(word, language)` with `concept` NULL
- no duplicated `(word, language, concept)` with `concept` not NULL
- every relation points to existing words
- `relation_type` is `definition` or `translation`
- `language` is `EN` or `ES`
- no empty words and no leading/trailing spaces

Run from `new_app/`:

```
python -m unittest discover -s tests -v
python tests/integrity_checks.py database.db api_database.db
```

The unit tests first validate the queries themselves on an in-memory database: a clean
version passes every invariant, and one defect of each kind is seeded to verify that only
the matching invariant detects it. Then all invariants run on the real databases
(`database.db`, `api_database.db`; override with `INTEGRITY_DBS="a.db;b.db"`).
The report script prints, for each database, the number of violations per invariant and
up to 5 examples.



