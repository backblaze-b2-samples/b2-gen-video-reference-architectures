# B2 configuration examples

Configuration templates for the buckets in these [reference architectures](../docs/architecture-index.md). Run command blocks from this repository's `examples/` directory using Bash, the B2 CLI v4, and `jq`. Authenticate the CLI with a provisioning credential before creating buckets or application keys. Configuration fields are documented in the [B2 API reference](https://www.backblaze.com/apidocs).

Set `ORG` to a globally unique bucket-name prefix. Set the additional variables used by the selected command block, and replace values shown in `<angle brackets>` before running it. Choose retention periods, lifecycle settings, and application-key capabilities for the workload; lifecycle rules permanently delete expired object versions.

| File | Applies to | Purpose |
|---|---|---|
| `lifecycle-scratch.json` | curated, renders, delivery buckets | Hide `scratch/` after 7 days, delete 1 day later |
| `lifecycle-staging-hidden.json` | review bucket | Delete hidden and superseded `inbox/staging/` versions 7 days after they are hidden. It never hides current objects, so assets awaiting review stay; the moderator and publisher hide them on quarantine or promotion |
| `lifecycle-keep-latest.json` | delivery bucket | Keep only the latest version under `delivery/`: B2 keeps every version by default, so rewritten playlists, posters and re-renders otherwise accumulate as billed storage. Reuse the shape for any prefix whose keys are rewritten |
| `lifecycle-provider-inputs.json` | runs bucket | Expire provider input staging under `inputs/`; keep durable `runs/` outputs |
| `lifecycle-checkpoints.json` | training bucket | Hide `checkpoints/` after 30 days, delete 7 days later. Promote keepers before then, because B2 lifecycle works on prefix and age and cannot keep the last K checkpoints |
| `object-lock-governance.json` | raw and manifests buckets (defaults); models bucket (enable only) | Native API request fragments keyed by call: `fileLockEnabled` in `b2_create_bucket`, then `defaultRetention` in `b2_update_bucket`. Add the call's other required fields (`accountId`, plus `bucketName` and `bucketType` or `bucketId`) before sending; the CLI equivalents are below |
| `event-notifications-staging.json` | review bucket | Signed webhook on new `inbox/staging/` objects |
| `cors-playback.json` | delivery or renders bucket | Cross-origin GET/HEAD with Range for HLS players and review UIs |
| `bucket-info-cache-control.json` | delivery bucket | Default `Cache-Control` on downloads ([docs](https://www.backblaze.com/docs/cloud-storage-configure-cache-control-policies-with-the-native-api)); per-file metadata overrides it, for example a short max-age on HLS playlists |

Several prefixes share one bucket, so a lifecycle `--lifecycle-rules` value must contain every rule for that bucket. Merge the arrays before applying, because an update replaces the whole list. Never apply `lifecycle-scratch.json` (which hides current objects by age) to `inbox/staging/` or any prefix that holds assets awaiting review.

```bash
# Buckets (names are globally unique).
: "${ORG:?Set ORG to a globally unique prefix}"
b2 bucket create --file-lock-enabled "$ORG-genvid-raw" allPrivate
b2 bucket create "$ORG-genvid-curated" allPrivate
b2 bucket create "$ORG-genvid-datasets" allPrivate
b2 bucket create "$ORG-genvid-training" allPrivate
b2 bucket create --file-lock-enabled "$ORG-genvid-models" allPrivate  # retain released weights per object; no default
b2 bucket create "$ORG-genvid-renders" allPrivate
b2 bucket create "$ORG-genvid-runs" allPrivate
b2 bucket create --file-lock-enabled "$ORG-genvid-manifests" allPrivate
b2 bucket create --file-lock-enabled "$ORG-genvid-review" allPrivate   # lock enabled, no default retention: legal hold per object
b2 bucket create "$ORG-genvid-delivery" allPrivate

# Default retention on raw footage and manifests (governance; compliance mode cannot be shortened)
b2 bucket update --default-retention-mode governance --default-retention-period "365 days" "$ORG-genvid-raw"
b2 bucket update --default-retention-mode governance --default-retention-period "365 days" "$ORG-genvid-manifests"

# Lifecycle, CORS, cache headers
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-genvid-curated"
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-genvid-renders"
b2 bucket update --lifecycle-rules "$(cat lifecycle-provider-inputs.json)" "$ORG-genvid-runs"
b2 bucket update --lifecycle-rules "$(cat lifecycle-staging-hidden.json)" "$ORG-genvid-review"
# Delivery bucket: merge lifecycle-scratch.json and lifecycle-keep-latest.json into one array first
b2 bucket update --lifecycle-rules "$(jq -s add lifecycle-scratch.json lifecycle-keep-latest.json)" "$ORG-genvid-delivery"
b2 bucket update --lifecycle-rules "$(cat lifecycle-checkpoints.json)" "$ORG-genvid-training"
b2 bucket update --cors-rules "$(cat cors-playback.json)" "$ORG-genvid-delivery"
b2 bucket update --cors-rules "$(cat cors-playback.json)" "$ORG-genvid-renders"
b2 bucket update --bucket-info "$(cat bucket-info-cache-control.json)" "$ORG-genvid-delivery"

# Event Notifications are enabled on request by Backblaze Support. Rules use the native API
# b2_set_bucket_notification_rules (key needs writeBucketNotifications); the body is event-notifications-staging.json.
```

For the optional public-delivery variant, create a separate bucket containing only cleared delivery assets:

```bash
b2 bucket create "$ORG-genvid-public" allPublic
b2 bucket update --lifecycle-rules "$(cat lifecycle-keep-latest.json)" "$ORG-genvid-public"
b2 bucket update --cors-rules "$(cat cors-playback.json)" "$ORG-genvid-public"
b2 bucket update --bucket-info "$(cat bucket-info-cache-control.json)" "$ORG-genvid-public"
```

The models bucket has Object Lock enabled with no default retention. Set governance retention per released weight version; cached upstream weights remain removable. Set the provider-input lifecycle window to cover the queue and fetch window before applying it.

## Scoped application keys (one bucket, one optional prefix per key)

The pipeline writer includes `listBuckets` for the `HeadBucket` preflight used by the optional Genblaze backend. Its bucket restriction remains in effect. The separate manifest writer publishes approved audit copies to the retained manifest bucket.

```bash
# Models, self-hosted rendering, and hosted-provider runs
b2 key create --bucket "$ORG-genvid-models" model-publisher listFiles,readFiles,writeFiles,writeFileRetentions
b2 key create --bucket "$ORG-genvid-models" --name-prefix models/ worker-model-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-models" --name-prefix loras/ worker-lora-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-renders" worker-render-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-renders" --name-prefix renders/ render-share-signer readFiles
b2 key create --bucket "$ORG-genvid-runs" pipeline-writer listBuckets,listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-runs" --name-prefix inputs/ input-signer readFiles

# Curation, training, review, and delivery
b2 key create --bucket "$ORG-genvid-curated" --name-prefix curated/ shard-source-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-datasets" --name-prefix datasets/ shard-packer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-datasets" --name-prefix datasets/ trainer-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-training" --name-prefix artifacts/ artifact-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-review" --name-prefix published/ finishing-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-delivery" finishing-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-delivery" transcoder listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-delivery" --name-prefix renders/ mux-signer readFiles
b2 key create --bucket "$ORG-genvid-raw"       --name-prefix raw/           ingest-writer        listFiles,writeFiles
b2 key create --bucket "$ORG-genvid-raw"       --name-prefix raw/           curation-reader      listFiles,readFiles
b2 key create --bucket "$ORG-genvid-raw"                                    takedown-admin       listFiles,readFiles,deleteFiles,bypassGovernance   # audited break-glass only
b2 key create --bucket "$ORG-genvid-curated"                                curated-writer       listFiles,readFiles,writeFiles,deleteFiles
b2 key create --bucket "$ORG-genvid-training"  --name-prefix checkpoints/   checkpoint-writer    listFiles,readFiles,writeFiles,deleteFiles
b2 key create --bucket "$ORG-genvid-training"  --name-prefix checkpoints/   promotion-reader     listFiles,readFiles   # publisher downloads keepers with this
b2 key create --bucket "$ORG-genvid-manifests" --name-prefix manifests/     manifest-writer      listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-genvid-review"    --name-prefix inbox/staging/ generator-writer     writeFiles
b2 key create --bucket "$ORG-genvid-review"    --name-prefix inbox/         moderator            listFiles,readFiles,writeFiles,deleteFiles
b2 key create --bucket "$ORG-genvid-review"    --name-prefix inbox/staging/ mam-staging-reader   listFiles,readFiles
b2 key create --bucket "$ORG-genvid-review"    --name-prefix published/     mam-published-reader listFiles,readFiles
b2 key create --bucket "$ORG-genvid-review"                                 publisher            listFiles,readFiles,writeFiles   # copies to published/, hides staging; no deleteFiles
b2 key create --bucket "$ORG-genvid-review"                                 legal-hold-admin     readFileLegalHolds,writeFileLegalHolds
b2 key create --bucket "$ORG-genvid-delivery"  --name-prefix delivery/      edge-signer          readFiles
```

`b2 key create` prints the secret once. Store it in a secrets manager or a gitignored `0600` `.env`, never in shell history, job specs or logs. Bucket, lifecycle, retention and notification changes need an admin key (or the master key). Run them once from provisioning and keep that key out of runtime services.

## LanceDB embedding tables

Use the [LanceDB connection profile](lancedb.md) for pinned dependencies, credential scope and single-writer commit requirements.
