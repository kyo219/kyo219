<div align="center">

# Hi, I'm mokumoku(kyo219) 👋

Building ML tools and cozy virtual spaces.

</div>

## 🛠️ Projects

**[MokuMoku Town](https://mokumoku.town/en/)** 🏙️<br>
A virtual office in your browser. _Loosely connected, deeply focused._

**[LightGBM-MoE](https://github.com/kyo219/LightGBM-MoE)** 🌲<br>
A regime-switching / Mixture-of-Experts extension of LightGBM.

## 🌱 OSS Contributions

<!-- OSS-CONTRIB:START -->
[![numpyro](https://img.shields.io/badge/numpyro%20%28%E2%AD%90%202.7k%29-5%20merged-brightgreen?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pyro-ppl/numpyro/pulls?q=is%3Apr%20author%3Akyo219)

- [#2251](https://github.com/pyro-ppl/numpyro/pull/2251) — Speed up posterior diagnostics (summary 1.7x, effective_sample_size 2.1x)

- [#2250](https://github.com/pyro-ppl/numpyro/pull/2250) — Drop the masked logsumexp reduction in mixture `log_prob`

- [#2248](https://github.com/pyro-ppl/numpyro/pull/2248) — Fix generator being appended instead of a list in scan `carry_shapes`

- [#2247](https://github.com/pyro-ppl/numpyro/pull/2247) — Avoid per-step host sync in the SVI progress-bar loop

- [#2222](https://github.com/pyro-ppl/numpyro/pull/2222) — **Removed unnecessary deep copies in module sampling and batch-shape promotion**
  - Replaced full parameter and distribution copies with structure-only or shallow copies, substantially lowering peak memory usage and making eager batch-shape promotion about 3× faster on large arrays.
  - **Why it matters:** Bayesian inference with large neural networks and distributions can avoid duplicating gigabytes of unchanged parameters, reducing out-of-memory failures and improving eager-execution performance without changing model behavior.

[![LightGBM](https://img.shields.io/badge/LightGBM%20%28%E2%AD%90%2018.7k%29-1%20merged%20%C2%B7%201%20open-brightgreen?style=for-the-badge&logo=github&logoColor=white)](https://github.com/lightgbm-org/LightGBM/pulls?q=is%3Apr%20author%3Akyo219)

- [#7247](https://github.com/lightgbm-org/LightGBM/pull/7247) — **Added LightGBM-MoE to the official external repositories list**
  - Documented a C++-native Mixture-of-Experts extension that combines specialized GBDTs through a learned gating function.
  - **Why it matters:** It makes regime-aware gradient boosting easier to discover for problems where one global model struggles with heterogeneous data, such as changing market conditions or distinct user segments.

- [#7246](https://github.com/lightgbm-org/LightGBM/pull/7246) — **Added native `int8` input support for pre-discretized features** _(under review)_
  - Eliminates the intermediate `float32` copy at the Python–C++ boundary, reducing feature-matrix memory usage by up to 75% while preserving identical predictions.
  - **Why it matters:** Large, low-cardinality datasets can be passed to LightGBM without temporarily quadrupling their memory footprint, making training and inference more practical in memory-constrained environments.
<!-- OSS-CONTRIB:END -->
