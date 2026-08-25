# Evaluation results — `baseline`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.630** |
| Accuracy | 0.667 |
| Escalated to arbiter | 30/60 (50%) |
| Flagged for human review | 33/60 (55%) |
| Cost per resume | $0.0148 |
| Total cost | $0.891 |
| Latency p50 / p95 (model time) | 31.3s / 44.0s |
| Wall clock, whole batch | 249s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 1.000 | 0.800 | 0.889 | 20 |
| hold | 0.500 | 0.200 | 0.286 | 20 |
| reject | 0.556 | 1.000 | 0.714 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 16 | 4 | 0 |
| **true hold** | 0 | 4 | 16 |
| **true reject** | 0 | 0 | 20 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| early_career | 0/6 | 0% |
| production_light_ai | 0/7 | 0% |
| adjacent_shipper | 3/6 | 50% |
| demo_specialist | 4/7 | 57% |
| quiet_builder | 6/7 | 86% |
| academic_researcher | 6/6 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Anjali Deshmukh | production_generalist | advance | advance | 7.5 | 8.0 | yes | The panel spread (9.0 / 8.0 / 1.0) is not a genuine disagreement about the same evidence — the three raters read the same resume consistently and simply found the evidence heavily concentrated in two of the three dimensions. Resolving on... |
| Delphine Aubert | production_generalist | advance | advance | 7.5 | 6.0 | yes | The disagreement is less a conflict than a split profile: two panelists converge at 9 on the dimensions this posting weights most heavily, and the third scores 3 on a dimension the rubric itself says is 'the hardest dimension to find evi... |
| Lucas Ferreira | production_generalist | advance | advance | 7.5 | 9.0 | yes | The panel does not actually disagree on the evidence — it disagrees on how to weight one silent dimension. Two of the three dimensions are strongly and consistently supported, and the third is a gap of evidence rather than a contrary sig... |
| Rafael Duarte | production_generalist | advance | advance | 7.5 | 6.0 | yes | The panel is not actually in conflict — the three scores measure different things and the evidence supports all three readings. The apparent disagreement is between two strong build/ship scores and one weak client-facing score, and the r... |
| Cormac Delaney | production_generalist | advance | advance | 7.3 | 9.0 | yes | The panel does not actually disagree on facts — it disagrees on how to weigh a bimodal profile: exceptional on the two dimensions this posting weights most heavily, and empty on the third. Both readings survive scrutiny, so the resolutio... |
| Fatima Zahra | production_generalist | advance | advance | 7.0 | 3.0 | yes | The panel's disagreement is narrower than the score spread suggests: all three agents credit the same body of concrete evidence, and differ mainly on how far it extends past build-time into operational ownership and client-facing work.  ... |
| Oscar Nakamura | production_generalist | advance | advance | 7.0 | 8.0 | yes | The panel's apparent disagreement is largely an artifact of dimension scope rather than a genuine conflict of judgment: the production and technical reviewers are reading the same body of build/deploy evidence and reaching consistent con... |
| Elena Vasquez | quiet_builder | advance | advance | 7.0 | 6.0 | yes | The panel's disagreement is largely an artifact, not a substantive split: the production_reality agent returned a parse failure (score 0.0 at confidence 0.0), which carries no information and must not be read as a finding of zero product... |
| Bennett Cross | adjacent_shipper | advance | advance | 6.5 | 7.0 | yes | The panel is not actually in conflict on the facts — the three raters read the same evidence and agree on its shape: strong production ownership, solid but incomplete agentic depth, and near-absent client-facing signal. The disagreement ... |
| Ewan Brackenridge | quiet_builder | advance | advance | 6.5 | 8.0 | yes | The panel is not actually in conflict — it split along dimensions, with two strong technical/production reads and one zero on client-facing signal. Resolving each:  **Production reality (agree with 7, and I'd hold confidence low).** The ... |
| Mateo Guzman | quiet_builder | advance | advance | 6.5 | 8.0 | yes | The disagreement is less a conflict than a division of labor: the two technical panelists are reading the same evidence set and largely agree, while the client-facing panelist is reporting an absence rather than contradicting them. Resol... |
| Sana Qureshi | quiet_builder | advance | advance | 6.5 | 8.0 | yes | The panel's spread is not a genuine contradiction — the three agents assessed different dimensions and each is internally well-supported by quoted evidence. Resolving them against the posting's own weighting:  **Production reality (uphel... |
| Astrid Bergman | quiet_builder | advance | advance | 6.4 | 8.0 | yes | The panel's spread is less a disagreement than three dimensions measuring different things, and the two low-scoring rationales are compatible with the high one. Resolving each:  **Production reality — sustained at ~8 (raised confidence).... |
| Tobias Reinhardt | quiet_builder | advance | advance | 6.4 | 8.0 | yes | The panel is less in conflict than it appears: the three raters are scoring different dimensions, and the real tension is between a high-but-low-confidence production score (8 @ 0.55) and a confident zero on client-facing signal (0 @ 0.8... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 6.0 | 5.0 | yes | The panel isn't actually in conflict about the facts — all three agents read the same evidence consistently — the spread comes from each dimension weighting different gaps. Resolving: the strongest signal is the one this posting weights ... |
| Keiko Yamashita | adjacent_shipper | advance | hold ⚠ | 6.0 | 8.0 | yes | The panel's spread is mostly an artifact of two reviewers scoring different things from the same evidence, not a genuine factual conflict. The production_reality reviewer scored the candidate's overall engineering track record (8/0.6); t... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 6.0 | 7.0 | yes | The panel's spread is real but resolvable: the three agents are measuring different things and each is largely right within its own lane. On production reality, the high score holds up. The evidence is unusually concrete about live syste... |
| Dele Adeyemi | adjacent_shipper | advance | hold ⚠ | 5.5 | 7.0 | yes | Resolution note first: the technical_integration panelist returned a parse failure (score 0.0, confidence 0.0, 'No rationale returned'). That is a missing reading, not a finding of zero technical depth, and it must not be averaged in as ... |
| Julius Amankwah | adjacent_shipper | advance | hold ⚠ | 5.5 | 7.0 | yes | The panel's spread is not a real contradiction — the three graders are measuring different things and each is largely right within its lane. Resolving them:  **Production reality (agree with 8, keep confidence moderate).** This is the st... |
| Hugo Lindqvist | quiet_builder | advance | hold ⚠ | 5.5 | 6.0 | yes | The panel is not far apart on substance — the two technical reviewers converge at 6.0/0.5 confidence, and the client-facing reviewer's 0.0 is a finding of no evidence rather than a contrary reading of the same evidence. The real disagree... |
| Rina Matsumoto | demo_specialist | hold | hold | 4.0 | 6.0 | yes | The panel does not actually disagree about the facts — it disagrees about how much a strong technical profile can compensate for missing production and client-facing evidence. On the underlying evidence the three reviewers are consistent... |
| Saoirse Lachlan | demo_specialist | hold | hold | 3.5 | 6.0 | yes | The panel spread (6.0 / 2.0 / 0.0) looks like disagreement but is not — all three graders read the same evidence set consistently and arrived at compatible readings. The variance is dimensional, not interpretive: the candidate is genuine... |
| Andres Villalobos | early_career | hold | reject ⚠ | 3.5 | 5.0 | yes | The panel's spread is not a genuine conflict — it reflects three lenses landing on the same underlying fact pattern: a real, shipped data pipeline with an LLM feature bolted on, and nothing else this posting asks for by name.  Resolving ... |
| Ingrid Solberg | early_career | hold | reject ⚠ | 3.3 | 1.0 | no | [production_reality] Some evidence points to real production ownership — "Built and maintained Python microservices that validate incoming transaction metadata against compliance rules, catching 94% of malformed payment data before downs... |
| Beatrix Hollowell | demo_specialist | hold | reject ⚠ | 3.0 | 5.0 | yes | The panel's disagreement is narrower than the score spread suggests. All three reviewers read the same evidence the same way — as benchmark- and eval-framed work — and differ only on how much credit that earns. The technical_integration ... |
| Mei-Lin Chow | demo_specialist | hold | reject ⚠ | 3.0 | 6.0 | yes | The panel does not actually disagree on the underlying facts — all three reviewers read the same evidence the same way; they differ only in how much credit to give benchmark-framed technical work. Resolving that: the technical reviewer's... |
| Priya Raghunathan | demo_specialist | hold | hold | 3.0 | 5.0 | yes | The panel is less divided than it appears: all three reviewers read the same evidence set and agree it describes building and evaluating models, not shipping and supporting them. The apparent split is only that technical_integration cred... |
| Zainab Iqbal | demo_specialist | hold | hold | 3.0 | 5.0 | yes | The panel is not actually in factual conflict — all three graders cite the same two evidence lines and differ only in what those lines are worth against their dimension. The technical grader's 5.0 is the high mark, and it is defensible: ... |
| Hana Novak | demo_specialist | hold | reject ⚠ | 2.5 | 4.0 | yes | The panel's apparent disagreement is narrower than it looks: two agents converge at 1.0 with high confidence (0.85) on production and client-facing evidence, while the third scored 5.0 on technical depth but at only 0.5 confidence and wi... |
| Vera Klimenko | early_career | hold | reject ⚠ | 2.5 | 4.0 | yes | The disagreement is narrower than the spread suggests: the production_reality reviewer scored 5.0 but its own rationale concedes the same limitation the other two reviewers weight heavily — that the AI work is 'fairly thin' with 'no ment... |
| Jonah Steinberg | early_career | hold | reject ⚠ | 2.0 | 3.0 | yes | The panel's apparent disagreement is narrower than it looks: all three agents converge on the same underlying read, and differ only on how much credit the candidate's infrastructure work deserves. The production_reality agent scored 3.0 ... |
| Rohan Malhotra | early_career | hold | reject ⚠ | 2.0 | 2.0 | no | [production_reality] There is some production evidence but almost none of it involves AI/agentic systems as the posting demands — the caching refactor ('reduce average response latency from 320ms to 180ms') and stock-level aggregation AP... |
| Larissa Petrov | production_light_ai | hold | reject ⚠ | 1.3 | 1.0 | no | [production_reality] The evidence is overwhelmingly production infrastructure/SRE work — API gateways, Kubernetes, incident response, uptime SLAs — with no agentic system, memory, tools, or orchestration work described; the only AI-relev... |
| Chiara Bellini | early_career | hold | reject ⚠ | 1.0 | 0.0 | no | [production_reality] The only AI-related evidence is testing and documenting an integration "before production rollout" — explicitly pre-production QA work, not ownership of a shipped, used-in-production system. There is no evidence of b... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles/dates ("Senior AI Solutions Architect \| Oregon Department of Administrative Services") and bare technology lists ("GPT-4, Claude API, LangChain, LlamaIndex"; "Azure OpenA... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles, degrees, and unadorned skill/tool lists like "LangChain, LlamaIndex, Hugging Face Transformers, TensorFlow, PyTorch" and "Pinecone, Weaviate, Milvus, FAISS, Elasticsearch... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence contains only role titles, a degree, and bare technology/tool lists like "ChatGPT, Claude, Gemini, LLaMA... LangChain, LlamaIndex, RAG frameworks" and "AWS, Azure, Google Cloud, Lambda, EC2, S3..." with ... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence contains no sentences describing any system that was built, deployed, or used in production — the AI/ML line is merely a list of tool names ("LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API,... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] The evidence describes production infrastructure engineering (Kubernetes, PostgreSQL, Terraform, monitoring) with real uptime SLAs like "Manage Kubernetes cluster infrastructure serving 40+ clinical applications with... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence describes production infrastructure engineering work ("Led the design and rollout of a new CI/CD platform serving 80+ engineers", "Managed a multi-region EKS cluster on AWS") but contains zero mentions o... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote describes academic/research work — "evaluated on benchmark dataset," "published results in Journal of Operations Research Quarterly," "manuscript under review at ICML" — with no mention of deployment, pro... |
| Marcus Feldman | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes research benchmarking and publication ('published results on MLPerf and SPEC benchmarks', 'Published 5 papers in top venues (NeurIPS, ICML, ICLR)') rather than any deployed system serving real ... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes academic research and publications—NER benchmarks on internal test sets, papers in ACL/NAACL/EMNLP proceedings, a dissertation, and mentorship on "reproducibility standards" and "code archiving... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence consists entirely of skills lines and job titles (e.g., "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" and "Payment processing APIs: Stripe, Square, and internal ledger ... |
| Omar Benali | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence is a bare skills/keyword list (e.g., "RAG systems, vector databases, semantic search" and "Claude API, GPT-4, LangChain integration points") with no sentence describing what was built, deploye... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence shows strong production ownership—"Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users" and "Led incident response team; reduced mean time to resolution f... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence shows genuine production engineering experience ('Production engineering leader with 7 years building and operating mission-critical logistics and supply-chain systems at scale') but none of it relates t... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes solid production infrastructure work — e.g., "Designed and deployed distributed vehicle inspection scheduling API serving 14 regional offices; handles 8,000+ daily requests with 99.97% uptime S... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes production-grade payment infrastructure work ("Architected and operated payment processing infrastructure handling 2.3M transactions daily", "maintained 99.97% uptime SLA") which is genuinely p... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes production infrastructure, DevOps, and reliability engineering (e.g., "Owned on-call rotation for 24/7 production support across 12 microservices" and "Designed disaster recovery procedures for... |
| Claire Fontaine | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes a QA/testing career ("Quality assurance specialist with 6 years of progressive experience testing digital media platforms") with no mention of building, deploying, or maintaining AI/LLM/agentic... |
| Imani Robinson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence shows only generic financial-operations tooling — "Built internal dashboard using SQL and Tableau for real-time reconciliation reporting" and "Automated routine reporting tasks using Python scripts" — wi... |
| Malik Johnson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes a healthcare data analyst role (SQL reporting, Tableau dashboards, Snowflake migration testing) with zero mentions of LLMs, generative AI, agentic systems, or AI-driven solutions of any kind — ... |
| Devon Whitaker | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes academic research work—"peer-reviewed publications on uncertainty quantification in structural biology" with citation counts, a "Thesis defended with distinction," and benchmark performance on ... |
| Kwame Asante | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] Every piece of evidence describes research, publication, or benchmark work — e.g., "synthetic transaction datasets" for fraud detection, papers "published... in *ACM TIST*" and "*NeurIPS 2023*", and a "Dissertation..... |
| Tomas Herrera | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes academic research and publication work — e.g., "Conducted research on recommendation systems and user behavior modeling," "Developed and evaluated multiple sequence-to-sequence models on propri... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes exploratory or strategic activity — "AI implementation roadmap development," "Strategic assessment of emerging language models," "Large language model exploration for script analysis," and "Gen... |
| Nadia Haddad | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes IT helpdesk and systems administration work ("Manage infrastructure and systems support for 120+ internal users", "Administered Windows Server environments", "Deployed patches and security upda... |
| Nia Carrington | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes supply chain and logistics work ("optimizing logistics operations and warehouse management systems", "reducing overstock incidents by 28%") and a reporting dashboard built in "Excel/SQL" that t... |
| Tariq Mansour | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] None of the evidence relates to AI/LLM/agentic systems at all — it describes SQL troubleshooting, Python validation scripts, Tableau dashboards, ETL pipelines, and an AWS migration for an e-commerce analyst role, e.g... |
