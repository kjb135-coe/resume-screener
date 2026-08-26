# Evaluation results — `recalibrated`

60 of 60 resumes scored. Prompt caching: on.

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.389** |
| Accuracy | 0.483 |
| Escalated to arbiter | 25/60 (42%) |
| Flagged for human review | 33/60 (55%) |
| Cost per resume | $0.0223 |
| Total cost | $1.338 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-sonnet-5` | $1.091 | 81% |
| `claude-haiku-4-5-20251001` | $0.248 | 19% |
| Latency p50 / p95 (model time) | 16.1s / 22.6s |
| Wall clock, whole batch | 123s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.655 | 0.950 | 0.776 | 20 |
| hold | 0.323 | 0.500 | 0.392 | 20 |
| reject | 0.000 | 0.000 | 0.000 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 19 | 1 | 0 |
| **true hold** | 10 | 10 | 0 |
| **true reject** | 0 | 20 | 0 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| academic_researcher | 0/6 | 0% |
| demo_specialist | 0/7 | 0% |
| keyword_stuffer | 0/7 | 0% |
| wrong_domain | 0/7 | 0% |
| early_career | 3/6 | 50% |
| quiet_builder | 6/7 | 86% |
| adjacent_shipper | 6/6 | 100% |
| production_generalist | 7/7 | 100% |
| production_light_ai | 7/7 | 100% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Cormac Delaney | production_generalist | advance | advance | 9.0 | 6.0 | yes | Strong direct evidence of production deployment and technical/integration depth—"Shipped customer dispute resolution agent to production, handling 150K+ disputes monthly with 89% autonomous resolution rate" and the agentic tool-calling f... |
| Rafael Duarte | production_generalist | advance | advance | 8.3 | 2.0 | no | [production_reality] The claim "Architected and shipped multi-agent workflow system for document processing; now handles 12K+ documents daily across 40+ enterprise clients with 99.2% uptime" directly evidences a shipped, actively-used pr... |
| Fatima Zahra | production_generalist | advance | advance | 8.0 | 2.0 | no | [production_reality] The claim of building "fallback logic and retry handlers to manage 99.2% uptime" for a tool-calling framework integrating 14 external APIs describes an operational, live system with measurable production reliability,... |
| Lucas Ferreira | production_generalist | advance | advance | 8.0 | 6.0 | yes | Strong, explicit production and technical evidence—"Shipped clinical decision support agent serving 47 hospitals; processes 12,000+ patient cases monthly in production" and "Built multi-turn diagnostic orchestration system with tool call... |
| Anjali Deshmukh | production_generalist | advance | advance | 7.0 | 6.0 | yes | Strong, weighted evidence of production ownership and agentic/integration depth ("Designed and deployed autonomous order management agent serving 12,000+ daily transactions across 8 retail partners... implemented monitoring dashboards tr... |
| Delphine Aubert | production_generalist | advance | advance | 7.0 | 6.0 | yes | Strong, well-evidenced production ownership ("On-call for the service; managed three production incidents...") and concrete agentic/tool-orchestration integration ("chains tool calls to a custom fact-checking service and downstream capti... |
| Mateo Guzman | quiet_builder | advance | advance | 7.0 | 5.0 | yes | Strong production and technical evidence—"Architected and deployed an agentic system for automated drug compound screening that processes 50,000+ chemical structures daily" with multi-turn Claude agent workflows and 99.98% uptime—clearly... |
| Bennett Cross | adjacent_shipper | advance | advance | 6.0 | 6.0 | yes | Strong production evidence ("multi-agent document analysis service...processes 15,000+ documents monthly with 99.2% uptime SLA") shows real deployed systems with orchestration and API integration, but memory/tool-use specifics and any cl... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 6.0 | 4.0 | no | [production_reality] "Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers" directly evidences a production-deployed agentic system serving real user load, not a demo or prototype. \| [technical_in... |
| Dele Adeyemi | adjacent_shipper | advance | advance | 6.0 | 4.0 | no | [production_reality] The claim that the exception handler "processes 8,000+ daily alerts, reducing manual triage time by 72% across 12 regional warehouses" describes a live, operating production system with measurable ongoing impact, not... |
| Julius Amankwah | adjacent_shipper | advance | advance | 6.0 | 5.0 | yes | Strong production evidence ("Led the design and launch of an LLM-powered clinical documentation assistant... across Meridian's network") anchors the score, but technical/agentic depth is undetermined due to a parsing failure and client-f... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 6.0 | 5.0 | yes | "Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBOL systems via REST layers" is strong production and integration evidence but lacks explicit mention of ... |
| Vera Klimenko | early_career | hold | advance ⚠ | 6.0 | 0.0 | no | [production_reality] The evidence describes systems with real usage metrics rather than demos—"Built REST endpoints for a public-facing licensing status portal used by 12,000+ monthly users"—but this is government/civic software with no ... |
| Oscar Nakamura | production_generalist | advance | advance | 6.0 | 5.0 | yes | Strong, specific production and technical evidence ("processes approximately 12,000 shipment events daily" and "tool-calling agents that integrate with warehouse management systems, carrier APIs, and customer notification services") supp... |
| Elena Vasquez | quiet_builder | advance | advance | 6.0 | 5.0 | yes | Strong production evidence ("reduced manual review queue from 180k to 12k monthly items") and solid API integration work, but no explicit agentic memory/orchestration detail and no client-facing or cross-functional evidence, so the compo... |
| Ewan Brackenridge | quiet_builder | advance | advance | 6.0 | 5.0 | yes | Strong production evidence for an agentic system—"handled 280+ incidents autonomously in its first six months of production, reducing on-call burden by approximately 18 hours per week"—demonstrates real deployment and tool-use, though or... |
| Tobias Reinhardt | quiet_builder | advance | advance | 6.0 | 5.0 | yes | Strong production evidence ("Architected and deployed production LLM-powered product description generation system processing 180K+ merchandise items monthly") and solid agentic/orchestration work ("Designed agentic workflow using Claude... |
| Rina Matsumoto | demo_specialist | hold | advance ⚠ | 5.7 | 4.0 | no | [production_reality] The strongest production-adjacent evidence is "Owned development of internal LLM serving infrastructure; built multi-model endpoint abstraction supporting OpenAI, Anthropic, and open-weight model inference with autom... |
| Hugo Lindqvist | quiet_builder | advance | advance | 5.7 | 3.0 | no | [production_reality] The evidence describes shipped, operating systems at real scale and reliability rather than demos, e.g. "maintains <300ms latency across 12 regional databases with 99.98% uptime," and the multi-agent Claude/LangChain... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 5.0 | 5.0 | yes | Strong production evidence ("Architected and shipped real-time transaction dispute resolution agent serving 50K+ daily users, integrating GPT-4 with internal risk models via API layer") is offset by thin agentic-architecture detail (no m... |
| Andres Villalobos | early_career | hold | advance ⚠ | 5.0 | 4.0 | yes | Production evidence is strong—"the extraction workflow now runs daily across roughly 2,000 facilities, handling approximately 50,000 documents per day"—but the record is silent on client-facing or cross-functional communication, with wor... |
| Ingrid Solberg | early_career | hold | advance ⚠ | 5.0 | 3.0 | yes | The RAG/LangChain tool ("assist the support team in searching historical disputes and generating templated responses") shows real internal usage but lacks agentic orchestration/memory, explicit production-support signals, or any client-f... |
| Astrid Bergman | quiet_builder | advance | advance | 5.0 | 3.0 | yes | The agentic build with tool use—"Implemented agentic settlement workflow using Claude API with tool use for dispute resolution, enabling autonomous handling of 73% of chargeback cases without manual intervention"—shows real orchestration... |
| Beatrix Hollowell | demo_specialist | hold | advance ⚠ | 4.0 | 4.0 | yes | Evidence shows concrete agentic orchestration work ("Implemented agentic workflow orchestration using LangGraph to handle product comparison, inventory lookup, and pricing logic in sequence") but is framed entirely in benchmarking/eval t... |
| Hana Novak | demo_specialist | hold | advance ⚠ | 4.0 | 3.0 | yes | Evidence is consistently research/eval-oriented ("Built evaluation framework comparing 7 LLM variants... on 8 medical reasoning benchmarks") with a multi-agent architecture ("Architected multi-agent framework for clinical decision suppor... |
| Mei-Lin Chow | demo_specialist | hold | advance ⚠ | 4.0 | 4.0 | yes | Technical depth is solid ("Designed multi-agent system for payment reconciliation using Claude and GPT-4; agent successfully routes queries across three independent financial APIs with 99.2% accuracy on evaluation set"), but this and the... |
| Priya Raghunathan | demo_specialist | hold | advance ⚠ | 4.0 | 3.0 | yes | The evidence shows solid agentic-system design depth ("I architected our agentic reasoning layer using a custom implementation of tool-use patterns with Claude and GPT-4") but reads as research/evaluation work with no deployment, client,... |
| Saoirse Lachlan | demo_specialist | hold | advance ⚠ | 4.0 | 3.0 | yes | The candidate shows genuine agentic orchestration depth ("Engineered an agentic workflow that chains document retrieval, constraint validation, and cost optimization in sequence... reducing latency per inference from 8.2 seconds to 2.1 s... |
| Zainab Iqbal | demo_specialist | hold | advance ⚠ | 4.0 | 3.0 | yes | The strongest evidence, "Architected multi-agent framework for automating bill summary generation and legislative impact analysis using GPT-4 and Claude with dynamic routing logic," shows real orchestration depth but no memory component,... |
| Theo Vandenberg | production_light_ai | hold | hold | 3.5 | 1.0 | no | [production_reality] The evidence demonstrates strong production infrastructure experience (e.g., "Led on-call rotation for critical payment APIs; maintained 99.97% uptime SLA") but contains no mention of AI, LLMs, agentic systems, or Ge... |
| Rohan Malhotra | early_career | hold | hold | 3.3 | 1.0 | no | [production_reality] The clearest AI-related evidence is only exploratory — "I prototyped a solution using prompt engineering and explored a few different API providers" — with no mention of deployment, production use, or ongoing support... |
| Sana Qureshi | quiet_builder | advance | hold ⚠ | 3.3 | 1.0 | no | [production_reality] The only substantive production claim is the unsupported summary line "Backend engineer with 6 years of experience building production AI systems and media infrastructure," with no accompanying sentence describing a ... |
| Jonah Steinberg | early_career | hold | hold | 3.0 | 0.0 | no | [production_reality] No rationale returned. \| [technical_integration] The only AI-related evidence, "Implemented LLM-powered code review suggestions integrated into GitHub Actions CI pipeline," describes an LLM feature integrated into a... |
| Amara Nwosu | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence consists entirely of job titles and unexplained tool/technology lists like "GPT-4, Claude API, LangChain, LlamaIndex" with no sentence describing what was built, deployed, or used in production. \| [tech... |
| Dashiell Monroe | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence consists entirely of skill/tool lists like "Large language models (LLMs), GPT-4, Claude, and prompt engineering frameworks" with no sentence describing a system that was built, deployed, or used in produ... |
| Isaac Mwangi | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence lists only titles and skill/tool names such as "ChatGPT, GPT-4, Claude, LangChain, LlamaIndex, Hugging Face Transformers, TensorFlow, PyTorch" with no sentence describing a system that shipped or was use... |
| Omar Benali | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] All evidence is skills-list phrasing with no sentence describing a shipped, used-in-production system, e.g. "Claude API, GPT-4, LangChain integration points" names tools without describing what was built or deployed.... |
| Rosalind Pike | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence consists only of job titles and skill/tool lists such as "ChatGPT, Claude, Gemini, LLaMA, Mistral, Llama 2, GPT-4, Azure OpenAI, Anthropic API, HuggingFace, TensorFlow, PyTorch, Scikit-learn, XGBoost, La... |
| Yuki Tanaka | keyword_stuffer | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence is limited to skills/tool lists such as "LangChain, LlamaIndex, Hugging Face Transformers, OpenAI API, Anthropic Claude, Mistral AI" with no sentence describing what was built, deployed, or maintained in... |
| Larissa Petrov | production_light_ai | hold | hold | 3.0 | 0.0 | no | [production_reality] All evidence describes production infrastructure/API/reliability engineering (e.g., "Managed production Kubernetes clusters handling 1.2TB/day of streaming data") with no mention whatsoever of AI, LLMs, agentic syste... |
| Lars Thorvaldsen | production_light_ai | hold | hold | 3.0 | 0.0 | no | [production_reality] The evidence shows strong production engineering in logistics/supply-chain systems (e.g. "Led redesign of order-routing microservices handling 180K shipments daily across 12 regional distribution centers") but contai... |
| Wren Sutcliffe | production_light_ai | hold | hold | 3.0 | 0.0 | no | [production_reality] No rationale returned. \| [technical_integration] None of the evidence mentions agentic systems, memory, tools, orchestration, LLMs, or AI/GenAI integration at all—the closest quote, "Maintained and scaled Redis clus... |
| Grace Okonkwo | wrong_domain | reject | hold ⚠ | 3.0 | 2.0 | no | [production_reality] While the candidate shows clear production infrastructure experience (e.g., "Led the design and rollout of a new CI/CD platform serving 80+ engineers across four offices"), none of the evidence describes AI/LLM/agent... |
| Imani Robinson | wrong_domain | reject | hold ⚠ | 3.0 | 2.0 | no | [production_reality] The evidence describes payment operations work ('Monitor transaction flows across ACH, wire, and card networks') with generic scripting and dashboarding ('Automated routine reporting tasks using Python scripts'), but... |
| Tariq Mansour | wrong_domain | reject | hold ⚠ | 3.0 | 0.0 | no | [production_reality] The evidence describes production data/ETL/analytics work like "Maintained ETL pipelines syncing product catalogs from supplier systems into Shopify; handled 50K+ daily SKU updates" but contains no mention of AI, LLM... |
| Marcus Feldman | academic_researcher | reject | hold ⚠ | 2.7 | 1.0 | no | [production_reality] The evidence describes purely research-oriented work such as "benchmarked against PyTorch and JAX on synthetic operator graphs" and "published results on MLPerf and SPEC benchmarks," with no mention of production dep... |
| Chiara Bellini | early_career | hold | hold | 2.7 | 1.0 | no | [production_reality] The only AI-related evidence, "Tested and documented integration between legacy inventory database and new LLM-powered demand forecasting tool," describes a testing/documentation role on a tool, not a shipped product... |
| Signe Aalborg | production_light_ai | hold | hold | 2.7 | 1.0 | no | [production_reality] The evidence shows strong production engineering (e.g., "Designed and deployed distributed vehicle inspection scheduling API serving 14 regional offices; handles 8,000+ daily requests with 99.97% uptime SLA") but non... |
| Camila Restrepo | production_light_ai | hold | hold | 2.5 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] The evidence describes only distributed video streaming, API gateway, and Kubernetes infrastructure work—e.g. "Architect and maintain distributed video streaming infr... |
| Emil Kowalczyk | production_light_ai | hold | hold | 2.5 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] The evidence describes production infrastructure, database, and DevOps work (e.g., "Managed Kubernetes cluster infrastructure serving 40+ clinical applications") with... |
| Kwame Asante | academic_researcher | reject | hold ⚠ | 2.3 | 1.0 | no | [production_reality] The evidence is dominated by research/benchmark framing such as "achieved 94.2% AUC on internal benchmark against 89% baseline" and publications, with no mention of deployment, production use, or ongoing support, ind... |
| Tomas Herrera | academic_researcher | reject | hold ⚠ | 2.3 | 1.0 | no | [production_reality] The evidence is entirely research-oriented ('Research Scientist, Quantix Labs' publishing findings and dissertations in academic venues) with no mention of production deployment, ongoing support, or real user load, e... |
| Aleksandr Volkov | keyword_stuffer | reject | hold ⚠ | 2.3 | 1.0 | no | [production_reality] All evidence describes exploratory, research-oriented activity rather than shipped systems, as in "Large language model exploration for script analysis and development" — exploration, not deployment or production use... |
| Devon Whitaker | academic_researcher | reject | hold ⚠ | 2.0 | 2.0 | no | [production_reality] All evidence describes academic research and benchmark evaluation rather than production systems, e.g. "Evaluated models on CASP14 and CAMEO benchmark datasets, achieving mean absolute error improvements of 12% relat... |
| Freya Ashcombe | academic_researcher | reject | hold ⚠ | 2.0 | 2.0 | no | [production_reality] All evidence is research/publication-oriented, exemplified by "published results in *Journal of Operations Research Quarterly* (2025, 12 citations to date)" rather than any system deployed and used in production. \| ... |
| Ravi Chandrasekar | academic_researcher | reject | hold ⚠ | 2.0 | 2.0 | no | [production_reality] The candidate's entire history is academic/research-oriented, exemplified by "Lead development of named entity recognition models for government policy document analysis; achieved 91.2% F1 on internal NILT-Policy-202... |
| Malik Johnson | wrong_domain | reject | hold ⚠ | 2.0 | 4.0 | yes | The evidence shows only a Senior Data Analyst role with SQL reporting, Tableau dashboards, and a Snowflake migration ("tested data accuracy post-migration and validated 99.2% match rate"), with no mention of AI/LLM/agentic systems, produ... |
| Nadia Haddad | wrong_domain | reject | hold ⚠ | 2.0 | 3.0 | yes | Evidence shows only IT helpdesk/sysadmin work ("Administered Windows Server environments supporting Parks & Recreation and Planning departments") with zero mention of AI, agentic systems, or LLM integration, which actively contradicts th... |
| Nia Carrington | wrong_domain | reject | hold ⚠ | 2.0 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] The evidence shows a supply chain professional with skills like "WMS (Blue Yonder, Manhattan Associates), ERP (SAP), Excel (pivot tables, VLOOKUP, macros), SQL, Table... |
| Claire Fontaine | wrong_domain | reject | hold ⚠ | 1.0 | 3.0 | yes | The evidence shows only QA/testing automation work ("Built automated test framework in Python to validate file upload, transcoding, and proxy generation workflows") with no mention of agentic systems, LLMs, or production AI deployment, d... |
