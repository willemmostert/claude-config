---
name: no-node-modules-on-gdrive
description: npm install corrupts node_modules on Google Drive virtual filesystem -- always clone repos to local disk
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fb0588ea-4b10-47af-9d34-53184c04129a
---

Never run npm install inside a Google Drive-synced folder. The virtual filesystem corrupts tar extraction (TAR_ENTRY_ERROR) and breaks symlinks in node_modules.

**Why:** Google Drive's virtual FS can't handle deep nested paths and symlinks that npm creates. Modules install but end up with invalid package.json files and missing dependencies.

**How to apply:** When setting up the dev environment, always clone wurk-app and wurk-api to a local disk path (e.g. C:\Dev\wurk-app on Windows, ~/Dev/wurk-app on Mac). The GotWurk EA folder and context files can stay on Google Drive since they're just markdown.
