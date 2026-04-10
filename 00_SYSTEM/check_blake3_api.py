"""Check blake3 API surface."""
import blake3
print(f"Version: {blake3.__version__}")
print(f"Dir: {[x for x in dir(blake3) if not x.startswith('_')]}")
# Try without max_threads
h = blake3.blake3(b"test")
print(f"Hash: {h.hexdigest()}")
# Check if max_threads is a param
import inspect
sig = inspect.signature(blake3.blake3)
print(f"Params: {list(sig.parameters.keys())}")
