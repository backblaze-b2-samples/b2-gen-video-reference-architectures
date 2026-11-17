# Contributing

The architecture catalog is the extension point. Edit `catalog/architectures.yaml`, then run `python3 tools/generate_catalog.py`. Do not hand-edit generated README tables or indexes.

- **New architecture:** copy an existing `architectures/*/architecture.md` and name it after the use case, not the tool. Add its audience, problem, workflow, capabilities, integrations, `off_object_storage`, scale, security, compliance and links to the catalog. Reuse the configs in `examples/`.
- **New integration:** add it under the relevant catalog architecture with:
  - `connection`
  - `connection_type` (one of the shared values in `CONNECTION_LABELS` in `tools/generate_catalog.py`)
  - `url` (authoritative documentation) and, where one exists, `setup_url` (the B2 setup guide)

  Connection types and their labels are shared across the B2 category repos. If this repo does not use a value yet, add it to the schema enum and `CONNECTION_LABELS` in the same change; a test checks that the enum matches what the catalog uses.
- **New sample application:** build it in its own repository (for example under `backblaze-b2-samples`), then add a `samples:` entry to the catalog with `group`, `summary` and, where it fits, `architectures` and `relevance`.
- Regenerate `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt` and `llms-full.txt` in the same change.

**Content rules:**
- Attribute to a vendor only what its docs or code show, and label B2-side patterns as such.
- Never hardcode a region or endpoint.
- Link to B2 pricing instead of quoting numbers.

**Security:** never put real keys anywhere. Use scoped keys, not the master key, unless provisioning requires it, and say so when it does.

**Tests:** run `python3 tools/generate_catalog.py --check`, `python3 tools/check_markdown_links.py` and `python3 -m pytest tests`. When you add outbound links, also run `python3 tools/check_markdown_links.py --external`.
