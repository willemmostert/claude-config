---
name: dev-environment
description: "Dev environment setup notes -- clone locally, run Expo with npx expo start"
metadata: 
  node_type: memory
  type: project
  originSessionId: fb0588ea-4b10-47af-9d34-53184c04129a
---

wurk-app and wurk-api must be cloned to a local disk, not run from Google Drive. See [[no-node-modules-on-gdrive]].

**Setup steps for a new machine:**
1. Clone repos locally: `git clone https://github.com/willemmostert/wurk-app.git ~/Dev/wurk-app`
2. `cd ~/Dev/wurk-app && npm install`
3. `npx expo start` for dev server (add `--web` for browser preview)
4. Expo Go app on phone can scan QR code for mobile preview

**Tech stack:** Expo SDK 56, React Native 0.85, Expo Router (file-based), TypeScript

**Why:** Google Drive corrupts node_modules during npm install. Local clone is required for development. Git keeps everything in sync.
