# Evaluation results — `baseline`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.847** |
| Accuracy | 0.850 |
| Escalated to arbiter | 28/60 (47%) |
| Flagged for human review | 29/60 (48%) |
| Cost per resume | $0.0299 |
| Total cost | $1.796 |
| Latency p50 / p95 (model time) | 19.4s / 32.9s |
| Wall clock, whole batch | 168s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 1.000 | 0.900 | 0.947 | 20 |
| hold | 0.867 | 0.650 | 0.743 | 20 |
| reject | 0.741 | 1.000 | 0.851 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 18 | 2 | 0 |
| **true hold** | 0 | 13 | 7 |
| **true reject** | 0 | 0 | 20 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 1/7 | 14% |
| adjacent_shipper | 4/6 | 67% |
| demo_specialist | 6/7 | 86% |
| academic_researcher | 6/6 | 100% |
| early_career | 6/6 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| quiet_builder | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Cormac Delaney | production_generalist | advance | advance | 7.8 | 7.0 | yes | Averaging the panel's dimension scores with the rubric's emphasis on production reality and technical/integration depth as primary criteria: Production reality (9.0, conf 0.7) is well-supported by concrete, scaled, live-system evidence —... |
| Rafael Duarte | production_generalist | advance | advance | 7.3 | 5.0 | no | [production_reality] Multiple quotes describe systems that shipped and are actively used at scale, not demos: "now handles 12K+ documents daily across 40+ enterprise clients with 99.2% uptime," "deployed to production serving 60+ interna... |
| Lucas Ferreira | production_generalist | advance | advance | 6.8 | 9.0 | yes | Weighting the three panel dimensions per the posting's emphasis (production reality and technical/integration depth as primary, client-facing signal as a differentiator but not disqualifying): Production reality scores strongly on quoted... |
| Fatima Zahra | production_generalist | advance | advance | 6.7 | 5.0 | no | [production_reality] The evidence describes a deployed, operating system with production infrastructure — "6 years building and operating production agent systems" and "Deployed agentic system on AWS using ECS with auto-scaling; managed ... |
| Oscar Nakamura | production_generalist | advance | advance | 6.3 | 8.0 | yes | Production reality and technical/integration depth both score strongly and consistently across panelists, anchored in concrete quotes: "Built and deployed a multi-agent orchestration system" processing "approximately 12,000 shipment even... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.0 | 8.0 | yes | Weighting the three dimensions per the job description: production_reality (9.0, conf 0.85) is well-supported with direct quotes like "Designed and deployed autonomous order management agent serving 12,000+ daily transactions across 8 re... |
| Delphine Aubert | production_generalist | advance | advance | 6.0 | 8.0 | yes | Weighting the three dimensions as the rubric specifies, but the technical_integration panelist's rationale did not parse, leaving that axis largely unsubstantiated. Production reality is strong and well-evidenced: "Built and shipped an a... |
| Sana Qureshi | quiet_builder | advance | advance | 6.0 | 8.0 | yes | Averaging the three dimension scores per the rubric's weighting: production_reality (8.0) is well-supported by specific, scaled claims like "Built and maintained core recommendation engine serving 12M+ daily active users" and "Engineered... |
| Bennett Cross | adjacent_shipper | advance | advance | 5.7 | 7.0 | yes | Averaging the panel's three dimension scores with the posting's own emphasis in mind. Production reality (8.0, conf .75) is well supported: "Architected and deployed a multi-agent document analysis service for compliance workflows... sys... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 5.5 | 8.0 | yes | Weighting the three dimensions as the rubric specifies: production_reality is strongly supported by concrete, quantified operational evidence — "processes 8,000+ daily alerts, reducing manual triage time by 72% across 12 regional warehou... |
| Elena Vasquez | quiet_builder | advance | advance | 5.5 | 7.0 | yes | Averaging across the three panel dimensions with the posting's own weighting: production reality is well-evidenced by concrete operational metrics ("processing 2.3M images daily with 94% first-pass accuracy," "reduced manual review queue... |
| Tobias Reinhardt | quiet_builder | advance | advance | 5.5 | 7.0 | yes | Averaging the three panel dimensions with weighting toward production reality and technical depth (as the rubric instructs), while treating client-facing absence as a real but not disqualifying gap. Production reality evidence is solid b... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 5.3 | 7.0 | yes | Weighting the three dimensions per the job description's own emphasis (production deployment and agentic/technical integration are the core requirements, client-facing signal is an explicit but secondary differentiator): Production reali... |
| Ewan Brackenridge | quiet_builder | advance | advance | 5.0 | 6.0 | yes | Averaging the panel's assessments: production_reality (6.0) is supported by concrete operational quotes — "monitors production deployments in real-time" and "automated incident remediation that uses LLM reasoning to execute pre-approved ... |
| Mateo Guzman | quiet_builder | advance | advance | 5.0 | 8.0 | yes | Weighting the three dimensions per the rubric's emphasis on this posting's specific profile: Production reality (8.0, conf 0.7) is well-supported — quotes like 'processes 50,000+ chemical structures daily,' 'currently serving 150+ daily ... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 4.7 | 6.0 | yes | Weighting the three dimensions per the job's emphasis: production_reality (7.0, conf 0.55) is reasonably well-supported by direct quotes — "serving 2.8M monthly shoppers," integration "via REST APIs" with named platforms, and "processing... |
| Astrid Bergman | quiet_builder | advance | advance | 4.0 | 6.0 | yes | Weighting the three dimensions per the rubric's emphasis on production reality and technical depth, with client-facing signal being the hardest to find and largely absent here: Production reality shows plausible production-scale metrics ... |
| Hugo Lindqvist | quiet_builder | advance | advance | 4.0 | 6.0 | yes | Production reality: solid non-AI production evidence — 'REST and gRPC APIs supporting warehouse management system used by 340+ facilities moving 8M pallets annually' and '<300ms latency across 12 regional databases with 99.98% uptime' sh... |
| Julius Amankwah | adjacent_shipper | advance | hold ⚠ | 3.7 | 6.0 | yes | Weighting the three dimensions per the job description's own emphasis: production reality is reasonably well supported ("an LLM-powered clinical documentation assistant that automates medical note generation for over 800 physicians acros... |
| Keiko Yamashita | adjacent_shipper | advance | hold ⚠ | 3.5 | 7.0 | yes | The panel's dimension scores diverge sharply because the evidence base is uneven: strong on infrastructure/production claims, weak on the posting's specific agentic-system requirements, and absent on client-facing signal. Production real... |
| Ingrid Solberg | early_career | hold | hold | 3.5 | 3.0 | yes | Averaging across the panel's dimension-specific findings, weighted per the rubric's emphasis on production reality and technical depth over client-facing signal: (1) Production reality: strong evidence exists for non-AI systems at scale ... |
| Zainab Iqbal | demo_specialist | hold | hold | 2.5 | 5.0 | yes | Evidence such as 'Architected multi-agent framework for automating bill summary generation and legislative impact analysis using GPT-4 and Claude with dynamic routing logic' and 'Implemented RAG pipeline integrating 50,000+ archived legi... |
| Andres Villalobos | early_career | hold | hold | 2.3 | 2.0 | no | [production_reality] There is genuine production evidence — the workflow "runs daily across roughly 2,000 facilities, handling approximately 50,000 documents per day" — but this describes an ETL/data pipeline, not an agentic AI system wi... |
| Vera Klimenko | early_career | hold | hold | 2.3 | 3.0 | yes | Weighting the three dimensions per the rubric's emphasis on this posting's specific profile: Production reality (4.0, conf 0.6) is credible but narrow — evidence like "integrated OpenAI API to auto-classify permit types, reducing manual ... |
| Beatrix Hollowell | demo_specialist | hold | hold | 2.0 | 5.0 | yes | Weighting production reality heavily per the rubric's instruction: evidence consistently frames work in benchmark/eval terms — "89.2% accuracy on internal eval set," "measured latency at 340ms per request on benchmarking hardware," "mult... |
| Mei-Lin Chow | demo_specialist | hold | hold | 2.0 | 3.0 | yes | The evidence centers on benchmark and evaluation metrics ('94.7% F1 on internal benchmark dataset', '99.2% accuracy on evaluation set', 'improved baseline accuracy from 87% to 92.3%') rather than deployed systems used by real users — the... |
| Rina Matsumoto | demo_specialist | hold | hold | 2.0 | 3.0 | yes | Weighting production reality most heavily per the rubric: evidence is dominated by benchmark/eval metrics ("benchmarked at 78% tool selection accuracy on held-out test set", "measured 87% semantic correctness on internal eval set", "83% ... |
| Saoirse Lachlan | demo_specialist | hold | hold | 2.0 | 3.0 | yes | Averaging the three panel dimensions with the posting's explicit emphasis on production deployment: Production reality scored 2.0 because evidence describes benchmarked systems ("94% retrieval accuracy," "87% accuracy on held-out test be... |
| Rohan Malhotra | early_career | hold | hold | 2.0 | 3.0 | yes | Averaging across the three panel dimensions with the posting's own weighting (production reality and technical/agentic depth as primary, client-facing as a differentiator): Production reality (3.0) shows genuine shipped backend work ('re... |
| Jonah Steinberg | early_career | hold | hold | 1.7 | 3.0 | yes | Weighted synthesis of the three dimensions per the rubric. Production reality (score 3, confidence 0.6): infrastructure evidence like "Developed monitoring and alerting for build infrastructure using Prometheus and Grafana" and "Maintain... |
| Hana Novak | demo_specialist | hold | hold | 1.5 | 5.0 | yes | Weighting production reality heavily per the job description's explicit emphasis ("not demos or prototypes, but systems used in production"), the candidate's evidence is uniformly research/academic in nature: "Architected multi-agent fra... |
| Chiara Bellini | early_career | hold | hold | 1.3 | 1.0 | no | [production_reality] The evidence describes pre-production and support-adjacent work — "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool; identified 3 critical data mapping i... |
| Larissa Petrov | production_light_ai | hold | hold | 1.3 | 1.0 | no | [production_reality] The evidence shows strong production infrastructure experience ("Built and maintained the infrastructure backbone for a distributed API gateway serving 2.8M requests per day", "Managed production Kubernetes clusters ... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence describes research and academic outputs — an internal benchmark ('achieved 91.2% F1 on internal NILT-Policy-2025 benchmark with 847 manually annotated documents'), publications ('Published "Multilingual ... |
| Tomas Herrera | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence describes research/publication work — e.g., "Published primary dissertation work as 'Sequential Embeddings for E-Commerce Product Graphs' in ACM Transactions on Information Systems" and "Published findin... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles/dates ("Senior AI Solutions Architect \| Oregon Department of Administrative Services") and bare technology lists ("GPT-4, Claude API, LangChain, LlamaIndex"; "Azure OpenA... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of skills lines and title/date fragments (e.g., "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" and "Payment processing APIs: Stripe, Square, and intern... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles, dates, and skill/tool lists such as "ChatGPT, GPT-4, Claude, LangChain, LlamaIndex" and "Vector database implementations, RAG system components" with no sentence describi... |
| Omar Benali | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every piece of evidence is a bare noun-phrase or skills-list fragment—e.g. "Large language models, generative AI frameworks, RAG systems, vector databases, semantic search" and "Claude API, GPT-4, LangChain integrati... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] The evidence describes strong production engineering ("99.97% uptime SLA", "on-call rotation covers 24/7 operations for three production services", "Kubernetes" scaling) but none of it involves AI/LLM/agentic systems... |
| Devon Whitaker | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes academic research and publication output—e.g., "Contributed to three peer-reviewed publications on uncertainty quantification in structural biology" and "Thesis defended with distinction on dee... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote describes benchmark evaluation, publication, or academic research—e.g. "evaluated on benchmark dataset of 15,000+ real-world inventory trajectories," "published... in Proceedings of NeurIPS 2023," and "re... |
| Kwame Asante | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote describes research artifacts—"synthetic transaction datasets," "published research... in preprint phase," "4 peer-reviewed papers," "designed evaluation framework for anomaly detection models across 7 pub... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence consists entirely of job titles, degree information, and skills/tool lists—e.g., "AI & Machine Learning: LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API..." and "Kubernetes clusters and cont... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence shows strong production engineering credentials in logistics/supply-chain systems—"Led redesign of order-routing microservices handling 180K shipments daily" and "Managed 4-person on-call team; establish... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes production infrastructure and reliability engineering work ("achieved 99.95% uptime SLA and reduced MTTR from 45 minutes to 12 minutes", "Implemented comprehensive monitoring stack across 40+ s... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes infrastructure/DevOps work—GitLab Runner on Kubernetes, EKS cluster management, Terraform automation, Prometheus/Grafana monitoring, OPA policy-as-code, and cloud cost auditing—with none of it ... |
| Imani Robinson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes a Payment Operations Specialist role with internal tooling like "Built internal dashboard using SQL and Tableau for real-time reconciliation reporting" and "Automated routine reporting tasks us... |
| Malik Johnson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes a Senior Data Analyst/BI career in healthcare reporting (SQL reports, EHR queries, a Snowflake migration validation), with zero mentions of AI, LLMs, agentic systems, or any production AI deplo... |
| Nadia Haddad | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes only traditional IT operations/help desk work — "Manage infrastructure and systems support for 120+ internal users" and "Deployed patches and security updates on 180 desktop and laptop systems"... |
| Tariq Mansour | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes production data/analytics work like SQL troubleshooting, Tableau dashboards, ETL pipelines, and an AWS migration ('Supported migration of legacy systems to AWS, ensuring zero downtime during tr... |
| Marcus Feldman | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes research and benchmarking work — "published results on MLPerf and SPEC benchmarks" and "benchmarked against PyTorch and JAX on synthetic operator graphs" — with no mention of deployment, users,... |
| Priya Raghunathan | demo_specialist | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] None of the provided evidence mentions explaining work to non-technical audiences, client engagement, or cross-functi... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] Every quote uses exploratory/advisory language—"roadmap development," "strategic assessment," "exploration," "tool comparison matrices"—which describes research and evaluation activity, not systems that shipped or ar... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence consists entirely of job titles, dates, and long lists of tools/technologies (e.g., "ChatGPT, Claude, Gemini, LLaMA, Mistral... LangChain, LlamaIndex, RAG frameworks") with no sentences describing what w... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] None of the evidence mentions AI, LLMs, agentic systems, memory/tools/orchestration, or GenAI at all—it describes production infrastructure work like "Architect and maintain distributed video streaming infrastructure... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence describes production infrastructure and DevOps work — Kubernetes clusters, disaster recovery, database optimization, monitoring — with strong operational rigor ("Manage Kubernetes cluster infrastructure ... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence describes production infrastructure engineering (payment processing, Kubernetes, PostgreSQL, AWS cost optimization) with strong operational rigor, e.g. "maintained 99.97% uptime SLA through systematic re... |
| Claire Fontaine | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes QA/testing work ("Developed and maintained automated test suites using Selenium and Appium, reducing regression testing time by 35%" and "Built automated test framework in Python to validate fi... |
| Nia Carrington | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes a supply chain professional building Excel/SQL dashboards and inventory forecasting ('Developed automated reporting dashboard in Excel/SQL that tracks KPIs for 15 distribution centers' and 'Red... |
