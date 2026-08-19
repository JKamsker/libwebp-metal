#!/usr/bin/env python3
"""Static and fail-closed checks for all research experiment guards.

This test never grants the benchmark lease and therefore cannot start timed
work. It does use forced make dry-runs to verify that one selected build flag
defines exactly its matching private macro.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import benchmark_metal_ablation as metal_ablation
import test_backref_cost_attribution_v1_process_ownership as attribution_ownership
import test_backref_cost_attribution_v2_process_ownership as attribution_v2_ownership
import test_backref_cost_attribution_v3_process_ownership as attribution_v3_ownership
import test_backref_cost_attribution_v4_process_ownership as attribution_v4_ownership
import test_backref_cost_attribution_v5_process_ownership as attribution_v5_ownership
import test_backref_cost_attribution_v6_process_ownership as attribution_v6_ownership
import test_backref_cost_attribution_v7_process_ownership as attribution_v7_ownership
import test_backref_cost_attribution_v8_process_ownership as attribution_v8_ownership
import test_backref_cost_attribution_v9_process_ownership as attribution_v9_ownership
import test_backref_cost_attribution_v10_process_ownership as attribution_v10_ownership
import test_backref_cost_attribution_v11_process_ownership as attribution_v11_ownership
import test_next_boundary_operator_portability as boundary_portability


ROOT = Path(__file__).resolve().parents[1]
MATRIX = (
    (
        "WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT",
        "WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT",
        "WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT",
        "src/enc/profile_enc.o",
    ),
    (
        "WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT",
        "WEBP_USE_METAL_CROSSOVER_EXPERIMENT",
        "WEBP_METAL_CROSSOVER_EXPERIMENT",
        "tools/metal_benchmark.o",
    ),
    (
        "WEBP_BUILD_METAL_BATCH_EXPERIMENT",
        "WEBP_USE_METAL_BATCH_EXPERIMENT",
        "WEBP_METAL_BATCH_EXPERIMENT",
        "extras/metal_encode_batch_experiment.o",
    ),
    (
        "WEBP_BUILD_METAL_ABLATION_EXPERIMENT",
        "WEBP_USE_METAL_ABLATION_EXPERIMENT",
        "WEBP_METAL_ABLATION_EXPERIMENT",
        "extras/metal_import_bench.o",
    ),
    (
        "WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT",
        "WEBP_USE_METAL_PREDICTOR_EXPERIMENT",
        "WEBP_METAL_PREDICTOR",
        "src/enc/predictor_enc_metal.o",
    ),
    (
        "WEBP_BUILD_PREDICTOR_BOUNDARY_EXPERIMENT",
        "WEBP_USE_PREDICTOR_BOUNDARY_EXPERIMENT",
        "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT",
        "src/enc/boundary_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_EXACT_EXPERIMENT",
        "WEBP_USE_BACKREF_EXACT_EXPERIMENT",
        "WEBP_BACKREF_EXACT_EXPERIMENT",
        "src/enc/boundary_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT",
        "WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT",
        "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT",
        "src/enc/backref_cache_search_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT",
        "WEBP_USE_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT",
        "WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT",
        "src/enc/cache_size_serial_sweep_enc.o",
    ),
    (
        "WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT",
        "WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT",
        "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT",
        "src/enc/cache_size_single_pass_slab_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT",
        "WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT",
        "src/enc/backref_cost_traceback_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT",
        "src/enc/backref_cost_workspace_ab_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT",
        "src/enc/backref_cost_workspace_remote_v2_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT",
        "src/enc/backref_cost_workspace_remote_v3_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT",
        "src/enc/backref_cost_workspace_remote_v4_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT",
        "src/enc/backref_cost_workspace_remote_v5_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT",
        "src/enc/backref_cost_interval_search_v1_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT",
        "src/enc/backref_cost_interval_search_v2_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT",
        "src/enc/backref_cost_interval_search_v3_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT",
        "src/enc/backref_cost_interval_specialization_v1_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT",
        "src/enc/backref_cost_attribution_v1_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT",
        "src/enc/backref_cost_attribution_v2_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT",
        "src/enc/backref_cost_attribution_v3_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT",
        "src/enc/backref_cost_attribution_v4_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT",
        "src/enc/backref_cost_attribution_v5_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT",
        "src/enc/backref_cost_attribution_v6_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT",
        "src/enc/backref_cost_attribution_v7_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT",
        "src/enc/backref_cost_attribution_v8_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT",
        "src/enc/backref_cost_attribution_v9_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT",
        "src/enc/backref_cost_attribution_v10_experiment_enc.o",
    ),
    (
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT",
        "WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT",
        "src/enc/backref_cost_attribution_v11_experiment_enc.o",
    ),
)


def run(argv: list[str], environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in (
        "WEBP_BENCHMARK_SESSION",
        "WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT",
        "WEBP_METAL_CROSSOVER_EXPERIMENT",
        "WEBP_METAL_BATCH_EXPERIMENT",
        "WEBP_METAL_ABLATION_EXPERIMENT",
        "WEBP_METAL_PREDICTOR",
        "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT",
        "WEBP_BACKREF_EXACT_EXPERIMENT",
        "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT",
        "WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT",
        "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT",
        "WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT",
        "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT",
    ):
        env.pop(name, None)
    if environment:
        env.update(environment)
    return subprocess.run(
        argv, cwd=ROOT, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )


def require_failure(argv: list[str], message: str,
                    environment: dict[str, str] | None = None) -> None:
    result = run(argv, environment)
    assert result.returncode != 0, f"command unexpectedly succeeded: {argv}"
    assert message in result.stdout, (argv, message, result.stdout)


def check_build_matrix() -> None:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile.unix").read_text(encoding="utf-8")
    guard_sources = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory in ("scripts", "tools", "extras", "src/enc", "src/dsp")
        for path in (ROOT / directory).glob("*")
        if path.is_file()
    )
    macros = {row[1] for row in MATRIX}
    for build_flag, macro, runtime_flag, object_file in MATRIX:
        assert f"option({build_flag}" in cmake
        assert macro in cmake
        assert f"{build_flag} ?= 0" in makefile
        assert runtime_flag in guard_sources
        result = run([
            "make", "-B", "-n", "-f", "makefile.unix",
            "WEBP_ENABLE_METAL=1", f"{build_flag}=1", object_file,
        ])
        assert result.returncode == 0, result.stdout
        assert f"-D{macro}=1" in result.stdout, (build_flag, result.stdout)
        leaked = sorted(
            other for other in macros - {macro}
            if f"-D{other}=1" in result.stdout
        )
        assert not leaked, (build_flag, leaked, result.stdout)

    default = run([
        "make", "-B", "-n", "-f", "makefile.unix",
        "WEBP_ENABLE_METAL=0", "examples/cwebp",
    ])
    assert default.returncode == 0, default.stdout
    assert not any(f"-D{macro}=1" in default.stdout for macro in macros)
    assert "src/enc/profile_enc.o" not in default.stdout
    assert "src/enc/boundary_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cache_search_experiment_enc.o" not in default.stdout
    assert "src/enc/cache_size_serial_sweep_enc.o" not in default.stdout
    assert "src/enc/cache_size_single_pass_slab_enc.o" not in default.stdout
    assert "src/enc/backref_cost_traceback_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_workspace_ab_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_workspace_remote_v2_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_workspace_remote_v3_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_workspace_remote_v4_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_workspace_remote_v5_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_interval_search_v1_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_interval_search_v2_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_interval_search_v3_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_interval_specialization_v1_experiment_enc.o" not in default.stdout
    assert "src/enc/backref_cost_attribution_v1_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v1_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v2_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v2_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v3_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v3_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v4_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v4_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v7_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v7_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v8_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v8_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v9_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v9_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v10_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v10_experiment_runner" not in default.stdout
    assert "src/enc/backref_cost_attribution_v11_experiment_enc.o" not in default.stdout
    assert "tools/backref_cost_attribution_v11_experiment_runner" not in default.stdout
    assert "list(REMOVE_ITEM WEBP_ENC_SRCS" in cmake
    assert not any(
        f"add_definitions(-D{macro}" in cmake for macro in macros
    )


def check_omitted_targets() -> None:
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/webp_metal_benchmark"],
        "WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "extras/metal_encode_batch_experiment"],
        "WEBP_BUILD_METAL_BATCH_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "extras/metal_import_bench"],
        "WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_traceback_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tests/backref_cost_traceback_experiment_test"],
        "WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_workspace_ab_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_workspace_remote_v2_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_workspace_remote_v3_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_workspace_remote_v4_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_workspace_remote_v5_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_interval_search_v1_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_interval_search_v2_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_interval_search_v3_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_interval_specialization_v1_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v1_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v2_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v3_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v4_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v7_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v8_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v9_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v10_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT=1",
    )
    require_failure(
        ["make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
         "tools/backref_cost_attribution_v11_experiment_runner"],
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT=1",
    )


def check_promoted_ablation_control() -> None:
    source = (ROOT / "src/enc/picture_csp_enc_metal.mm").read_text(
        encoding="utf-8"
    )
    correctness = (ROOT / "scripts/test_metal.sh").read_text(encoding="utf-8")
    assert "constexpr bool kDefaultBlock2x2 = true;" in source
    assert "legacy_per_pixel) set -- WEBP_METAL_LOSSY_BLOCK_2X2=0" in correctness

    # The released timed matrix remains the historical experiment. Reversing
    # it here would create a follow-up that improperly reused item 4's gate.
    matrix = metal_ablation.matrix_document(
        [metal_ablation.SUITES["lossy"]]
    )
    suite = matrix["suites"][0]
    assert matrix["baseline"] == (
        "all optimization flags disabled; 256 threads per stage"
    )
    assert suite["baseline_environment"]["WEBP_METAL_LOSSY_BLOCK_2X2"] == "0"
    variants = {variant["name"]: variant for variant in suite["variants"]}
    assert "legacy_per_pixel" not in variants
    assert variants["block_2x2"]["delta"] == {
        "WEBP_METAL_LOSSY_BLOCK_2X2": "1"
    }


def check_runtime_and_lease_refusals() -> None:
    python = sys.executable
    with tempfile.TemporaryDirectory(prefix="webp-guard-test-") as temporary:
        output = str(Path(temporary) / "output")
        timed = (
            (
                [python, "scripts/encoder_stage_profile.py", "run"],
                "WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT": "1"},
            ),
            (
                ["scripts/run_metal_crossover_operator.sh"],
                "WEBP_METAL_CROSSOVER_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_CROSSOVER_EXPERIMENT": "1"},
            ),
            (
                [python, "scripts/benchmark_metal.py", "run", "--runner",
                 "makefile.unix", "--output", output,
                 "--acknowledge-exclusive-session"],
                "WEBP_METAL_CROSSOVER_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_CROSSOVER_EXPERIMENT": "1"},
            ),
            (
                [python, "scripts/metal_crossover_operator.py", "run",
                 "--runner", "makefile.unix", "--output-dir", output,
                 "--acknowledge-exclusive-session"],
                "WEBP_METAL_CROSSOVER_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_CROSSOVER_EXPERIMENT": "1"},
            ),
            (
                ["scripts/run_metal_batch_experiment.sh"],
                "WEBP_METAL_BATCH_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_BATCH_EXPERIMENT": "1"},
            ),
            (
                [python, "scripts/benchmark_metal_ablation.py", "--run",
                 "--output", output],
                "WEBP_METAL_ABLATION_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_ABLATION_EXPERIMENT": "1"},
            ),
            (
                ["scripts/benchmark_predictor_metal_experiment.sh"],
                "WEBP_METAL_PREDICTOR=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_METAL_PREDICTOR": "1"},
            ),
            (
                [python, "scripts/run_next_boundary_experiments.py", "run",
                 "predictor_boundary", output],
                "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_PREDICTOR_BOUNDARY_EXPERIMENT": "1"},
            ),
            (
                [python, "scripts/run_next_boundary_experiments.py", "run",
                 "backref_exact", output],
                "WEBP_BACKREF_EXACT_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_BACKREF_EXACT_EXPERIMENT": "1"},
            ),
            (
                [python, "scripts/run_backref_cache_search_experiment.py",
                 "run", "backref_cache_search", output],
                "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT=1",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT": "1"},
            ),
            (
                [python,
                 "scripts/run_cache_size_single_pass_slab_experiment.py",
                 "run", output],
                "WEBP_BENCHMARK_SESSION=exclusive",
                "WEBP_BENCHMARK_SESSION=exclusive",
                {"WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT": "1"},
            ),
        )
        for argv, runtime_message, lease_message, runtime_environment in timed:
            require_failure(argv, runtime_message)
            require_failure(argv, lease_message, runtime_environment)
        # The row-12 operator is frozen to its historical protocol commit and
        # correctly rejects this newer source tree at its hash boundary. Its
        # own committed protocol test retains the original session-refusal
        # assertion; follow-up protocols must test their new launchers.


def main() -> int:
    boundary_portability.main()
    attribution_ownership.main()
    attribution_v2_ownership.main()
    attribution_v3_ownership.main()
    attribution_v4_ownership.main()
    attribution_v5_ownership.main()
    attribution_v6_ownership.main()
    attribution_v7_ownership.main()
    attribution_v8_ownership.main()
    attribution_v9_ownership.main()
    attribution_v10_ownership.main()
    attribution_v11_ownership.main()
    check_build_matrix()
    check_omitted_targets()
    check_promoted_ablation_control()
    check_runtime_and_lease_refusals()
    print("PASS: thirty-one independent build/runtime guards, fail-closed "
          "leases, and attribution v1-v11 process ownership")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
