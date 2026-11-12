# Ledger export

The export runs nightly and writes one file per account. Nothing is uploaded until the batch closes. It is not a cron job, but a queue consumer: each message carries one account and its cut-off time.

Three things change in this release:

- The worker reads the cut-off from the message, retries failed accounts, and records each attempt.
- The file now lives in the archive bucket.
- The retry window lands in the config file.

Draft: the export holds the file in staging until finance signs off. The file stays visible to ops during that time. The file keeps its original name. The file is never edited after sign-off.

It works. And it scales.

Why this matters: a missing export used to surface only at month end. Now the alert fires the next morning, not after the close.
