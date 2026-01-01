# How to Install JustAsk

**JustAsk v1.0.0** - Intelligent LLM Query Router for Android

---

## Requirements

- **Android Version:** 8.0 or higher
- **Storage:** 50 MB free space
- **RAM:** 2 GB recommended
- **Internet:** Required (for queries, offline queueing available)

---

## Installation Steps

### Step 1: Download APK

1. Visit GitHub Releases:
   ```
   https://github.com/vn6295337/justask/releases
   ```

2. Find latest release (e.g., **v1.0.0**)

3. Download APK file:
   ```
   justask-v1.0.0.apk
   ```

### Step 2: Enable Unknown Sources

**Android Settings:**

1. Open **Settings** app
2. Navigate to **Security** (or **Apps & notifications** on some devices)
3. Find **Unknown Sources** or **Install from Unknown Sources**
4. Toggle **ON** to allow installation from sources other than Play Store

**Note:** This is a one-time setup. You only need to do this once.

### Step 3: Install APK

1. Open **Files** app or **Downloads** folder
2. Locate `justask-v1.0.0.apk`
3. Tap the APK file
4. Tap **"Install"** when prompted
5. Wait for installation (usually <10 seconds)
6. Tap **"Done"** or **"Open"**

### Step 4: Grant Permissions

When app launches for the first time:
- [ ] Grant **Internet** permission (required for LLM queries)
- [ ] Grant **Network State** permission (for offline detection)

### Step 5: Launch App

1. Find **"JustAsk"** in your app drawer
2. Tap to launch
3. App initializes database (first launch ~2 seconds)
4. Ready to use!

---

## First Use

### Sending Your First Query

1. Input a question in the search box
2. Tap the **Send button** (blue circle with arrow icon)
3. Wait for response (3-10 seconds on first query)
4. Response displays with:
   - **Model Used:** Which LLM provided the answer
   - **Category:** How the query was classified
   - **Response Time:** How long it took to get the answer

### Example Queries to Try

- **News:** "What's in the news today?"
- **General Knowledge:** "What is artificial intelligence?"
- **Creative:** "Write a short poem about technology"

### Understanding Response Metadata

Each response shows:
- **Model:** The LLM provider used (Gemini, Groq, or OpenRouter)
- **Category:** Business News, General Knowledge, or Creative
- **Time:** Response time in seconds

Example:
```
Model: gemini-1.5-flash
Category: business_news
Time: 4.2s
```

---

## Features

### Online Queries
- Query multiple LLM providers (Gemini, Groq, OpenRouter)
- Intelligent routing by query type
- Response time tracking
- Auto-failover if provider is unavailable

### Offline Support
- Write queries while offline
- Queries save locally
- Auto-sync when online
- See "Query saved. Will sync when online" badge

### Response Caching
- Repeated queries cached locally (7 days)
- Instant responses for cached queries
- "Cached response" badge shown
- Up to 50 MB cache size

### Privacy
- **All data stored locally on your device**
- **No cloud sync**
- **No tracking or analytics**
- **No API keys exposed**
- Queries stored in device's local SQLite database

---

## Troubleshooting

### Issue: "Cannot install. Unknown sources not enabled"

**Solution:**
1. Go to Settings → Security
2. Enable "Unknown Sources"
3. Return to Downloads folder
4. Try installing APK again

---

### Issue: "App crashes immediately after launch"

**Solution:**
1. Uninstall app: Long-press JustAsk → Uninstall
2. Restart phone
3. Ensure Android 8.0 or higher: Settings → About → Android Version
4. Ensure 50+ MB free storage: Settings → Storage
5. Download and install fresh APK

---

### Issue: "Cannot connect to backend / Network error"

**Solution:**
1. Check internet connection (WiFi or mobile data)
2. Verify connection is active (try opening browser)
3. Backend may be waking up on first request (Render free tier)
4. Wait 10-15 seconds for first response
5. Subsequent queries should be faster

---

### Issue: "Query sent but no response (stuck loading)"

**Solution:**
1. Check internet still connected
2. Wait up to 10 seconds (network latency)
3. If still loading after 10s:
   - Close app (Settings → Apps → JustAsk → Force Stop)
   - Reopen app
   - Try again
4. If persistent: All LLM providers may be rate-limited, try again in 1 minute

---

### Issue: "Offline query not syncing when online"

**Solution:**
1. Ensure device is actually online (WiFi or mobile data)
2. Close and reopen app (triggers sync)
3. Check Sync Status:
   - Badge showing "Will sync when online" means pending
   - Sync happens automatically in background (may take 5-30 seconds)
4. If manual sync needed: Restart app

---

### Issue: "Not enough storage"

**Solution:**
1. Free up at least 50 MB space
2. Delete unnecessary apps or files
3. Clear cache: Settings → Apps → JustAsk → Storage → Clear Cache
4. Try installing again

---

## Uninstallation

To remove JustAsk:

1. Long-press JustAsk icon in app drawer
2. Tap **"Uninstall"**
3. Confirm deletion
4. All local data deleted (offline queue, cache, settings)

---

## Settings / Info Screen

Tap the **Settings tab** (bottom right) to:
- View app version
- See cache size
- Access clear cache option (future release)
- View privacy statement

---

## Data Privacy

### What JustAsk Does NOT Do
- Never stores queries in cloud
- Never sends data to tracking services
- Never exposes API keys
- Never requires login or account
- Never sells or shares data

### What JustAsk DOES Do
- Stores queries locally on device (SQLite)
- Caches responses (7 days, auto-expire)
- Syncs offline queries to backend for processing
- Deletes data when app is uninstalled

---

## Performance Tips

### For Faster Responses
1. **Use WiFi** - More stable than mobile data
2. **Close other apps** - Frees up memory
3. **Re-use queries** - Cached responses are instant
4. **Be specific** - Better queries get faster, better responses

### Cache Management
- Repeated queries cached automatically
- 7-day expiration (after 7 days, query again)
- Up to 50 MB total cache size
- Older entries deleted when limit exceeded
- Clear cache in Settings if needed

---

## Advanced Usage

### Offline Mode

When offline:
1. Input query normally
2. Tap Send
3. Query saves to local queue
4. Message: "No internet connection. Query will be saved and synced when online."
5. Badge shows: "Query saved. Will sync when online."
6. When online: Query automatically syncs
7. Response appears once backend processes it

### Batch Offline

You can queue multiple queries offline:
1. Disable internet (Airplane Mode)
2. Input 5+ different queries
3. Each saves locally
4. Enable internet
5. All queries sync in background
6. Responses appear as they're processed

### Using Different Query Types

**Business News**
- Keywords: "news", "latest", "today", "current"
- Example: "What's in the news today?"
- Routes to Gemini (has search access)

**Creative**
- Keywords: "write", "poem", "story", "creative", "compose"
- Example: "Write a haiku about programming"
- Routes to Groq (fast for creative tasks)

**General Knowledge**
- Everything else
- Example: "What is quantum computing?"
- Routes to Groq (default, reliable)

---

## Support & Feedback

### Report Issues

Found a bug? Want to request a feature?

GitHub Issues: https://github.com/vn6295337/justask/issues

Include:
- Android version
- Query that caused issue
- Error message (if any)
- Steps to reproduce

### Source Code

Open source project: https://github.com/vn6295337/justask

---

## What's Next

### Planned Features (Phase 2)
- iOS app
- F-Droid distribution
- CLI mode (terminal interface)
- Web interface
- Custom categories
- Export query history

### Feedback Welcome

Your feedback shapes the future of JustAsk. Please share:
- Feature requests
- Bug reports
- Usage feedback
- Improvement ideas

---

## License

JustAsk is open source. See LICENSE file for details.

---

## FAQ

### Q: Is my data private?
**A:** Yes! All data stays on your device. No cloud sync, no tracking, no analytics.

### Q: Do I need to create an account?
**A:** No account needed. Just download and use.

### Q: What if backend is down?
**A:** App continues offline. Queries queue locally and sync when backend is back online.

### Q: Why is first response slow?
**A:** Backend deployed on free tier (Render). First request wakes up backend (~15 seconds).

### Q: Can I use JustAsk without internet?
**A:** Yes, offline mode saves queries. They sync when you're online again.

### Q: Is this app free?
**A:** Yes, completely free. Backend uses free tier LLM APIs with rate limits.

### Q: Why no app store?
**A:** Direct APK distribution avoids app store review process and fees. Simple to update.

---

## Quick Start Checklist

- [ ] Android 8.0+ device
- [ ] Enable Unknown Sources
- [ ] Download APK
- [ ] Install APK
- [ ] Grant permissions
- [ ] Launch JustAsk
- [ ] Send first query
- [ ] Try offline mode
- [ ] Enable caching

**You're all set! Start asking questions!**
