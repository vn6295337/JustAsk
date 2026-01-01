# Quick APK Build & Release Checklist

**Complete Phase 4.2 & 4.3 in 30 minutes**

---

## Prerequisites (Do Once)

```bash
# 1. Install EAS CLI
npm install -g eas-cli

# 2. Login to Expo
eas login
# Enter your Expo credentials

# 3. Verify installation
eas --version
# Should show: eas/X.X.X
```

---

## Build APK (Phase 4.2)

### Step 1: Navigate to app directory
```bash
cd justask/app
```

### Step 2: Start build
```bash
eas build --platform android --type apk
```

### Step 3: When prompted
- Press Enter for default profile (production)
- Choose: APK (not App Bundle)

### Step 4: Wait 5-15 minutes
- Monitor at: https://expo.dev/dashboard
- Or watch terminal output

### Step 5: Download APK
```bash
# When build completes, copy download URL
# Or download from dashboard
# Save as: justask-v1.0.0.apk
```

### Expected Result
- File size: ~45-50 MB
- Signed and ready to release
- Contains version 1.0.0

---

## Release to GitHub (Phase 4.3)

### Step 1: Create GitHub release
```bash
cd justask

# Using GitHub CLI
gh release create v1.0.0 \
  --title "JustAsk v1.0.0 - MVP Release" \
  --notes "First release: Query multiple LLMs, offline support, response caching." \
  /path/to/justask-v1.0.0.apk
```

**OR manually on GitHub:**
1. Go to: https://github.com/vn6295337/justask/releases
2. Click "Draft a new release"
3. Tag: `v1.0.0`
4. Title: `JustAsk v1.0.0 - MVP Release`
5. Upload APK file
6. Publish

### Step 2: Create git tag
```bash
git tag v1.0.0-android-mvp
git push origin v1.0.0-android-mvp
```

### Step 3: Verify release
- [ ] Visit: https://github.com/vn6295337/justask/releases/tag/v1.0.0
- [ ] APK downloadable
- [ ] Release notes visible
- [ ] File size shown (~50 MB)

---

## Final Checklist

- [ ] EAS CLI installed (`npm install -g eas-cli`)
- [ ] Logged into Expo (`eas login`)
- [ ] APK built successfully
- [ ] APK downloaded (~50 MB)
- [ ] GitHub release created
- [ ] APK uploaded to release
- [ ] Git tag created and pushed
- [ ] Release visible on GitHub

---

## What's Included in Release

**Complete MVP:**
- Backend deployed: https://justask-api.onrender.com/
- 3 LLM providers (Gemini, Groq, OpenRouter)
- Intelligent routing (News, Creative, General)
- Offline queueing with auto-sync
- 7-day response caching
- Zero cloud storage (local SQLite only)
- Privacy-first design

**Documentation:**
- INSTALL.md - Installation guide for users
- README.md - Project overview
- APK_BUILD_STEPS.md - Detailed build guide
- PHASE_4_BUILD_RELEASE.md - Full reference

**Testing Ready:**
- e2e_testing_guide.md (15 test scenarios)
- stress_testing_guide.md (10 stress tests)
- security_testing_guide.md (10 security checks)
- accessibility_testing_guide.md (12 a11y tests)

---

## After Release

### Share with Users
```
GitHub Release Link:
https://github.com/vn6295337/justask/releases/tag/v1.0.0

Share with beta testers via:
- Email
- Discord
- GitHub discussions
- Social media
```

### Monitor
- Check Render backend logs
- Track rate limit usage
- Collect user feedback
- Monitor for crashes

### Next Phase
- iOS app
- F-Droid distribution
- Web interface
- New features based on feedback

---

## Need Help?

Refer to:
- `APK_BUILD_STEPS.md` - Detailed build guide
- `INSTALL.md` - Installation troubleshooting
- `PHASE_4_BUILD_RELEASE.md` - Complete reference

---

**You're 30 minutes away from a live release!**
