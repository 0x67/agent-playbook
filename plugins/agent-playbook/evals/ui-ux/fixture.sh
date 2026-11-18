#!/bin/sh
set -e
cat > brief.md <<'X'
# Members screen

Workspace admins see the list of members with name, email, role, and last active date.
An admin can invite a member by email from a dialog, change a member's role, and remove a member.
Viewers can open the screen but cannot change anything.
X
cat > tokens.css <<'X'
:root {
  --color-surface: #ffffff;
  --color-surface-raised: #f6f7f9;
  --color-text: #1b1f24;
  --color-text-muted: #5b6470;
  --color-border: #d5d9df;
  --color-action-primary: #1f5fd1;
  --color-on-action-primary: #ffffff;
  --color-text-danger: #b3261e;
  --space-2: 8px;
  --space-4: 16px;
  --space-6: 24px;
  --radius-md: 8px;
}
X
