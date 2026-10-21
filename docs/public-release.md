# Public release and private research inputs

This public repository starts from a reviewed, metadata-only snapshot. Earlier commits and raw collection material remain in a separate private archive; they are not ancestors of this repository. The public repository has the original project URL.

The corpus retains 1,071 bibliographic records, screening decisions and rule-derived themes. Original abstracts are omitted from JSONL, CSV, SQLite, RIS, embedded HTML and map payloads. `source_abstract_available` records only whether an abstract existed in the original retrieval, not permission to redistribute it. The original 465 available abstracts are not 465 publicly released abstracts.

Raw retrieval responses are private/local research inputs, not included in this snapshot. Search expressions, request logs, DOI identities, source links and original seed-reference edges remain available. Tags and screening decisions were established on the original available title/abstract material; they cannot be fully rerun from an abstract-stripped public snapshot alone. This limitation is intentional and must not be hidden.

For local reacquisition, run `harvest.py`, `discover.py` and `enrich.py` as applicable. They save raw inputs under ignored paths. `build.py` performs screening using local inputs and strips original abstracts before writing distributable records. Source availability, metadata drift and incomplete current-year coverage still apply. Recheck record counts and map changes after every new retrieval.

To regenerate the current public exports without new retrieval, use the committed processed JSONL as the release input, `build_map.py` for maps, and `finalize.py` for the README. Run `validate_public.py` before pushing and `package_public.py` for public archives. Only materials with separately established permissions should ever be deliberately added beyond this default.
