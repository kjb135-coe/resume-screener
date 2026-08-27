# Evaluation results — `var1`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.814** |
| Accuracy | 0.817 |
| Escalated to arbiter | 28/60 (47%) |
| Flagged for human review | 31/60 (52%) |
| Cost per resume | $0.0159 |
| Total cost | $0.956 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-sonnet-5` | $0.715 | 75% |
| `claude-haiku-4-5-20251001` | $0.241 | 25% |
| Latency p50 / p95 (model time) | 12.2s / 15.5s |
| Wall clock, whole batch | 99s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.950 | 0.950 | 0.950 | 20 |
| hold | 0.765 | 0.650 | 0.703 | 20 |
| reject | 0.739 | 0.850 | 0.791 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 19 | 1 | 0 |
| **true hold** | 1 | 13 | 6 |
| **true reject** | 0 | 3 | 17 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 1/7 | 14% |
| keyword_stuffer | 5/7 | 71% |
| academic_researcher | 5/6 | 83% |
| early_career | 5/6 | 83% |
| quiet_builder | 6/7 | 86% |
| adjacent_shipper | 6/6 | 100% |
| demo_specialist | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Rafael Duarte | production_generalist | advance | advance | 7.3 | 5.0 | no | [production_reality] The evidence explicitly describes a system that shipped and operates at scale in production, not a demo: "Architected and shipped multi-agent workflow system for document processing; now handles 12K+ documents daily ... |
| Cormac Delaney | production_generalist | advance | advance | 7.2 | 9.0 | yes | Strong, unambiguous production and technical depth—"Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly with 89% autonomous resolution rate" alongside detailed agentic memory/orchestration work—anchor... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 7.0 | 2.0 | no | [production_reality] The strongest production signal is "Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers," which explicitly describes a live, shipped system handling real user load rather than... |
| Delphine Aubert | production_generalist | advance | advance | 7.0 | 6.0 | yes | Strong shipped agentic system evidence ("tool-calling to fetch user viewing history... orchestrates multi-step reasoning") combined with genuine production ownership ("On-call for the service; managed three production incidents last quar... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.5 | 8.0 | yes | Strong production ownership ("On-call for production incidents... reduced customer escalations by 31%") and solid agentic/tool-integration evidence ("autonomous order management agent serving 12,000+ daily transactions... uses tool calli... |
| Oscar Nakamura | production_generalist | advance | advance | 6.5 | 8.0 | yes | Strong evidence of production-grade agentic integration—"tool-calling agents that integrate with warehouse management systems, carrier APIs, and customer notification services" and incident response work—demonstrates real production owne... |
| Hugo Lindqvist | quiet_builder | advance | advance | 6.5 | 8.0 | yes | Strong evidence of production-grade agentic systems — "Architected multi-agent supply chain orchestration system using Claude API and LangChain, processing real-time shipment data across 47 distribution centers" and APIs "used by 340+ fa... |
| Fatima Zahra | production_generalist | advance | advance | 6.0 | 8.0 | yes | Strong production and integration evidence—"Led design and deployment of an intelligent permitting agent for water rights allocation, now processing 12,000+ monthly requests" and the multi-agent orchestration architecture—confirms real s... |
| Lucas Ferreira | production_generalist | advance | advance | 6.0 | 9.0 | yes | Strong, well-evidenced production deployment ("Shipped clinical decision support agent serving 47 hospitals; processes 12,000+ patient cases monthly in production") and genuine agentic orchestration work ("multi-turn diagnostic orchestra... |
| Elena Vasquez | quiet_builder | advance | advance | 5.5 | 8.0 | yes | Strong production evidence ("reduced manual review queue from 180k to 12k monthly items") and solid integration work via a custom state machine support high marks on those two dimensions, but the complete absence of any client-facing or ... |
| Mateo Guzman | quiet_builder | advance | advance | 5.3 | 7.0 | yes | Strong production and technical evidence ("Architected and deployed an agentic system for automated drug compound screening that processes 50,000+ chemical structures daily... using Claude API with function calling") confirms real produc... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 5.0 | 7.0 | yes | Strong production evidence — "Architected and deployed an LLM-powered shipment exception handler that processes 8,000+ daily alerts, reducing manual triage time by 72% across 12 regional warehouses" — confirms real production LLM/RAG dep... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 5.0 | 7.0 | yes | Strong production evidence ("Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBOL systems via REST layers") and solid integration depth are undercut by a n... |
| Sana Qureshi | quiet_builder | advance | advance | 5.0 | 8.0 | yes | Strong production and technical evidence—"Built and maintained core recommendation engine serving 12M+ daily active users... using multi-agent orchestration system" and "Developed Python-based agentic framework for video transcription qu... |
| Bennett Cross | adjacent_shipper | advance | advance | 4.5 | 8.0 | yes | Strong production evidence ("system processes 15,000+ documents monthly with 99.2% uptime SLA") is undercut by the lack of explicit memory/tool/orchestration detail in the agentic system and a complete absence of client-facing or cross-f... |
| Ewan Brackenridge | quiet_builder | advance | advance | 4.3 | 7.0 | yes | Strong production/agentic evidence—"Built an agentic system for automated incident remediation that uses LLM reasoning to execute pre-approved infrastructure operations" and "monitors production deployments in real-time, using Claude's A... |
| Julius Amankwah | adjacent_shipper | advance | advance | 4.0 | 7.0 | yes | Strong production evidence — "Led the design and launch of an LLM-powered clinical documentation assistant that automates medical note generation for over 800 physicians across Meridian's network" — confirms real deployment at scale, but... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 4.0 | 8.0 | yes | The single strong signal—"Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer"—proves production deployment and API integration but la... |
| Ingrid Solberg | early_career | hold | advance ⚠ | 4.0 | 2.0 | no | [production_reality] The strongest production signal is "Built and maintained Python microservices that validate incoming transaction metadata against compliance rules, catching 94% of malformed payment data before downstream processing,... |
| Astrid Bergman | quiet_builder | advance | advance | 4.0 | 7.0 | yes | Strong production-scale evidence ("classified 156M historical transactions with 96.8% merchant category accuracy") is undercut by a single unelaborated agentic line ("Implemented agentic settlement workflow using Claude API with tool use... |
| Vera Klimenko | early_career | hold | hold | 3.5 | 4.0 | yes | Production deployment is real ("500+ permit applications monthly" and accuracy improved 78%→86%) but technical depth is thin—evidence shows only LLM classification/prompt work ("Implemented prompt templates and evaluation scripts for LLM... |
| Beatrix Hollowell | demo_specialist | hold | hold | 3.0 | 4.0 | yes | Solid agentic orchestration and RAG engineering work ('Implemented agentic workflow orchestration using LangGraph to handle product comparison, inventory lookup, and pricing logic in sequence') is undercut by the total absence of product... |
| Priya Raghunathan | demo_specialist | hold | hold | 3.0 | 5.0 | yes | The evidence shows real agentic/tool-use build work ("I architected our agentic reasoning layer using a custom implementation of tool-use patterns with Claude and GPT-4") but no confirmation of production deployment, memory/orchestration... |
| Rina Matsumoto | demo_specialist | hold | hold | 3.0 | 5.0 | yes | Evidence centers on internal infrastructure ownership—"Owned development of internal LLM serving infrastructure; built multi-model endpoint abstraction supporting OpenAI, Anthropic, and open-weight model inference with automatic rate-lim... |
| Andres Villalobos | early_career | hold | hold | 3.0 | 6.0 | yes | The system runs at real production scale ("roughly 2,000 facilities, handling approximately 50,000 documents per day"), but the actual AI work described is narrow LLM-output integration into a validation layer, not agentic systems with m... |
| Hana Novak | demo_specialist | hold | hold | 2.0 | 3.0 | yes | The candidate's strongest claim, "Architected multi-agent framework for clinical decision support using LangGraph and Claude API," demonstrates orchestration tooling knowledge but never states deployment, production use, memory systems, ... |
| Mei-Lin Chow | demo_specialist | hold | hold | 2.0 | 4.0 | yes | Evidence like "Designed multi-agent system for payment reconciliation using Claude and GPT-4" and "Architected RAG pipeline for transaction classification" shows genuine agentic/GenAI build work but with no indication of production deplo... |
| Saoirse Lachlan | demo_specialist | hold | hold | 2.0 | 4.0 | yes | Evidence like "Designed and implemented a multi-agent retrieval-augmented generation system to optimize supply chain document analysis and route planning" shows genuine technical/agentic work but with no mention of production deployment,... |
| Zainab Iqbal | demo_specialist | hold | hold | 2.0 | 5.0 | yes | Evidence shows only technical build work ("Architected multi-agent framework for automating bill summary generation and legislative impact analysis using GPT-4 and Claude with dynamic routing logic") with no mention of production deploym... |
| Rohan Malhotra | early_career | hold | hold | 2.0 | 2.0 | no | [production_reality] The only LLM-specific work described is explicitly a short-lived exploration rather than a shipped system — "I took on a short project to evaluate whether we could use an LLM to help automatically categorize incoming... |
| Tobias Reinhardt | quiet_builder | advance | hold ⚠ | 2.0 | 4.0 | yes | The agentic workflow claim—"Designed agentic workflow using Claude API and LangChain that autonomously categorizes products, extracts attributes, and generates SEO-optimized descriptions"—shows relevant tool integration but never confirm... |
| Jonah Steinberg | early_career | hold | hold | 1.5 | 4.0 | yes | The lone AI-specific evidence, "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline, reducing time-to-merge by ~15% for flagged PRs," shows a shipped feature but no agentic systems (memory/tools/orc... |
| Larissa Petrov | production_light_ai | hold | hold | 1.3 | 1.0 | no | [production_reality] The only AI-related evidence is a minor add-on—"integrated a basic LLM API call to categorize error messages automatically"—which describes a small production feature, not the agentic, memory/tools/orchestration syst... |
| Freya Ashcombe | academic_researcher | reject | hold ⚠ | 1.0 | 2.0 | no | [production_reality] Every quote describes benchmark evaluation, publication, or academic research rather than shipped production systems, exemplified by "evaluated on benchmark dataset of 15,000+ real-world inventory trajectories achiev... |
| Chiara Bellini | early_career | hold | hold | 1.0 | 0.0 | no | [production_reality] The strongest claim is only pre-production testing—"identified 3 critical data mapping issues before production rollout"—which describes validation work, not ownership of a deployed, in-use system. \| [technical_inte... |
| Aleksandr Volkov | keyword_stuffer | reject | hold ⚠ | 1.0 | 0.0 | no | [production_reality] Every quote describes research, exploration, and assessment rather than shipped systems, exemplified by "Generative AI platform research for animation and visual effects applications. Tool comparison matrices for ima... |
| Rosalind Pike | keyword_stuffer | reject | hold ⚠ | 1.0 | 0.0 | no | [production_reality] The only substantive work description is "Machine learning model assessment for distribution networks. Data pipeline architecture exploration. Predictive analytics for shipment routing." — language that reads as expl... |
| Kwame Asante | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] Every quote describes research, benchmarking, or synthetic/internal work rather than production deployment, exemplified by "achieved 94.2% AUC on internal benchmark against 89% baseline" on "synthetic transaction dat... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence is entirely a list of skills and titles with no descriptive sentences of what was built or shipped, e.g. "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" names tools witho... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of unelaborated skills/tool lists, such as "ChatGPT, GPT-4, Claude, LangChain, LlamaIndex, Hugging Face Transformers, TensorFlow, PyTorch," with no sentence describing what was built, s... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] Every quote describes video-streaming/backend infrastructure engineering (e.g., "Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users across three continents") with zer... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] The evidence describes strong, genuine production infrastructure/SRE work ("Manage Kubernetes cluster infrastructure serving 40+ clinical applications with 99.95% uptime SLA") but contains zero mention of AI, LLMs, a... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] Every piece of evidence describes strong production infrastructure work (e.g., "Designed and deployed distributed vehicle inspection scheduling API serving 14 regional offices; handles 8,000+ daily requests with 99.9... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] All evidence describes production infrastructure engineering (e.g., "Built Kubernetes infrastructure for a containerized order processing system that transitioned from on-premises to AWS") with zero mention of AI, LL... |
| Devon Whitaker | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes academic research artifacts, e.g. "Contributed to three peer-reviewed publications on uncertainty quantification in structural biology, with cumulative citation count of 47 across venues includ... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] The entire evidence set is academic/research in nature—e.g., "Published \"Multilingual NER in Low-Resource Government Domains\" in Proceedings of ACL 2025"—with no mention of a deployed, production-used system, on-ca... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a bare skills-line or job title with no sentence describing what was built, deployed, or used in production, e.g. "AI and machine learning strategy development" and "GPT-4, Claude API, LangChain, Llama... |
| Omar Benali | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a bare skills/tool list such as "Claude API, GPT-4, LangChain integration points" with no sentence describing what was built, deployed, or supported in production. \| [technical_integration] Every piec... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] Every quote describes payment-processing infrastructure, database, and observability work (e.g., "Architected and operated payment processing infrastructure handling 2.3M transactions daily across 47 regions") with z... |
| Malik Johnson | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes SQL reporting, healthcare data analytics, and Snowflake migration work (e.g., "Develop and maintain 15+ recurring SQL reports on claims data, insurance denials, and billing cycles") with no men... |
| Nadia Haddad | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence consists entirely of IT/helpdesk and sysadmin work such as "Administered Windows Server environments supporting Parks & Recreation and Planning departments," with no mention of any AI, LLM, or agentic sy... |
| Tariq Mansour | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes production data/e-commerce engineering work ("Maintained ETL pipelines syncing product catalogs from supplier systems into Shopify; handled 50K+ daily SKU updates") but contains no mention of A... |
| Marcus Feldman | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] Every quote describes benchmarked, published research artifacts rather than shipped systems, as in "published results on MLPerf and SPEC benchmarks showing 2.3× improvement over baselines," with no mention of product... |
| Tomas Herrera | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence points to research and publication work with no production deployment, exemplified by "Published findings on attention mechanisms for fashion recommendation in the ICML 2025 Workshop on Machine Learning ... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] The only AI-related evidence is a bare skills list, "AI & Machine Learning: LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API, Anthropic Claude, Mistral AI, Cohere, Ollama, CrewAI, AutoGen, LiteLLM, Ray, W... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence contains no mention of AI/LLM/agentic systems whatsoever—only generic production infrastructure roles like "Senior Production Engineer, Meridian Logistics \| Portland, OR \| March 2023 – Present" with no... |
| Claire Fontaine | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] This is a QA specialist's resume with no mention of AI, LLMs, agents, or any production AI system whatsoever — the closest evidence is "Built automated test framework in Python to validate file upload, transcoding, a... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence describes production infrastructure/DevOps engineering (CI/CD, Kubernetes, Terraform, monitoring) with no mention of LLMs, agentic systems, or AI/ML work at all, as shown by "Led the design and rollout o... |
| Imani Robinson | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] None of the evidence describes any AI/agentic system, let alone one in production—only payment operations work such as "Monitor transaction flows across ACH, wire, and card networks; resolve settlement discrepancies"... |
| Nia Carrington | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The only AI-related evidence is "Assisted in pilot project evaluating machine learning for demand forecasting," which describes a pilot/evaluation role, not a production system built, deployed, or supported by the ca... |
