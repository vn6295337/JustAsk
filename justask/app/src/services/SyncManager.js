import NetInfo from '@react-native-community/netinfo';
import APIClient from './APIClient';
import Database from './Database';
import store from '../store';
import { addMessage, updateMessage } from '../store/querySlice';

// Must not exceed the server's /queue/sync batch limit
const BATCH_SIZE = 20;

const SyncManager = {
  isSyncing: false,
  _current: null,

  /**
   * Start sync process if online.
   * `isSyncing` is set synchronously, so the reconnect handler and the manual
   * Sync button share one in-flight run instead of duplicating LLM calls.
   */
  syncPending: () => {
    if (SyncManager._current) {
      console.log('⏳ Sync already in progress, joining it');
      return SyncManager._current;
    }

    SyncManager.isSyncing = true;
    SyncManager._current = SyncManager._run().finally(() => {
      SyncManager.isSyncing = false;
      SyncManager._current = null;
    });
    return SyncManager._current;
  },

  _run: async () => {
    try {
      // Check network status
      const networkState = await NetInfo.fetch();
      if (!networkState.isConnected) {
        console.log('❌ No internet connection, sync deferred');
        return false;
      }

      // Get pending queries
      const pending = await Database.getPendingQueries();
      if (pending.length === 0) {
        console.log('✅ No pending queries to sync');
        return true;
      }

      console.log(`🔄 Syncing ${pending.length} pending queries...`);

      let synced = 0;
      let failed = 0;
      let aborted = false;

      for (let i = 0; i < pending.length; i += BATCH_SIZE) {
        const chunk = pending.slice(i, i + BATCH_SIZE);
        try {
          const result = await SyncManager.performSync(chunk);
          synced += result.synced;
          failed += result.failed;
        } catch (error) {
          // The server may have processed (and billed) part of this chunk before
          // the request failed. Do NOT re-send immediately: count an attempt for
          // each item and leave it for a later sync; items that reach the attempt
          // limit become 'failed'. Stop here, the network/server is unhealthy.
          console.error('❌ Sync batch failed:', error.message || error);
          // 429 = our own rate limit / sync guard: the server did no work, so
          // no attempt is consumed.
          // 451 = region block: permanent, so fail the items now (no retries).
          if (error.status !== 429) {
            for (const q of chunk) {
              await Database.recordSyncFailure(
                q.id,
                error.message || 'Sync request failed',
                error.status === 451
              );
            }
          }
          aborted = true;
          break;
        }
      }

      console.log(`✅ Synced ${synced} queries, ${failed} failed`);
      return !aborted;
    } catch (error) {
      console.error('❌ Sync error:', error.message);
      return false;
    }
  },

  /**
   * Update the chat placeholder for a queued query (or append a message for
   * legacy queue rows that have no placeholder).
   */
  _applyToChat: async (queuedQuery, fields) => {
    const { text, llmUsed, category, responseTime } = fields;
    const placeholderId = queuedQuery.message_id;

    if (placeholderId) {
      store.dispatch(
        updateMessage({
          id: placeholderId,
          updates: { text, llmUsed, category, responseTime, isCached: false, isQueued: false },
        })
      );
      try {
        await Database.updateMessage(placeholderId, {
          text,
          llm_used: llmUsed || null,
          category: category || null,
          response_time: responseTime || null,
          is_cached: 0,
          is_queued: 0,
        });
      } catch (dbError) {
        console.error('Failed to update queued message in chat history:', dbError);
      }
      return;
    }

    const message = {
      id: `synced-${queuedQuery.id}-${Date.now()}`,
      type: 'assistant',
      text,
      llmUsed,
      category,
      responseTime,
      isCached: false,
      isQueued: false,
    };
    store.dispatch(addMessage(message));
    try {
      await Database.saveMessage(message);
    } catch (dbError) {
      console.error('Failed to save synced message to chat history:', dbError);
    }
  },

  /**
   * Send one batch (<= BATCH_SIZE) and apply per-item results.
   * Throws only if the request itself fails.
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

    const syncResult = await APIClient.syncOfflineQueries(syncPayload);

    if (!syncResult.responses || !Array.isArray(syncResult.responses)) {
      throw new Error('Invalid response format from sync endpoint');
    }

    for (const queuedQuery of queries) {
      const responseData = syncResult.responses.find(r => String(r.id) === String(queuedQuery.id));

      if (responseData && responseData.success !== false && responseData.response) {
        try {
          const fields = {
            text: responseData.response,
            llmUsed: responseData.llm_used || 'unknown',
            category: responseData.category || 'general',
            responseTime: responseData.response_time || 0,
          };
          // Transactional: response row + 'synced' status together
          await Database.saveOfflineResponse(
            queuedQuery.id,
            fields.text,
            fields.llmUsed,
            fields.category,
            fields.responseTime
          );
          await SyncManager._applyToChat(queuedQuery, fields);
          synced++;
        } catch (saveError) {
          console.error(
            `❌ Failed to save response for queue ID ${queuedQuery.id}:`,
            saveError.message || saveError
          );
          try {
            await Database.recordSyncFailure(queuedQuery.id, 'Failed to save response');
          } catch (e) {
            // ignore; nothing more to do
          }
          failed++;
        }
      } else if (responseData?.deferred) {
        // Server never started this item (time budget): leave pending, free retry
        failed++;
      } else {
        // Failed item: count an attempt; 'permanent' (validation) or attempt cap => failed
        const permanent = !!responseData?.permanent;
        console.warn(`⚠️ Sync failed for queue ID ${queuedQuery.id}`);
        try {
          const status = await Database.recordSyncFailure(
            queuedQuery.id,
            responseData?.error || 'No response from backend',
            permanent
          );
          if (status === 'failed') {
            await SyncManager._applyToChat(queuedQuery, {
              text: 'Could not answer this question. Please ask it again.',
              llmUsed: null,
              category: null,
              responseTime: null,
            });
          }
        } catch (dbError) {
          console.error('Failed to record sync failure:', dbError);
        }
        failed++;
      }
    }

    return { success: true, synced, failed };
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
