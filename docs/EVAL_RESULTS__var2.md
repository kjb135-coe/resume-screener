# Evaluation results — `var2`

52 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.837** |
| Accuracy | 0.846 |
| Escalated to arbiter | 27/52 (52%) |
| Flagged for human review | 29/52 (56%) |
| Cost per resume | $0.0161 |
| Total cost | $0.838 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-sonnet-5` | $0.621 | 74% |
| `claude-haiku-4-5-20251001` | $0.217 | 26% |
| Latency p50 / p95 (model time) | 12.7s / 16.4s |
| Wall clock, whole batch | 93s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.950 | 1.000 | 0.974 | 19 |
| hold | 1.000 | 0.600 | 0.750 | 20 |
| reject | 0.650 | 1.000 | 0.788 | 13 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 19 | 0 | 0 |
| **true hold** | 1 | 12 | 7 |
| **true reject** | 0 | 0 | 13 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 0/7 | 0% |
| early_career | 5/6 | 83% |
| academic_researcher | 6/6 | 100% |
| adjacent_shipper | 6/6 | 100% |
| demo_specialist | 7/7 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| quiet_builder | 6/6 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Delphine Aubert | production_generalist | advance | advance | 7.0 | 9.0 | yes | Strong production ownership ("On-call for the service; managed three production incidents last quarter including a model latency spike") and clear agentic depth ("tool-calling to fetch user viewing history... then orchestrates multi-step... |
| Fatima Zahra | production_generalist | advance | advance | 7.0 | 5.0 | no | [production_reality] The claim that the candidate "Led design and deployment of an intelligent permitting agent for water rights allocation, now processing 12,000+ monthly requests" describes a system that is actually shipped and operati... |
| Cormac Delaney | production_generalist | advance | advance | 6.5 | 9.0 | yes | Strong evidence of production ownership ("Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly with 89% autonomous resolution rate") and deep agentic engineering ("Designed persistent memory layer for ... |
| Rafael Duarte | production_generalist | advance | advance | 6.5 | 8.0 | yes | Strong, well-evidenced production and technical depth—"handles 12K+ documents daily across 40+ enterprise clients with 99.2% uptime" and "orchestration logic for multi-turn interactions... across 5M+ monthly API calls"—satisfy the postin... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 6.0 | 7.0 | yes | Strong production and integration evidence—"Architected and deployed an LLM-powered shipment exception handler that processes 8,000+ daily alerts" with a concrete agentic/RAG pipeline on AWS—anchors high production and technical scores, ... |
| Anjali Deshmukh | production_generalist | advance | advance | 6.0 | 9.0 | yes | Strong production and technical evidence—"On-call for production incidents... reduced customer escalations by 31%" and an agentic system with tool calling and memory serving "12,000+ daily transactions"—clearly satisfy the posting's core... |
| Oscar Nakamura | production_generalist | advance | advance | 6.0 | 8.0 | yes | Strong production and integration evidence ("I led the incident response to reroute affected shipments through a fallback orchestration pattern" and "tool-calling agents that integrate with warehouse management systems, carrier APIs, and... |
| Lucas Ferreira | production_generalist | advance | advance | 5.5 | 9.0 | yes | Strong production evidence — "On-call for production incidents; established monitoring dashboards tracking agent hallucination rates and API latency; resolved critical integration failure with hospital pharmacy system in 4 hours" — suppo... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 5.0 | 6.0 | yes | Strong production and agentic-engineering evidence — "Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers" and "Engineered the agentic layer using Claude API with function calling" — clearly satis... |
| Vera Klimenko | early_career | hold | advance ⚠ | 5.0 | 2.0 | no | [production_reality] The evidence describes a live, running system with real usage and iterative improvement rather than a demo: "Contributed to a Python-based document processing system that ingested 500+ permit applications monthly; in... |
| Ewan Brackenridge | quiet_builder | advance | advance | 5.0 | 8.0 | yes | Strong production and agentic-orchestration evidence—"Built an agentic system for automated incident remediation that uses LLM reasoning to execute pre-approved infrastructure operations—the system successfully handled 280+ incidents aut... |
| Mateo Guzman | quiet_builder | advance | advance | 5.0 | 8.0 | yes | Strong production and technical/integration evidence ("Architected and deployed an agentic system for automated drug compound screening that processes 50,000+ chemical structures daily") is undercut by a complete absence of client-facing... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 4.7 | 7.0 | yes | Strong production evidence ("Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users") is undercut by no mention of memory/tools/orchestration for agentic design and no client-facing or cross-functio... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 4.5 | 8.0 | yes | Strong production evidence—"Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer" with 99.99% uptime—demonstrates real deployment, but ... |
| Sana Qureshi | quiet_builder | advance | advance | 4.5 | 8.0 | yes | Strong production evidence ("<50ms p99 latency" at 50K req/s) and partial agentic-system depth ("agentic framework ... leveraging Claude API and custom reward models") are undercut by a complete absence of client-facing or cross-function... |
| Bennett Cross | adjacent_shipper | advance | advance | 4.0 | 6.0 | yes | The evidence shows one genuine shipped agentic integration — "Architected and deployed a multi-agent document analysis service for compliance workflows, integrating Claude API with internal document retrieval system" — but it lacks detai... |
| Julius Amankwah | adjacent_shipper | advance | advance | 4.0 | 7.0 | yes | The system "Led the design and launch of an LLM-powered clinical documentation assistant that automates medical note generation for over 800 physicians" shows genuine production deployment, but it is described only at a skills-line level... |
| Astrid Bergman | quiet_builder | advance | advance | 4.0 | 7.0 | yes | "Implemented agentic settlement workflow using Claude API with tool use for dispute resolution, enabling autonomous handling of 73% of chargeback cases" shows solid production-grade agentic/tool-use work but no evidence of memory/orchest... |
| Elena Vasquez | quiet_builder | advance | advance | 4.0 | 7.0 | yes | Strong production-scale evidence ("processing 2.3M images daily with 94% first-pass accuracy") and real API integration ("integrated with legacy SOAP APIs through custom adapter layer") are undercut by lack of detail on agentic memory/to... |
| Hugo Lindqvist | quiet_builder | advance | advance | 4.0 | 6.0 | yes | Solid agentic/LLM engineering evidence ("Architected multi-agent supply chain orchestration system using Claude API and LangChain, processing real-time shipment data across 47 distribution centers") supports moderate technical depth, but... |
| Andres Villalobos | early_career | hold | hold | 3.0 | 5.0 | yes | Production evidence of a real, scaled pipeline ("runs daily across roughly 2,000 facilities... 50,000 documents per day") is offset by the fact that the work is an ETL/extraction and validation pipeline, not an agentic system with memory... |
| Ingrid Solberg | early_career | hold | hold | 3.0 | 4.0 | yes | The RAG/LangChain and GPT-4 classification work shows real GenAI integration but lacks memory/orchestration or confirmed production ownership ("Implemented a retrieval-augmented generation (RAG) system using LangChain to assist the suppo... |
| Mei-Lin Chow | demo_specialist | hold | hold | 2.5 | 5.0 | yes | The candidate shows genuine multi-agent/API orchestration skill ("agent successfully routes queries across three independent financial APIs with 99.2% accuracy on evaluation set") but every claim is framed around benchmarks and evaluatio... |
| Rohan Malhotra | early_career | hold | hold | 2.3 | 1.0 | no | [production_reality] The clearest production-adjacent AI work is explicitly non-agentic and latency-constrained rather than an owned, iterated system, as shown by "this feature runs inference through an external API and returns suggestio... |
| Zainab Iqbal | demo_specialist | hold | hold | 2.3 | 5.0 | yes | Evidence shows research-grade agentic work with metrics ("achieved 89% retrieval precision on held-out evaluation set") and a multi-agent orchestration build ("Architected multi-agent framework for automating bill summary generation and ... |
| Beatrix Hollowell | demo_specialist | hold | hold | 2.0 | 6.0 | yes | Evidence shows real orchestration/agentic depth ("Implemented agentic workflow orchestration using LangGraph to handle product comparison, inventory lookup, and pricing logic in sequence") but nothing indicates production deployment, use... |
| Priya Raghunathan | demo_specialist | hold | hold | 2.0 | 5.0 | yes | Evidence describes a research/evaluation-style agentic system ("comprehensive evaluation framework for the agents using 2,400 manually annotated scenes") with genuine tool-use/RAG architecture but no indication of production deployment, ... |
| Rina Matsumoto | demo_specialist | hold | hold | 2.0 | 4.0 | yes | All evidence — including the strongest technical claim, "Implemented function-calling orchestration layer enabling tool composition across 40+ API integrations; benchmarked at 78% tool selection accuracy on held-out test set" — describes... |
| Saoirse Lachlan | demo_specialist | hold | hold | 2.0 | 4.0 | yes | Evidence is consistently research/eval-bench oriented rather than production or client-facing—"Published technical deep-dive on arXiv examining retrieval quality trade-offs...340 GitHub stars" and a multi-agent RAG system validated only ... |
| Jonah Steinberg | early_career | hold | hold | 2.0 | 4.0 | yes | The only relevant evidence, "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline," shows narrow LLM-tooling integration with no agentic memory/orchestration, no production-ownership language, and ze... |
| Hana Novak | demo_specialist | hold | hold | 1.7 | 2.0 | no | [production_reality] Every quote — e.g., "Architected multi-agent framework for clinical decision support using LangGraph and Claude API" — describes architecture, benchmarking, or thesis work with no mention of deployment, users, or pro... |
| Chiara Bellini | early_career | hold | hold | 1.0 | 0.0 | no | [production_reality] The strongest AI-related evidence is "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool" and "Participated in pilot program testing AI-driven package scan... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every piece of evidence is a bare title or skills/tool list—e.g., "GPT-4, Claude API, LangChain, LlamaIndex"—with no sentence describing what was built, deployed, or supported in production. \| [technical_integration... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every quote is a bare skills/tool listing such as "Retrieval-augmented generation (RAG) architecture patterns" with no sentence describing what was built, deployed, or supported in production, so there is no evidence... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence consists of job titles, skill lists, and technology names such as "Vector database implementations, RAG system components, Transformer model documentation" with no sentence describing what was built, dep... |
| Omar Benali | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every quote is a bare skills/title fragment such as "Claude API, GPT-4, LangChain integration points" with no sentence describing what was built, deployed, or used in production, so there is no evidence of shipped sy... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] The evidence consists entirely of role titles and unadorned tool/skill lists such as "LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API, Anthropic Claude" with no sentence describing what was built, deploy... |
| Larissa Petrov | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] All evidence describes general infrastructure/backend production work with no mention of AI, LLMs, agentic systems, or GenAI at all, e.g. "Built and maintained the infrastructure backbone for a distributed API gatewa... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] All evidence describes production infrastructure engineering (APIs, databases, Kubernetes, monitoring) with zero mention of AI/ML/LLM/agentic systems, e.g. "Designed horizontal scaling strategy for containerized work... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence describes research/academic output rather than production deployment, exemplified by "evaluated on benchmark dataset of 15,000+ real-world inventory trajectories achieving 23% MAPE improvement... |
| Kwame Asante | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence describes research and benchmarking work — e.g. "Designed and implemented novel deep learning architectures for detecting payment fraud patterns in synthetic transaction datasets; achieved 94.... |
| Marcus Feldman | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes academic research and benchmarking, exemplified by "published results on MLPerf and SPEC benchmarks showing 2.3× improvement over baselines," with no mention of production deployment, users, or... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every piece of evidence describes academic/research output rather than production systems—e.g. "Published \"Multilingual NER in Low-Resource Government Domains\" in Proceedings of ACL 2025 (34 citations to date)"—wit... |
| Tomas Herrera | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] All evidence describes research/publication outputs like "Published primary dissertation work as 'Sequential Embeddings for E-Commerce Product Graphs' in ACM Transactions on Information Systems (July 2023, 14 citatio... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes only exploratory and research-stage work — "Large language model exploration for script analysis and development" and "Preliminary testing of text-to-image and video generation platforms" — wit... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] Every quote describes production video streaming/infrastructure engineering (e.g., "Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users across three continents") with ... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence describes strong production infrastructure work ("Manage Kubernetes cluster infrastructure serving 40+ clinical applications with 99.95% uptime SLA") but contains no mention of AI, LLMs, agentic systems,... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes production infrastructure/DevOps work (e.g., "Architected and deployed a multi-region e-commerce platform handling 8,000+ concurrent users during peak sales events") with zero mention of AI, LL... |
| Devon Whitaker | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] Every quote describes research/academic work — e.g., "Thesis defended with distinction on deep learning for protein dynamics prediction" — with no mention of deployment, users, or production ownership, which the post... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence consists entirely of a job title, a skills list, and education—e.g. "AI & Machine Learning: ChatGPT, Claude, Gemini, LLaMA, Mistral, Llama 2, GPT-4, Azure OpenAI, Anthropic API, HuggingFace, TensorFlow, ... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence shows a strong production engineering background in logistics/supply-chain systems (e.g., "Senior Production Engineer, Meridian Logistics \| Portland, OR \| March 2023 – Present") but contains no mention... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] The evidence describes production payment infrastructure and reliability engineering with no mention of AI, LLMs, agents, or GenAI whatsoever, e.g. "Architected and operated payment processing infrastructure handling... |
