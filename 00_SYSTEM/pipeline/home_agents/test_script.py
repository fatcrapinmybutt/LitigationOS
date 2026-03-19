import time
t0 = time.perf_counter()
from litigation_context_mcp import db
conn = db.get_connection()
elapsed = time.perf_counter() - t0
print(f'get_connection: {elapsed*1000:.0f}ms')

# Verify error_telemetry table
tables = {r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
assert 'error_telemetry' in tables, f'MISSING error_telemetry in {tables}'
print('error_telemetry: EXISTS')

# Test telemetry
db.record_error(conn, db.ErrorCode.ERR_FTS_SYNTAX, 'test', 'test msg')
c = conn.execute('SELECT COUNT(*) as c FROM error_telemetry').fetchone()['c']
print(f'Telemetry rows: {c}')

# Test FTS sanitizer  
assert db.sanitize_fts_query('test bad') == 'test bad'
assert db.sanitize_fts_query('') == '""'
print('FTS sanitizer: PASS')

# Test StructuredError
e = db.StructuredError(db.ErrorCode.ERR_DISK_FULL, 'no space')
assert 'Insufficient disk space' in e.hint
print('StructuredError: PASS')

# Test circuit breaker
assert db._db_circuit.status['state'] == 'closed'
print('Circuit breaker: CLOSED')

# Test health state
assert not db.health.degraded
print('Health: NOT DEGRADED')

# Count ErrorCodes
print(f'ErrorCodes: {len(db.ErrorCode)}')
print(f'Recovery hints: {len(db._RECOVERY_HINTS)}')

conn.close()
print('ALL TESTS PASSED')
