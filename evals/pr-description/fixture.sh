#!/bin/sh
set -e
cat > change.diff <<'X'
--- a/src/cache.rs
+++ b/src/cache.rs
@@ -10,9 +10,14 @@ impl Cache {
-    pub fn get(&self, key: &str) -> Option<Bytes> {
-        self.map.get(key).cloned()
+    pub fn get(&self, key: &str) -> Option<Bytes> {
+        let entry = self.map.get(key)?;
+        if entry.expires_at <= Instant::now() {
+            return None;
+        }
+        Some(entry.value.clone())
     }
X
