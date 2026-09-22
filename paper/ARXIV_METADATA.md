# arXiv submission metadata

**Title**
From Evidence to Intervention: State Error Propagation and Abstention in Longitudinal LLM-Mediated Psychological Support

**Author**
Naimur Rahman

**Primary category**
cs.CL

**Suggested cross-list**
cs.AI

**Abstract**
Longitudinal LLM-mediated support depends not only on generating plausible responses but on maintaining the right user state across repeated interactions. We study how errors in a persistent representation of situation, appraisal, emotion, regulatory goal, and prior exercise propagate into downstream intervention decisions. A controlled synthetic benchmark compares three architectures using Qwen3-8B: dialogue history only (A), naive structured state (B), and reliability-aware structured state with provenance, temporal scope, contradiction handling, and deferral (C). Six evidence conditions are evaluated over five observations per trajectory. A pre-analysis computational amendment fixed a 20-base held-out pilot before held-out performance was inspected, yielding 1,590 primary and 600 matched-control turn outcomes. Structured state did not improve clean-condition state recall over history prompting (B-A = -8.83 percentage points, 95% bootstrap CI [-19.83, 0.50]). Injected unsupported inference increased persistence in B by 28.33 points [16.67, 41.67], but the associated decision-error increase was not clearly separated from zero. Most importantly, C reduced absolute propagation burden relative to B (-18.11 points [-26.48, -10.60]) while sharply reducing coverage (-76.98 points [-89.20, -63.33]) and increasing conditional state-error propagation rate by 10.18 points [5.27, 15.41]. The reference-mode sensitivity analysis showed the same direction. These results show that lower absolute error burden can be obtained through selectivity without better conditional state reliability. Reliability claims for longitudinal LLM systems should therefore report state-error incidence, conditional propagation, propagation burden, and coverage jointly rather than treating abstention-driven reductions as sufficient evidence of improved reliability.

**Comments**
10 pages, 3 figures, 3 tables. Synthetic non-clinical benchmark; locked 20-base held-out pilot. Code, frozen processed outcomes, and offline reproducibility package accompany the preprint.

**License**
Choose deliberately in the arXiv submission UI; no manuscript license is inferred by the repository tooling.
