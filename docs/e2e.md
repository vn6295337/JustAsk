# JustAsk Mobile App - E2E Testing Guide

**Phase 3: Section 3.1 - End-to-End Testing**

Test execution: Manual on Android device/emulator
Expected duration: 30-45 minutes
Test date: ____________________
Tested by: ____________________

---

## Pre-Test Setup

### Environment
- [ ] Android device or emulator running (Android 8.0+)
- [ ] App installed and running
- [ ] Backend deployed and live (https://justask-api.onrender.com/)
- [ ] Network connection available (WiFi or mobile)
- [ ] SQLite database initialized on first app launch

### Test Data
- Queries for testing:
  - **News**: "What's in the news today?"
  - **General**: "What is artificial intelligence?"
  - **Creative**: "Write a short poem about technology"

---

## Test Scenario 1: Normal Online Flow

**Objective**: User queries backend when online, receives response with metadata

### Steps
1. Launch app
2. Ensure online status (WiFi/mobile enabled)
3. Input query: "What is artificial intelligence?"
4. Tap Send button
5. Observe response loading (spinner)

### Expected Results
- [ ] Response loads within 10 seconds
- [ ] Response text displays
- [ ] Model shows: "gemini-1.5-flash" or "mixtral-8x7b-32768" or "gpt-3.5-turbo"
- [ ] Category shows: "general_knowledge"
- [ ] Response time shows (e.g., "3.5s")
- [ ] No error message displayed
- [ ] Response is cached (next identical query shows "Cached response" badge)

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 2: News Category Routing

**Objective**: Verify news queries route to correct provider

### Steps
1. Clear query field
2. Input query: "What's in the news today?"
3. Tap Send button
4. Wait for response

### Expected Results
- [ ] Response received within 10 seconds
- [ ] Category shows: "business_news"
- [ ] Model shows: "gemini-1.5-flash" (primary for news)
- [ ] Response time displays
- [ ] Response content is relevant to news

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 3: Creative Category Routing

**Objective**: Verify creative queries route to correct provider

### Steps
1. Clear query field
2. Input query: "Write a short poem about technology"
3. Tap Send button
4. Wait for response

### Expected Results
- [ ] Response received within 10 seconds
- [ ] Category shows: "creative"
- [ ] Model shows: "mixtral-8x7b-32768" (primary for creative)
- [ ] Response is creative content (poem, story, etc.)
- [ ] Response time displays

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 4: Cache Hit Behavior

**Objective**: Verify cached responses are used without API call

### Steps
1. Use query from Scenario 1: "What is artificial intelligence?"
2. Clear query field
3. Input the exact same query again
4. Tap Send button
5. Observe response load time

### Expected Results
- [ ] Response displays **instantly** (under 500ms)
- [ ] "Cached response" badge appears
- [ ] Response text is **identical** to first query
- [ ] Response time shows 0ms or cache load time
- [ ] Model and Category same as original query

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 5: Cache Miss (Different Query)

**Objective**: Verify different queries don't use cache

### Steps
1. Input new query: "Who is Albert Einstein?"
2. Tap Send button
3. Wait for response

### Expected Results
- [ ] Response loads (5-10 seconds, not cached)
- [ ] "Cached response" badge **does NOT** appear
- [ ] Response time shows 5-10 seconds (API call time)
- [ ] Response content is different from previous query

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 6: Offline Query Queueing

**Objective**: User can query offline, query is saved locally

### Steps
1. **Disable network** (airplane mode or turn off WiFi)
2. Wait 2 seconds for offline detection
3. Observe offline banner at top
4. Input query: "What is climate change?"
5. Tap Send button
6. Observe response area

### Expected Results
- [ ] Offline banner shows: "No internet connection" (red)
- [ ] Error message shows: "No internet connection. Query will be saved and synced when online."
- [ ] "Query saved. Will sync when online." badge appears
- [ ] No response text shown
- [ ] App doesn't crash
- [ ] Input field remains functional

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 7: Offline Queue Multiple Queries

**Objective**: Multiple queries can be queued while offline

### Steps
1. **Remain offline** (from Scenario 6)
2. Input query: "What is quantum computing?"
3. Tap Send button
4. Input query: "Explain blockchain"
5. Tap Send button
6. Input query: "What is machine learning?"
7. Tap Send button

### Expected Results
- [ ] All 3 queries queue without crashing
- [ ] Each shows "Query saved" badge
- [ ] Each shows "Will sync when online"
- [ ] Queue count shows 3 pending queries (in logs)
- [ ] No error messages

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 8: Offline→Online Sync

**Objective**: Queued queries are synced and responses retrieved when online

### Steps
1. **Re-enable network** (turn off airplane mode or enable WiFi)
2. Wait 2-3 seconds for network detection
3. Observe app behavior
4. Check if responses appear for queued queries

### Expected Results
- [ ] Offline banner disappears within 2 seconds
- [ ] App detects network restoration
- [ ] Sync initiates automatically (logs show "Syncing..." or similar)
- [ ] Queued query responses appear one by one (or all at once)
- [ ] Response times may be longer (includes offline period)
- [ ] All 3 responses from Scenarios 6-7 appear with metadata
- [ ] "Will sync when online" badges removed

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 9: Sync with Network Interruption (Retry Logic)

**Objective**: Sync recovers from temporary network loss

### Steps
1. Queue 2 queries while offline
2. Re-enable network
3. Sync begins
4. **Quickly disable network again** (within 2 seconds)
5. Wait 3 seconds
6. **Re-enable network again**

### Expected Results
- [ ] Sync pauses when network lost
- [ ] Sync retries when network restored (exponential backoff: 1s, 5s, 30s)
- [ ] Queued responses eventually appear (after retries)
- [ ] No crashes during network transitions
- [ ] Error message shown if sync fails after 3 attempts

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 10: Error Handling - Invalid Input

**Objective**: App handles invalid/empty queries gracefully

### Steps
1. Ensure online
2. Tap Send button **without** typing query
3. Observe error message

### Expected Results
- [ ] Error message shows: "Please enter a question"
- [ ] No API call made
- [ ] Error message clears when user starts typing
- [ ] App remains responsive

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 11: Error Handling - Rate Limit

**Objective**: App gracefully handles rate limit responses

### Steps
1. Ensure online
2. Send 5 rapid queries in quick succession
3. Observe responses

### Expected Results
- [ ] First few queries succeed normally
- [ ] If rate limited: Error shows "Rate limited. All providers are busy. Please try again in a moment."
- [ ] Failover works (secondary/tertiary provider used)
- [ ] No app crash
- [ ] User can retry after waiting

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 12: Error Handling - Timeout

**Objective**: App handles slow/timeout responses

### Steps
1. Ensure online
2. Send query
3. Wait 15+ seconds (beyond timeout)

### Expected Results
- [ ] After 10 seconds: App shows timeout error or "Request timed out. Check your internet connection."
- [ ] If backend slow: Response may appear after 10+ seconds
- [ ] App doesn't freeze
- [ ] User can retry

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 13: Failover Behavior (Provider Failure)

**Objective**: Verify secondary/tertiary providers used on primary failure

**Note**: This requires manually testing or using network proxy to simulate provider failure. For MVP, we trust backend failover logic.

### Steps
1. Review backend logs at https://dashboard.render.com
2. Verify failover chain in logs for failed primary requests
3. Or: Use Charles Proxy to block primary provider

### Expected Results
- [ ] When primary fails, secondary provider (Groq) is used
- [ ] When secondary fails, tertiary (OpenRouter) is used
- [ ] User receives response from whichever provider succeeds
- [ ] Response metadata shows which provider was used

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️ / **Manual Verification**

Notes: _____________________________________________________________________

---

## Test Scenario 14: UI Responsiveness During Load

**Objective**: App remains responsive while fetching response

### Steps
1. Send query
2. While loading (spinner showing):
   - Try to type in input field
   - Try to scroll
   - Try to interact with buttons

### Expected Results
- [ ] Input field disabled while loading
- [ ] Send button disabled while loading (opacity reduced)
- [ ] Spinner visible in send button
- [ ] Back button/navigation still functional
- [ ] Can dismiss keyboard

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Test Scenario 15: Settings Screen (Info & Future Actions)

**Objective**: Verify settings screen shows app info

### Steps
1. Tap Settings tab at bottom
2. Observe screen content
3. Check for app version, cache info, etc.

### Expected Results
- [ ] Settings screen displays
- [ ] Shows app version (e.g., "1.0.0")
- [ ] Shows cache size if available
- [ ] Clear Cache button exists (optional for MVP)
- [ ] Privacy statement displayed

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Summary Results

### Test Execution Summary
- Total Scenarios: 15
- Passed: ___ / 15
- Failed: ___ / 15
- Blocked: ___ / 15
- Success Rate: ___%

### Critical Issues Found
1. _______________________________________________________________________
2. _______________________________________________________________________
3. _______________________________________________________________________

### Non-Critical Issues Found
1. _______________________________________________________________________
2. _______________________________________________________________________

### Recommendations
_________________________________________________________________________
_________________________________________________________________________

### Sign-Off
- Tested by: _________________________ Date: __________
- Approved by: _________________________ Date: __________

---

## Appendix: Device Information

**Device/Emulator Details:**
- Device Model: _____________________
- OS Version: _____________________
- RAM: _____________________
- Network Type (WiFi/Mobile): _____________________

**Backend Status:**
- Health Check: https://justask-api.onrender.com/api/health
- Status: ✅ OK / ❌ DOWN

**App Logs (if needed):**
```
[Paste relevant console logs or crash reports here]
```
