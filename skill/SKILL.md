---
name: b2-gen-video
description: Design or review Backblaze B2 storage for generative video. Covers training-corpus curation (Cosmos Curator, Daft, Pixeltable, video2dataset), diffusion training with streamed shards and checkpoints (MosaicML Streaming, LitData, Ray Train, MLflow, ZenML, W&B), self-hosted ComfyUI farms, hosted multi-provider generation with provenance manifests (application workers, Runway, Replicate), moderation and approval (Event Notifications, legal hold, iconik), and finishing and CDN delivery (Cloudflare, Fastly, bunny.net, Mux).
---

# B2 for generative video

Pick a workflow from the bundled [architecture catalog](references/architecture-catalog.md). It also lists the related B2 sample applications.

Use the canonical [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage) for service behavior, limits and setup steps, since these change. Link pricing claims to [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) instead of copying numbers.

## Rules
- For LanceDB embedding tables, follow the architecture's pinned connection profile and serialize all table mutations through one writer service. Endpoint settings alone do not establish safe commit behavior across Lance versions.
- Use the S3-compatible API. Derive `https://s3.<region>.backblazeb2.com` from `B2_REGION` and never hardcode a region or endpoint.
- Configure each integration through its documented B2 backend or provider preset, custom S3 endpoint, or SDK-based worker, with the required operations and credential scope. For tools that only accept URLs (Replicate, Mux), hand over a presigned GET URL. For tools with an upload API (Runway), the app reads from B2 with a scoped key and relays the bytes.
- Each key covers one bucket, one optional prefix and a set of capabilities. Give each role its own key: ingest-writer, curation-reader, trainer-reader, checkpoint-writer, worker-model-reader, manifest-writer, moderator, edge-signer. Group pre-approval stages under one prefix (`inbox/`) so one key covers them without reaching `published/`. Use the master key only for provisioning.
- Bucket names are globally unique, so expect collisions.
- Object Lock is set per bucket. Use governance-mode default retention for raw-footage and manifest buckets. The models bucket has no default; set retention per released weight version, so an audited `bypassGovernance` takedown key can still honour licence revocation and erasure requests. Legal hold also requires a lock-enabled bucket.
- B2 lifecycle rules hide and then delete by prefix and age. They cannot keep the last K checkpoints, so promote keepers before they expire. B2 keeps every version by default; add a keep-latest rule where keys are rewritten, and never age-hide a prefix that holds assets awaiting review.
- Event Notifications must be enabled by Support. Delivery is at-least-once, so verify `X-Bz-Event-Notification-Signature`, acknowledge quickly and make handlers idempotent.
- Copy provider outputs into B2 as soon as they are returned, because provider URLs expire (Replicate deletes API outputs after one hour by default). Write the manifest last. Verify asset hashes against the manifest; sign the manifest or use C2PA to establish authenticity.
- Relay Runway inputs through its ephemeral upload API (`runway://` URI, 24 h). Its URL ingest sends HEAD requests and a SigV4 presigned URL is signed for one method, so use the upload API or a public or CDN-fronted URL instead of a GET-presigned URL.
- For delivery, put a private bucket behind a signing edge app. Backblaze charges no download fees for egress to CDN partners (see pricing). Cloud Replication is DR, not delivery.
- Use Overdrive only when sustained training or curation reads are the measured bottleneck. Otherwise use Standard B2 with an NVMe cache.
- Keep these off B2: queues, tracking, rights, MAM and billing databases, in-RAM indexes, VRAM, NVMe scratch, signing keys and provider keys.

## Verify

Inside the full repository, run the validation commands in its `AGENTS.md`. When this skill is installed on its own, check recommendations against the linked product and integration documentation.
