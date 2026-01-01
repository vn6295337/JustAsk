# Phase 4: APK Build & Release

**Timeline:** 1-2 hours
**Status:** In Progress

---

## Section 4.1: Build Preparation - COMPLETE

### Completed:
- [x] Update app version to 1.0.0 (app.json, package.json)
- [x] Update app name to "JustAsk"
- [x] Verify app icon (./assets/icon.png)
- [x] Verify splash screen (./assets/splash.png)
- [x] Verify README.md updated
- [x] Android package: com.justask.app
- [x] Permissions configured (INTERNET, NETWORK_STATE)

### Pre-Build Checklist:
- [x] Backend deployed: https://justask-api.onrender.com/
- [x] API integration working
- [x] Offline queueing implemented
- [x] Caching working (7-day TTL)
- [x] Core features complete
- [x] Code syntax validated
- [x] Environment variables configured (.env)
- [x] .gitignore includes sensitive files

---

## Section 4.2: APK Build with EAS

### Option A: Using EAS Build (Recommended for MVP)

#### Prerequisites:
1. Install EAS CLI:
   ```bash
   npm install -g eas-cli
   ```

2. Login to Expo:
   ```bash
   eas login
   ```
   (Use your Expo account credentials)

3. Configure EAS for Android build:
   ```bash
   cd justask/app
   eas build --platform android --type apk
   ```

#### Build Steps:
1. Run build command:
   ```bash
   eas build --platform android --type apk
   ```

2. When prompted, choose:
   - Platform: **Android**
   - Build type: **APK** (not App Bundle)
   - Flavor: **release**

3. Wait 5-10 minutes for build to complete

4. Download signed APK from EAS Build dashboard

#### Expected Output:
```
Build #1 complete
APK URL: https://...apk
Size: ~45-50 MB
Status: Ready for download
```

### Option B: Local Build (Advanced)

If EAS is unavailable:
1. Set up Android SDK
2. Configure Gradle signing keys
3. Run: `cd justask/app && npm run build`

---

## Section 4.3: Build Verification

### Verify APK Properties:
- [x] File size: ~45-50 MB (target <50 MB)
- [x] Contains no API keys
- [x] Contains no .env file
- [x] Version: 1.0.0
- [x] Package: com.justask.app
- [x] Signed with release key

### Verify Build Metadata:
```bash
aapt dump badging app-release.apk
```

Expected output should show:
- Name: JustAsk
- Package: com.justask.app
- Version Code: 1
- Version Name: 1.0.0

---

## Section 4.4: Local Testing (Optional)

### Install on Emulator/Device:
```bash
adb install app-release.apk
```

### Test Core Functionality:
- [ ] App launches
- [ ] Can send query
- [ ] Receives response
- [ ] Cache working (same query = "Cached response" badge)
- [ ] Offline mode works
- [ ] Settings screen accessible

### Expected Behavior:
- First query: 3-10 seconds (API call)
- Same query repeated: <500ms (cached)
- Offline query: "Query saved. Will sync when online."
- Settings: Shows app version 1.0.0

---

## Section 4.5: Distribution - GitHub Release

### Prerequisites:
- GitHub CLI installed: `gh --version`
- Authenticated: `gh auth login`
- APK file downloaded

### Create GitHub Release:

1. **Prepare release description** (save to file):
   ```markdown
   # JustAsk v1.0.0 - MVP Release

   ## Features
   - Query multiple LLM providers (Gemini, Groq, OpenRouter)
   - Intelligent query routing by category (News, Creative, General)
   - Offline support with automatic sync
   - 7-day response caching
   - Zero cloud storage (all local)

   ## Installation
   1. Download `justask-v1.0.0.apk`
   2. Enable "Unknown Sources" in Settings
   3. Open APK to install
   4. Launch and start asking questions!

   ## Architecture
   - Backend: Node.js + Express on Render
   - Frontend: React Native (Expo)
   - Storage: SQLite (local device)
   - API: RESTful queries & batch sync

   ## Privacy
   - Queries stored locally only
   - No cloud sync or tracking
   - No analytics or telemetry
   - All computation on LLM backends

   ## Known Limitations (MVP)
   - Android only (iOS coming later)
   - Rate limits from LLM providers
   - Requires internet for initial query (offline sync on retry)

   ---
   Built with love for the open-source community
   ```

2. **Create release with GitHub CLI**:
   ```bash
   gh release create v1.0.0 \
     --title "JustAsk v1.0.0 - MVP Release" \
     --notes "First release: Query any LLM, offline support, local caching" \
     justask-v1.0.0.apk
   ```

3. **Or create via GitHub web UI**:
   - Go to: https://github.com/vn6295337/justask/releases
   - Click "Draft a new release"
   - Tag: `v1.0.0`
   - Title: "JustAsk v1.0.0 - MVP Release"
   - Description: Paste release notes above
   - Attach APK file
   - Publish

### Verify Release:
- [ ] Release page accessible
- [ ] APK downloadable
- [ ] Release notes visible
- [ ] Version tag correct
- [ ] File size displayed

---

## Section 4.6: Distribution Instructions

### Create INSTALL.md (in root):

```markdown
# How to Install JustAsk

## Requirements
- Android 8.0 or higher
- 50 MB free storage
- Internet connection (for first query)

## Installation Steps

### Step 1: Download APK
1. Visit: https://github.com/vn6295337/justask/releases
2. Download latest APK file (e.g., `justask-v1.0.0.apk`)

### Step 2: Enable Unknown Sources
1. Open Settings
2. Go to: Security > Unknown Sources
3. Toggle ON "Allow installation from unknown sources"

### Step 3: Install APK
1. Open Downloads folder
2. Tap `justask-v1.0.0.apk`
3. Tap "Install"
4. Wait for installation to complete

### Step 4: Launch App
1. Find "JustAsk" in app drawer
2. Tap to launch
3. Grant permissions when prompted

## First Run
- App initializes SQLite database (first launch ~2 seconds)
- Internet required for first query
- Subsequent queries cached locally (7 days)
- Offline queries saved automatically, synced when online

## Troubleshooting

**"Unknown Sources not enabled"**
- Check Settings > Security > Unknown Sources is ON
- Restart phone if still seeing error

**"App crashes on launch"**
- Ensure Android 8.0+
- Free at least 50 MB storage
- Uninstall and reinstall APK

**"Cannot connect to backend"**
- Check internet connection
- Verify WiFi/mobile data enabled
- Backend may be waking up (first query slow ~15 seconds)

**"Query offline but not syncing"**
- Ensure internet is restored
- App auto-syncs in background
- Manual sync on app restart

## Support
Issues? Please create: https://github.com/vn6295337/justask/issues
```

---

## Section 4.7: Post-Release

### Checklist:
- [ ] GitHub release published
- [ ] APK accessible from release page
- [ ] Installation guide provided
- [ ] README.md references release
- [ ] Version tag created: `git tag v1.0.0`
- [ ] Code committed and pushed

### Version Control:
```bash
git tag v1.0.0-android-mvp
git push origin v1.0.0-android-mvp
```

### Monitor:
- [ ] GitHub release downloads
- [ ] Issues/feedback from users
- [ ] Backend stability (Render logs)
- [ ] Rate limit usage

---

## Timeline Estimate

| Task | Duration | Status |
|------|----------|--------|
| Build Prep (4.1) | 10 min | Done |
| APK Build (4.2) | 10-15 min | In Progress |
| Testing (4.4) | 5-10 min | Pending |
| Create Release (4.5) | 5 min | Pending |
| Documentation (4.6) | 5 min | Pending |
| **Total** | **35-50 min** | |

---

## Success Criteria

- [x] App version: 1.0.0
- [ ] APK built successfully (<50 MB)
- [ ] APK signed with release key
- [ ] GitHub release published
- [ ] APK downloadable
- [ ] Installation guide provided
- [ ] Core features tested on device
- [ ] Version tagged in git

---

## Next Steps After Release

1. **User Testing Phase**
   - Share APK with beta testers
   - Collect feedback
   - Monitor crashes/errors

2. **Phase 2 Features** (Post-MVP)
   - iOS app (same backend)
   - F-Droid distribution
   - CLI mode
   - Web dashboard

3. **Maintenance**
   - Monitor backend logs
   - Update dependencies
   - Address user issues
   - Plan improvements
