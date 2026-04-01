# Design Decision: Async-Only Document Jobs

**Date:** 2026-03-31
**Branch:** feature/mlclient-259
**Commit (last sync impl):** 544d832

## Context

Branch `feature/mlclient-259` introduced async support for document jobs
(`AsyncWriteDocumentsJob`, `AsyncReadDocumentsJob`) alongside the existing
thread-based sync implementations (`WriteDocumentsJob`, `ReadDocumentsJob`).

The sync implementation used `ThreadPoolExecutor` + `queue.Queue` with a
conveyor belt thread and poison pill pattern. The async implementation uses
`asyncio.Semaphore` + `asyncio.gather()` with a single `AsyncMLClient`.

To decide whether to keep both implementations or consolidate, a full
benchmark comparison was run against MarkLogic Documents database (port 8000)
with matching configurations for both sync and async variants.

**Environment:** Linux 6.8.0-1047-aws, Python 3.10.12, Intel Xeon Platinum 8259CL @ 2.50GHz (8 cores)
**Benchmark settings:** pytest-benchmark, single round per test (`--benchmark-min-rounds=1 --benchmark-max-time=0.001`)
**Cache clearing:** MarkLogic caches cleared between sync and async suites

---

## Benchmark Results

### Write Operations (1000 documents)

| Configuration | Sync (ms) | Async (ms) | Delta (%) | Winner |
|--------------|-----------|------------|-----------|---------|
| Default settings | 363.98 | 393.32 | -8.1% | Sync |
| Default threads/concurrency, batch 100 | 347.67 | 276.78 | +20.4% | Async |
| Default threads/concurrency, batch 200 | 330.36 | 322.19 | +2.5% | Async |
| Default threads/concurrency, batch 300 | 324.07 | 341.19 | -5.3% | Sync |
| 4 threads/concurrency, default batch | 333.96 | 447.85 | -34.1% | Sync |
| 8 threads/concurrency, default batch | 268.33 | 373.18 | -39.1% | Sync |
| 12 threads/concurrency, default batch | 291.92 | 285.87 | +2.1% | Async |
| 24 threads/concurrency, default batch | 347.61 | 304.24 | +12.5% | Async |
| 4 threads/concurrency, batch 100 | 326.77 | 356.52 | -9.1% | Sync |
| 8 threads/concurrency, batch 100 | 403.99 | 341.71 | +15.4% | Async |
| 12 threads/concurrency, batch 100 | 295.27 | 667.12 | -125.9% | Sync |
| 24 threads/concurrency, batch 100 | 397.50 | 352.01 | +11.4% | Async |
| 4 threads/concurrency, batch 200 | 412.38 | 395.79 | +4.0% | Async |
| 8 threads/concurrency, batch 200 | 304.59 | 347.42 | -14.1% | Sync |
| 12 threads/concurrency, batch 200 | 418.97 | 372.23 | +11.2% | Async |
| 24 threads/concurrency, batch 200 | 311.36 | 307.83 | +1.1% | Async |
| 4 threads/concurrency, batch 300 | 330.88 | 366.98 | -10.9% | Sync |
| 8 threads/concurrency, batch 300 | 353.30 | 364.47 | -3.2% | Sync |
| 12 threads/concurrency, batch 300 | 306.25 | 437.56 | -42.9% | Sync |
| 24 threads/concurrency, batch 300 | 328.35 | 400.38 | -21.9% | Sync |
| Filesystem source, default settings | 546.23 | 688.56 | -26.1% | Sync |

**Write summary:** 21 configs, async wins 10 (47.6%), sync wins 11 (52.4%), avg delta -8.7%

### Read Operations (10000 documents)

| Configuration | Sync (ms) | Async (ms) | Delta (%) | Winner |
|--------------|-----------|------------|-----------|---------|
| Default settings | 2915.16 | 2568.78 | +11.9% | Async |
| Default threads/concurrency, batch 100 | 3233.55 | 2630.73 | +18.6% | Async |
| Default threads/concurrency, batch 200 | 3215.52 | 2489.59 | +22.6% | Async |
| Default threads/concurrency, batch 300 | 3130.51 | 2370.33 | +24.3% | Async |
| Default threads/concurrency, batch 500 | 3351.89 | 2384.85 | +28.9% | Async |
| Default threads/concurrency, batch 600 | 3623.43 | 2572.90 | +29.0% | Async |
| Default threads/concurrency, batch 700 | 3676.03 | 3006.80 | +18.2% | Async |
| Default threads/concurrency, batch 800 | 3532.80 | 2737.40 | +22.5% | Async |
| Default threads/concurrency, batch 900 | 3501.30 | 2799.77 | +20.0% | Async |
| Default threads/concurrency, batch 1000 | 3898.51 | 2892.66 | +25.8% | Async |
| 4 threads/concurrency, default batch | 2781.18 | 3055.06 | -9.9% | Sync |
| 8 threads/concurrency, default batch | 3619.37 | 2830.74 | +21.8% | Async |
| 12 threads/concurrency, default batch | 2956.03 | 2835.49 | +4.1% | Async |
| 24 threads/concurrency, default batch | 3810.50 | 2584.72 | +32.2% | Async |
| 4 threads/concurrency, batch 100 | 4089.12 | 3168.87 | +22.5% | Async |
| 8 threads/concurrency, batch 100 | 4452.32 | 3037.56 | +31.8% | Async |
| 12 threads/concurrency, batch 100 | 3945.22 | 2844.18 | +27.9% | Async |
| 24 threads/concurrency, batch 100 | 3152.76 | 3562.21 | -13.0% | Sync |
| 4 threads/concurrency, batch 200 | 2595.51 | 3242.68 | -24.9% | Sync |
| 8 threads/concurrency, batch 200 | 2923.22 | 2677.30 | +8.4% | Async |
| 12 threads/concurrency, batch 200 | 3168.58 | 2310.99 | +27.1% | Async |
| 24 threads/concurrency, batch 200 | 3049.91 | 2397.95 | +21.4% | Async |
| 4 threads/concurrency, batch 300 | 2718.82 | 2507.21 | +7.8% | Async |
| 8 threads/concurrency, batch 300 | 2807.36 | 2334.91 | +16.8% | Async |
| 12 threads/concurrency, batch 300 | 2889.17 | 2356.23 | +18.4% | Async |
| 24 threads/concurrency, batch 300 | 3052.30 | 2389.38 | +21.7% | Async |
| 4 threads/concurrency, batch 500 | 2620.97 | 2507.86 | +4.3% | Async |
| 8 threads/concurrency, batch 500 | 3631.65 | 2426.06 | +33.2% | Async |
| 12 threads/concurrency, batch 500 | 3072.01 | 2305.65 | +25.0% | Async |
| 24 threads/concurrency, batch 500 | 2969.54 | 2335.35 | +21.4% | Async |
| 4 threads/concurrency, batch 600 | 2791.11 | 2610.03 | +6.5% | Async |
| 8 threads/concurrency, batch 600 | 3327.90 | 2486.24 | +25.3% | Async |
| 12 threads/concurrency, batch 600 | 2948.50 | 2377.02 | +19.4% | Async |
| 24 threads/concurrency, batch 600 | 3614.47 | 2405.14 | +33.5% | Async |
| 4 threads/concurrency, batch 700 | 2745.69 | 2547.55 | +7.2% | Async |
| 8 threads/concurrency, batch 700 | 2927.15 | 2395.49 | +18.2% | Async |
| 12 threads/concurrency, batch 700 | 3058.51 | 2389.68 | +21.9% | Async |
| 24 threads/concurrency, batch 700 | 3323.72 | 2415.93 | +27.3% | Async |
| 4 threads/concurrency, batch 800 | 2932.52 | 2670.73 | +8.9% | Async |
| 8 threads/concurrency, batch 800 | 3134.99 | 2477.01 | +21.0% | Async |
| 12 threads/concurrency, batch 800 | 3155.89 | 2442.74 | +22.6% | Async |
| 24 threads/concurrency, batch 800 | 3471.19 | 2466.39 | +28.9% | Async |
| 4 threads/concurrency, batch 900 | 2737.53 | 2554.40 | +6.7% | Async |
| 8 threads/concurrency, batch 900 | 3616.87 | 2407.25 | +33.4% | Async |
| 12 threads/concurrency, batch 900 | 3216.00 | 2345.15 | +27.1% | Async |
| 24 threads/concurrency, batch 900 | 4052.26 | 2389.70 | +41.0% | Async |
| 4 threads/concurrency, batch 1000 | 3333.50 | 2694.28 | +19.2% | Async |
| 8 threads/concurrency, batch 1000 | 4000.06 | 2570.90 | +35.7% | Async |
| 12 threads/concurrency, batch 1000 | 4199.60 | 2367.23 | +43.6% | Async |
| 24 threads/concurrency, batch 1000 | 3732.53 | 2409.37 | +35.4% | Async |
| Filesystem output, default settings | 11774.24 | 9585.16 | +18.6% | Async |

**Read summary:** 50 configs, async wins 47 (94.0%), sync wins 3 (6.0%), avg delta +19.9%

Raw JSON data: `notes/*-8000.json`

---

## Key Observations

### Write Operations
- Mixed results: async wins 47.6% vs sync 52.4%
- Default settings favor sync (-8.1%), but batch 100 at default concurrency is best async config (+20.4%)
- High concurrency (24) with moderate batches (100-200) favors async
- Some configs show extreme degradation (12 concurrency/batch 100: -125.9%), suggesting resource contention
- Filesystem source is 26.1% slower in async

### Read Operations
- Async dominates with 94% win rate and +19.9% average improvement
- Higher concurrency (8-24) with larger batches (500-1000) yields 30-40% gains
- Best: 12 concurrency, batch 1000 at +43.6%
- Only 3 configs favor sync, all at low concurrency or specific batch sizes

---

## Decisions

### D1: Consolidate to async-only implementation

Remove sync classes (`DocumentsJob` ABC, sync `WriteDocumentsJob`, sync `ReadDocumentsJob`).
Rename async classes to drop the "Async" prefix:
- `AsyncWriteDocumentsJob` -> `WriteDocumentsJob`
- `AsyncReadDocumentsJob` -> `ReadDocumentsJob`

**Rationale:** Read operations show clear async advantage. Write operations are roughly
equal, but maintaining two parallel implementations doubles the maintenance cost.
The async architecture is simpler (no threading, no queues, no poison pills).

### D2: Adjust default settings

Write defaults changed based on benchmarks:
- `batch_size`: 50 -> **100** (best async write config at default concurrency: +20.4%)
- `concurrency` default: **8** (write is less sensitive to concurrency; avoids outlier degradation)

Read defaults:
- `batch_size`: 400 (unchanged, good balance)
- `concurrency` default: **16** (read benefits from higher concurrency; 8-24 range shows 20-40% gains)

The old CPU-based formula (`min(32, cpu_count + 4)`) was removed. It made sense for
ThreadPoolExecutor but not for async I/O where coroutines don't consume CPU cores.

### D3: Add `run_sync()` wrapper

Both job classes now expose `run_sync()` which wraps `asyncio.run(self.run())`,
enabling synchronous usage without requiring the caller to manage an event loop.

Cannot be called from within a running event loop (asyncio limitation).

---

## Breaking Changes

| Before | After |
|--------|-------|
| `WriteDocumentsJob(thread_count=N)` | `WriteDocumentsJob(concurrency=N)` |
| `ReadDocumentsJob(thread_count=N)` | `ReadDocumentsJob(concurrency=N)` |
| `job.start()` + `job.await_completion()` | `await job.run()` or `job.run_sync()` |
| `job.get_documents()` | `job.documents` (property, after run) |
| `AsyncWriteDocumentsJob` | `WriteDocumentsJob` |
| `AsyncReadDocumentsJob` | `ReadDocumentsJob` |
| Write default batch=50 | Write default batch=100 |
| Write default concurrency=cpu+4 | Write default concurrency=8 |
| Read default concurrency=cpu+4 | Read default concurrency=16 |

## Old Implementation Reference

The last commit containing the sync (ThreadPoolExecutor) implementation is `544d832`.
To view the old code: `git show 544d832:mlclient/jobs/documents_jobs.py`
