#!/usr/bin/env node
// =============================================================================
// LitigationOS CLI — litigos
// Command-line interface for litigation management and OMEGA scoring
// =============================================================================

const { Command } = require('commander');
const path = require('path');
const chalk = require('chalk');
const Table = require('cli-table3');

// ---------------------------------------------------------------------------
// Database Connection
// ---------------------------------------------------------------------------

const DEFAULT_DB_PATH = path.resolve(__dirname, '../../09_DATA/databases/litigationos.db');
const CONTEXT_DB_PATH = path.resolve(__dirname, '../../litigation_context.db');

function getDb(dbPath) {
  try {
    const Database = require('better-sqlite3');
    if (require('fs').existsSync(dbPath)) {
      return new Database(dbPath, { readonly: true });
    }
  } catch (e) {
    // fall through
  }
  return null;
}

function openDb() {
  return getDb(DEFAULT_DB_PATH) || getDb(CONTEXT_DB_PATH);
}

function withDb(fn) {
  const db = openDb();
  if (!db) {
    console.error(chalk.red('✗ Database not found. Checked:'));
    console.error(chalk.gray(`  - ${DEFAULT_DB_PATH}`));
    console.error(chalk.gray(`  - ${CONTEXT_DB_PATH}`));
    process.exit(1);
  }
  try {
    return fn(db);
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function tableOf(head, rows) {
  const table = new Table({
    head: head.map(h => chalk.cyan.bold(h)),
    style: { head: [], border: [] },
  });
  rows.forEach(r => table.push(r));
  return table.toString();
}

function safeQuery(db, sql, params = []) {
  try {
    return db.prepare(sql).all(...params);
  } catch {
    return [];
  }
}

function safeGet(db, sql, params = []) {
  try {
    return db.prepare(sql).get(...params);
  } catch {
    return null;
  }
}

function listTables(db) {
  return safeQuery(db, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    .map(r => r.name);
}

// ---------------------------------------------------------------------------
// CLI Program
// ---------------------------------------------------------------------------

const program = new Command();

program
  .name('litigos')
  .description('LitigationOS CLI — Litigation management from the command line')
  .version('1.0.0');

// --- litigos status ---
program
  .command('status')
  .description('System health overview')
  .action(() => {
    withDb(db => {
      const tables = listTables(db);

      console.log(chalk.bold.white('\n⚖️  LitigationOS — System Status\n'));
      console.log(chalk.green('● Database:'), chalk.white('Connected'));
      console.log(chalk.green('● Tables:'), chalk.white(tables.length));

      // Count evidence items
      const evidenceTable = tables.find(t => /evidence/i.test(t));
      if (evidenceTable) {
        const count = safeGet(db, `SELECT COUNT(*) as n FROM "${evidenceTable}"`);
        console.log(chalk.green('● Evidence items:'), chalk.white(count?.n ?? 'N/A'));
      }

      // Count documents
      const docTable = tables.find(t => /document/i.test(t));
      if (docTable) {
        const count = safeGet(db, `SELECT COUNT(*) as n FROM "${docTable}"`);
        console.log(chalk.green('● Documents:'), chalk.white(count?.n ?? 'N/A'));
      }

      // Count entities/people
      const entityTable = tables.find(t => /entit|person|people|actor/i.test(t));
      if (entityTable) {
        const count = safeGet(db, `SELECT COUNT(*) as n FROM "${entityTable}"`);
        console.log(chalk.green('● Entities:'), chalk.white(count?.n ?? 'N/A'));
      }

      // Show table list
      console.log(chalk.bold('\n📊 Database Tables:'));
      tables.forEach(t => {
        const count = safeGet(db, `SELECT COUNT(*) as n FROM "${t}"`);
        console.log(chalk.gray(`   ${t}`) + chalk.white(` (${count?.n ?? '?'} rows)`));
      });

      console.log();
    });
  });

// --- litigos omega ---
program
  .command('omega')
  .description('Show OMEGA scores')
  .option('-l, --limit <n>', 'Number of results', '20')
  .option('-s, --sort <field>', 'Sort field (score, name, date)', 'score')
  .action((opts) => {
    withDb(db => {
      const tables = listTables(db);
      const omegaTable = tables.find(t => /omega/i.test(t));

      console.log(chalk.bold.white('\n🎯 OMEGA Scores\n'));

      if (!omegaTable) {
        // Try to find scoring data in any table with score-like columns
        const scored = tables.find(t => {
          const cols = safeQuery(db, `PRAGMA table_info("${t}")`).map(c => c.name);
          return cols.some(c => /score|omega|weight|rating/i.test(c));
        });

        if (scored) {
          const cols = safeQuery(db, `PRAGMA table_info("${scored}")`).map(c => c.name);
          const scoreCol = cols.find(c => /score|omega|weight|rating/i.test(c));
          const nameCol = cols.find(c => /name|title|label|description|id/i.test(c)) || cols[0];

          const rows = safeQuery(db,
            `SELECT "${nameCol}", "${scoreCol}" FROM "${scored}" ORDER BY "${scoreCol}" DESC LIMIT ?`,
            [parseInt(opts.limit)]
          );

          if (rows.length) {
            console.log(tableOf([nameCol, scoreCol],
              rows.map(r => {
                const score = r[scoreCol];
                const bar = '█'.repeat(Math.min(Math.round((score || 0) * 20), 20));
                return [r[nameCol] || 'N/A', `${score ?? 'N/A'} ${chalk.green(bar)}`];
              })
            ));
          } else {
            console.log(chalk.yellow('No scored items found.'));
          }
        } else {
          console.log(chalk.yellow('No OMEGA score table found in database.'));
          console.log(chalk.gray('Available tables: ' + tables.join(', ')));
        }
      } else {
        const rows = safeQuery(db, `SELECT * FROM "${omegaTable}" LIMIT ?`, [parseInt(opts.limit)]);
        if (rows.length) {
          const keys = Object.keys(rows[0]);
          console.log(tableOf(keys, rows.map(r => keys.map(k => String(r[k] ?? '')))));
        } else {
          console.log(chalk.yellow('OMEGA table exists but is empty.'));
        }
      }
      console.log();
    });
  });

// --- litigos search <query> ---
program
  .command('search <query>')
  .description('Search evidence and documents')
  .option('-l, --limit <n>', 'Max results', '25')
  .action((query, opts) => {
    withDb(db => {
      const tables = listTables(db);
      const limit = parseInt(opts.limit);
      let totalHits = 0;

      console.log(chalk.bold.white(`\n🔍 Searching for: "${query}"\n`));

      tables.forEach(tableName => {
        const cols = safeQuery(db, `PRAGMA table_info("${tableName}")`);
        const textCols = cols.filter(c =>
          /text|varchar|char|clob/i.test(c.type) || c.type === ''
        ).map(c => c.name);

        if (textCols.length === 0) return;

        const whereClauses = textCols.map(c => `"${c}" LIKE ?`).join(' OR ');
        const params = textCols.map(() => `%${query}%`);

        const rows = safeQuery(db,
          `SELECT * FROM "${tableName}" WHERE ${whereClauses} LIMIT ?`,
          [...params, limit]
        );

        if (rows.length > 0) {
          totalHits += rows.length;
          console.log(chalk.cyan.bold(`── ${tableName} (${rows.length} match${rows.length > 1 ? 'es' : ''}) ──`));

          rows.forEach(row => {
            const keys = Object.keys(row);
            const displayCol = keys.find(k => /name|title|desc|content|text|label/i.test(k)) || keys[0];
            const idCol = keys.find(k => /^id$/i.test(k));

            const text = String(row[displayCol] || '').substring(0, 120);
            const id = idCol ? chalk.gray(`[${row[idCol]}] `) : '';
            console.log(`  ${id}${text}`);
          });
          console.log();
        }
      });

      if (totalHits === 0) {
        console.log(chalk.yellow('No results found.'));
      } else {
        console.log(chalk.green(`Found ${totalHits} result(s) across tables.\n`));
      }
    });
  });

// --- litigos stats ---
program
  .command('stats')
  .description('System statistics')
  .action(() => {
    withDb(db => {
      const tables = listTables(db);
      const fs = require('fs');

      console.log(chalk.bold.white('\n📈 LitigationOS Statistics\n'));

      // Database file size
      const dbPaths = [DEFAULT_DB_PATH, CONTEXT_DB_PATH];
      dbPaths.forEach(p => {
        try {
          const stat = fs.statSync(p);
          const sizeMB = (stat.size / (1024 * 1024)).toFixed(2);
          console.log(chalk.green('● DB Size:'), chalk.white(`${sizeMB} MB`), chalk.gray(`(${path.basename(p)})`));
        } catch { /* skip */ }
      });

      // Table stats
      console.log(chalk.green('● Tables:'), chalk.white(tables.length));

      let totalRows = 0;
      const tableStats = tables.map(t => {
        const count = safeGet(db, `SELECT COUNT(*) as n FROM "${t}"`)?.n ?? 0;
        totalRows += count;
        return [t, count];
      }).sort((a, b) => b[1] - a[1]);

      console.log(chalk.green('● Total rows:'), chalk.white(totalRows.toLocaleString()));

      console.log(chalk.bold('\n📊 Top Tables by Row Count:'));
      console.log(tableOf(
        ['Table', 'Rows'],
        tableStats.slice(0, 15).map(([name, count]) => [name, count.toLocaleString()])
      ));

      // Column count per table
      const totalCols = tables.reduce((sum, t) => {
        const cols = safeQuery(db, `PRAGMA table_info("${t}")`);
        return sum + cols.length;
      }, 0);

      console.log(chalk.green('\n● Total columns:'), chalk.white(totalCols));
      console.log();
    });
  });

// --- litigos deadlines ---
program
  .command('deadlines')
  .description('Show upcoming deadlines')
  .option('-a, --all', 'Show all deadlines including past')
  .action((opts) => {
    withDb(db => {
      const tables = listTables(db);

      console.log(chalk.bold.white('\n📅 Upcoming Deadlines\n'));

      // Find tables with date-like columns
      let found = false;

      tables.forEach(tableName => {
        const cols = safeQuery(db, `PRAGMA table_info("${tableName}")`);
        const dateCols = cols.filter(c =>
          /date|deadline|due|filing|hearing|scheduled|expires/i.test(c.name)
        ).map(c => c.name);

        if (dateCols.length === 0) return;

        const nameCol = cols.find(c =>
          /name|title|desc|label|type|matter|case/i.test(c.name)
        );
        const displayCol = nameCol ? nameCol.name : cols[0].name;

        dateCols.forEach(dateCol => {
          let sql;
          if (opts.all) {
            sql = `SELECT "${displayCol}", "${dateCol}" FROM "${tableName}" WHERE "${dateCol}" IS NOT NULL ORDER BY "${dateCol}" DESC LIMIT 20`;
          } else {
            sql = `SELECT "${displayCol}", "${dateCol}" FROM "${tableName}" WHERE "${dateCol}" IS NOT NULL AND "${dateCol}" >= date('now') ORDER BY "${dateCol}" ASC LIMIT 20`;
          }

          const rows = safeQuery(db, sql);
          if (rows.length > 0) {
            found = true;
            console.log(chalk.cyan.bold(`── ${tableName}.${dateCol} ──`));

            rows.forEach(row => {
              const dateVal = row[dateCol];
              const label = String(row[displayCol] || 'N/A').substring(0, 80);

              // Color code by urgency
              const now = new Date();
              const deadline = new Date(dateVal);
              const daysUntil = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));

              let icon, color;
              if (daysUntil < 0) {
                icon = '⚠️'; color = chalk.red;
              } else if (daysUntil <= 3) {
                icon = '🔴'; color = chalk.redBright;
              } else if (daysUntil <= 7) {
                icon = '🟡'; color = chalk.yellow;
              } else if (daysUntil <= 30) {
                icon = '🟢'; color = chalk.green;
              } else {
                icon = '⚪'; color = chalk.gray;
              }

              console.log(`  ${icon} ${color(dateVal)} — ${label}`);
            });
            console.log();
          }
        });
      });

      if (!found) {
        console.log(chalk.yellow('No deadline columns found in database tables.'));
        console.log(chalk.gray('Tip: Tables should have columns named like "deadline", "due_date", "hearing_date"'));
      }
      console.log();
    });
  });

// --- Parse and execute ---
program.parse();
