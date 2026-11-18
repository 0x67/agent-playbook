#!/bin/sh
set -e
cat > request.md <<'X'
From: head of customer success
Subject: invoice export

Finance people at our customers keep asking support for a way to get invoices out of the app.
Today they open each invoice and retype it into their ledger. Support logged 41 tickets about
this last quarter. Can we add an export? CSV is probably fine. Only workspace admins and the
billing role can see invoices today.
X
