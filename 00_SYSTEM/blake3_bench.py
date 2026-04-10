"""BLAKE3 vs xxHash benchmark with correct API."""
import blake3, xxhash, time, os

data = b"LITIGATION_BENCHMARK_DATA" * 100_000  # ~2.4 MB
threads = os.cpu_count() or 4

print(f"=== BLAKE3 vs xxHash BENCHMARK ===")
print(f"Data size: {len(data)/1e6:.1f} MB, iterations: 100, CPU cores: {threads}")
print()

# BLAKE3 single-thread
t0 = time.perf_counter()
for _ in range(100):
    blake3.blake3(data, max_threads=1).hexdigest()
b3_1t = time.perf_counter() - t0
b3_1tput = (len(data) * 100) / b3_1t / 1e9
print(f"BLAKE3 (1 thread):      {b3_1tput:.1f} GB/s  ({b3_1t:.3f}s)")

# BLAKE3 multi-thread
t0 = time.perf_counter()
for _ in range(100):
    blake3.blake3(data, max_threads=threads).hexdigest()
b3_mt = time.perf_counter() - t0
b3_mtput = (len(data) * 100) / b3_mt / 1e9
print(f"BLAKE3 ({threads} threads):     {b3_mtput:.1f} GB/s  ({b3_mt:.3f}s)")

# xxHash
t0 = time.perf_counter()
for _ in range(100):
    xxhash.xxh3_128(data).hexdigest()
xx_t = time.perf_counter() - t0
xx_tput = (len(data) * 100) / xx_t / 1e9
print(f"xxHash xxh3_128:        {xx_tput:.1f} GB/s  ({xx_t:.3f}s)")

print()
best = max(b3_mtput, xx_tput)
print(f"Winner: {'BLAKE3 multi' if b3_mtput > xx_tput else 'xxHash'} ({best:.1f} GB/s)")
print(f"BLAKE3 multi vs single: {b3_mtput/b3_1tput:.1f}x speedup")
print(f"BLAKE3 is crypto-secure: YES (SHA-3 class)")
print(f"xxHash is crypto-secure: NO (non-cryptographic)")
print()
print("VERDICT: Use BLAKE3 with max_threads=cpu_count for crypto-grade integrity + speed")
