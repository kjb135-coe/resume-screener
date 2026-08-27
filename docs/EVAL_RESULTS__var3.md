# Evaluation results — `var3`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.844** |
| Accuracy | 0.850 |
| Escalated to arbiter | 27/60 (45%) |
| Flagged for human review | 32/60 (53%) |
| Cost per resume | $0.0158 |
| Total cost | $0.946 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-sonnet-5` | $0.702 | 74% |
| `claude-haiku-4-5-20251001` | $0.244 | 26% |
| Latency p50 / p95 (model time) | 12.0s / 16.7s |
| Wall clock, whole batch | 101s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.900 | 0.900 | 0.900 | 20 |
| hold | 0.867 | 0.650 | 0.743 | 20 |
| reject | 0.800 | 1.000 | 0.889 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 18 | 2 | 0 |
| **true hold** | 2 | 13 | 5 |
| **true reject** | 0 | 0 | 20 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 2/7 | 29% |
| early_career | 4/6 | 67% |
| quiet_builder | 5/7 | 71% |
| academic_researcher | 6/6 | 100% |
| adjacent_shipper | 6/6 | 100% |
| demo_specialist | 7/7 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Delphine Aubert | production_generalist | advance | advance | 7.4 | 6.0 | yes | Strong production ownership ("On-call for the service; managed three production incidents last quarter") and deep agentic integration work ("Developed a live caption generation agent...that integrates with their existing playout infrastr... |
| Rafael Duarte | production_generalist | advance | advance | 7.3 | 5.0 | no | [production_reality] The evidence explicitly describes shipped, live, at-scale production systems with operational ownership, exemplified by "Owned on-call rotation for production infrastructure; reduced mean incident response time from ... |
| Fatima Zahra | production_generalist | advance | advance | 6.7 | 4.0 | no | [production_reality] The claim of "6 years building and operating production agent systems in government and public sector contexts" is directly backed by concrete deployment evidence, notably "Deployed agentic system on AWS using ECS wi... |
| Oscar Nakamura | production_generalist | advance | advance | 6.6 | 7.0 | yes | Strong evidence of production ownership ("comprehensive monitoring dashboards tracking agent decision latency, tool invocation error rates, and end-to-end resolution times") and deep agentic/tool-integration work ("multi-agent orchestrat... |
| Cormac Delaney | production_generalist | advance | advance | 6.5 | 9.0 | yes | Strong, concrete production and technical evidence—"Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly" and "Designed persistent memory layer for agent context... integrated with PostgreSQL and Redis... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.0 | 8.0 | yes | Strong, credible production evidence — "On-call for production incidents; implemented monitoring dashboards tracking agent success rate (now 94%), latency, and tool invocation patterns" — indicates a real, iterated agentic system in prod... |
| Lucas Ferreira | production_generalist | advance | advance | 6.0 | 9.0 | yes | Strong production and technical evidence—"Built multi-turn diagnostic orchestration system with tool calling to EMR APIs... agent chains reduce clinician review time by 38%" and "On-call for production incidents... resolved critical inte... |
| Mateo Guzman | quiet_builder | advance | advance | 6.0 | 8.0 | yes | Strong production and technical depth are well-supported by "Architected and deployed an agentic system for automated drug compound screening that processes 50,000+ chemical structures daily," but the complete absence of client-facing or... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 5.5 | 7.0 | yes | Strong production and integration evidence — "Architected and deployed an LLM-powered shipment exception handler that processes 8,000+ daily alerts, reducing manual triage time by 72% across 12 regional warehouses" — shows real deployed ... |
| Sana Qureshi | quiet_builder | advance | advance | 5.5 | 8.0 | yes | Strong production and technical evidence—"Built and maintained core recommendation engine serving 12M+ daily active users... using multi-agent orchestration system" and "Architected PostgreSQL and Redis infrastructure supporting stateful... |
| Bennett Cross | adjacent_shipper | advance | advance | 5.0 | 7.0 | yes | Strong production and integration evidence — "Architected and deployed a multi-agent document analysis service for compliance workflows, integrating Claude API with internal document retrieval system" — is undercut by near-total absence ... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 5.0 | 8.0 | yes | Production reality is strong ("Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBOL systems via REST layers and handles asynchronous job workflows"), but t... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 4.5 | 6.0 | yes | Strong production and technical evidence ("Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers" with agentic function-calling logic) is offset by a near-total absence of client-facing or cross-fun... |
| Vera Klimenko | early_career | hold | advance ⚠ | 4.5 | 3.0 | yes | Evidence shows a real production integration ("integrated OpenAI API to auto-classify permit types, reducing manual categorization by 40%") but lacks agentic/orchestration depth, on-call/monitoring detail, or direct client-facing communi... |
| Elena Vasquez | quiet_builder | advance | advance | 4.5 | 7.0 | yes | Strong production/integration evidence—"Integrated Claude API with custom state machine for document verification workflows; reduced manual review queue from 180k to 12k monthly items"—shows a real deployed system with orchestration, tho... |
| Hugo Lindqvist | quiet_builder | advance | advance | 4.5 | 6.0 | yes | Production and technical evidence like "Architected multi-agent supply chain orchestration system using Claude API and LangChain, processing real-time shipment data across 47 distribution centers" shows solid agentic/orchestration work a... |
| Julius Amankwah | adjacent_shipper | advance | advance | 4.0 | 7.0 | yes | Production deployment is credible ("Led the design and launch of an LLM-powered clinical documentation assistant that automates medical note generation for over 800 physicians") but the evidence never describes agentic architecture (memo... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 4.0 | 8.0 | yes | Strong production evidence ("Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer") is undercut by the posting's specific requirement f... |
| Ingrid Solberg | early_career | hold | advance ⚠ | 4.0 | 4.0 | yes | Production use is credible ("generates compliance reports consumed by six Fortune 500 financial institutions monthly"), but the RAG work described—"Implemented a retrieval-augmented generation (RAG) system using LangChain to assist the s... |
| Astrid Bergman | quiet_builder | advance | advance | 4.0 | 6.0 | yes | Production infrastructure work is real ("Architected real-time transaction reconciliation engine processing 2.3M+ daily settlement records") but the sole agentic evidence, "Implemented agentic settlement workflow using Claude API with to... |
| Ewan Brackenridge | quiet_builder | advance | hold ⚠ | 3.0 | 6.0 | yes | The only agentic/LLM evidence is a single monitoring tool—"Implemented a custom agent framework in Python that monitors production deployments in real-time, using Claude's API to analyze logs and metrics"—which shows some production LLM ... |
| Tobias Reinhardt | quiet_builder | advance | hold ⚠ | 3.0 | 6.0 | yes | The candidate shows real backend production scale ("handling 45K requests/second peak load") but the sole agentic evidence—"Designed agentic workflow using Claude API and LangChain that autonomously categorizes products..."—lacks any men... |
| Mei-Lin Chow | demo_specialist | hold | hold | 2.7 | 4.0 | yes | Evidence consistently frames work as benchmark/evaluation-set achievements ("99.2% accuracy on evaluation set") rather than deployed production systems with real users, monitoring, or client engagement, which this posting explicitly requ... |
| Priya Raghunathan | demo_specialist | hold | hold | 2.3 | 5.0 | yes | Evidence shows genuine agentic/technical work ("I architected our agentic reasoning layer using a custom implementation of tool-use patterns with Claude and GPT-4") but nothing indicating production deployment, on-call ownership, or clie... |
| Saoirse Lachlan | demo_specialist | hold | hold | 2.3 | 5.0 | yes | Evidence is limited to eval-stage/technical work like "achieving 94% retrieval accuracy on a curated eval set of 500 supply chain queries," with a multi-agent RAG system described but no deployment, production ownership, or client-facing... |
| Beatrix Hollowell | demo_specialist | hold | hold | 2.0 | 5.0 | yes | Evidence shows only benchmark-style technical work—"Implemented agentic workflow orchestration using LangGraph...measured latency at 340ms per request" and a blog post with GitHub stars—demonstrating some agentic/orchestration skill but ... |
| Hana Novak | demo_specialist | hold | hold | 2.0 | 3.0 | yes | The evidence is entirely research/academic (thesis on "Domain Adaptation of Transformer Models for Biomedical Text Classification," benchmarking "7 LLM variants... on 8 medical reasoning benchmarks") with a genuine agentic architecture h... |
| Rina Matsumoto | demo_specialist | hold | hold | 2.0 | 5.0 | yes | Evidence is consistently research/benchmark-oriented ("validated improvements through offline benchmarks showing 14-point increase," "benchmarked at 78% tool selection accuracy") with no mention of production deployment, live users, or c... |
| Zainab Iqbal | demo_specialist | hold | hold | 2.0 | 4.0 | yes | Evidence like "Architected multi-agent framework for automating bill summary generation and legislative impact analysis using GPT-4 and Claude with dynamic routing logic" shows genuine agentic/orchestration design but reads as benchmarke... |
| Rohan Malhotra | early_career | hold | hold | 2.0 | 2.0 | no | [production_reality] The evidence shows production backend work (caching, logging) but the only LLM-related work explicitly failed to reach production — "I prototyped a solution using prompt engineering and explored a few different API p... |
| Andres Villalobos | early_career | hold | hold | 1.5 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] The only LLM-related evidence — "I've contributed to the addition of a new LLM-based feature that extracts structured clinical findings from unstructured radiology re... |
| Larissa Petrov | production_light_ai | hold | hold | 1.3 | 1.0 | no | [production_reality] The evidence is overwhelmingly production infrastructure/SRE work with only one thin, non-agentic AI touchpoint—"Collaborated with the data team to add simple text classification to API logging—integrated a basic LLM... |
| Chiara Bellini | early_career | hold | hold | 1.0 | 0.0 | no | [production_reality] The strongest evidence, "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool; identified 3 critical data mapping issues before production rollout," describe... |
| Jonah Steinberg | early_career | hold | hold | 1.0 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] The only agentic/GenAI evidence is "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline," which shows a single LLM integration ... |
| Signe Aalborg | production_light_ai | hold | hold | 1.0 | 2.0 | no | [production_reality] The evidence shows strong production infrastructure experience (e.g., "Built real-time monitoring and alerting infrastructure using Prometheus and Grafana; on-call rotation covers 24/7 operations for three production... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] Every piece of evidence describes research, benchmarks, and publications rather than shipped production systems, exemplified by "Lead development of named entity recognition models for government policy document anal... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence is entirely research and exploratory language rather than shipped systems, exemplified by "Strategic assessment of emerging language models for creative workflows" and "Generative AI platform research fo... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of job titles, tool lists, and a degree (e.g., "LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API, Anthropic Claude") with no sentence describing what was built, deployed, or... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] All evidence describes production infrastructure/DevOps work (e.g., "Architected and deployed a multi-region e-commerce platform handling 8,000+ concurrent users") with zero mention of AI, LLMs, agents, or GenAI syst... |
| Malik Johnson | wrong_domain | reject | reject | 0.7 | 2.0 | no | [production_reality] This evidence describes a healthcare data analyst role with SQL reporting, Tableau dashboards, and a Snowflake migration—none of which mentions AI/ML, LLMs, agentic systems, or any AI solution shipped to production, ... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote points to academic/research output — e.g. "evaluated on benchmark dataset of 15,000+ real-world inventory trajectories achieving 23% MAPE improvement over baseline LSTM" — with no mention of deployment, u... |
| Kwame Asante | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence points to research/academic work rather than production deployment, exemplified by "synthetic transaction datasets; achieved 94.2% AUC on internal benchmark" and dissertation/publication crede... |
| Tomas Herrera | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence points to research and academic work, exemplified by "Published findings on attention mechanisms for fashion recommendation in the ICML 2025 Workshop on Machine Learning for E-Commerce (currently at 8 ci... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a bare skills-line fragment such as "GPT-4, Claude API, LangChain, LlamaIndex" or "Cloud platforms: AWS, Azure, Google Cloud" with no sentence describing a system that was built, shipped, or used in pr... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a bare skills/title listing with no sentence describing what was built, deployed, or shipped, e.g. "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" names tools without a... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence contains only job titles and unsupported skill labels like "LLM integration frameworks" and "Vector database implementations" with no sentence describing what was built, deployed, or used in production. ... |
| Omar Benali | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence is a bare skills/technology list with no sentence describing what was built, deployed, or used in production—e.g. "RAG systems, vector databases, semantic search" names tools without any claim... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The only substantive work description, "Machine learning model assessment for distribution networks. Data pipeline architecture exploration. Predictive analytics for shipment routing," uses exploratory/assessment lan... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] Every quote describes production infrastructure/DevOps/database work (e.g., "Manage Kubernetes cluster infrastructure serving 40+ clinical applications with 99.95% uptime SLA") with zero mention of AI/LLM/agentic sys... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes production logistics/supply-chain infrastructure work (e.g., "Led redesign of order-routing microservices handling 180K shipments daily across 12 regional distribution centers") with no mention... |
| Claire Fontaine | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] This candidate's evidence is entirely QA/testing-focused with no mention of AI, LLMs, agentic systems, or production AI deployment—e.g. "Led QA efforts for Prism's flagship streaming platform serving 2.4M monthly act... |
| Imani Robinson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes payment operations work (dashboards, reconciliation, PCI-DSS audit prep) with no mention of AI/LLM/agentic systems at all, let alone production deployment of one—e.g. "Built internal dashboard ... |
| Nadia Haddad | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] None of the evidence mentions AI, agentic systems, LLMs, or any production AI deployment—only IT operations work such as "Manage infrastructure and systems support for 120+ internal users across three regional office... |
| Tariq Mansour | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] None of the evidence describes AI/LLM/agentic systems in production—only e-commerce data engineering work like "Maintained ETL pipelines syncing product catalogs from supplier systems into Shopify; handled 50K+ daily... |
| Devon Whitaker | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] Every quote describes research/academic work ("Contributed to three peer-reviewed publications on uncertainty quantification in structural biology" and a "Thesis defended with distinction") with no mention of any sys... |
| Marcus Feldman | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes research and benchmarking work, exemplified by "published results on MLPerf and SPEC benchmarks showing 2.3× improvement over baselines," with no mention of deployment, production use, on-call,... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] No rationale returned. \| [technical_integration] None of the evidence mentions agentic systems, LLMs, memory/tools/orchestration, or AI integration at all — the closest quote is merely a skills list, "Kubernetes, AW... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence describes production payment-processing infrastructure work with no mention of AI, LLMs, agentic systems, or GenAI whatsoever, e.g. "Architected and operated payment processing infrastructure handling 2.... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes CI/CD, Kubernetes, and cloud infrastructure work (e.g., "Managed a multi-region EKS cluster on AWS, handling capacity planning, node autoscaling, and cost optimization") with zero mention of AI... |
| Nia Carrington | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The candidate's entire background is in supply chain/logistics with no AI/ML/agentic system evidence whatsoever, as shown by "Results-driven supply chain professional with 6 years of experience optimizing logistics o... |
