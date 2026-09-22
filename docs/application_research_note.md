# Research note: longitudinal state reliability in LLM-mediated psychological support

*Status: pre-empirical. No experiment has been run. This note describes a research design and its engineering, not findings.*

**Why longitudinal state matters.** A support system that remembers someone's situation, interpretation, feelings and goals across sessions can respond more coherently. It can also keep treating an interpretation the person has since revised as current, or record an inference the system made as if the person had said it. In emotion-regulation terms, that risks validating an outdated appraisal, or offering reappraisal to someone who asked to feel understood.

**Research question.** How do errors in a persistent psychological-state representation propagate into later intervention decisions, and can reliability-aware state management reduce that propagation without achieving reliability simply by declining to respond?

**Architecture.** Three systems see identical user evidence and use the same model: dialogue history only (A); an extracted structured state with last-write updates (B); and the same structured state with provenance, temporal scope, explicit/inferred status, contradiction and supersession handling, and a deferral rule (C).

**Controlled experiment.** Synthetic trajectories are generated from latent specifications: twelve everyday, non-clinical situations crossed with eight patterns of change over five check-ins. Controlled faults (missing, contradictory, superseded, unsupported and stale state) are applied only where each isolates its intended effect; this rule was fixed before any model was run and reduces the planned held-out matrix from 1,800 to 1,650 trajectories. The primary measure, State Error Propagation Rate, uses counterfactual single-slot repair to ask whether a specific state error caused a specific downstream decision error.

**Actual findings.** None yet. The planned model is Qwen3-8B in non-thinking mode, which could not be run in the environment where the package was built.

**Failures found so far (design, not results).** Auditing the first version exposed design defects that would have undermined the experiment: every trajectory shared one situation; calibration and test scenarios came from disjoint families; correction wording was applied to people who had never held the corrected view; and several analysis and freeze checks assumed a design that the diversified benchmark no longer has. These were fixed before any data existed. About 55–62% of the benchmark's text still comes from shared templates.

**Limitations.** Synthetic and authored scenarios; short, fixed schedules; explicit statements of interpretation that real conversations rarely contain; no expert or human review yet; no claim about clinical benefit.

**Follow-on questions.** Does propagation differ when the user reacts to the system's own responses (closed loop)? How does it change with less explicit appraisal language? Which reliability mechanism carries any effect, as tested by the prespecified ablations? Do automated fidelity judges miss state-induced errors that remain empathetic in tone?
