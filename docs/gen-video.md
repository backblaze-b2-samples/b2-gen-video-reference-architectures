# Generative video on Backblaze B2 (agent-readable)

Catalog updated: 2026-11-16. The [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage) is the authority on current product behavior.

## Workload
Generative video produces more data per request than almost any other AI workload. Training corpora run from hundreds of TB to PB, checkpoints from tens of GB to TB, and every generation leaves behind keyframes, takes, variants, frame sequences and delivery renditions. Hosted model providers return result URLs that expire.

## Where does B2 fit?
B2 can be the durable system of record across that lifecycle:

- raw footage lake and versioned shard releases that training clusters in any GPU cloud stream from;
- checkpoint, LoRA and model-weight store that ComfyUI and Diffusers workers pull from;
- output sink and provenance-manifest store for hosted multi-provider generation, with Object Lock on a dedicated bucket where retention matters;
- review and approval stages driven by Event Notifications and legal hold;
- CDN origin, with no B2 download fees for egress to CDN partners.

Configure each integration with the B2 regional endpoint, bucket region, addressing style, and scoped credentials specified in its setup guide. Select a B2-specific provider preset where the integration offers one. For APIs that only ingest URLs, hand over a presigned URL; for a CDN, use the bucket as origin.

## Which architecture fits my use case?

| Use case | Architecture | Key integrations |
|---|---|---|
| Curate a text-to-video training corpus from licensed footage | [curate-video-training-corpus](../architectures/curate-video-training-corpus/architecture.md) | rclone, video2dataset, Cosmos Curator, Daft, Pixeltable, LanceDB |
| Stream shards into training; version checkpoints and LoRAs | [stream-shards-train-video-diffusion](../architectures/stream-shards-train-video-diffusion/architecture.md) | MosaicML Streaming, LitData, Ray Train, Composer, MLflow, ZenML, W&B |
| Self-hosted ComfyUI farm with shared weights and outputs | [self-hosted-video-diffusion-farm](../architectures/self-hosted-video-diffusion-farm/architecture.md) | ComfyUI Cloud Storage nodes, HF Cache Sync |
| Hosted multi-provider generation with provenance | [hosted-multi-provider-generation-provenance](../architectures/hosted-multi-provider-generation-provenance/architecture.md) | Application workers, Runway API, Replicate |
| Moderate, review and approve before publishing | [moderate-review-approve-generated-video](../architectures/moderate-review-approve-generated-video/architecture.md) | iconik, EditShare FLOW, B2 Event Notifications |
| Finish, transcode and deliver through a CDN | [finish-package-deliver-generated-video](../architectures/finish-package-deliver-generated-video/architecture.md) | Cloudflare, bunny.net, Fastly, Telestream Vantage, Mux |

## B2 capabilities that apply
- **Access:** S3-compatible API, presigned URLs (provider handoff, review, Mux ingest), CORS for players, multipart upload for masters and checkpoints, and scoped application keys (one bucket, one optional prefix, and a capability list per key).
- **Change and lifecycle:** Event Notifications (signed webhooks, at-least-once delivery, enabled through Backblaze Support), and lifecycle rules that hide and then delete objects by prefix and age.
- **Protection:** Governance-mode default retention on raw footage and manifests, per-object retention on released weights, and legal hold on disputed assets. SSE-B2 is optional. Cloud Replication is bucket-to-bucket DR, not delivery.
- **Delivery:** server-side copy for stage promotion, `Cache-Control` from bucket info, and CDN-partner egress terms. See [pricing](https://www.backblaze.com/cloud-storage/pricing).

## When Overdrive may apply
[B2 Overdrive](https://www.backblaze.com/cloud-storage/b2-overdrive) may apply to sustained, high-throughput reads: multi-node diffusion training streaming shards, or GPU curation passes over PB of footage, where measurement shows object-store throughput rather than GPU decode is the bottleneck. Benchmark shard size and worker count against B2 first. Overdrive does not apply to hosted-API generation, moderation, or CDN-cached delivery.

## Where B2 does not fit
Keep these off object storage:

- job queues
- experiment-tracking, rights, MAM and billing databases
- in-RAM vector indexes
- node-local NVMe shard and weight caches
- GPU VRAM
- scratch frames during a render
- provider API keys and signing keys
- CDN edge caches

B2 is not a POSIX filesystem for in-place edits, and Cloud Replication is not a customer delivery mechanism.

## Provider output retention
Replicate deletes API outputs after one hour by default, so copy them to B2 within that window.

## Links
[README](../README.md) - [Architecture index](architecture-index.md) - [Related B2 samples](related-b2-samples.md) - [B2 config examples](../examples/README.md) - [B2 docs](https://www.backblaze.com/docs/cloud-storage) - [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) - [Backblaze Labs](https://backblazelabs.com/) - [B2 samples](https://github.com/backblaze-b2-samples)
