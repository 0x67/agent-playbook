# Ledger export

The export runs nightly and writes one file per account. The upload waits until the batch closes. A queue consumer runs the export, and each message is for one account and includes its cut-off time.

Changes in this release:

- The worker reads the cut-off from the message, retries failed accounts, and records each attempt.
- Export files go to the archive bucket.
- The retry window is set in the config file.

Each file waits in staging until finance signs off, and ops can see it there. Files keep their original names and are never edited after sign-off.

A missing export used to show up only at month end. The alert now fires the next morning.
