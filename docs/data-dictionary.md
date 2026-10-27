# Data dictionary

`data/processed/corpus.jsonl` is the canonical included corpus; one JSON object per bibliographic record. `screening_decisions.jsonl` includes exclusions. UTF-8 CSV exports use a BOM for Excel compatibility. Lists and nested objects remain JSON within CSV cells.

| Field | Meaning |
|---|---|
| id | First 16 hexadecimal SHA-256 characters of normalized DOI key, otherwise URL identity |
| doi | Lowercase DOI, empty if unknown; not a guarantee of peer review |
| title / authors / journal / publisher | Source metadata; missing values are not invented |
| date / date_source / year | Earliest available online field, then print, published or issued; precision varies |
| type | Source document type, not normalized across registries |
| tier / screening_reason | Scope decision and explicit rule code |
| tags | Rule-derived themes, not author keywords or verified method classifications |
| url / discovery_urls / streams | Main landing page and every retained discovery route |
| source / metadata_status | First metadata provider and current evidence level; source precedence is deterministic |
| abstract | Empty in public exports; original third-party abstract text is not redistributed |
| source_abstract_available | Whether an abstract existed in the original retrieval, not a redistribution grant |
| licenses | Deposited license declarations; scope and conflicts require assessment |
| relations | Original DOI relationships, not independently validated study equivalence |
| crossref_cited_by_snapshot | Crossref citation snapshot, incomplete and time dependent |
| reading_status / review_status | Fulltext reading and peer-review verification status, initially unverified |
| fulltext_status / local_pdf | Fetch status and retained original PDF if available |
| data_availability / code_availability | Assessed only with explicit source evidence; otherwise `not_assessed` |
| note_zh | Curator scope or evidence note |

`research_extraction_template.csv` adds empty research-question, decision-variable, model, method, data, baseline, evidence, limitation and replication fields. These are deliberately not inferred from titles.

`library.sqlite` provides `records` and an FTS5 `search` virtual table. SQLite FTS5 indexes title, authors, abstract and tags. See `scripts/search.py` for parameterized queries.

`citation_edges.jsonl` stores deposited backward references of the ten original seeds. Blank target DOI means unresolved reference, not a nonexistent publication. This is not a complete citation or co-citation network.

`possible_versions.json` lists normalized-title matches across identities. Similar titles with substantial wording differences can still be missed; data concept/version DOIs and thesis-derived articles need manual study-family linking.

`data/external_source_register.json` is a separate ledger for supplied web pages and other non-corpus leads. Each entry records source type, publication and review dates when known, access status, evidence role, a short claim summary when readable, limitations, and permitted use in this project. These entries are intentionally excluded from `corpus.jsonl`, bibliographic exports, citation edges, and corpus counts unless a primary scholarly or institutional record is independently identified and screened.

The bibliography omits project-news and portal entries, while the CSV/JSON/SQLite and offline viewer retain them. RIS/BibTeX can include preprints, posters and supporting data: import is not peer-review endorsement.
