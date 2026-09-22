# Focused literature review

Search date: 20 September 2026. Status: focused scoping review, not a systematic review or proof of priority. Primary papers, publisher records, ACL Anthology, arXiv, and author project pages were inspected. Search terms included the named benchmarks; Sirts/appraisal/annotation; Uusberg/reappraisal; therapeutic memory; intervention fidelity; and LLM evaluator reliability. Several broad queries returned irrelevant results; author publication lists and direct paper records were used to resolve them. Paywall/anti-bot limitations are identified below. No source data or patient transcripts are imported.

## Psychological foundation

1. **Gross (1998), The Emerging Field of Emotion Regulation: An Integrative Review.** Review of General Psychology, 2, 271–299. [Publisher DOI](https://doi.org/10.1037/1089-2680.2.3.271). The process model distinguishes where regulation acts in emotion generation. This supports separating situations, interpretations, emotions, and regulation strategies. Bibliographic record verified; publisher full text was inaccessible in this session. No numerical finding is taken from it.

2. **Uusberg, Taxer, Yih, H. Uusberg, and Gross (2019), Reappraising Reappraisal.** Emotion Review, 11(4), 267–282. [Publisher](https://doi.org/10.1177/1754073919862617). Conceptual precursor to the expanded framework below. Bibliography and its relationship to the later paper verified. Reappraisal is more specific than reassuring wording.

3. **A. Uusberg, Ford, H. Uusberg, and Gross (2023), Reappraising reappraisal: an expanded view.** Cognition and Emotion, 37(3), 357–370. [Publisher](https://doi.org/10.1080/02699931.2023.2208340); [author-hosted full text](https://static1.squarespace.com/static/56f5c928356fb063f3e181fb/t/653562feb4d7092b3f999e7b/1697997567825/Uusberg_etal_2023_Reappraisal.pdf). Full-text framework inspected. It distinguishes changing construals from changing goals, object-level from mental-state representations, and disengaging from an interpretation from adopting another. This experiment deliberately covers only evidence-grounded exploration of alternative construals. It does not operationalise all reappraisal tactics or assume positive reframing is universally appropriate.

4. **Kuo, Fitzpatrick, Ip, and Uliaszek (2022), The who and what of validation: an experimental examination of validation and invalidation of specific emotions and the moderating effect of emotion dysregulation.** Borderline Personality Disorder and Emotion Dysregulation, 9, 15. [DOI](https://doi.org/10.1186/s40479-022-00185-x); [full text](https://d-nb.info/1263433359/34). Validation recognises the intelligibility of an emotional response in context. The study examines emotion-specific and person-related variation; it does not justify a universal benefit claim. Our distinction between validating a feeling and asserting an unverified external motive is an epistemic operationalisation, not a claim that this paper validates our entire rubric.

## Work directly relevant to Kairit Sirts and Helen Uusberg

5. **Agarwal and Sirts (2025), Exploratory Study into Relations between Cognitive Distortions and Emotional Appraisals.** CLPsych, 127–139. [Paper](https://aclanthology.org/2025.clpsych-1.11/). The study relates appraisal dimensions to distortion categories and examines reframing. Methods use predicted appraisal ratings and an existing thought-record resource. Associations and model-derived labels are not ground truth about an individual. This motivates explicit appraisal representation but does not license diagnosing distortions in this benchmark.

6. **Ruder, A. Uusberg, and Sirts (2025), Assessing the Reliability and Validity of GPT-4 in Annotating Emotion Appraisal Ratings.** CLPsych, 1–11. [Paper](https://aclanthology.org/2025.clpsych-1.1/). Full-text methods/results inspected. They evaluate reader-annotated appraisal dimensions and repeated completions. The findings support investigating aggregation, not assuming an LLM can identify longitudinal intervention errors. **Andero Uusberg**, not Helen Uusberg, is the coauthor of this paper. Helen's direct grounding here comes from items 2–3.

7. **Milintsevich, Sirts, and Dias (2024), Your Model Is Not Predicting Depression Well And That Is Why: A Case Study of PRIMATE Dataset.** [Paper](https://aclanthology.org/2024.clpsych-1.13/). The annotation audit identifies validity problems and emphasises evidence spans and expert reannotation. This informs our separation of latent specification, observable evidence, and adjudication. We neither use PRIMATE nor estimate depression.

Sirts's [author page](https://ksirts.github.io/) and [ACL record](https://aclanthology.org/people/kairit-sirts/unverified/) were checked for relevance. These records establish research context, not endorsement, supervision, or validation of this project.

## Simulation, intervention evaluation, and fidelity

8. **Wang et al. (2024), PATIENT-Ψ: Using Large Language Models to Simulate Patients for Training Mental Health Professionals.** [EMNLP paper](https://aclanthology.org/2024.emnlp-main.711/). Cognitive models precede simulated dialogue, with professional evaluation of a training application. This supports latent-first construction but its patient realism and professional training findings do not transfer to our non-clinical templates. The paper also reports limitations of automatic assessment of simulation fidelity.

9. **Zhao et al. (2024), ESC-Eval: Evaluating Emotion Support Conversations in Large Language Models.** [EMNLP paper](https://aclanthology.org/2024.emnlp-main.883/). Uses role-playing conversations, human ratings, and a learned evaluator. Multi-turn support evaluation already exists. Its broad support ratings do not directly identify which corrupted state proposition changed a subsequent decision.

10. **Li, Yao, Bunyi, Frank, Hwang, and Liu (2025), CounselBench: A Large-Scale Expert Evaluation and Adversarial Benchmarking of Large Language Models in Mental Health Question Answering.** [Author project](https://llm-eval-mental-health.github.io/counselbench-2025/); [preprint](https://arxiv.org/abs/2506.08584). Expert evaluations and adversarial questions expose issues including unsupported assumptions; automated judges can overrate responses and miss expert-identified concerns. We use this as motivation for judge audits, without importing public help-seeking posts or treating their clinical rating scheme as our validated instrument.

11. **Huang et al. (2026), TherapyGym: Evaluating and Aligning Clinical Fidelity and Safety in Therapy Chatbots.** [Preprint and full text](https://arxiv.org/html/2603.18008v1). Methods inspected: CBT rating dimensions, therapy-specific safety labels, simulated interactions, expert judge benchmarking, and reinforcement learning. Its analysis distinguishes rank association from absolute agreement and reports dimension-dependent judge performance. We do not reproduce the CTRS or claim that our much narrower fidelity rubric inherits its psychometric validity.

12. **Madani and Srihari (2025), ESC-Judge: A Framework for Comparing Emotional Support Conversational Agents.** [Preprint](https://arxiv.org/abs/2505.12531). Applies Hill's Exploration–Insight–Action framework to synthetic roles and pairwise evaluation, with human agreement assessment. The reported agreement is task-specific. We instead require error-type sensitivity, specificity, missing judgments, and absolute disagreement on predetermined state traps.

13. **Aghakhani et al. (2025), From Conversation to Automation: Leveraging LLMs for Problem-Solving Therapy Analysis.** [Findings of ACL](https://aclanthology.org/2025.findings-acl.1292/). Annotates intervention strategies and evaluates automatic identification in therapy transcripts. Strategy detection and competent implementation are distinct. No transcripts from this work are used; problem-solving therapy is outside our intervention families.

## Longitudinal memory and modular systems

14. **Zhong et al. (2024), MemoryBank: Enhancing Large Language Models with Long-Term Memory.** [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/29946); [preprint](https://arxiv.org/abs/2305.10250). Combines retrieval, updating, and forgetting for persistent user memory, including psychologically oriented companionship. Persistent memory and time-sensitive updates are prior art; retaining a user profile does not establish its psychological accuracy.

15. **Wu et al., LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory.** [2024 preprint, full text](https://arxiv.org/html/2410.10813v1). Evaluates extraction, cross-session and temporal reasoning, updates, and abstention with controlled histories. Its construction and temporal/update tasks are close methodological neighbours. Our five-point design is far shorter and must not be presented as equivalent long-context difficulty.

16. **Abbasi and Naderi (2025), PsycholexTherapy: Simulating Reasoning in Psychotherapy with Small Language Models in Persian.** [Preprint](https://arxiv.org/abs/2510.03913). The verified abstract reports structured therapeutic reasoning, memory, and multi-turn comparisons. Full text was not available through HTML here. We therefore establish overlap at the architecture level and leave detailed fault-injection overlap unresolved, rather than asserting their method lacks it.

17. **Jewell, McAlister, Deliberto, Wallis, Winns, and Huberty (2026), From Personalization to Therapeutic Continuity: Framework for Memory in AI-Powered Mental Health Systems.** JMIR AI, 5:e99950. [Publisher](https://ai.jmir.org/2026/1/e99950), DOI 10.2196/99950. Publisher metadata/abstract verified; full text was blocked by anti-bot checks. The proposed distinction among episodic, pattern, semantic, and state-responsive memory is directly relevant. This further rules out claiming psychologically informed memory itself as new. Detailed empirical overlap requires full-text follow-up before submission.

## Reliability of LLM evaluation

18. **Zheng et al. (2023), Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.** [Paper](https://arxiv.org/abs/2306.05685). Supports explicit analysis of judge biases and human agreement. General conversational preferences do not validate psychological fidelity judgments.

19. **Shi et al. (2024), Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge.** [Paper](https://arxiv.org/abs/2406.07791). Position sensitivity motivates blinded single-response assessment and random presentation order. Repeated samples from one judge share systematic biases and are not independent experts.

## Synthesis and limitations

The literature supports an appraisal–emotion–goal–strategy–feedback representation, evidence-aware updates, and separate evaluation of fidelity and evaluator reliability. It does **not** establish that our proposed C architecture outperforms B or A. A controlled study can test that proposition only after genuine inference and independent audit. This review is bounded, includes preprints, and has two material full-text gaps (items 16–17). No claim of exhaustive coverage, first discovery, clinical effectiveness, or publication readiness follows.
