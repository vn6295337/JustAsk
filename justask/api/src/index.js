import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import config from './config.js';
import queryRoutes from './routes/query.js';
import { loadGeoDb } from './middleware/regionBlock.js';

const app = express();

// Behind Render's proxy: use X-Forwarded-For for req.ip (per-IP rate limiting)
app.set('trust proxy', 1);

// ============================================
// Middleware
// ============================================

// Security headers
app.use(helmet());

// CORS - Allow requests from mobile app
app.use(
  cors({
    // Explicit allowlist (add more via CORS_ORIGINS, comma-separated).
    // Native mobile requests send no Origin header and are not affected.
    origin: [
      'http://localhost:8081', // Expo dev server
      'http://localhost:3000', // Local testing
      'http://localhost:19000', // Expo tunnel
      'http://localhost:19006', // Expo web
      ...config.corsOrigins,
    ],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
  })
);

// HTTP logging. 'tiny' omits the client IP address and user agent:
// the privacy notice states the server does not store IP addresses.
app.use(morgan('tiny'));

// JSON body parser
// 20 queries x 2000 chars (worst case JSON-escaped) fits well under 256kb
app.use(express.json({ limit: '256kb' }));

// ============================================
// Routes
// ============================================

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Query routes
app.use('/api', queryRoutes);

// ============================================
// Error Handling Middleware
// ============================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    status: 404,
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);

  const status = err.status || err.statusCode || 500;
  // Do not leak internal/upstream error text on 5xx
  const message =
    status >= 500 ? 'Internal server error' : err.message || 'Bad request';

  res.status(status).json({
    error: message,
    status: status,
  });
});

// ============================================
// Server Startup
// ============================================

// Region block needs the geo database. Fail closed: refuse to start without it,
// so Render keeps the previous deploy instead of serving blocked regions.
try {
  await loadGeoDb();
  console.log('[RegionBlock] Geo database loaded');
} catch (error) {
  console.error('[RegionBlock] FATAL: geo database failed to load:', error.message);
  process.exit(1);
}

const PORT = config.port;
const NODE_ENV = config.nodeEnv;

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Environment: ${NODE_ENV}`);
});

export default app;
