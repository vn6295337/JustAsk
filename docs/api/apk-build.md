# JustAsk APK Build Steps - Phase 4.2

**Complete guide to build production APK and release to GitHub**

---

## Prerequisites

### 1. Install EAS CLI
```bash
npm install -g eas-cli
```

### 2. Verify Installation
```bash
eas --version
# Should output: eas/X.X.X
```

### 3. Expo Account Setup

If you don't have an Expo account:
```bash
eas auth:signup
```

If you have an account:
```bash
eas auth:login
```

### 4. Verify Node & NPM
```bash
node --version  # Should be 18+
npm --version   # Should be 9.6+
```

---

## Step 1: Prepare App Directory

```bash
cd justask/app
```

Verify files exist:
```bash
ls -la
# Should show:
# - App.js
# - app.json
# - package.json
# - eas.json (optional, will create if needed)
```

---

## Step 2: Create/Update eas.json (if needed)

If `eas.json` doesn't exist, create it:

```bash
cat > eas.json << 'EOF'
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "production": {
      "android": {
        "buildType": "apk"
      }
    }
  }
}
EOF
```

---

## Step 3: Clean Dependencies (if needed)

If you've had npm install issues:

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules
rm -rf node_modules

# Remove lock file
rm -f package-lock.json

# Fresh install
npm install
```

---

## Step 4: Start Build

### Option A: Guided Build (Recommended)

```bash
eas build --platform android --type apk
```

When prompted:
- **Build profile**: Press Enter (uses production profile)
- **Keystore**: Press Enter (use existing or create new)
- **Build type**: Confirm APK (not App Bundle)

Wait 5-15 minutes for build to complete.

### Option B: Direct Build Command

```bash
eas build --platform android --type apk --clear
```

The `--clear` flag clears previous build cache.

---

## Step 5: Monitor Build Progress

Option 1: **Watch in Terminal**
- Output will show real-time build status
- Wait for "Build complete" message

Option 2: **Check Online Dashboard**
```
https://expo.dev/dashboard
```
- Sign in with your Expo account
- Navigate to your app
- View build status and logs

---

## Step 6: Download APK

Once build completes:

### From Terminal Output:
```
Build complete!
APK URL: https://...
```

Copy and paste URL in browser to download.

### From Expo Dashboard:
1. Go to: https://expo.dev/dashboard
2. Select "justask" app
3. Click "Build" tab
4. Find latest build
5. Click "Download APK"

---

## Step 7: Verify APK

After downloading to `~/Downloads/`:

```bash
# Check file size
ls -lh ~/Downloads/justask*.apk

# Should show: ~45-50 MB

# Verify APK integrity
unzip -t ~/Downloads/justask*.apk > /dev/null && echo "APK valid" || echo "APK corrupted"

# Extract APK info
aapt dump badging ~/Downloads/justask*.apk | grep -E "package:|versionName:|versionCode:"
```

Expected output:
```
package: name='com.justask.app'
versionName='1.0.0'
versionCode='1'
```

---

## Step 8: Rename APK (Optional)

For clarity:

```bash
cp ~/Downloads/justask*.apk ~/Downloads/justask-v1.0.0.apk
```

---

## Step 9: Local Testing (Optional but Recommended)

### Test on Emulator:

1. Start Android emulator
2. Install APK:
   ```bash
   adb install ~/Downloads/justask-v1.0.0.apk
   ```

3. Launch app from emulator

4. Test:
   - [ ] App launches
   - [ ] Can type query
   - [ ] Tap Send button
   - [ ] Response appears
   - [ ] Settings tab accessible

### Test on Real Device:

1. Enable USB Debugging:
   - Settings → Developer Options → USB Debugging

2. Connect device via USB

3. Verify device recognized:
   ```bash
   adb devices
   # Should show device listed
   ```

4. Install APK:
   ```bash
   adb install ~/Downloads/justask-v1.0.0.apk
   ```

5. Test on device (same as above)

---

## Step 10: Prepare for GitHub Release

### Create release directory:

```bash
mkdir -p ~/justask-release
cp ~/Downloads/justask-v1.0.0.apk ~/justask-release/
cd ~/justask-release
```

### Verify file:
```bash
ls -lh justask-v1.0.0.apk
```

---

## Step 11: Create GitHub Release

### Option A: GitHub CLI

```bash
# Navigate to repo
cd justask

# Create release
gh release create v1.0.0 \
  --title "JustAsk v1.0.0 - MVP Release" \
  --notes "First release: Query any LLM, offline support, 7-day caching.

Features:
- Gemini, Groq, OpenRouter integration
- Offline query queueing with auto-sync
- 7-day response caching
- Zero cloud storage (local SQLite)
- Privacy-first design

Installation:
1. Download APK
2. Enable Unknown Sources (Settings > Security)
3. Install APK
4. Launch and start querying!

Privacy: All queries stored locally. No tracking. No analytics. No cloud sync." \
  ~/justask-release/justask-v1.0.0.apk
```

### Option B: GitHub Web UI

1. Go to: https://github.com/vn6295337/justask/releases

2. Click "Draft a new release"

3. Fill in:
   - **Tag:** `v1.0.0`
   - **Title:** `JustAsk v1.0.0 - MVP Release`
   - **Description:** (see release notes above)

4. **Attach files:**
   - Drag and drop `justask-v1.0.0.apk`

5. Click **"Publish release"**

---

## Step 12: Verify Release

```bash
# List releases
gh release list

# View specific release
gh release view v1.0.0
```

Check on GitHub:
```
https://github.com/vn6295337/justask/releases/tag/v1.0.0
```

Verify:
- [ ] Release visible
- [ ] APK downloadable
- [ ] Release notes display correctly
- [ ] File size shown (~50 MB)

---

## Step 13: Create Git Tag

In repo root:

```bash
cd justask

# Create tag
git tag v1.0.0-android-mvp

# Push tag
git push origin v1.0.0-android-mvp

# Verify
git tag -l
```

---

## Troubleshooting

### Build Fails with "Unauthorized"
```bash
# Re-login to Expo
eas logout
eas login
```

### Build Fails with "Invalid EAS project"
```bash
# Initialize EAS
eas project:create
```

### Build Takes Too Long
- Normal: 5-15 minutes
- Check status on https://expo.dev/dashboard
- Can check logs for errors

### APK Download Fails
- Try downloading from web dashboard instead
- Check internet connection
- Try build again with `--clear` flag

### GitHub Release Fails
```bash
# Verify gh CLI is logged in
gh auth login

# Try again
gh release create v1.0.0 ...
```

---

## Build Complete Checklist

- [ ] EAS CLI installed (`eas --version`)
- [ ] Logged into Expo account (`eas auth:login`)
- [ ] Node/npm correct versions
- [ ] In `justask/app` directory
- [ ] Build started (`eas build --platform android --type apk`)
- [ ] Build completed (5-15 min)
- [ ] APK downloaded
- [ ] APK verified (size ~50 MB)
- [ ] Tested on device/emulator (optional)
- [ ] GitHub release created
- [ ] APK uploaded to release
- [ ] Release notes added
- [ ] Git tag created (`git tag v1.0.0-android-mvp`)
- [ ] Tag pushed (`git push origin v1.0.0-android-mvp`)

---

## Next Steps

Once release is published:

1. **Share with Beta Testers**
   - Send GitHub release link
   - Get feedback
   - Monitor for crashes

2. **Monitor Production**
   - Check Render backend logs
   - Monitor rate limits
   - Track user issues

3. **Plan Phase 2**
   - iOS app
   - F-Droid distribution
   - New features based on feedback

---

## Commands Reference

```bash
# Install EAS
npm install -g eas-cli

# Login
eas login

# Build APK
eas build --platform android --type apk

# List releases (GitHub CLI)
gh release list

# Create release (GitHub CLI)
gh release create v1.0.0 --notes "..." justask-v1.0.0.apk

# Create git tag
git tag v1.0.0-android-mvp
git push origin v1.0.0-android-mvp

# Test APK on device
adb install justask-v1.0.0.apk
```

---

**You're ready to build and release!**
