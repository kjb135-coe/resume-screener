# Evaluation results — `baseline`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.601** |
| Accuracy | 0.633 |
| Escalated to arbiter | 33/60 (55%) |
| Flagged for human review | 33/60 (55%) |
| Cost per resume | $0.0154 |
| Total cost | $0.925 |
| Latency p50 / p95 (model time) | 33.7s / 46.0s |
| Wall clock, whole batch | 264s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 1.000 | 0.700 | 0.824 | 20 |
| hold | 0.400 | 0.200 | 0.267 | 20 |
| reject | 0.556 | 1.000 | 0.714 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 14 | 6 | 0 |
| **true hold** | 0 | 4 | 16 |
| **true reject** | 0 | 0 | 20 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 0/7 | 0% |
| early_career | 1/6 | 17% |
| demo_specialist | 3/7 | 43% |
| quiet_builder | 3/7 | 43% |
| adjacent_shipper | 4/6 | 67% |
| academic_researcher | 6/6 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Fatima Zahra | production_generalist | advance | advance | 8.0 | 3.0 | yes | The panel's disagreement is narrow and largely one of emphasis rather than substance — all three graders read the same evidence as concrete and quoted, and none flagged a parse failure or an unsupported inference. Resolving each dimensio... |
| Delphine Aubert | production_generalist | advance | advance | 7.5 | 3.0 | yes | The panel's spread (9.0 / 7.0 / 6.0) reflects genuine differences in evidence density per dimension rather than a real disagreement about the candidate, and the three rationales are mutually consistent — each cites distinct quotes and no... |
| Lucas Ferreira | production_generalist | advance | advance | 7.5 | 9.0 | yes | The disagreement is not actually a conflict about the same evidence — it is two strong dimensions and one genuinely empty one, and the resolution depends on how the rubric weights an absence.  On the two dimensions this posting weights m... |
| Rafael Duarte | production_generalist | advance | advance | 7.5 | 8.0 | yes | The panel is not actually in conflict on the facts — all three agents read the same evidence and agree on what it contains. The spread (9/9/1) reflects a candidate who is unusually strong on the two dimensions this posting weights most h... |
| Cormac Delaney | production_generalist | advance | advance | 7.0 | 6.0 | yes | The panel is not actually in conflict — the two production/technical raters converge at 8.0 and the low score is confined to a single, structurally different dimension. Resolving the spread means deciding how much the client-facing gap s... |
| Oscar Nakamura | production_generalist | advance | advance | 6.8 | 7.0 | yes | The panel is not actually in conflict — the three raters examined different dimensions and each is internally consistent with the quoted evidence. The apparent spread (8/8/1) reflects a genuinely lopsided candidate rather than a scoring ... |
| Sana Qureshi | quiet_builder | advance | advance | 6.8 | 8.0 | yes | The panel's spread is not a genuine contradiction — the three scorers looked at different dimensions and largely agreed on the same underlying evidence: this is a strong builder/operator profile with no visible client-facing signal.  On ... |
| Bennett Cross | adjacent_shipper | advance | advance | 6.5 | 7.0 | yes | The panel is not actually in conflict on substance — the two technical raters converge on the same core artifact, and the third scored a dimension the evidence simply never addresses. Resolving the spread is therefore a weighting questio... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 6.5 | 7.0 | yes | The panel does not actually disagree about the evidence — all three agents read the same record consistently — it disagrees about how to weigh a candidate who is strong on the two engineering dimensions and empty on the third. Resolving ... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 6.5 | 7.0 | yes | The panel's spread is not a genuine contradiction — the three raters agree on the underlying evidence and simply weight different dimensions of it. Resolving them against this posting's specific priorities:  **Production reality (accept ... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.5 | 9.0 | yes | The panel is not actually in conflict — the three scores describe different, non-overlapping parts of the same thin evidence set, and all three read the same quotes consistently. Resolving them:  **Production reality (upheld, ~8.5 rather... |
| Elena Vasquez | quiet_builder | advance | advance | 6.5 | 8.0 | yes | The panel's spread is not a factual disagreement — the three agents assessed different dimensions and largely agree on what the evidence contains. The resolution is a weighting question: how much should a confidently-scored zero on clien... |
| Mateo Guzman | quiet_builder | advance | advance | 6.5 | 8.0 | yes | The panel does not actually disagree about the facts — it disagrees about how much a hard zero on one dimension should weigh. Resolving that against this specific posting: the two dimensions the JD leads with (production-deployed agentic... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 5.5 | 6.0 | yes | The panel is not actually in conflict — the three scores measure different things and are mutually consistent: a candidate with genuine production evidence, partial agentic depth, and no client-facing signal. Resolving each dimension aga... |
| Astrid Bergman | quiet_builder | advance | hold ⚠ | 5.5 | 6.0 | yes | The panel's spread is mostly a disagreement about how much weight to give an absent dimension versus a partially-evidenced one, and both can be resolved against the posting's own priorities.  **Production reality (agree with ~6, and I'd ... |
| Ewan Brackenridge | quiet_builder | advance | hold ⚠ | 5.0 | 7.0 | yes | The panel's split is mostly about how much credit the same quotes deserve, not about what the evidence says, and it resolves cleanly on inspection. The production_reality agent (7.0) and technical_integration agent (4.0) read an identica... |
| Julius Amankwah | adjacent_shipper | advance | hold ⚠ | 4.8 | 6.0 | yes | The panel's spread is narrower than it looks: all three reviewers are reading the same single AI sentence and disagreeing mainly about what weight to give it, not about what the evidence says.  Resolving the disagreement:  **Production r... |
| Keiko Yamashita | adjacent_shipper | advance | hold ⚠ | 4.5 | 8.0 | yes | The panel's disagreement is not a genuine conflict — it reflects three lenses measuring different things about the same evidence, and all three readings survive scrutiny. Resolving them:  **Production reality (adjusted 8.0 → 7.0, confide... |
| Ingrid Solberg | early_career | hold | hold | 4.5 | 6.0 | yes | The disagreement is real but resolvable, and it comes down to *what kind* of production experience the evidence documents. The production_reality panelist scored 7.0 on strong quotes — microservices "built and maintained" that catch "94%... |
| Hugo Lindqvist | quiet_builder | advance | hold ⚠ | 4.5 | 6.0 | yes | The panel's disagreement is narrower than it looks: all three lenses agree the candidate is a capable production distributed-systems engineer whose AI/agentic evidence is thin, and they differ mainly on how much credit the non-AI product... |
| Tobias Reinhardt | quiet_builder | advance | hold ⚠ | 4.0 | 4.0 | yes | Two of three panel dimensions returned usable signal; the third (production_reality) failed to parse and returned 0.0 at 0.0 confidence, which is a missing reading rather than a negative finding and must not be treated as a zero. The ver... |
| Priya Raghunathan | demo_specialist | hold | hold | 3.5 | 6.0 | yes | The panel is less divided than it appears: all three reviewers read the same profile — a strong, hands-on applied-ML/agentic builder whose evidence sits on the research and platform-internals side of the line this posting draws. The tech... |
| Rina Matsumoto | demo_specialist | hold | hold | 3.5 | 6.0 | yes | The panel's disagreement is narrower than the raw spread (1.0 / 7.0 / 1.0) suggests. The technical reviewer awarded 7.0 but at the lowest confidence on the panel (0.6), and its own rationale concedes the decisive point: the evidence 'ske... |
| Zainab Iqbal | demo_specialist | hold | hold | 3.5 | 5.0 | yes | The panel is not in substantive conflict — all three reviewers read the same narrow evidence set and diverge only on how much credit to extend for what is unstated. Resolving that: the technical reviewer is right that the core agentic ev... |
| Mei-Lin Chow | demo_specialist | hold | reject ⚠ | 3.0 | 5.0 | yes | The panel's apparent disagreement is narrower than the score spread suggests: all three agents read the same evidence the same way, and differ only in how much credit to give for build detail that never crosses into production. The techn... |
| Rohan Malhotra | early_career | hold | reject ⚠ | 3.0 | 4.0 | yes | The panel's apparent disagreement (4.0 / 2.0 / 0.0) is not a real conflict — the three raters are measuring different things and their underlying reading of the evidence is identical. All three cite the same small set of quotes and reach... |
| Beatrix Hollowell | demo_specialist | hold | reject ⚠ | 2.5 | 4.0 | yes | The panel is less divided than it appears: two dimensions agree at 1.0 with high confidence (0.85), and the mid-score on technical depth (5.0, confidence 0.7) is itself hedged by the same concern that drives the low scores elsewhere. Res... |
| Hana Novak | demo_specialist | hold | reject ⚠ | 2.5 | 5.0 | yes | The panel is not in substantive disagreement — it is scoring the same profile from three angles and converging on the same picture: a strong research/benchmarking candidate with no production or client-facing evidence. The apparent gap (... |
| Saoirse Lachlan | demo_specialist | hold | reject ⚠ | 2.5 | 4.0 | yes | The panel disagreed on magnitude, not direction — all three read the same evidence as research-and-benchmark work rather than shipped systems, and the resolution is that the technical score (4.0, confidence 0.6) is the outlier that needs... |
| Andres Villalobos | early_career | hold | reject ⚠ | 2.5 | 3.0 | yes | The panel is directionally unanimous (3.0 / 2.0 / 0.0); the only real disagreement is how much credit the production dimension deserves, and that disagreement stems from a scoring error worth correcting before it propagates.  **Resolving... |
| Vera Klimenko | early_career | hold | reject ⚠ | 2.5 | 4.0 | yes | The panel's disagreement is narrower than it looks: all three reviewers read the same evidence and found the same ceiling, differing only on how much credit the one production artifact deserves. The production_reality reviewer's 4.0 (con... |
| Jonah Steinberg | early_career | hold | reject ⚠ | 2.0 | 3.0 | yes | The panel is not actually in substantive disagreement — all three reviewers converge on the same picture (3.0/2.0/0.0), differing only in how much credit to extend to a single line of AI evidence. Resolving that: the sole AI-related item... |
| Larissa Petrov | production_light_ai | hold | reject ⚠ | 1.3 | 1.0 | no | [production_reality] The evidence shows strong production infrastructure work ("Managed production Kubernetes clusters handling 1.2TB/day of streaming data", "99.97% uptime SLA achievement over 28 consecutive months") but almost none of ... |
| Chiara Bellini | early_career | hold | reject ⚠ | 1.0 | 0.0 | no | [production_reality] The evidence describes testing/pilot participation, not production ownership or building: "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool; identified 3... |
| Tariq Mansour | wrong_domain | reject | reject | 1.0 | 3.0 | yes | There is no real disagreement to resolve here — all three panelists converged on the same underlying finding, and the only variance is in how much partial credit each gave for adjacent, non-AI work. On production reality (1.0, conf 0.90)... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of vague, buzzword-laden phrases like "AI implementation roadmap development," "strategic assessment of emerging language models," and "large language model exploration" — none of which... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles/dates ("Senior AI Solutions Architect \| Oregon Department of Administrative Services") and bare technology lists ("GPT-4, Claude API, LangChain, LlamaIndex"; "RAG systems... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles, dates, and skill/tool lists (e.g., "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" and "Payment processing APIs: Stripe, Square, and inte... |
| Omar Benali | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every quote is a bare skills/keyword fragment ("RAG systems, vector databases, semantic search", "Docker containerization, Kubernetes orchestration concepts", "Claude API, GPT-4, LangChain integration points") with n... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] All evidence describes production infrastructure and reliability engineering for video streaming platforms — e.g., "Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] The evidence shows strong production reality in general software/infrastructure engineering—e.g., "Designed and deployed distributed vehicle inspection scheduling API serving 14 regional offices; handles 8,000+ daily... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence describes production infrastructure/DevOps work ("Managed a multi-region EKS cluster on AWS... across development, staging, and production environments", "Architected a GitLab Runner infrastructure on Ku... |
| Imani Robinson | wrong_domain | reject | reject | 0.7 | 1.0 | no | [production_reality] None of the evidence describes AI/agentic systems in production or otherwise; the closest production-flavored claims are non-AI operational tasks like "Built internal dashboard using SQL and Tableau for real-time rec... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes academic research: architectures "evaluated on benchmark dataset," results "published in Journal of Operations Research Quarterly" and "Proceedings of NeurIPS 2023," plus conference presentatio... |
| Tomas Herrera | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence points to a research profile — a "Research Scientist" title, work "Developed and evaluated multiple sequence-to-sequence models on proprietary e-commerce datasets" framed as benchmark improvement, and pu... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The only substantive work described is exploratory/evaluative — "Machine learning model assessment for distribution networks. Data pipeline architecture exploration. Predictive analytics for shipment routing" — which... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence contains only job titles/dates ("Senior Infrastructure Engineer \| Vertex Systems Inc. \| June 2023 – Present"), a degree, and a bare skills list ("LangChain, LlamaIndex, Hugging Face Transformers, OpenA... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes strong production infrastructure work ("Manage Kubernetes cluster infrastructure serving 40+ clinical applications with 99.95% uptime SLA", "On-call rotation lead; handled 200+ production incid... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence is entirely about logistics/supply-chain infrastructure (order-routing microservices, warehouse management systems, inventory sync) with strong production signal — e.g. 'reduced latency p99 from 850ms to... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes production infrastructure/DevOps work ("Architected and deployed a multi-region e-commerce platform," "Built Kubernetes infrastructure for a containerized order processing system," "Implemented... |
| Claire Fontaine | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes QA/testing work on media platforms ("Developed and maintained automated test suites using Selenium and Appium", "Built automated test framework in Python to validate file upload, transcoding, a... |
| Malik Johnson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes SQL reporting, healthcare data analysis, and a Snowflake migration ("Develop and maintain 15+ recurring SQL reports on claims data", "Assisted with migration of legacy reporting system to Snowf... |
| Nadia Haddad | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes IT helpdesk and systems administration work ("Manage infrastructure and systems support for 120+ internal users," "Administered Windows Server environments," "Managed 300+ support tickets month... |
| Nia Carrington | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The candidate's evidence is entirely from supply chain/logistics work with no AI/agentic systems shipped to production — the only AI-related item is "Assisted in pilot project evaluating machine learning for demand f... |
| Devon Whitaker | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes academic research work—"Developing machine learning approaches for protein structure prediction validation within a team of 8 researchers" and contributions to "three peer-reviewed publications... |
| Kwame Asante | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] Every quote describes research artifacts—"synthetic transaction datasets," "internal benchmark," published papers ("Published 4 peer-reviewed papers in top-tier venues"), a benchmark framework using "public financial... |
| Marcus Feldman | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes research artifacts—"Developed TensorBind, an automatic scheduling framework" and "Implemented reverse-mode AD compiler in LLVM; benchmarked against PyTorch and JAX on synthetic operator graphs"... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes academic/research roles ('Senior Research Scientist', 'Postdoctoral Researcher') producing benchmarks and publications ('achieved 91.2% F1 on internal NILT-Policy-2025 benchmark', 'Published "M... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence consists entirely of job titles, dates, degrees, and unsupported skill phrases like "LLM integration frameworks" and "Generative AI model evaluation" — none describe what was built, deployed, or maintain... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] All evidence describes production infrastructure engineering (payment processing, Kubernetes, PostgreSQL, observability, Vault) with no mention of AI/ML, LLMs, agentic systems, memory, tools, or orchestration anywher... |
