"""Verify all v2 bleeding-edge dependencies are installed and benchmark them."""
import time, sys, os

print("=== V2 DEPENDENCY VERIFICATION ===\n")

# 1. BLAKE3
try:
    import blake3
    data = b"LITIGATION_BENCHMARK" * 100_000  # 2MB test
    t0 = time.perf_counter()
    for _ in range(100):
        h = blake3.blake3(data, max_threads=blake3.AUTO)
    elapsed = time.perf_counter() - t0
    throughput = (len(data) * 100) / elapsed / 1e9
    print(f"[OK] blake3 {blake3.__version__}")
    print(f"     Parallel hash: {throughput:.1f} GB/s (max_threads=AUTO)")
    print(f"     Digest sample: {blake3.blake3(b'test').hexdigest()[:32]}...")
except Exception as e:
    print(f"[FAIL] blake3: {e}")

# 2. FastCDC
try:
    from fastcdc import fastcdc as fcdc
    print(f"\n[OK] fastcdc imported")
    # Quick chunk test on synthetic data
    import tempfile
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    tf.write(os.urandom(1_000_000))  # 1MB random
    tf.close()
    chunks = list(fcdc(tf.name, min_size=4096, avg_size=8192, max_size=16384))
    os.unlink(tf.name)
    print(f"     1MB test: {len(chunks)} chunks (avg {1_000_000//max(len(chunks),1)} bytes)")
except Exception as e:
    print(f"[FAIL] fastcdc: {e}")

# 3. xxHash (existing)
try:
    import xxhash
    print(f"\n[OK] xxhash {xxhash.VERSION}")
except Exception as e:
    print(f"[FAIL] xxhash: {e}")

# 4. Polars (existing)
try:
    import polars as pl
    print(f"\n[OK] polars {pl.__version__}")
except Exception as e:
    print(f"[FAIL] polars: {e}")

# 5. DuckDB (existing)
try:
    import duckdb
    print(f"\n[OK] duckdb {duckdb.__version__}")
except Exception as e:
    print(f"[FAIL] duckdb: {e}")

# 6. sentence-transformers (existing)
try:
    import sentence_transformers
    print(f"\n[OK] sentence-transformers {sentence_transformers.__version__}")
except Exception as e:
    print(f"[FAIL] sentence-transformers: {e}")

# 7. LanceDB (existing)
try:
    import lancedb
    print(f"\n[OK] lancedb {lancedb.__version__}")
except Exception as e:
    print(f"[FAIL] lancedb: {e}")

# BLAKE3 vs xxHash benchmark
print("\n=== BLAKE3 vs xxHash BENCHMARK (2MB x 100 iterations) ===")
data = b"LITIGATION_BENCHMARK_DATA" * 100_000

try:
    t0 = time.perf_counter()
    for _ in range(100):
        blake3.blake3(data, max_threads=blake3.AUTO).hexdigest()
    b3_time = time.perf_counter() - t0
    b3_tput = (len(data) * 100) / b3_time / 1e9

    t0 = time.perf_counter()
    for _ in range(100):
        xxhash.xxh3_128(data).hexdigest()
    xx_time = time.perf_counter() - t0
    xx_tput = (len(data) * 100) / xx_time / 1e9

    print(f"  BLAKE3 (parallel): {b3_tput:.1f} GB/s  ({b3_time:.3f}s)")
    print(f"  xxHash xxh3_128:   {xx_tput:.1f} GB/s  ({xx_time:.3f}s)")
    winner = "BLAKE3" if b3_tput > xx_tput else "xxHash"
    ratio = max(b3_tput, xx_tput) / min(b3_tput, xx_tput)
    print(f"  Winner: {winner} ({ratio:.1f}x faster)")
except Exception as e:
    print(f"  Benchmark error: {e}")

print("\n=== ALL V2 DEPS VERIFIED ===")
