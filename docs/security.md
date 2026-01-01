# JustAsk Mobile App - Security Testing Guide

**Phase 3: Section 3.3 - Security Testing**

Test execution: Manual and automated
Expected duration: 30-45 minutes
Test date: ____________________
Tested by: ____________________

---

## Pre-Test Setup

### Environment
- [ ] Android device or emulator running
- [ ] App installed and running
- [ ] Backend deployed on Render
- [ ] Network access available
- [ ] Device has development tools enabled (Settings → Developer Options)

### Tools (Optional)
- [ ] Charles Proxy (network inspection)
- [ ] Burp Suite Community (traffic analysis)
- [ ] File explorer (APK inspection)
- [ ] Logcat (console logs)
- [ ] Binary analysis tools (optional)

---

## Security Test 1: API Keys Not Exposed

**Objective**: Verify no sensitive credentials in APK or network traffic

### Test 1a: Source Code Review
**Steps**
1. Review `.env` files in repo
2. Check `justask/app/.env` contents
3. Verify `.gitignore` includes `.env`
4. Search for hardcoded API keys in source

### Expected Results
- [ ] `.env` file exists (local only, not committed)
- [ ] `.gitignore` includes `.env`
- [ ] No hardcoded API keys in JavaScript files
- [ ] No Supabase keys in app code
- [ ] No Gemini/Groq/OpenRouter keys in app code
- [ ] Backend URL is public-facing only

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 1b: APK Content Inspection
**Steps**
1. If available: Extract APK from device (`adb pull /data/app/...`)
2. Unzip APK: `unzip app.apk`
3. Search assets and code for:
   - "supabase"
   - "gemini"
   - "groq"
   - API keys (base64, hex, etc.)
4. Check for `build.gradle` secrets

### Expected Results
- [ ] APK contains no API keys
- [ ] APK contains no Supabase URL (or public URL only)
- [ ] APK contains no LLM provider credentials
- [ ] Backend URL is public (https://justask-api.onrender.com/)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 1c: Network Traffic Inspection (Optional)
**Steps**
1. Set up Charles Proxy or Burp Suite
2. Configure device to use proxy
3. Send query through app
4. Inspect network traffic

### Expected Results
- [ ] POST /api/query contains only: `{ query: "..." }`
- [ ] No API keys in headers
- [ ] No authentication tokens exposed
- [ ] Response contains: `{ response, llm_used, category }`
- [ ] HTTPS used (padlock icon in browser)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 2: Data Storage Security

**Objective**: Verify queries stored locally only, no cloud sync

### Test 2a: Local Database Inspection
**Steps**
1. Enable Developer Options on device
2. Connect via ADB (Android Debug Bridge)
3. Access SQLite database:
   ```bash
   adb shell
   sqlite3 /data/data/com.justask.app/databases/justask.db
   .tables
   SELECT * FROM offline_queue;
   SELECT * FROM cache;
   ```
4. Verify data location

### Expected Results
- [ ] SQLite database exists at expected location
- [ ] offline_queue contains only local queries (no upload timestamps)
- [ ] cache contains queries and responses (local only)
- [ ] offline_responses contains synced data
- [ ] No cloud sync headers/flags
- [ ] No API endpoints for uploading user data

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 2b: Verify No Cloud Sync
**Steps**
1. Monitor network traffic (Logcat or Proxy)
2. Send offline query
3. Go back online
4. Monitor sync process
5. Verify POST targets only `/api/queue/sync`

### Expected Results
- [ ] POST targets backend only: `/api/queue/sync`
- [ ] No requests to analytics services
- [ ] No requests to third-party servers
- [ ] No Firebase, Mixpanel, Segment, etc.
- [ ] Backend stores nothing (stateless)
- [ ] No cookies or persistent session tokens

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 2c: Persistent Data Check
**Steps**
1. Send query and get response (cache it)
2. Force stop app (Settings → Apps → JustAsk → Force Stop)
3. Clear app cache/storage (Settings → Apps → JustAsk → Storage → Clear Cache)
4. Restart app
5. Check if cached response persists

### Expected Results
- [ ] Cache persists after force stop (SQLite data preserved)
- [ ] Cache cleared only by "Clear Cache" action
- [ ] No automatic cloud recovery
- [ ] Data remains local

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 3: Input Validation

**Objective**: App prevents injection attacks and malformed input

### Test 3a: SQL Injection Prevention
**Steps**
1. Input query: `'; DROP TABLE offline_queue; --`
2. Send query
3. Check if query is processed or rejected
4. Check if database tables still exist

### Expected Results
- [ ] Query processed normally (treated as text)
- [ ] No database error shown
- [ ] Database tables intact
- [ ] No SQL execution
- [ ] SQLite prepared statements used (safe)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 3b: XSS-like Input (Response Display)
**Steps**
1. Input query: `<script>alert('xss')</script>`
2. Send query
3. Observe how response displays

### Expected Results
- [ ] Query processed as text
- [ ] No script execution
- [ ] React escapes HTML by default
- [ ] Script tags displayed as text (not executed)
- [ ] No app crash

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 3c: Very Long Input
**Steps**
1. Input extremely long query (2000+ characters)
2. Send query

### Expected Results
- [ ] App handles long input gracefully
- [ ] Backend validation enforced (max ~2000 chars)
- [ ] Error message if too long: "Input too long"
- [ ] No app crash
- [ ] No buffer overflow

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 3d: Special Characters
**Steps**
1. Input query with special chars: `🔐 !@#$%^&*() <>&"'`
2. Send query

### Expected Results
- [ ] Query processed normally
- [ ] Backend handles Unicode
- [ ] Response displays correctly
- [ ] No encoding issues
- [ ] No app crash

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 4: Authentication & Authorization

**Objective**: Verify no auth bypass possible

### Test 4a: Direct API Access
**Steps**
1. On device (or via proxy): Attempt direct API call to backend
   ```
   POST https://justask-api.onrender.com/api/query
   { query: "test" }
   ```
2. Send without any auth header
3. Observe response

### Expected Results
- [ ] Backend accepts unauthenticated requests (by design - public API)
- [ ] Response is normal
- [ ] Backend doesn't expose sensitive data
- [ ] No admin endpoints accessible without auth

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 4b: Rate Limiting (Not Auth, but Access Control)
**Steps**
1. Attempt 100 rapid requests to backend
2. Monitor for 429 responses

### Expected Results
- [ ] Rate limit enforced at backend
- [ ] 429 Too Many Requests returned
- [ ] App handles gracefully
- [ ] No way to bypass rate limit from client

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 5: Permissions & Privacy

**Objective**: Verify app requests only necessary permissions

### Test 5a: Manifest Review
**Steps**
1. Extract APK and read `AndroidManifest.xml`
2. Review requested permissions
3. Check against `app.json` in source

### Expected Results
- [ ] Only requests: `android.permission.INTERNET`
- [ ] Only requests: `android.permission.ACCESS_NETWORK_STATE`
- [ ] No camera, microphone, contacts, SMS permissions
- [ ] No location permission
- [ ] No file access beyond app-private storage

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 5b: Runtime Permissions Check
**Steps**
1. Go to Settings → Apps → JustAsk → Permissions
2. Review all granted permissions
3. Attempt to revoke permissions
4. Test app functionality

### Expected Results
- [ ] Only INTERNET and NETWORK_STATE shown
- [ ] Permissions grant minimal access
- [ ] Revoking permissions shows appropriate error
- [ ] No crash when permissions revoked

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 5c: Privacy Statement Visible
**Steps**
1. Open app Settings screen
2. Look for privacy statement

### Expected Results
- [ ] Privacy statement visible: "Queries stored locally only, no history"
- [ ] No claim of cloud backup (false promise)
- [ ] Statement is accurate

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 6: Transport Security (HTTPS)

**Objective**: Verify all network traffic encrypted

### Test 6a: Backend HTTPS
**Steps**
1. Check backend URL: https://justask-api.onrender.com/
2. Visit in browser
3. Check SSL certificate

### Expected Results
- [ ] HTTPS used (not HTTP)
- [ ] Valid SSL certificate
- [ ] No certificate warnings
- [ ] Render provides free SSL

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 6b: App Network Traffic
**Steps**
1. Monitor network traffic (Logcat or Proxy)
2. Observe all requests

### Expected Results
- [ ] All requests to backend use HTTPS
- [ ] No HTTP fallback
- [ ] No mixed content (HTTP + HTTPS)
- [ ] Certificate pinning not required (Render managed)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 7: Error Message Security

**Objective**: Verify error messages don't leak sensitive info

### Test 7a: Backend Error Responses
**Steps**
1. Send malformed request to backend
2. Send request to non-existent endpoint
3. Observe error messages returned

### Expected Results
- [ ] Error messages are generic: "Bad request", "Not found"
- [ ] No stack traces exposed
- [ ] No database details exposed
- [ ] No file paths shown
- [ ] No API key hints

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 7b: App Error Messages
**Steps**
1. Trigger various errors:
   - Timeout (kill network mid-request)
   - Invalid input (special chars)
   - Rate limit (send 100 requests)
2. Observe error messages shown to user

### Expected Results
- [ ] User-friendly error messages
- [ ] No technical jargon
- [ ] No stack traces
- [ ] No file paths
- [ ] Messages helpful but not revealing

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 8: Data Deletion & Privacy

**Objective**: Verify user can delete local data

### Test 8a: Clear Cache Button
**Steps**
1. Send queries to populate cache (5+ queries)
2. Go to Settings screen
3. Tap "Clear Cache" (or equivalent)
4. Verify cache cleared

### Expected Results
- [ ] Clear Cache button exists (if implemented)
- [ ] Cache table emptied after tap
- [ ] App remains functional
- [ ] No residual data
- [ ] SQLite database file size reduced

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 8b: App Uninstall Data Removal
**Steps**
1. Go to Settings → Apps → JustAsk
2. Tap "Storage"
3. Verify cache/data storage location
4. Uninstall app
5. Reinstall and verify no old data

### Expected Results
- [ ] All data in app-private storage (deleted on uninstall)
- [ ] No residual data on device after uninstall
- [ ] Fresh install = empty cache/queue
- [ ] No cloud restore

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Security Test 9: Cryptography (If Applicable)

**Objective**: Verify data encryption (optional for MVP)

### Note
SQLite encryption is optional for MVP but recommended.

### Test 9a: SQLite Database Inspection
**Steps**
1. Pull SQLite database file via ADB
2. Attempt to open with text editor
3. Check if data is readable

### Expected Results
- [ ] If encrypted: Binary/unreadable data
- [ ] If unencrypted: This is acceptable for MVP (local-only data)
- [ ] Database file permissions restricted to app user

### Status
- **Pass** ✅ / **Fail** ❌ / **N/A** (Not implemented in MVP)

Notes: _____________________________________________________________________

---

## Security Test 10: Known Vulnerabilities

**Objective**: Check dependencies for known vulnerabilities

### Test 10a: NPM Audit
**Steps**
1. In app directory: `npm audit`
2. Review output
3. Check for high/critical vulnerabilities

### Expected Results
- [ ] No critical vulnerabilities
- [ ] Low vulnerabilities acceptable (can document)
- [ ] High vulnerabilities should be patched
- [ ] Dependencies up-to-date

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 10b: Dependency Review
**Steps**
1. Review all dependencies in `package.json`
2. Check for deprecated packages
3. Verify maintained packages

### Expected Results
- [ ] All dependencies actively maintained
- [ ] No deprecated packages
- [ ] Latest versions within reason
- [ ] No end-of-life packages

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Summary Results

### Test Execution Summary
- Total Security Tests: 20+
- Passed: ___
- Failed: ___
- Blocked: ___
- Success Rate: ___%

### Critical Security Issues
1. _______________________________________________________________________
2. _______________________________________________________________________

### Medium Risk Issues
1. _______________________________________________________________________

### Low Risk Issues (Acceptable)
1. _______________________________________________________________________

### Compliance Assessment
- [ ] No API keys exposed: **PASS**
- [ ] Local storage only: **PASS**
- [ ] HTTPS enforced: **PASS**
- [ ] Input validation: **PASS**
- [ ] Privacy compliant: **PASS**

### Recommendations
_________________________________________________________________________
_________________________________________________________________________

### Sign-Off
- Tested by: _________________________ Date: __________
- Security Lead: _________________________ Date: __________
