# JustAsk Mobile App - Stress Testing Guide

**Phase 3: Section 3.2 - Stress Testing**

Test execution: Manual on Android device/emulator
Expected duration: 20-30 minutes
Test date: ____________________
Tested by: ____________________

---

## Pre-Test Setup

### Environment
- [ ] Android device or emulator running
- [ ] App installed and running
- [ ] Backend deployed and live
- [ ] Network connection available (strong WiFi/mobile)
- [ ] Device has sufficient memory (target 2GB+)
- [ ] Battery at 50%+ (extended test)

### Tools
- [ ] Console/Logcat access (for monitoring)
- [ ] Memory/CPU monitor (optional)

---

## Stress Test 1: Concurrent Queries (10 queries)

**Objective**: App handles multiple simultaneous requests without crashing

### Steps
1. Ensure online, app responsive
2. Clear query field
3. **Rapidly input and send 10 queries in sequence** (no waiting for responses):
   - "What is AI?"
   - "What is ML?"
   - "What is blockchain?"
   - "What is quantum computing?"
   - "What is IoT?"
   - "What is 5G?"
   - "What is cloud computing?"
   - "What is cybersecurity?"
   - "What is data science?"
   - "What is web3?"
4. Monitor as responses arrive
5. Allow 30 seconds for all responses to load

### Expected Results
- [ ] All 10 queries sent without error
- [ ] No app crash during rapid queries
- [ ] App remains responsive
- [ ] Responses arrive (may be in different order)
- [ ] All 10 responses eventually show
- [ ] Memory usage reasonable (no memory leak)
- [ ] No "Rate limited" errors (or expected if rate limit hit)

### Expected Behavior
- Some queries may get rate limited (expected behavior)
- Failover to secondary/tertiary providers may occur
- Order of responses may differ from input order

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 2: Rapid Cache Access

**Objective**: Repeated cache hits don't cause issues

### Steps
1. Ensure online
2. Input and send: "What is artificial intelligence?"
3. Wait for response (to cache it)
4. **Rapidly tap Send 10 times** with same query (within 5 seconds)
5. Observe response display updates

### Expected Results
- [ ] App handles rapid taps without crashing
- [ ] "Cached response" badge shows consistently
- [ ] Responses display instantly (all cache hits)
- [ ] No memory issues
- [ ] Input field remains functional
- [ ] No duplicate responses stacked

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 3: Offline Queue Stress (5+ queries)

**Objective**: Large offline queue handles multiple queries

### Steps
1. **Enable offline mode** (airplane mode)
2. Queue 5 different queries:
   - "Query 1"
   - "Query 2"
   - "Query 3"
   - "Query 4"
   - "Query 5"
3. Send each query in rapid succession
4. Allow database to record all queries
5. Observe queue storage

### Expected Results
- [ ] All 5 queries queue successfully
- [ ] Each shows "Will sync when online" badge
- [ ] No crashes during queueing
- [ ] Database stores all 5 queries
- [ ] Queue counter (in logs) shows 5 pending

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 4: Offline→Online Sync Load

**Objective**: Sync handles large queue without failure

### Steps
1. **Remain in offline mode** with 5 queued queries
2. **Enable network** (turn off airplane mode)
3. Monitor sync process
4. Allow up to 60 seconds for all queries to sync
5. Observe responses appearing

### Expected Results
- [ ] Sync initiates when network detected
- [ ] All 5 responses eventually arrive
- [ ] Response order may differ from queue order
- [ ] No app crash during sync
- [ ] Database updates with synced responses
- [ ] "Will sync when online" badges removed
- [ ] No duplicate responses

### Sync Timeline (Expected)
- First response: 3-5 seconds
- Remaining responses: Within 30 seconds
- All responses: Within 60 seconds

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 5: Rate Limiting Enforcement

**Objective**: Backend rate limits respected, failover works under load

### Steps
1. Ensure online
2. Send 20 rapid queries in quick succession
3. Monitor error responses
4. Wait 2 minutes
5. Send 5 more queries

### Expected Results
- [ ] First 10-15 queries succeed (within rate limits)
- [ ] Subsequent queries may get "Rate limited" error
- [ ] Error message: "Rate limited. All providers are busy..."
- [ ] Failover between providers evident in logs
- [ ] After 1-2 minute wait: New queries succeed again
- [ ] No app crash due to rate limiting
- [ ] Graceful error handling shown to user

### Rate Limit Thresholds (Backend)
- Gemini: 60 req/min
- Groq: 30 req/min
- OpenRouter: Varies

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 6: Cache Size Limits (50MB)

**Objective**: Cache respects 50MB size limit

### Steps
1. Ensure online
2. Send 50 different queries to build up cache
3. Each query: Different topic (e.g., "Topic 1", "Topic 2", etc.)
4. Monitor cache size growth
5. Query cache table to see entry count

### Expected Results
- [ ] Cache stores 50+ entries without crashing
- [ ] Cache respects 50MB limit (older entries deleted)
- [ ] App performance remains responsive
- [ ] New queries still cache normally
- [ ] No memory leak

### Cache Management
- Oldest entries deleted when limit exceeded
- Cache checked before API call
- Size calculated from response TEXT field

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 7: Long Response Handling

**Objective**: App handles large/long responses

### Steps
1. Ensure online
2. Input query: "Write a detailed explanation of quantum mechanics including all key concepts and equations"
3. Wait for response
4. Observe response display

### Expected Results
- [ ] Long response displays correctly
- [ ] Text wraps properly
- [ ] Scrolling works if response is very long
- [ ] No text truncation or corruption
- [ ] Response time still displayed
- [ ] UI remains responsive

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 8: Memory Stability (Extended Use)

**Objective**: App memory usage stable over extended period

### Steps
1. Ensure online
2. Send query and get response
3. Clear response (new query)
4. Repeat for 5 minutes (one query every 30 seconds)
5. Monitor memory usage (if available)

### Expected Results
- [ ] Memory usage stable (no consistent growth)
- [ ] No lag after 5 minutes of use
- [ ] Smooth scrolling maintained
- [ ] Text input remains responsive
- [ ] No stutter or jank
- [ ] No memory warning messages

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 9: Network Switching

**Objective**: App handles WiFi↔Mobile switching

### Steps
1. Connect to WiFi
2. Send query, get response
3. Switch to Mobile data
4. Send different query
5. Switch back to WiFi
6. Send another query
7. Observe network detection

### Expected Results
- [ ] App detects network changes within 2 seconds
- [ ] Queries work on both WiFi and mobile data
- [ ] No crashes during network switch
- [ ] Offline detection accurate
- [ ] Responses succeed on either network type
- [ ] No orphaned responses or duplicates

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Stress Test 10: Rapid Online↔Offline Cycling

**Objective**: App handles frequent network changes

### Steps
1. Enable offline (airplane mode)
2. Queue 2 queries
3. Enable online
4. Allow 5 seconds
5. Disable offline again
6. Queue 2 more queries
7. Enable online
8. Monitor sync process

### Expected Results
- [ ] All 4 queries eventually sync
- [ ] No crashes during toggling
- [ ] Sync retries work correctly
- [ ] Exponential backoff observed in logs
- [ ] Final state consistent (all responses show)
- [ ] No data loss

### Status
- **Pass** ✅ / **Fail** ❌ / **Blocked** ⏸️

Notes: _____________________________________________________________________

---

## Summary Results

### Test Execution Summary
- Total Stress Tests: 10
- Passed: ___ / 10
- Failed: ___ / 10
- Blocked: ___ / 10
- Success Rate: ___%

### Critical Issues Found
1. _______________________________________________________________________
2. _______________________________________________________________________

### Performance Observations
- Average Response Time (normal): _________ seconds
- Average Response Time (cached): _________ ms
- Memory Usage (initial): _________ MB
- Memory Usage (after tests): _________ MB
- Memory Increase: _________ MB

### Recommendations
_________________________________________________________________________
_________________________________________________________________________

### Sign-Off
- Tested by: _________________________ Date: __________
- Approved by: _________________________ Date: __________
