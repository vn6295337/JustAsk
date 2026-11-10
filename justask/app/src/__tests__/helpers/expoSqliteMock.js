// expo-sqlite-compatible adapter over Node's built-in sqlite (test only)
const { DatabaseSync } = process.getBuiltinModule('node:sqlite');

const wrap = (raw) => ({
  closed: false,
  execAsync: async (sql) => raw.exec(sql),
  runAsync: async (sql, params = []) => {
    const r = raw.prepare(sql).run(...params);
    return { lastInsertRowId: Number(r.lastInsertRowid), changes: r.changes };
  },
  getFirstAsync: async (sql, params = []) => raw.prepare(sql).get(...params) || null,
  getAllAsync: async (sql, params = []) => raw.prepare(sql).all(...params),
  withTransactionAsync: async (fn) => {
    raw.exec('BEGIN');
    try {
      await fn();
      raw.exec('COMMIT');
    } catch (e) {
      raw.exec('ROLLBACK');
      throw e;
    }
  },
  closeAsync: async function () {
    raw.close();
    this.closed = true;
  },
});

let opens = 0;
module.exports = {
  __esModule: true,
  get opens() { return opens; },
  openDatabaseAsync: jest.fn(async () => {
    opens++;
    await new Promise((r) => setTimeout(r, 5)); // make init race observable
    return wrap(new DatabaseSync(':memory:'));
  }),
};
