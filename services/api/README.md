# Observation service

Run through the root Makefile or Compose. Package: `field_notebook`. Runtime: Python 3.11+.

`python -m field_notebook --help` shows host, port, database, root-path and ephemeral `--memory` options.
The default executable binds loopback. Compose explicitly binds the container interface; only its web proxy is published to the host.

Source modules: `domain.py` + `validation.py` own values; `ports.py` owns capability contracts; `policy.py` owns orchestration; `memory.py` and `sqlite_store.py` implement adapters; `http.py` maps HTTP; `__main__.py` composes.

This backend started from the Python workbook's tested implementation. Its storage contract tests are retained here so ecosystem changes cannot silently weaken replay, conflict, transaction or receipt semantics.
