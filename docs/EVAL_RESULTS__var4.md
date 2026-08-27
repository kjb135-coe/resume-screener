# Evaluation results — `var4`

59 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.861** |
| Accuracy | 0.864 |
| Escalated to arbiter | 29/59 (49%) |
| Flagged for human review | 31/59 (53%) |
| Cost per resume | $0.0162 |
| Total cost | $0.957 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-sonnet-5` | $0.711 | 74% |
| `claude-haiku-4-5-20251001` | $0.246 | 26% |
| Latency p50 / p95 (model time) | 13.1s / 17.3s |
| Wall clock, whole batch | 104s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 1.000 | 0.950 | 0.974 | 20 |
| hold | 0.929 | 0.650 | 0.765 | 20 |
| reject | 0.731 | 1.000 | 0.844 | 19 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 19 | 1 | 0 |
| **true hold** | 0 | 13 | 7 |
| **true reject** | 0 | 0 | 19 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| production_light_ai | 0/7 | 0% |
| adjacent_shipper | 5/6 | 83% |
| academic_researcher | 5/5 | 100% |
| demo_specialist | 7/7 | 100% |
| early_career | 6/6 | 100% |
| keyword_stuffer | 7/7 | 100% |
| production_generalist | 7/7 | 100% |
| quiet_builder | 7/7 | 100% |
| wrong_domain | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Fatima Zahra | production_generalist | advance | advance | 7.3 | 4.0 | no | [production_reality] The candidate describes a system that was actually "Deployed agentic system on AWS using ECS with auto-scaling; managed container orchestration and CI/CD pipeline improvements," which indicates genuine production dep... |
| Rafael Duarte | production_generalist | advance | advance | 7.3 | 5.0 | no | [production_reality] The evidence explicitly describes shipped, in-use systems with operational ownership rather than demos, as in "Architected and shipped multi-agent workflow system for document processing; now handles 12K+ documents d... |
| Oscar Nakamura | production_generalist | advance | advance | 7.0 | 8.0 | yes | Strong production and technical evidence—"Built and deployed a multi-agent orchestration system... reduced manual intervention on exception cases by 68%"—confirms real production ownership and agentic depth, but the near-total absence of... |
| Cormac Delaney | production_generalist | advance | advance | 6.5 | 9.0 | yes | Strong, quantified production evidence ("Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly with 89% autonomous resolution rate") and deep agentic/integration detail ("Designed persistent memory laye... |
| Lucas Ferreira | production_generalist | advance | advance | 6.3 | 9.0 | yes | Strong production and technical evidence—"Shipped clinical decision support agent serving 47 hospitals; processes 12,000+ patient cases monthly in production" and tool/memory orchestration work—firmly support high marks on those two dime... |
| Delphine Aubert | production_generalist | advance | advance | 6.0 | 8.0 | yes | Strong production and technical evidence—"Deployed to production supporting 40+ live events monthly with 99.2% uptime" and on-call incident ownership—are undercut by a near-total absence of client-facing or cross-functional signal, since... |
| Mateo Guzman | quiet_builder | advance | advance | 6.0 | 8.0 | yes | Strong production evidence ("processes 50,000+ chemical structures daily" and "150+ daily queries... with 94% relevance ratings") and solid agentic/tool-use work ("Built multi-turn agent workflows using Claude API with function calling")... |
| Tobias Reinhardt | quiet_builder | advance | advance | 6.0 | 8.0 | yes | Strong production and technical evidence—"Architected and deployed production LLM-powered product description generation system processing 180K+ merchandise items monthly" using "agentic workflow using Claude API and LangChain"—demonstra... |
| Anjali Deshmukh | production_generalist | advance | advance | 5.7 | 8.0 | yes | Strong production and technical evidence—"On-call for production incidents; implemented monitoring dashboards tracking agent success rate (now 94%)" and a deployed agent "serving 12,000+ daily transactions across 8 retail partners"—is un... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 5.5 | 6.0 | yes | Strong production evidence ("serving 2.8M monthly shoppers") and solid tool-use/orchestration work ("Engineered the agentic layer using Claude API with function calling") are undercut by the near-total absence of client-facing or cross-f... |
| Elena Vasquez | quiet_builder | advance | advance | 5.5 | 1.0 | no | [production_reality] The claim to have "Architected autonomous agent pipeline for license plate recognition across 847 field locations, processing 2.3M images daily with 94% first-pass accuracy" describes a concrete, scaled, running syst... |
| Sana Qureshi | quiet_builder | advance | advance | 5.3 | 8.0 | yes | Strong production and technical depth evidence — "Built and maintained core recommendation engine serving 12M+ daily active users" and "40-node Kubernetes cluster" — is undercut by a complete absence of client-facing or cross-functional ... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 5.0 | 8.0 | yes | Strong production evidence ("Architected and deployed an LLM-powered shipment exception handler that processes 8,000+ daily alerts, reducing manual triage time by 72%") and solid but partial agentic/technical depth via RAG tool integrati... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 4.5 | 7.0 | yes | Strong production evidence ("Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBOL systems via REST layers") is undercut by the absence of any mention of ag... |
| Astrid Bergman | quiet_builder | advance | advance | 4.5 | 7.0 | yes | Strong evidence of a production agentic system — "enabling autonomous handling of 73% of chargeback cases without manual intervention" via Claude API tool use — supports solid production and integration scores, but the complete absence o... |
| Ewan Brackenridge | quiet_builder | advance | advance | 4.5 | 6.0 | yes | Solid evidence of production agentic work — "Implemented a custom agent framework in Python that monitors production deployments in real-time, using Claude's API to analyze logs and metrics" — but lacks memory components, business-system... |
| Bennett Cross | adjacent_shipper | advance | advance | 4.2 | 7.0 | yes | The evidence shows a genuine production agentic system ("multi-agent document analysis service... processes 15,000+ documents monthly with 99.2% uptime SLA") but lacks detail on memory/orchestration mechanics and contains zero evidence o... |
| Julius Amankwah | adjacent_shipper | advance | advance | 4.0 | 7.0 | yes | Strong production deployment evidence ("used in production... over 800 physicians") is undercut by the absence of agentic orchestration/memory/tools ("no mention of agentic orchestration, tool use, or memory components") and no client-fa... |
| Hugo Lindqvist | quiet_builder | advance | advance | 4.0 | 6.0 | yes | Solid production and integration evidence—"Developed REST and gRPC APIs supporting warehouse management system used by 340+ facilities moving 8M pallets annually" and "Architected multi-agent supply chain orchestration system using Claud... |
| Ingrid Solberg | early_career | hold | hold | 3.5 | 4.0 | yes | The RAG system deployed for the support team ("improved support response time by 22%") shows genuine production use but is not the agentic system with memory/tools/orchestration the posting requires, and the only cross-team evidence is i... |
| Keiko Yamashita | adjacent_shipper | advance | hold ⚠ | 3.3 | 7.0 | yes | The one strong signal — "Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer" — shows genuine production deployment but no detail on a... |
| Hana Novak | demo_specialist | hold | hold | 3.0 | 5.0 | yes | The strongest evidence, "Architected multi-agent framework for clinical decision support using LangGraph and Claude API," shows genuine agentic/orchestration engineering but lacks any indication of production deployment (no monitoring, o... |
| Rina Matsumoto | demo_specialist | hold | hold | 3.0 | 5.0 | yes | The evidence base is dominated by benchmark/eval framing—"benchmarked at 78% tool selection accuracy on held-out test set of 200 complex multi-step tasks"—which shows real orchestration/integration skill but explicitly reads as demo-stag... |
| Vera Klimenko | early_career | hold | hold | 3.0 | 4.0 | yes | The one concrete production system—"integrated OpenAI API to auto-classify permit types, reducing manual categorization by 40%"—shows real LLM-in-production usage but is a single API-call classifier, not an agentic system with memory, to... |
| Mei-Lin Chow | demo_specialist | hold | hold | 2.5 | 5.0 | yes | Evidence like "Designed multi-agent system for payment reconciliation using Claude and GPT-4; agent successfully routes queries across three independent financial APIs with 99.2% accuracy on evaluation set" shows real orchestration/integ... |
| Andres Villalobos | early_career | hold | hold | 2.2 | 3.0 | yes | The candidate shows real production ownership of a data pipeline but only peripheral LLM involvement — "I've contributed to the addition of a new LLM-based feature... working closely with the ML team to integrate their model predictions ... |
| Beatrix Hollowell | demo_specialist | hold | hold | 2.0 | 3.0 | yes | The strongest technical evidence — "Implemented agentic workflow orchestration using LangGraph... measured latency at 340ms per request on benchmarking hardware" — explicitly describes benchmarking, not a production system used by real u... |
| Saoirse Lachlan | demo_specialist | hold | hold | 2.0 | 6.0 | yes | Evidence shows technical depth in agentic orchestration ("Engineered an agentic workflow that chains document retrieval, constraint validation, and cost optimization in sequence") but nothing indicates production deployment, real users, ... |
| Jonah Steinberg | early_career | hold | hold | 2.0 | 4.0 | yes | The lone AI-related evidence, "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline," shows a real integration but not an agentic system with memory/tools/orchestration nor confirmed production owner... |
| Rohan Malhotra | early_career | hold | hold | 2.0 | 4.0 | yes | The only GenAI evidence is a shallow API-call integration—"I integrated a smaller LLM-based product bundling feature that suggests complementary items to customers during checkout; this feature runs inference through an external API"—sho... |
| Priya Raghunathan | demo_specialist | hold | hold | 1.5 | 5.0 | yes | Production_reality parse failed and no evidence was cited anywhere suggesting shipped/production ownership, while the only concrete technical claim—"I architected our agentic reasoning layer using a custom implementation of tool-use patt... |
| Chiara Bellini | early_career | hold | hold | 1.3 | 1.0 | no | [production_reality] The strongest evidence, "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool; identified 3 critical data mapping issues before production rollout," describe... |
| Zainab Iqbal | demo_specialist | hold | hold | 1.3 | 4.0 | yes | Production_reality parse failed (treated as 0/0 confidence, effectively no signal either way) and client_communication found zero evidence of client-facing or cross-functional work; only technical_integration found partial credit for "Ar... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] Every quote describes research/academic output rather than shipped production systems, epitomized by "published results in Journal of Operations Research Quarterly (2025, 12 citations to date)" with no mention of dep... |
| Kwame Asante | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] Every piece of evidence points to research/academic work rather than production deployment, exemplified by "Designed and implemented novel deep learning architectures for detecting payment fraud patterns in synthetic... |
| Tomas Herrera | academic_researcher | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence describes research and academic publication work — e.g. "Published primary dissertation work as 'Sequential Embeddings for E-Commerce Product Graphs' in ACM Transactions on Information Systems" — with no... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence describes assessment, research, and exploration activity rather than shipped systems, exemplified by "Strategic assessment of emerging language models for creative workflows" and "Large language model ex... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] All evidence is a list of skills/tools with no sentence describing what was built or deployed, e.g. "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" names technologies without describi... |
| Isaac Mwangi | keyword_stuffer | reject | reject | 0.7 | 1.0 | no | [production_reality] Every piece of evidence is a bare skills-list fragment such as "LLM integration frameworks" or "RAG system components" with no sentence describing what was built, deployed, or used in production. \| [technical_integr... |
| Emil Kowalczyk | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] Despite strong production infrastructure evidence like "On-call rotation lead; handled 200+ production incidents annually with average resolution time of 18 minutes," there is no mention of AI/LLM/agentic systems, me... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.7 | 1.0 | no | [production_reality] The evidence describes extensive production ownership of logistics/supply-chain systems (e.g., "reduced latency p99 from 850ms to 280ms and improved system availability to 99.97%") but contains zero mention of AI, LL... |
| Malik Johnson | wrong_domain | reject | reject | 0.7 | 2.0 | no | [production_reality] This candidate's entire evidence base is healthcare data analytics work with no mention of AI, LLMs, agentic systems, or GenAI whatsoever — e.g. "Partner with clinical and operations teams to design dashboards tracki... |
| Nia Carrington | wrong_domain | reject | reject | 0.7 | 2.0 | no | [production_reality] The only AI-related evidence is peripheral and explicitly not production ownership: "Assisted in pilot project evaluating machine learning for demand forecasting; gathered requirements and provided feedback on system... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote describes academic research and publication output (e.g., "Published \"Multilingual NER in Low-Resource Government Domains\" in Proceedings of ACL 2025") with no mention of shipped systems, production dep... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a title/tool list with no sentence describing what was built, deployed, or used in production—e.g. "GPT-4, Claude API, LangChain, LlamaIndex" names tools without any account of a shipped system. \| [te... |
| Omar Benali | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] Every quote is a bare skills/keyword list with no sentence describing what was built, shipped, or used in production, e.g. "RAG systems, vector databases, semantic search" names concepts without any claim of deployme... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence contains only job titles, skill lists, and education (e.g., "AI & Machine Learning: LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API...") with no sentence describing any system that was built... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] The evidence shows strong production infrastructure and streaming engineering experience (e.g., "Architect and maintain distributed video streaming infrastructure handling 40M+ monthly active users across three conti... |
| Larissa Petrov | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes infrastructure/SRE/DevOps work (API gateways, Kubernetes clusters, load balancers, on-call runbooks) with zero mention of LLMs, agentic systems, AI/GenAI, or Digital Employee offerings, so desp... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes solid production backend/infrastructure work (e.g., "Designed and deployed distributed vehicle inspection scheduling API serving 14 regional offices; handles 8,000+ daily requests with 99.97% u... |
| Theo Vandenberg | production_light_ai | hold | reject ⚠ | 0.3 | 1.0 | no | [production_reality] All evidence describes production payment/infrastructure engineering (e.g., "Led on-call rotation for critical payment APIs; maintained 99.97% uptime SLA through systematic reliability improvements and incident respo... |
| Nadia Haddad | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] The evidence describes IT helpdesk/sysadmin work with no mention of AI, LLMs, or agentic systems at all — e.g. "Deployed patches and security updates on 180 desktop and laptop systems" — so there is nothing to evalua... |
| Devon Whitaker | academic_researcher | reject | reject | 0.0 | 0.0 | no | [production_reality] All evidence is academic/research work with no production deployment—e.g., "Contributed to three peer-reviewed publications on uncertainty quantification in structural biology, with cumulative citation count of 47 ac... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence consists entirely of job titles, employment dates, and skills lists like "AI & Machine Learning: ChatGPT, Claude, Gemini, LLaMA, Mistral, Llama 2, GPT-4, Azure OpenAI, Anthropic API, HuggingFace, TensorF... |
| Wren Sutcliffe | production_light_ai | hold | reject ⚠ | 0.0 | 0.0 | no | [production_reality] All evidence describes production infrastructure/DevOps engineering (e.g., "Architected and deployed a multi-region e-commerce platform handling 8,000+ concurrent users") with zero mention of AI, LLMs, agents, or Gen... |
| Claire Fontaine | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes a QA specialist's testing/automation work with no mention of AI, LLMs, agentic systems, or any production deployment of AI solutions—e.g., "Developed and maintained automated test suites using ... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence describes production infrastructure/DevOps work (CI/CD, Kubernetes, Terraform) but contains zero mentions of AI/ML/LLM/agentic systems shipped to production, e.g. "Led the design and rollout of a new CI/... |
| Imani Robinson | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] The evidence shows only payment operations and BI/automation work ('Built internal dashboard using SQL and Tableau for real-time reconciliation reporting' and 'Automated routine reporting tasks using Python scripts')... |
| Tariq Mansour | wrong_domain | reject | reject | 0.0 | 0.0 | no | [production_reality] None of the evidence describes any AI/LLM/agentic system at all, let alone one in production — e.g. "Maintained ETL pipelines syncing product catalogs from supplier systems into Shopify; handled 50K+ daily SKU update... |
