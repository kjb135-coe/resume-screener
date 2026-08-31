# Evaluation results — `baseline`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.900** |
| Accuracy | 0.900 |
| Escalated to arbiter | 12/60 (20%) |
| Flagged for human review | 8/60 (13%) |
| Cost per resume | $0.0047 |
| Total cost | $0.279 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-haiku-4-5-20251001` | $0.247 | 89% |
| `gpt-5.6-luna` | $0.032 | 11% |
| Latency p50 / p95 (model time) | 7.7s / 11.2s |
| Wall clock, whole batch | 98s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.900 | 0.900 | 0.900 | 20 |
| hold | 0.895 | 0.850 | 0.872 | 20 |
| reject | 0.905 | 0.950 | 0.927 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 18 | 1 | 1 |
| **true hold** | 2 | 17 | 1 |
| **true reject** | 0 | 1 | 19 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| early_career | 3/6 | 50% |
| quiet_builder | 5/7 | 71% |
| wrong_domain | 6/7 | 86% |
| academic_researcher | 6/6 | 100% |
| adjacent_shipper | 6/6 | 100% |
| demo_specialist | 7/7 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| production_light_ai | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Delphine Aubert | production_generalist | advance | advance | 9.3 | 2.0 | no | [production_reality] The strongest evidence is: "Built and shipped an autonomous content recommendation agent serving Nexus's streaming platform to 2.8M monthly active users." \| [technical_integration] The strongest evidence is: "Develo... |
| Rafael Duarte | production_generalist | advance | advance | 9.3 | 2.0 | no | [production_reality] The candidate demonstrates substantial production ownership, including that they "Architected and shipped multi-agent workflow system for document processing; now handles 12K+ documents daily across 40+ enterprise cl... |
| Fatima Zahra | production_generalist | advance | advance | 8.7 | 2.0 | no | [production_reality] The evidence states, "AI engineer with 6 years building and operating production agent systems in government and public sector contexts," supported by deployment on AWS with auto-scaling, though it does not explicitl... |
| Bennett Cross | adjacent_shipper | advance | advance | 7.0 | 8.0 | yes | The candidate has strong production and technical evidence: "Architected and deployed a multi-agent document analysis service for compliance workflows, integrating Claude API with internal document retrieval system; system processes 15,0... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 7.0 | 5.0 | no | [production_reality] The strongest production evidence is "Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers." \| [technical_integration] The strongest technical evidence is "Engineered the agen... |
| Ewan Brackenridge | quiet_builder | advance | advance | 7.0 | 9.0 | yes | The candidate shows strong hands-on agentic engineering and production relevance, especially having "Built an agentic system for automated incident remediation that uses LLM reasoning to execute pre-approved infrastructure operations." H... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 6.7 | 7.0 | no | [production_reality] The evidence strongly demonstrates production use: "Architected and deployed an LLM-powered shipment exception handler that processes 8,000+ daily alerts, reducing manual triage time by 72% across 12 regional warehou... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.7 | 9.0 | no | [production_reality] The strongest production evidence is: "Designed and deployed autonomous order management agent serving 12,000+ daily transactions across 8 retail partners; agent uses tool calling to query inventory APIs, trigger ful... |
| Cormac Delaney | production_generalist | advance | advance | 6.7 | 10.0 | no | [production_reality] The strongest evidence is: "Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly with 89% autonomous resolution rate." \| [technical_integration] The strongest evidence is: "Implem... |
| Lucas Ferreira | production_generalist | advance | advance | 6.7 | 10.0 | no | [production_reality] The candidate demonstrates substantial production ownership, including being "On-call for production incidents; established monitoring dashboards tracking agent hallucination rates and API latency." \| [technical_int... |
| Tobias Reinhardt | quiet_builder | advance | advance | 6.7 | 7.0 | no | [production_reality] The candidate provides strong production-scale evidence: "Architected and deployed production LLM-powered product description generation system processing 180K+ merchandise items monthly". \| [technical_integration] ... |
| Julius Amankwah | adjacent_shipper | advance | advance | 6.3 | 6.0 | no | [production_reality] The strongest production evidence is that they "Led the design and launch of an LLM-powered clinical documentation assistant that automates medical note generation for over 800 physicians across Meridian's network." ... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 6.3 | 7.0 | no | [production_reality] The evidence strongly demonstrates production ownership because the candidate "Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBOL sy... |
| Andres Villalobos | early_career | hold | advance ⚠ | 6.3 | 1.0 | no | [production_reality] The strongest production signal is: "I work within the clinical data integration team on the PatientSync platform, a system that processes electronic health records from hospital networks across the Southwest region.... |
| Oscar Nakamura | production_generalist | advance | advance | 6.3 | 10.0 | no | [production_reality] The strongest production evidence is: "I now spend roughly 20% of my time on-call managing agent behavior anomalies and iterating on prompt refinements based on production telemetry." \| [technical_integration] The c... |
| Mateo Guzman | quiet_builder | advance | advance | 6.3 | 8.0 | no | [production_reality] The candidate demonstrates substantial production usage and operational reliability, stating, "Built RAG system with vector embeddings to enable researchers to query historical trial results—currently serving 150+ da... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 6.0 | 10.0 | yes | The candidate has strong production and technical evidence, having "Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer." However, no ... |
| Vera Klimenko | early_career | hold | advance ⚠ | 6.0 | 1.0 | yes | The candidate shows meaningful applied AI and integration experience through a system that "ingested 500+ permit applications monthly" and "integrated OpenAI API to auto-classify permit types," but the evidence does not establish product... |
| Astrid Bergman | quiet_builder | advance | advance | 6.0 | 7.0 | yes | The candidate shows strong technical relevance and meaningful production scale through “Implemented agentic settlement workflow using Claude API with tool use for dispute resolution” and an engine processing “2.3M+ daily settlement recor... |
| Elena Vasquez | quiet_builder | advance | advance | 6.0 | 8.0 | yes | The candidate shows strong technical depth through “Engineered LLM-powered claim summarization agent that processes 15k documents per day; integrated with legacy SOAP APIs through custom adapter layer,” but the evidence does not explicit... |
| Rina Matsumoto | demo_specialist | hold | hold | 5.5 | 8.0 | yes | The candidate shows strong agentic engineering depth, especially a "function-calling orchestration layer enabling tool composition across 40+ API integrations," but the evidence does not establish production operation with real users or ... |
| Ingrid Solberg | early_career | hold | hold | 5.0 | 5.0 | no | [production_reality] The strongest production evidence is that the audit system "now generates compliance reports consumed by six Fortune 500 financial institutions monthly." \| [technical_integration] The clearest AI implementation evid... |
| Rohan Malhotra | early_career | hold | hold | 5.0 | 5.0 | no | [production_reality] The strongest production evidence is: "I built out the instrumentation and logging for the recommendation service to better track cache hit rates and model inference timing, making it easier for the team to debug per... |
| Larissa Petrov | production_light_ai | hold | hold | 5.0 | 7.0 | no | [production_reality] Strong production evidence is shown by "Managed production Kubernetes clusters handling 1.2TB/day of streaming data". \| [technical_integration] The only direct AI integration evidence is limited to "integrated a bas... |
| Hugo Lindqvist | quiet_builder | advance | hold ⚠ | 5.0 | 8.0 | no | [production_reality] The evidence strongly supports production ownership through "Developed REST and gRPC APIs supporting warehouse management system used by 340+ facilities moving 8M pallets annually". \| [technical_integration] The can... |
| Hana Novak | demo_specialist | hold | hold | 4.7 | 4.0 | no | [production_reality] The evidence shows substantial engineering work but does not establish production deployment or operational ownership, with the strongest relevant claim being "Architected multi-agent framework for clinical decision ... |
| Emil Kowalczyk | production_light_ai | hold | hold | 4.7 | 7.0 | no | [production_reality] Strong production evidence is shown by "On-call rotation lead; handled 200+ production incidents annually with average resolution time of 18 minutes". \| [technical_integration] The evidence demonstrates substantial ... |
| Lars Thorvaldsen | production_light_ai | hold | hold | 4.3 | 8.0 | no | [production_reality] The candidate demonstrates substantial production ownership through "Production engineering leader with 7 years building and operating mission-critical logistics and supply-chain systems at scale". \| [technical_inte... |
| Theo Vandenberg | production_light_ai | hold | hold | 4.3 | 9.0 | no | [production_reality] The strongest production evidence is: "Architected and operated payment processing infrastructure handling 2.3M transactions daily across 47 regions; designed circuit breaker patterns reducing cascading failures by 9... |
| Mei-Lin Chow | demo_specialist | hold | hold | 4.0 | 5.0 | no | [production_reality] The evidence describes evaluation results rather than shipped systems, stating that the agent had "99.2% accuracy on evaluation set." \| [technical_integration] The candidate demonstrates hands-on agentic API integra... |
| Signe Aalborg | production_light_ai | hold | hold | 4.0 | 8.0 | no | [production_reality] The evidence strongly demonstrates production ownership through "Built real-time monitoring and alerting infrastructure using Prometheus and Grafana; on-call rotation covers 24/7 operations for three production servi... |
| Wren Sutcliffe | production_light_ai | hold | hold | 4.0 | 8.0 | no | [production_reality] Strong production evidence is shown by "Architected and deployed a multi-region e-commerce platform handling 8,000+ concurrent users during peak sales events; reduced latency from 450ms to 180ms through strategic Clo... |
| Beatrix Hollowell | demo_specialist | hold | hold | 3.7 | 9.0 | no | [production_reality] The evidence describes advanced development but does not establish production deployment or operational use, stating only that the candidate "Developed multi-agent retrieval-augmented generation (RAG) framework for p... |
| Priya Raghunathan | demo_specialist | hold | hold | 3.7 | 8.0 | no | [production_reality] The evidence shows substantial implementation work but no production deployment, operational ownership, or real-user usage, with the strongest context being "Senior ML Engineer, Luminous Media Labs \| San Francisco, ... |
| Saoirse Lachlan | demo_specialist | hold | hold | 3.3 | 8.0 | no | [production_reality] The evidence describes evaluated and optimized systems but does not establish production deployment or operational use, as shown by "achieving 94% retrieval accuracy on a curated eval set of 500 supply chain queries.... |
| Camila Restrepo | production_light_ai | hold | hold | 3.3 | 8.0 | no | [production_reality] The candidate shows strong production ownership through "Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users across three continents," although the evidence does not e... |
| Zainab Iqbal | demo_specialist | hold | hold | 3.0 | 7.0 | yes | The candidate shows meaningful agentic-system depth, having "Architected multi-agent framework for automating bill summary generation and legislative impact analysis using GPT-4 and Claude with dynamic routing logic," but the evidence do... |
| Jonah Steinberg | early_career | hold | hold | 3.0 | 5.0 | yes | The candidate shows meaningful but limited technical integration through "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline," but the evidence does not establish production ownership of AI systems... |
| Grace Okonkwo | wrong_domain | reject | hold ⚠ | 3.0 | 4.0 | yes | The candidate shows production infrastructure ownership—“Managed a multi-region EKS cluster on AWS, handling capacity planning, node autoscaling, and cost optimization across development, staging, and production environments”—but provide... |
| Chiara Bellini | early_career | hold | reject ⚠ | 2.0 | 2.0 | no | [production_reality] The evidence shows pre-production validation rather than ownership of a deployed system: "identified 3 critical data mapping issues before production rollout". \| [technical_integration] The strongest technical evide... |
| Sana Qureshi | quiet_builder | advance | reject ⚠ | 2.0 | 4.0 | yes | The evidence is largely unsupported summary and skills-list language: “Backend engineer with 6 years of experience building production AI systems and media infrastructure,” without describing shipped systems, integrations, operational ow... |
| Malik Johnson | wrong_domain | reject | reject | 2.0 | 2.0 | no | [production_reality] The strongest production-use evidence is "Develop and maintain 15+ recurring SQL reports on claims data, insurance denials, and billing cycles," but there is no evidence of deployed AI or agentic systems. \| [technic... |
| Tariq Mansour | wrong_domain | reject | reject | 2.0 | 1.0 | yes | The candidate has limited production integration evidence—“Maintained ETL pipelines syncing product catalogs from supplier systems into Shopify; handled 50K+ daily SKU updates”—but no evidence of production AI, agentic systems, LLMs, or ... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 1.7 | 2.0 | no | [production_reality] The evidence emphasizes research evaluation rather than shipped systems, stating, "Designed and implemented few-shot learning pipeline for transfer across 12 government agencies' distinct entity taxonomies; evaluated... |
| Imani Robinson | wrong_domain | reject | reject | 1.7 | 1.0 | no | [production_reality] The evidence shows operational payment monitoring but no shipped or supported AI system, as indicated by "Monitor transaction flows across ACH, wire, and card networks; resolve settlement discrepancies". \| [technica... |
| Nadia Haddad | wrong_domain | reject | reject | 1.7 | 3.0 | no | [production_reality] The evidence shows operational ownership of existing infrastructure but no shipped AI system, as the candidate "Manage[s] infrastructure and systems support for 120+ internal users across three regional offices." \| ... |
| Nia Carrington | wrong_domain | reject | reject | 1.7 | 1.0 | no | [production_reality] The evidence shows operational process improvements but no shipped AI systems, as the resume states, "Developed automated reporting dashboard in Excel/SQL that tracks KPIs for 15 distribution centers; cut manual repo... |
| Devon Whitaker | academic_researcher | reject | reject | 1.3 | 3.0 | no | [production_reality] The evidence indicates research rather than deployed systems, stating "Developing machine learning approaches for protein structure prediction validation." \| [technical_integration] The candidate demonstrates advanc... |
| Tomas Herrera | academic_researcher | reject | reject | 1.3 | 3.0 | no | [production_reality] The evidence describes academic experimentation rather than shipped systems, stating, "Conducted extensive experiments on three large-scale e-commerce datasets (Instacart, Amazon Reviews, and internal university data... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 1.3 | 1.0 | no | [production_reality] The evidence describes strategy and research rather than shipped systems, including "AI implementation roadmap development across content production pipelines." \| [technical_integration] The candidate shows exposure... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 1.3 | 1.0 | no | [production_reality] The evidence only identifies the candidate as "Senior Fintech Solutions Architect \| PaymentVault Technologies \| Atlanta, GA \| March 2023 – Present" and does not describe any shipped, monitored, or production-used ... |
| Claire Fontaine | wrong_domain | reject | reject | 1.3 | 2.0 | no | [production_reality] The evidence shows testing work but does not establish ownership or support of deployed production systems: "Quality assurance specialist with 6 years of progressive experience testing digital media platforms, stream... |
| Freya Ashcombe | academic_researcher | reject | reject | 1.0 | 2.0 | no | [production_reality] The evidence describes research rather than shipped systems, including "Investigated attention mechanisms for time-series forecasting in logistics networks; published \"Temporal Attention in Supply Chain Demand Predi... |
| Marcus Feldman | academic_researcher | reject | reject | 1.0 | 2.0 | no | [production_reality] The evidence is research-focused, stating "ML systems researcher with 6 years of experience designing and evaluating compiler optimization frameworks and runtime systems for deep learning workloads," with no demonstr... |
| Amara Nwosu | keyword_stuffer | reject | reject | 1.0 | 2.0 | no | [production_reality] The evidence provides no specific shipped or operational system, and only identifies the candidate as "Senior AI Solutions Architect \| Oregon Department of Administrative Services \| Portland, OR *March 2024 – Prese... |
| Omar Benali | keyword_stuffer | reject | reject | 1.0 | 2.0 | no | [production_reality] The only relevant evidence is the role title “Senior AI Solutions Architect \| BioTech Innovations Labs \| Boston, MA \| January 2024 – Present,” which does not establish that any AI systems shipped or are used in pr... |
| Rosalind Pike | keyword_stuffer | reject | reject | 1.0 | 2.0 | no | [production_reality] The only role evidence is "Senior AI Solutions Architect \| Nexus Logistics Group \| January 2024 – Present," which does not describe a shipped, monitored, supported, or production-used system. \| [technical_integrat... |
| Kwame Asante | academic_researcher | reject | reject | 0.7 | 2.0 | no | [production_reality] The evidence describes research and benchmarks rather than deployed systems, including "Designed and implemented novel deep learning architectures for detecting payment fraud patterns in synthetic transaction dataset... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence only identifies the candidate as "Senior AI Solutions Architect \| Vertex Commerce Solutions \| Atlanta, GA \| March 2023 – Present" and does not describe a shipped, supported, or production-used system.... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence provides no production ownership or shipped AI systems, only the role title "Senior Infrastructure Engineer \| Vertex Systems Inc. \| June 2023 – Present." \| [technical_integration] The evidence shows i... |
