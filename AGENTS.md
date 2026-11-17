# Agent guide

Use this repository to design or review Backblaze B2 storage for generative video workloads: corpus curation, diffusion training, self-hosted generation, hosted multi-provider generation with provenance, moderation and approval, and finishing and delivery.

<!-- CODEGRAPH_START -->
## CodeGraph

If a `.codegraph/` directory exists at the repository root, run `codegraph explore "<question or symbols>"` before grep, find or broad file reads to locate or understand code. If it doesn't exist, skip CodeGraph; indexing is the maintainer's call.
<!-- CODEGRAPH_END -->

## Sources of truth

1. `catalog/architectures.yaml` is the machine-readable catalog of architectures, third-party integrations (with `connection_type`) and external sample applications.
2. `schemas/architecture-catalog.schema.json` validates the catalog.
3. `architectures/*/architecture.md` holds the detailed design, B2 zones and security boundaries.
4. `examples/` contains B2 configuration templates.
5. Current Backblaze product behavior is authoritative at <https://www.backblaze.com/docs/cloud-storage>. Pricing is authoritative at <https://www.backblaze.com/cloud-storage/pricing>.

Describe the documented connection for each integration: a B2 backend or provider preset, a custom S3 endpoint, presigned URLs, or an application worker using an SDK. Specify the endpoint, region, addressing style, required operations, and credential scope. Attribute product capabilities to the linked vendor documentation or source code. Describe sample applications by the workflow they implement. Use `native-b2-option` for an actual B2 backend or B2-specific provider preset; use `s3-custom-endpoint` for a configurable S3 connection.

To read the summary and every architecture in a single file, use `llms-full.txt`.

## Generated files

After editing the catalog, run `python3 tools/generate_catalog.py`. Do not hand-edit the generated sections in `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt` or `llms-full.txt`. `llms-full.txt` concatenates the narrative pages, so regenerate it after editing `docs/gen-video.md` or any `architecture.md`.

```bash
python3 tools/generate_catalog.py --check
python3 tools/check_markdown_links.py            # add --external to probe outbound links
python3 -m pytest tests
```

## Operational invariants

- Derive `https://s3.<region>.backblazeb2.com` from the bucket region. Never hardcode a real region.
- Use scoped application keys: one bucket, one optional prefix, and a capability list per key. Keep master and admin keys out of runtime services.
- Object Lock applies per bucket, so retained data (raw footage, manifests, released weights) gets its own bucket.
- B2 lifecycle hides and then deletes by prefix and age; it cannot keep the last K objects.
- Event Notifications are enabled through Backblaze Support. Delivery is at-least-once and signed, so verify signatures and keep handlers idempotent.
- Treat presigned URLs as bearer credentials.
- Cloud Replication is bucket-to-bucket DR, not delivery.
- Never commit credentials, real presigned URLs or customer media.
