# AA Metrics Refresh: Offline Test Results

| Fake API response | Result |
|---|---|
| 2 pages: 200 + 60 valid models, plus 1 model without an intelligence index and 1 without a slug on each page (264 total) | 2 calls to `/api/v2/language/models/free`, each sending the API key. 260 records kept; the 4 incomplete models were skipped. Speed fields read from their new nested location. Blended price = (3 × 1.4 + 4.4) / 4 = 2.15. Math index empty (NULL). All 27 database columns present. |
| HTTP 410 "Gone" | Stops with an error that includes 410. Database not touched. |
| Pages that never end (`has_more` always true) | Stops after 20 pages with a "Pagination did not finish" error. |
| Database steps: mapped-slug check, backup, delete, insert, rollback | Not tested offline. |
