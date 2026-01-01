import NetInfo from '@react-native-community/netinfo';
import APIClient from './APIClient';
import Database from './Database';
import store from '../store';
import { addMessage } from '../store/querySlice';

const SyncManager = {
  isSyncing: false,

  /**
   * Start sync process if online
   * Syncs all pending queries with exponential backoff retry
   */
  syncPending: async () => {
    // Prevent concurrent syncs
    if (SyncManager.isSyncing) {
      console.log('⏳ Sync already in progress');
      return false;
    }

    try {
      // Check network status
      const networkState = await NetInfo.fetch();
      if (!networkState.isConnected) {
        console.log('❌ No internet connection, sync deferred');
        return false;
      }

      SyncManager.isSyncing = true;

      // Get pending queries
      const pending = await Database.getPendingQueries();
      if (pending.length === 0) {
        console.log('✅ No pending queries to sync');
        SyncManager.isSyncing = false;
        return true;
      }

      console.log(`🔄 Syncing ${pending.length} pending queries...`);

      // Attempt sync with retry
      const result = await SyncManager.syncWithRetry(pending);

      if (result.success) {
        console.log(`✅ Synced ${result.synced} queries successfully`);
        if (result.failed > 0) {
          console.warn(`⚠️ ${result.failed} queries failed to sync`);
        }
        return true;
      } else {
        console.error('❌ Sync failed after retries');
        return false;
      }
    } catch (error) {
      console.error('❌ Sync error:', error.message);
      return false;
    } finally {
      SyncManager.isSyncing = false;
    }
  },

  /**
   * Sync with exponential backoff retry
   * Retries up to 3 times: 1s, 5s, 30s
   */
  syncWithRetry: async (queries, attempt = 1, maxAttempts = 3) => {
    try {
      const result = await SyncManager.performSync(queries);
      return result;
    } catch (error) {
      if (attempt < maxAttempts) {
        const delays = [1000, 5000, 30000]; // 1s, 5s, 30s
        const delayMs = delays[attempt - 1];

        console.warn(
          `⚠️ Sync attempt ${attempt} failed. Retrying in ${delayMs / 1000}s...`
        );

        await new Promise(resolve => setTimeout(resolve, delayMs));
        return SyncManager.syncWithRetry(queries, attempt + 1, maxAttempts);
      } else {
        throw error;
      }
    }
  },

  /**
   * Perform the actual sync operation
   */
  performSync: async (queries) => {
    let synced = 0;
    let failed = 0;

    // Build sync payload with queue IDs so backend can map responses
    const syncPayload = queries.map(q => ({
      id: q.id,
      query: q.query,
      timestamp: q.timestamp || null,
    }));

    try {
      // Call backend sync endpoint with queue IDs
      const syncResult = await APIClient.syncOfflineQueries(syncPayload);

      if (!syncResult.responses || !Array.isArray(syncResult.responses)) {
        throw new Error('Invalid response format from sync endpoint');
      }

      // Process each queued query by matching response by ID
      for (let i = 0; i < queries.length; i++) {
        const queuedQuery = queries[i];

        // Try to find a response that matches the queue id
        const responseData = syncResult.responses.find(r => String(r.id) === String(queuedQuery.id));

        if (responseData && responseData.response) {
          try {
            // Save the response to database using the original queue id
            await Database.saveOfflineResponse(
              queuedQuery.id,
              responseData.response,
              responseData.llm_used || 'unknown',
              responseData.category || 'general',
              responseData.response_time || 0
            );

            // Add response message to Redux store and chat history
            const messageId = `synced-${queuedQuery.id}-${Date.now()}`;
            const message = {
              id: messageId,
              type: 'assistant',
              text: responseData.response,
              llmUsed: responseData.llm_used || 'unknown',
              category: responseData.category || 'general',
              responseTime: responseData.response_time || 0,
              isCached: false,
              isQueued: false,
            };

            // Properly dispatch using imported action
            store.dispatch(addMessage(message));

            // Save to chat history
            try {
              await Database.saveMessage(message);
            } catch (dbError) {
              console.error('Failed to save synced message to chat history:', dbError);
            }

            synced++;
          } catch (saveError) {
            console.error(
              `❌ Failed to save response for queue ID ${queuedQuery.id}:`,
              saveError.message || saveError
            );
            failed++;
          }
        } else {
          console.warn(`⚠️ No response received from backend for queue ID ${queuedQuery.id}`);
          failed++;
        }
      }

      return {
        success: true,
        synced,
        failed,
      };
    } catch (error) {
      console.error('❌ Sync perform error:', error.message || error);
      throw error;
    }
  },

  /**
   * Schedule background sync (called when network comes online)
   */
  scheduleSync: async () => {
    console.log('📡 Network restored, triggering sync...');
    // Delay slightly to allow network to stabilize
    await new Promise(resolve => setTimeout(resolve, 1000));
    await SyncManager.syncPending();
  },

  /**
   * Get sync status and pending count
   */
  getStatus: async () => {
    try {
      const pending = await Database.getPendingQueries();
      const synced = await Database.getSyncedResponses();

      return {
        isSyncing: SyncManager.isSyncing,
        pendingCount: pending.length,
        syncedCount: synced.length,
      };
    } catch (error) {
      console.error('❌ Get status error:', error);
      return {
        isSyncing: SyncManager.isSyncing,
        pendingCount: 0,
        syncedCount: 0,
      };
    }
  },
};

export default SyncManager;
