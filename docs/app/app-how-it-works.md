## How JustAsk App works:

**Architecture:**
- React Native mobile app (Android/iOS) built with Expo SDK 54
- Three-tier architecture: **justask/app (mobile)** → **justask/api (port 3000)** → **justask-router (port 3001)**
- Two-tab navigation: Home (query interface) and Settings

**Tech Stack (SDK 54):**
| Package | Version |
|---------|---------|
| expo | ~54.0.0 |
| react | 19.1.0 |
| react-native | 0.81.5 |
| expo-sqlite | ~16.0.10 |
| @reduxjs/toolkit | ^2.5.0 |
| react-redux | ^9.2.0 |

**Main Components:**
- **HomeScreen.js** - Chat interface where users ask questions
- **SettingsScreen** - App configuration
- **Redux store** - Manages query state (loading, response, errors)
- **SQLite database** - Local persistence for chat history and cache (expo-sqlite)

**Query Flow:**
1. User types question in text input
2. App checks local cache first (7-day TTL, 50MB limit)
3. If cache miss, **mobile app** sends `POST /api/query` to **justask/api** at `https://justask-api.onrender.com`
4. **justask/api** internally calls **justask-router** at `/best-models?limit=10` to get ranked model list
5. **justask/api** tries models in rank order using the ranked fallback chain
6. **justask/api** returns final response back to mobile app with: response, llm_used, category, response_time, model_rank, selection_score
7. Response cached locally and displayed in chat bubble

**Offline Handling:**
- Monitors network status via NetInfo
- If API fails, query saved to offline queue in SQLite
- Auto-syncs queued queries when connection restored
- Shows "No internet connection" banner when offline

**Caching System:**
- Hash-based query cache (FNV-1a algorithm)
- Stores responses with metadata (LLM used, category, response time)
- Automatic expiration after 7 days
- Size limit enforcement (50MB, deletes oldest entries)

**Chat Features:**
- Persistent conversation history (SQLite)
- Message bubbles showing user questions and AI responses
- Displays which model/provider was used
- Shows query category and response time
- Skeleton loader during API calls

**Data Storage:**
- Chat history persists across app restarts
- Cache managed with size limits
- Offline queue for failed requests

---

## Key Implementation Details

### Keyboard Handling (Android)
The input bar stays visible above the keyboard using:
- Keyboard event listeners (`keyboardDidShow`/`keyboardDidHide`)
- Absolute positioning for input section with dynamic `bottom` value
- FlatList with dynamic `paddingBottom` to account for input + keyboard height

```javascript
// HomeScreen.js - Keyboard tracking
const [keyboardHeight, setKeyboardHeight] = useState(0);

useEffect(() => {
  const showSub = Keyboard.addListener('keyboardDidShow', (e) => {
    setKeyboardHeight(e.endCoordinates.height);
  });
  const hideSub = Keyboard.addListener('keyboardDidHide', () => {
    setKeyboardHeight(0);
  });
  return () => { showSub.remove(); hideSub.remove(); };
}, []);

// Input section positioned absolutely
<View style={{ position: 'absolute', bottom: keyboardHeight, left: 0, right: 0 }}>
```

### Database Singleton Pattern (expo-sqlite)
Prevents race conditions from concurrent `Database.init()` calls:

```javascript
// Database.js
let db = null;
let initPromise = null;

init: async () => {
  if (db) return db;                    // Already initialized
  if (initPromise) return initPromise;  // Init in progress, wait

  initPromise = (async () => {
    db = await SQLite.openDatabaseAsync(DATABASE_NAME);
    await Database.createTables();
    return db;
  })();

  return initPromise;
}
```

### expo-sqlite API (SDK 54)
Migrated from `react-native-sqlite-storage` to `expo-sqlite`:

| Old API | New API |
|---------|---------|
| `SQLite.openDatabase()` | `SQLite.openDatabaseAsync()` |
| `db.executeSql(sql, params)` | `db.runAsync(sql, params)` |
| `result[0].rows.item(i)` | Direct array access |
| `result[0].insertId` | `result.lastInsertRowId` |
| `db.executeSql()` for SELECT | `db.getAllAsync()` or `db.getFirstAsync()` |
| `db.close()` | `db.closeAsync()` |

### Provider Formatter
Displays human-readable model names in chat bubbles:

```javascript
// providerFormatter.js
export { formatProvider };  // Named export (not default)

// Usage in MessageBubble.js
import { formatProvider } from '../utils/providerFormatter';
formatProvider('groq').displayName  // "Groq"
formatProvider('groq').subtitle     // "Standard"
```

---

## Configuration

### app.config.js
```javascript
android: {
  softwareKeyboardLayoutMode: "resize",  // For standalone builds
  package: "com.justask.app",
  permissions: ["INTERNET", "ACCESS_NETWORK_STATE"]
},
extra: {
  backendUrl: process.env.EXPO_PUBLIC_BACKEND_URL || 'https://justask-api.onrender.com',
  cacheTtlDays: '7',
  cacheSizeLimitMb: '50',
}
```

### Running the App
```bash
# Development with tunnel (for physical device testing)
npx expo start --tunnel

# Clear cache and restart
npx expo start --tunnel -c

# Run expo doctor to check for issues
npx expo-doctor
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Keyboard covers input | Uses keyboard event listeners + absolute positioning |
| `db.executeSql is not a function` | Migrated to expo-sqlite async API |
| `formatProvider is not a function` | Changed to named export `export { formatProvider }` |
| Database NullPointerException | Singleton pattern prevents concurrent init |
| Network Error in Expo Go | Check phone WiFi/data, verify backend is awake |
| `softwareKeyboardLayoutMode` not working | Only works in standalone builds, not Expo Go |
