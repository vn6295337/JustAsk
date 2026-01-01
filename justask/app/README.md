# JustAsk Mobile App

React Native (Expo) mobile app for JustAsk - Intelligent LLM Query Router.

## Setup

### Prerequisites

- Node.js 18+ LTS
- npm 9.6+
- Android device or emulator (for testing)
- Expo CLI: `npm install -g expo-cli`

### Installation

```bash
# Install dependencies
npm install

# Create .env from example
cp .env.example .env

# Update .env with your backend URL
EXPO_PUBLIC_BACKEND_URL=https://justask-api.onrender.com
```

## Development

### Run App

```bash
# Start Expo dev server
npm start

# Run on Android emulator
npm run android

# Run on iOS simulator
npm run ios

# Run on web
npm run web
```

### Project Structure

```
src/
├── screens/          # Screen components
│   ├── HomeScreen.js       # Query input + response display
│   └── SettingsScreen.js   # Settings & info
├── store/            # Redux state management
│   ├── index.js      # Store configuration
│   └── querySlice.js # Query reducer
├── services/         # API & utility services
│   └── APIClient.js  # Backend API client
└── utils/            # Utilities
```

### State Management (Redux)

Store structure:
```javascript
{
  query: {
    query: string,
    response: string,
    loading: boolean,
    error: string,
    llmUsed: string,
    category: string,
    responseTime: number,
    isOffline: boolean,
    offlineQueued: boolean,
    cachedResponse: boolean,
  }
}
```

### API Integration

Calls to backend (`POST /api/query`):

```javascript
const response = await APIClient.query("What is AI?");
// Returns:
// {
//   response: "AI is...",
//   llm_used: "Groq",
//   category: "general_knowledge",
//   response_time: 2500
// }
```

## Testing

```bash
# Run tests
npm test

# Watch mode
npm run test:watch
```

## Recent Fixes (Nov 2025)

### Fixed Issues
1. **Blank screen after send** - Fixed unstable FlatList keys. Changed from compound keys (`${msg.id}-${idx}`) to simple ID-based keys (`item.id`). This resolved React reconciliation issues causing the chat to disappear.

2. **Offline queueing not persisting** - Replaced fragile `updateLastMessage` reducer (using array index) with robust `updateMessage(id, updates)` reducer. Now messages are updated by unique ID, preventing state loss when Redux store resets.

3. **Manual sync responses not appearing in chat** - Implemented end-to-end queue ID mapping:
   - Frontend sends `{ id, query, timestamp }` to backend
   - Backend returns `{ id, response, llm_used, category, ... }`
   - Frontend matches responses by ID instead of array index
   - Synced responses now properly integrate into chat history

4. **Metadata not displaying** - Fixed by correcting message update mechanism. Model name, category, and response time now display correctly as they're properly persisted through Redux.

### Code Changes
- **Frontend:** `src/screens/HomeScreen.js`, `src/store/querySlice.js`, `src/services/SyncManager.js`, `src/components/MessageBubble.js`
- **Backend:** `justask/api/src/routes/query.js`, `justask/api/src/middleware/validate.js`

### Build APK

```bash
# Build release APK
npm run build

# Download from EAS Build dashboard
```

## Environment Variables

See `.env.example` for all available options:

- `EXPO_PUBLIC_BACKEND_URL` - Backend API base URL
- `EXPO_PUBLIC_API_TIMEOUT` - Request timeout (ms)
- `EXPO_PUBLIC_CACHE_TTL_DAYS` - Cache expiration (days)
- `EXPO_PUBLIC_OFFLINE_QUEUE_MAX_SIZE` - Max offline queue size
- `EXPO_PUBLIC_CACHE_SIZE_LIMIT_MB` - Cache size limit (MB)

## License

MIT
