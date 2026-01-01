import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import config from './config.js';
import queryRoutes from './routes/query.js';

const app = express();

// ============================================
// Middleware
// ============================================

// Security headers
app.use(helmet());

// CORS - Allow requests from mobile app
app.use(
  cors({
    origin: [
      'http://localhost:8081', // Expo dev server
      'http://localhost:3000', // Local testing
      'http://localhost:19000', // Expo tunnel
      'http://localhost:19006', // Expo web
      '*', // Allow all origins for MVP (restrict in production)
    ],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);

// HTTP logging
app.use(morgan('combined'));

// JSON body parser
app.use(express.json());

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
  const message = err.message || 'Internal server error';

  res.status(status).json({
    error: message,
    status: status,
  });
});

// ============================================
// Server Startup
// ============================================

const PORT = config.port;
const NODE_ENV = config.nodeEnv;

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Environment: ${NODE_ENV}`);
});

export default app;
