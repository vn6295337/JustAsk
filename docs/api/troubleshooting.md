# Troubleshooting

## Installation

| Problem | Cause | Solution |
|---------|-------|----------|
| "Unknown sources not enabled" | Security setting off | Settings → Security → Enable Unknown Sources |
| "Installation failed" | Storage full | Free 50+ MB space |
| "Wrong Android version" | Device <8.0 | Requires Android 8.0+ |

## App Runtime

| Problem | Cause | Solution |
|---------|-------|----------|
| App crashes on launch | SQLite init failed | Uninstall, restart phone, reinstall |
| Input not responding | Keyboard issue | Tap input field again, close keyboard |
| Response loading forever | Network dead | Check WiFi/mobile data, close other apps |
| "Rate limited" error | Too many requests | Wait 1-2 minutes, retry |
| "All providers unavailable" | Backend down | Wait 5-10 minutes, retry |
| Response shows cached | Not desired | Send different query or restart app |

## Offline Mode

| Problem | Cause | Solution |
|---------|-------|----------|
| Query not saved offline | Network just restored | Disable/enable airplane mode again |
| Query not syncing | Still offline | Enable WiFi or mobile data |
| Sync taking long | Network slow | Wait, poor connection? Try WiFi |
| Sync failed after retry | All retries exhausted | Query lost, send again when stable |

## Performance

| Problem | Cause | Solution |
|---------|-------|----------|
| First response slow (15s) | Render cold start | Normal, subsequent requests faster |
| Query response slow (>10s) | Network latency or provider busy | Retry or wait |
| App laggy | Low memory | Close other apps |
| Cache not working | Query different | Cache only for exact same query |

## Uninstall

| Problem | Cause | Solution |
|---------|-------|----------|
| Cannot uninstall | App in use | Close app first, try again |
| Data not deleted | Non-standard uninstall | Use Settings → Apps → Uninstall |

## Backend

| Problem | Cause | Solution |
|---------|-------|----------|
| Cannot reach backend | URL wrong | Check BACKEND_URL in .env |
| 400 error | Invalid query | Query must be 1-2000 chars, non-empty |
| 429 error | Rate limited | Wait 1-2 min, exponential backoff |
| 500 error | All providers down | Retry after 5-10 min |

## Report Issues

GitHub: https://github.com/vn6295337/justask/issues

Include:
- Android version
- Reproduction steps
- Error message (exact)
- Device type
