from __future__ import annotations

"""
Fusion Kernel Superset Map Graph (deterministic).

Purpose
- Make the repository's "fusion universe" inspectable:
  - capability gates (CUDA/Triton feature detection)
  - fused kernels + their fallbacks
  - validation references (tests, smoke checks)
  - performance models (roofline-ish + kernel-specific sketches)
  - memory traffic models (bytes moved per element/tensor)
  - tracks (non-kernel fusion lanes such as GEMM+epilogue)

Design constraints
- Offline-first export (graph.json + HTML embed).
- Neo4j/Bloom-friendly CSV export: one primary label per node via :LABEL,
  and a subtype via `kind`.
- No network calls, no external dependencies in graph export path.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass(frozen=True)
class Node:
    id: str
    label: str          # Neo4j label (Category in Bloom)
    name: str           # caption
    kind: str           # subtype (used by offline explorer filters)
    doc: Optional[str] = None


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str           # Neo4j relationship type
    doc: Optional[str] = None


def build_graph() -> Dict[str, List[dict]]:
    # -----------------------------------------
    # Capabilities (runtime + compile-time gates)
    # -----------------------------------------
    nodes: List[Node] = [
        Node(id="cap:cuda", label="Capability", name="CUDA Available", kind="capability",
             doc="True when torch.cuda.is_available() and inputs are CUDA tensors."),
        Node(id="cap:triton", label="Capability", name="Triton Available", kind="capability",
             doc="True when Triton import succeeds and kernel compilation is possible."),
        Node(id="cap:triton_erf", label="Capability", name="Triton erf() support", kind="capability",
             doc="True when tl.math.erf is available (required for exact GELU in Triton)."),
        Node(id="cap:triton_reduction", label="Capability", name="Triton reduction gate", kind="capability",
             doc="Conservative gate for reduction-heavy kernels (LayerNorm/Softmax)."),
        Node(id="cap:torch_fallback", label="Capability", name="Torch fallback path", kind="capability",
             doc="Always available: torch reference ops used when Triton path is unavailable or gated."),
        Node(id="cap:fp16", label="Capability", name="FP16 dtype supported", kind="capability",
             doc="Kernel supports float16 inputs; performance depends on GPU architecture."),
        Node(id="cap:bf16", label="Capability", name="BF16 dtype supported", kind="capability",
     doc="Kernel supports bfloat16 inputs; performance depends on GPU architecture."),

# Libraries
Node(id="lib:torch", label="Library", name="PyTorch", kind="library",
     doc="Reference implementations + fallback semantics."),
Node(id="lib:triton", label="Library", name="Triton", kind="library",
     doc="Primary kernel authoring system for fused pointwise/reduction kernels."),
Node(id="lib:cublaslt", label="Library", name="cuBLASLt", kind="library",
     doc="GEMM + epilogue fusion API for NVIDIA GPUs (track target)."),
Node(id="lib:cutlass", label="Library", name="CUTLASS", kind="library",
     doc="Template library for GEMM/epilogue fusion kernels (track target)."),

# Planned expansions (validation first, then kernels)
        Node(id="val:reductions", label="Validation", name="Reductions coverage", kind="validation", doc="Planned: expand validation coverage for reduction-style kernels (numerics, shapes, edge cases)."),
        Node(id="track:validation_expansion", label="Track", name="Validation expansion lane", kind="track", doc="Planned: expand validation coverage (especially reductions) before implementing additional kernels."),
        Node(id="kernel:layernorm_backward", label="Kernel", name="LayerNormFused (bwd)", kind="kernel", doc="Planned: LayerNorm backward kernel lane; gated on reductions validation coverage."),
        Node(id="kernel:masked_softmax_multiblock", label="Kernel", name="MaskedSoftmax (multi-block)", kind="kernel", doc="Planned: multi-block masked softmax; gated on reductions validation coverage."),
        Node(id="kernel:attention_block_fusion", label="Kernel", name="Attention block fusion", kind="kernel", doc="Planned: fused attention block kernels (QK^T, mask+softmax, PV); gated on validation and real-hardware benchmarking."),
        Node(id="track:benchmarking_real_hw", label="Track", name="Real-hardware benchmarking lane", kind="track", doc="Planned: benchmark on real hardware to drive perf and memory submodels."),
        Node(id="perf:occupancy", label="PerfModel", name="Occupancy model", kind="perf_model", doc="Planned: model kernel occupancy as a function of registers, shared memory, and launch params."),
        Node(id="perf:vectorization", label="PerfModel", name="Vectorization model", kind="perf_model", doc="Planned: model vectorization and memory coalescing efficiency."),
        Node(id="mem:shared_mem_pressure", label="MemoryModel", name="Shared-memory pressure model", kind="memory_model", doc="Planned: model shared-memory usage and its impact on occupancy and performance."),

    ]

    # -----------------
    # Reference ops / fallbacks
    # -----------------
    nodes += [
        Node(id="op:torch_gelu_tanh", label="Op", name="torch.gelu(approx='tanh')", kind="op",
             doc="Reference implementation for tanh-approx GELU."),
        Node(id="op:torch_gelu_exact", label="Op", name="torch.gelu(approx='none')", kind="op",
             doc="Reference implementation for exact GELU (erf-based)."),
        Node(id="op:torch_layernorm", label="Op", name="torch.layer_norm", kind="op",
             doc="Reference implementation for LayerNorm."),
        Node(id="op:torch_softmax_masked", label="Op", name="torch.softmax + mask", kind="op",
             doc="Reference masked softmax pattern (mask add -> softmax)."),
        Node(id="op:torch_matmul", label="Op", name="torch.matmul", kind="op",
             doc="Reference GEMM; later replaced by cuBLASLt/CUTLASS epilogue fusion."),
        Node(id="op:torch_add", label="Op", name="torch.add", kind="op", doc="Reference elementwise add."),
    ]

    # -----------------
    # Kernels
    # -----------------
    nodes += [
        Node(id="ker:fused_bias_gelu_tanh", label="Kernel", name="FusedBiasGelu (tanh)", kind="kernel",
             doc="Forward: y = gelu_tanh(x + bias) [+ residual]. Triton fast-path; torch fallback."),
        Node(id="ker:fused_bias_gelu_exact", label="Kernel", name="FusedBiasGeluExact (erf)", kind="kernel",
             doc="Forward: y = gelu_exact(x + bias) [+ residual]. Triton fast-path requires tl.math.erf; torch fallback."),
        Node(id="ker:layernorm_fwd", label="Kernel", name="LayerNormFused (fwd)", kind="kernel",
             doc="Fused layernorm forward (mean/var reduction + affine)."),
        Node(id="ker:layernorm_bwd_ref", label="Kernel", name="LayerNormBackward (ref)", kind="kernel",
             doc="Correctness-first LayerNorm backward (torch reference, graph-enabler for future fusion)."),
        Node(id="ker:masked_softmax_fwd", label="Kernel", name="MaskedSoftmax (fwd)", kind="kernel",
             doc="Masked softmax forward (single-block)."),
        Node(id="ker:masked_softmax_multiblock_fwd", label="Kernel", name="MaskedSoftmaxMultiBlock (fwd)", kind="kernel",
             doc="Multi-block masked softmax forward (Triton static-range loops; supports large N)."),
    ]

    # Performance models (sketches)
    # -----------------
    nodes += [
        Node(id="perf:roofline_pointwise", label="PerfModel", name="Roofline (pointwise)", kind="perf_model",
             doc="Pointwise fusion tends to be memory-bandwidth bound; model = bytes_moved / BW + launch_overhead."),
        Node(id="perf:layernorm_model", label="PerfModel", name="LayerNorm perf sketch", kind="perf_model",
             doc="Reduction-heavy; perf depends on warp-level reductions, L2 reuse, and vectorized loads."),
        Node(id="perf:softmax_model", label="PerfModel", name="Softmax perf sketch", kind="perf_model",
             doc="Stability path: max-reduction -> exp -> sum-reduction -> normalize. Multi-pass unless fused carefully."),
        Node(id="perf:gemm_epilogue_model", label="PerfModel", name="GEMM+epilogue perf sketch", kind="perf_model",
             doc="Dominated by GEMM throughput; epilogue should be fused into GEMM to avoid extra memory round-trips."),
        Node(id="perf:launch_overhead", label="PerfModel", name="Kernel launch overhead", kind="perf_model",
             doc="Small tensors may be launch-bound; fusion helps by reducing kernel count."),
    ]

    # -----------------
    # Memory traffic models (bytes moved)
    # -----------------
    nodes += [
        Node(id="mem:bias_gelu", label="MemoryModel", name="Bias+GELU traffic", kind="memory_model",
             doc="Per element: read x + read bias (+ read residual optional) + write y. Bias often cached; effective BW varies."),
        Node(id="mem:layernorm_fwd", label="MemoryModel", name="LayerNorm fwd traffic", kind="memory_model",
             doc="Reads x; writes y; plus reads gamma/beta. Internal reductions read x multiple times unless cached."),
        Node(id="mem:masked_softmax_fwd", label="MemoryModel", name="Masked softmax fwd traffic", kind="memory_model",
             doc="Reads logits + mask; writes probs. Multi-pass (max, sum) unless fused with online algorithms."),
        Node(id="mem:gemm_epilogue", label="MemoryModel", name="GEMM+epilogue traffic", kind="memory_model",
             doc="Ideal: one write of output with fused epilogue; avoid intermediate output buffers."),
    ]

    # -----------------
    # Tools / scripts
    # -----------------
    nodes += [
        Node(id="tool:env_check", label="Tool", name="env_check.py", kind="tool", doc="Prints capability detection details."),
        Node(id="tool:bench_bias_gelu", label="Tool", name="bench_bias_gelu.py", kind="tool", doc="Microbenchmark for bias+GELU kernels."),
        Node(id="tool:bench_sweep", label="Tool", name="bench_sweep.py", kind="tool", doc="Benchmark sweep harness across shapes/dtypes."),
        Node(id="tool:profile_bias_gelu", label="Tool", name="profile_bias_gelu.py", kind="tool", doc="Profiler-friendly run for fused bias+GELU."),
        Node(id="tool:build_graph", label="Tool", name="build_graph.py", kind="tool", doc="Exports HTML/JSON/CSV/Cypher graph artifacts."),
        Node(id="tool:smoke_test", label="Tool", name="smoke_test.py", kind="tool", doc="Repo smoke test (imports + tiny runs)."),
        Node(id="tool:bloom_perspective_seed", label="Tool", name="bloom_perspective_seed.py", kind="tool", doc="Deterministically rewrites Bloom perspective exports (categories, relationship types, captions, colors)."),
        Node(id="tool:bench_reductions", label="Tool", name="bench_reductions.py", kind="tool", doc="Microbenchmark for reduction-heavy kernels (LayerNorm, masked softmax, multi-block softmax)."),
        Node(id="tool:profile_reductions", label="Tool", name="profile_reductions.py", kind="tool", doc="Profiler-friendly runner for reduction-heavy paths (LayerNorm + masked softmax)."),
        Node(id="tool:model_memory", label="Tool", name="model_memory.py", kind="tool", doc="Deterministic memory-traffic estimator for kernels; emits JSON sketches for graph attachment."),
        Node(id="tool:bloom_perspective_validate", label="Tool", name="bloom_perspective_validate.py", kind="tool", doc="Summarizes and sanity-checks Bloom-exported perspective JSON (schema-flexible)."),
    ]

    # -----------------
    # Artifacts (export outputs)
    # -----------------
    nodes += [
        Node(id="art:graph_json", label="Artifact", name="graph.json", kind="artifact"),
        Node(id="art:html_viewer", label="Artifact", name="FusionKernelSuperset_Map.html", kind="artifact"),
        Node(id="art:nodes_csv", label="Artifact", name="nodes.csv", kind="artifact"),
        Node(id="art:edges_csv", label="Artifact", name="edges.csv", kind="artifact"),
        Node(id="art:neo4j_constraints", label="Artifact", name="neo4j_constraints.cypher", kind="artifact"),
        Node(id="art:neo4j_indexes", label="Artifact", name="neo4j_indexes.cypher", kind="artifact"),
        Node(id="art:neo4j_import", label="Artifact", name="neo4j_import.cypher", kind="artifact"),
        Node(id="art:neo4j_import_no_apoc", label="Artifact", name="neo4j_import_no_apoc.cypher", kind="artifact"),
        Node(id="art:bloom_style", label="Artifact", name="BloomStyle.md", kind="artifact"),
        Node(id="art:bloom_setup", label="Artifact", name="Neo4j_Bloom_Perspective_Setup.md", kind="artifact"),
        Node(id="art:bloom_seed_rules", label="Artifact", name="BloomPerspectiveSeedRules.json", kind="artifact", doc="Deterministic Bloom perspective seed rules used by the seeder."),
        Node(id="art:bloom_perspective_template", label="Artifact", name="BloomPerspectiveTemplate.json", kind="artifact", doc="Generated template Bloom perspective JSON (convenience starter; patching a baseline export remains preferred)."),
        Node(id="art:bloom_perspective_seeded", label="Artifact", name="FusedKernelsLab.seeded-perspective.json", kind="artifact", doc="Seeded Bloom perspective export produced by bloom_perspective_seed.py (filename is conventional; may be overridden)."),
    ]

    # -----------------
    # Edges (relationships)
    # -----------------
    edges: List[Edge] = [
        # Capability gating (fast-path)
        Edge("ker:fused_bias_gelu_tanh", "cap:cuda", "REQUIRES"),
        Edge("ker:fused_bias_gelu_tanh", "cap:triton", "REQUIRES"),
        Edge("ker:fused_bias_gelu_exact", "cap:cuda", "REQUIRES"),
        Edge("ker:fused_bias_gelu_exact", "cap:triton", "REQUIRES"),
        Edge("ker:fused_bias_gelu_exact", "cap:triton_erf", "REQUIRES"),
        Edge("ker:layernorm_fwd", "cap:cuda", "REQUIRES"),
        Edge("ker:layernorm_fwd", "cap:triton", "REQUIRES"),
        Edge("ker:layernorm_fwd", "cap:triton_reduction", "REQUIRES"),
        Edge("ker:masked_softmax_fwd", "cap:cuda", "REQUIRES"),
        Edge("ker:masked_softmax_fwd", "cap:triton", "REQUIRES"),
        Edge("ker:masked_softmax_fwd", "cap:triton_reduction", "REQUIRES"),

        # Fallback edges (reference implementations)
        Edge("ker:fused_bias_gelu_tanh", "op:torch_gelu_tanh", "FALLBACK_TO"),
        Edge("ker:fused_bias_gelu_exact", "op:torch_gelu_exact", "FALLBACK_TO"),
        Edge("ker:layernorm_fwd", "op:torch_layernorm", "FALLBACK_TO"),
        Edge("ker:masked_softmax_fwd", "op:torch_softmax_masked", "FALLBACK_TO"),
        Edge("track:gemm_epilogue", "op:torch_matmul", "FALLBACK_TO"),
        Edge("track:gemm_epilogue", "op:torch_add", "FALLBACK_TO"),

        # Perf + memory models
        Edge("ker:fused_bias_gelu_tanh", "perf:roofline_pointwise", "MODELED_BY"),
        Edge("ker:fused_bias_gelu_exact", "perf:roofline_pointwise", "MODELED_BY"),
        Edge("ker:layernorm_fwd", "perf:layernorm_model", "MODELED_BY"),
        Edge("ker:masked_softmax_fwd", "perf:softmax_model", "MODELED_BY"),
        Edge("track:gemm_epilogue", "perf:gemm_epilogue_model", "MODELED_BY"),
        Edge("ker:fused_bias_gelu_tanh", "mem:bias_gelu", "HAS_MEMORY_MODEL"),
        Edge("ker:fused_bias_gelu_exact", "mem:bias_gelu", "HAS_MEMORY_MODEL"),
        Edge("ker:layernorm_fwd", "mem:layernorm_fwd", "HAS_MEMORY_MODEL"),
        Edge("ker:masked_softmax_fwd", "mem:masked_softmax_fwd", "HAS_MEMORY_MODEL"),
        Edge("track:gemm_epilogue", "mem:gemm_epilogue", "HAS_MEMORY_MODEL"),
        Edge("perf:roofline_pointwise", "perf:launch_overhead", "INCLUDES"),

        # Validation references
        Edge("tool:smoke_test", "val:smoke_repo", "EMITS"),
        Edge("tool:env_check", "val:capability_gates", "EMITS"),
        Edge("tool:bench_sweep", "val:bench_sweep_sanity", "EMITS"),
        Edge("val:smoke_repo", "ker:fused_bias_gelu_tanh", "COVERS"),
        Edge("val:smoke_repo", "ker:fused_bias_gelu_exact", "COVERS"),
        Edge("val:smoke_repo", "ker:layernorm_fwd", "COVERS"),
        Edge("val:smoke_repo", "ker:masked_softmax_fwd", "COVERS"),
        Edge("val:unit_bias_gelu", "ker:fused_bias_gelu_tanh", "COVERS"),
        Edge("val:unit_bias_gelu", "ker:fused_bias_gelu_exact", "COVERS"),

        # Benchmark relationships
        Edge("tool:bench_bias_gelu", "ker:fused_bias_gelu_tanh", "BENCHMARKS"),
        Edge("tool:bench_bias_gelu", "ker:fused_bias_gelu_exact", "BENCHMARKS"),
        Edge("tool:profile_bias_gelu", "ker:fused_bias_gelu_tanh", "PROFILES"),

        # Reduction benchmarks/profiles
        Edge("tool:bench_reductions", "ker:layernorm_fwd", "BENCHMARKS"),
        Edge("tool:bench_reductions", "ker:masked_softmax_fwd", "BENCHMARKS"),
        Edge("tool:bench_reductions", "ker:masked_softmax_multiblock_fwd", "BENCHMARKS"),
        Edge("tool:profile_reductions", "ker:layernorm_fwd", "PROFILES"),
        Edge("tool:profile_reductions", "ker:masked_softmax_fwd", "PROFILES"),
        Edge("tool:model_memory", "mem:layernorm_fwd", "EMITS"),
        Edge("tool:model_memory", "mem:masked_softmax_fwd", "EMITS"),
        Edge("tool:bloom_perspective_validate", "art:bloom_perspective_template", "COVERS"),

        # Validation (unit test) coverage
        Edge("val:unit_layernorm", "ker:layernorm_fwd", "COVERS"),
        Edge("val:unit_masked_softmax", "ker:masked_softmax_fwd", "COVERS"),
        Edge("val:unit_masked_softmax", "ker:masked_softmax_multiblock_fwd", "COVERS"),
        Edge("val:unit_layernorm_backward", "ker:layernorm_bwd_ref", "COVERS"),

        # Library dependencies
        Edge("ker:layernorm_fwd", "lib:triton", "DEPENDS_ON"),
        Edge("ker:masked_softmax_fwd", "lib:triton", "DEPENDS_ON"),
        Edge("ker:masked_softmax_multiblock_fwd", "lib:triton", "DEPENDS_ON"),
        Edge("ker:layernorm_bwd_ref", "lib:torch", "DEPENDS_ON"),
        Edge("track:gemm_epilogue", "lib:cublaslt", "DEPENDS_ON"),
        Edge("track:gemm_epilogue", "lib:cutlass", "DEPENDS_ON"),
        Edge("track:attention_block", "lib:triton", "DEPENDS_ON"),
        # Artifact export relationships
        Edge("tool:build_graph", "art:graph_json", "EXPORTS"),
        Edge("tool:build_graph", "art:html_viewer", "EXPORTS"),
        Edge("tool:build_graph", "art:nodes_csv", "EXPORTS"),
        Edge("tool:build_graph", "art:edges_csv", "EXPORTS"),
        Edge("tool:build_graph", "art:neo4j_constraints", "EXPORTS"),
        Edge("tool:build_graph", "art:neo4j_indexes", "EXPORTS"),
        Edge("tool:build_graph", "art:neo4j_import", "EXPORTS"),
        Edge("tool:build_graph", "art:neo4j_import_no_apoc", "EXPORTS"),
        Edge("tool:build_graph", "art:bloom_style", "EXPORTS"),
        Edge("tool:build_graph", "art:bloom_setup", "EXPORTS"),
        Edge("tool:build_graph", "art:bloom_seed_rules", "EXPORTS"),
        Edge("tool:build_graph", "art:bloom_perspective_template", "EXPORTS"),
        Edge("tool:bloom_perspective_seed", "art:bloom_seed_rules", "REQUIRES"),
        Edge("tool:bloom_perspective_seed", "art:bloom_perspective_seeded", "EXPORTS"),
        # Validation-first kernel expansion order (planned)
        Edge("val:correctness", "val:reductions", "INCLUDES"),
        Edge("track:validation_expansion", "val:reductions", "INCLUDES"),

        Edge("kernel:layernorm_fused", "val:reductions", "REQUIRES"),
        Edge("kernel:masked_softmax_fused", "val:reductions", "REQUIRES"),
        Edge("kernel:layernorm_backward", "val:reductions", "REQUIRES"),
        Edge("kernel:masked_softmax_multiblock", "val:reductions", "REQUIRES"),
        Edge("kernel:attention_block_fusion", "val:reductions", "REQUIRES"),

        Edge("track:kernel_expansion", "kernel:layernorm_backward", "INCLUDES"),
        Edge("track:kernel_expansion", "kernel:masked_softmax_multiblock", "INCLUDES"),
        Edge("track:attention_block", "kernel:attention_block_fusion", "INCLUDES"),

        # Benchmarking-driven perf and memory modeling (planned)
        Edge("track:benchmarking_real_hw", "perf:occupancy", "INCLUDES"),
        Edge("track:benchmarking_real_hw", "perf:vectorization", "INCLUDES"),
        Edge("track:benchmarking_real_hw", "mem:shared_mem_pressure", "INCLUDES"),

        Edge("kernel:layernorm_fused", "perf:occupancy", "MODELED_BY"),
        Edge("kernel:layernorm_fused", "mem:shared_mem_pressure", "HAS_MEMORY_MODEL"),
        Edge("kernel:masked_softmax_fused", "perf:vectorization", "MODELED_BY"),
        Edge("kernel:masked_softmax_fused", "mem:shared_mem_pressure", "HAS_MEMORY_MODEL"),
        Edge("kernel:attention_block_fusion", "perf:occupancy", "MODELED_BY"),
        Edge("kernel:attention_block_fusion", "perf:vectorization", "MODELED_BY"),
        Edge("kernel:attention_block_fusion", "mem:shared_mem_pressure", "HAS_MEMORY_MODEL"),

    ]

    return {"nodes": [n.__dict__ for n in nodes], "edges": [e.__dict__ for e in edges]}