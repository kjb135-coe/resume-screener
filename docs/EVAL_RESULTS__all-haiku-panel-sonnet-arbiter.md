# Evaluation results — `all-haiku-panel-sonnet-arbiter`

60 of 60 resumes scored. Prompt caching: on.

**Model overrides from baseline:**

- `triage`: `claude-haiku-4-5-20251001` → `claude-haiku-4-5-20251001`
- `panel`: `claude-sonnet-5` → `claude-haiku-4-5-20251001`
- `arbiter`: `claude-sonnet-5` → `claude-sonnet-5`

## Headline

| Metric | Value |
|---|---|
| **Macro-F1** | **0.516** |
| Accuracy | 0.533 |
| Escalated to arbiter | 23/60 (38%) |
| Flagged for human review | 59/60 (98%) |
| Cost per resume | $0.0214 |
| Total cost | $1.286 |

## Cost by model

Priced per model that actually spent the tokens. This used to be billed entirely at the first model in the cascade -- Haiku -- which understated real spend several-fold.

| Model | Cost | Share |
|---|---|---|
| `claude-haiku-4-5-20251001` | $0.868 | 68% |
| `claude-sonnet-5` | $0.417 | 32% |
| Latency p50 / p95 (model time) | 18.3s / 29.9s |
| Wall clock, whole batch | 183s |

## Per class

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| advance | 0.706 | 0.600 | 0.649 | 20 |
| hold | 0.455 | 0.250 | 0.323 | 20 |
| reject | 0.469 | 0.750 | 0.577 | 20 |

## Confusion matrix

Rows are ground truth, columns are predictions.

| | pred advance | pred hold | pred reject |
|---|---|---|---|
| **true advance** | 12 | 1 | 7 |
| **true hold** | 5 | 5 | 10 |
| **true reject** | 0 | 5 | 15 |

## Accuracy by archetype

This is the diagnostic that matters most — a headline number can look fine while one archetype fails completely.

| Archetype | Correct | Accuracy |
|---|---|---|
| early_career | 0/6 | 0% |
| demo_specialist | 2/7 | 29% |
| production_light_ai | 3/7 | 43% |
| quiet_builder | 3/7 | 43% |
| production_generalist | 4/7 | 57% |
| wrong_domain | 4/7 | 57% |
| academic_researcher | 5/6 | 83% |
| adjacent_shipper | 5/6 | 83% |
| keyword_stuffer | 6/7 | 86% |

## Every candidate

| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |
|---|---|---|---|---|---|---|---|
| Rafael Duarte | production_generalist | advance | advance | 7.8 | 9.0 | yes | Combining the three dimensions, weighted toward the posting's emphasis on production reality and integration depth. Production reality is very strong and directly evidenced: the candidate's document-processing agent 'now handles 12K+ doc... |
| Sofia Marchetti | adjacent_shipper | advance | advance | 7.0 | 8.0 | yes | The production_reality panelist's output failed to parse, but the underlying evidence cited elsewhere ('Architected and deployed an LLM-powered claims processing agent serving 40,000+ monthly users; integrates Claude API with legacy COBO... |
| Cormac Delaney | production_generalist | advance | advance | 7.0 | 9.0 | yes | The evidence strongly supports production reality and, by extension, technical depth, but is essentially silent on client-facing/cross-functional signal, which pulls the composite score down from what the production evidence alone would ... |
| Delphine Aubert | production_generalist | advance | advance | 7.0 | 6.0 | yes | The panel agreed strongly on production reality (9.0) and technical/integration depth (9.0), both well-supported by direct quotes: "Built and shipped an autonomous content recommendation agent serving Nexus's streaming platform to 2.8M m... |
| Keiko Yamashita | adjacent_shipper | advance | advance | 6.5 | 9.0 | yes | Weighing the three dimensions per the rubric: Production reality is strong and well-supported — the evidence describes live systems with real load and operational rigor, e.g. a dispute resolution agent 'serving 50K+ daily users,' a payme... |
| Lucas Ferreira | production_generalist | advance | advance | 6.5 | 9.0 | yes | Production reality is strong and well-evidenced: 'Shipped clinical decision support agent serving 47 hospitals; processes 12,000+ patient cases monthly in production' and 'live in 12 research centers, 2,100+ matches in first year' descri... |
| Bennett Cross | adjacent_shipper | advance | advance | 6.0 | 9.0 | yes | The panel's dimensions diverge sharply and must be reconciled rather than averaged blindly. Production reality is strongly supported: quotes like '8 years of production systems experience,' '18 months shipping LLM-powered features at sca... |
| Bruno Salvatore | adjacent_shipper | advance | advance | 6.0 | 7.0 | yes | The production_reality panelist's rationale failed to parse, but the underlying evidence supports a moderate-to-strong production signal: 'Built and deployed an LLM-powered product recommendation agent serving 2.8M monthly shoppers' and ... |
| Julius Amankwah | adjacent_shipper | advance | advance | 6.0 | 9.0 | yes | The panel's dimension scores can only be partially reconciled since the technical_integration agent's rationale failed to parse (score 0, confidence 0), so that score is disregarded rather than averaged in. Production reality is strongly... |
| Tobias Reinhardt | quiet_builder | advance | advance | 6.0 | 9.0 | yes | Resolving the panel: production_reality (9.0, conf 0.95) is well-supported by direct quotes describing a live, scaled system — "Architected and deployed production LLM-powered product description generation system processing 180K+ mercha... |
| Elena Vasquez | quiet_builder | advance | advance | 5.5 | 9.0 | yes | Production reality is well-supported and strong: quotes like '2.3M images daily with 94% first-pass accuracy' across '847 field locations,' 'reduced manual review queue from 180k to 12k monthly items,' 'processes 15k documents per day,' ... |
| Mateo Guzman | quiet_builder | advance | advance | 5.5 | 9.0 | yes | The panel evidence is uneven across the three dimensions the rubric asks for. Production reality is strongly supported: quotes like 'processes 50,000+ chemical structures daily,' 'currently serving 150+ daily queries,' '10,000+ daily mes... |
| Andres Villalobos | early_career | hold | advance ⚠ | 4.5 | 7.0 | yes | Aggregating the three dimensions: Production reality is solid at 7.0 (confidence 0.82), anchored in a concrete production metric — 'The extraction workflow now runs daily across roughly 2,000 facilities, handling approximately 50,000 doc... |
| Rohan Malhotra | early_career | hold | advance ⚠ | 4.3 | 5.0 | yes | Production reality is genuinely strong for a subset of work: the caching-layer refactor with measurable impact ('improved page load metrics for roughly 15% of traffic') and a live checkout LLM feature ('integrated a smaller LLM-based pro... |
| Priya Raghunathan | demo_specialist | hold | advance ⚠ | 4.0 | 3.0 | yes | Resolving across dimensions: Production reality is weak (score ~3) — the evidence describes model development and experimentation ('trained several variants of BERT on a 50K-sentence dataset,' 'fine-tuned Mistral 7B') with no mention of ... |
| Zainab Iqbal | demo_specialist | hold | advance ⚠ | 4.0 | 4.0 | yes | Weighing the three panel dimensions against the posting's explicit priorities: (1) Production reality (4.0, conf 0.8) — the evidence shows technical build claims like 'Architected multi-agent framework,' 'Implemented RAG pipeline,' 'Fine... |
| Larissa Petrov | production_light_ai | hold | advance ⚠ | 4.0 | 5.0 | yes | This posting is explicit that it wants a solutions-engineer profile focused on agentic AI in production, and the panel's evidence shows a mismatch on exactly that axis. Production reality is genuinely strong but for the wrong domain: "Bu... |
| Hana Novak | demo_specialist | hold | hold | 3.0 | 4.0 | yes | Weighting the three dimensions per the rubric's emphasis on production reality: production_reality (2.0, conf 0.92) is well-supported — evidence like 'thesis on domain adaptation' and 'published technical blog post' plus evaluation-frame... |
| Wren Sutcliffe | production_light_ai | hold | hold | 3.0 | 8.0 | yes | The panel's evidence is inconsistent with what this posting actually requires. Production_reality correctly identifies strong operational rigor — 'multi-region e-commerce platform handling 8,000+ concurrent users,' '99.95% uptime SLA,' '... |
| Fatima Zahra | production_generalist | advance | hold ⚠ | 2.5 | 8.0 | yes | Two of the three panel dimensions (production_reality and technical_integration) failed to parse and returned no rationale or usable evidence at 0.0 confidence — this is a data gap, not a substantiated finding of zero production or techn... |
| Isaac Mwangi | keyword_stuffer | reject | hold ⚠ | 2.0 | 3.0 | yes | All three dimensions are undermined by the same core problem: the extracted evidence consists only of job titles ('Senior AI Solutions Architect,' 'E-commerce AI Specialist,' 'Analytics Developer') and skill-line phrases ('LLM integratio... |
| Theo Vandenberg | production_light_ai | hold | hold | 1.7 | 1.0 | no | [production_reality] This candidate has strong production systems experience—'maintained 99.97% uptime SLA' and 'handled 2.3M transactions daily' are genuine production ownership signals. However, none of this evidence describes AI, LLM,... |
| Malik Johnson | wrong_domain | reject | hold ⚠ | 1.5 | 3.0 | yes | Averaging the three dimensions with appropriate weight on the missing AI-specific evidence. Production reality (3.0, conf 0.85): evidence shows genuine production ownership but exclusively in data/BI infrastructure — 'Develop and maintai... |
| Kwame Asante | academic_researcher | reject | hold ⚠ | 1.3 | 2.0 | no | [production_reality] This candidate's entire portfolio is research and academic output with no evidence of production systems. The quotes describe 'synthetic transaction datasets,' 'internal benchmark,' published papers, and a dissertati... |
| Emil Kowalczyk | production_light_ai | hold | hold | 1.3 | 2.0 | no | [production_reality] This candidate has strong production infrastructure and reliability engineering credentials — "Manage Kubernetes cluster infrastructure serving 40+ clinical applications with 99.95% uptime SLA" and "On-call rotation ... |
| Claire Fontaine | wrong_domain | reject | hold ⚠ | 1.3 | 2.0 | no | [production_reality] The candidate has 6 years of production experience in QA for streaming platforms—'testing digital media platforms, streaming applications, and content delivery systems'—but every claim describes validation and testin... |
| Tariq Mansour | wrong_domain | reject | hold ⚠ | 1.3 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] The candidate has demonstrable production experience with data pipelines, cloud migration, and Python scripting, but none of the evidence describes building agentic s... |
| Beatrix Hollowell | demo_specialist | hold | hold | 1.0 | 3.0 | yes | Two of three panel dimensions (production_reality, technical_integration) failed to return usable rationale and carry zero confidence, so no evidence-backed claims can be credited there — treated as unsupported/absent rather than scored ... |
| Devon Whitaker | academic_researcher | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] All four evidence items describe research, publication, and academic work with no mention of production systems, clie... |
| Freya Ashcombe | academic_researcher | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] No evidence of explaining technical work to non-technical audiences, client engagement, or cross-functional collabora... |
| Tomas Herrera | academic_researcher | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence describes pure research and academic publication work ("Published findings on attention mechanisms for f... |
| Dele Adeyemi | adjacent_shipper | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate has no explicit evidence of explaining technical work to non-technical audiences, client engagement, or... |
| Mei-Lin Chow | demo_specialist | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows strong technical depth in ML systems (RAG, multi-agent, fine-tuning) with quantified production me... |
| Rina Matsumoto | demo_specialist | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows deep technical depth in LLM infrastructure, evaluation, and agentic systems—all core to the role—b... |
| Saoirse Lachlan | demo_specialist | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate demonstrates strong technical depth in RAG, multi-agent systems, and inference optimization—all relevan... |
| Chiara Bellini | early_career | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate shows zero evidence of explaining technical work to non-technical audiences, cross-functional collabora... |
| Ingrid Solberg | early_career | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence describes strong technical depth in Python, LLMs, and backend systems—"Implemented a retrieval-augmented... |
| Jonah Steinberg | early_career | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] No evidence of explaining technical work to non-technical audiences, client engagement, or cross-functional collabora... |
| Vera Klimenko | early_career | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence contains zero quotes describing explanation of technical work to non-technical audiences, client engagem... |
| Aleksandr Volkov | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows strategic AI work ("AI implementation roadmap development") and tool familiarity, but contains no ... |
| Amara Nwosu | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provides a skills inventory (GPT-4, Claude API, LangChain, Azure OpenAI) but contains no concrete exampl... |
| Dashiell Monroe | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provides no direct examples of explaining technical work to non-technical audiences, cross-functional co... |
| Omar Benali | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provided contains no quotes describing client-facing communication, cross-functional collaboration with ... |
| Rosalind Pike | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provides only a skills inventory and role titles with no concrete examples of explaining technical work ... |
| Yuki Tanaka | keyword_stuffer | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provided contains only technical skill lists and role titles with no description of client-facing work, ... |
| Anjali Deshmukh | production_generalist | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate has zero evidence of client-facing communication, cross-functional collaboration with sales or delivery... |
| Oscar Nakamura | production_generalist | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provided contains zero direct quotes about explaining technical work to non-technical audiences, cross-f... |
| Camila Restrepo | production_light_ai | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate's evidence describes exceptional production infrastructure work at scale—'7 years building reliable, sc... |
| Lars Thorvaldsen | production_light_ai | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate demonstrates strong production systems experience and cross-functional coordination ("coordinated with ... |
| Signe Aalborg | production_light_ai | hold | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows strong production engineering and infrastructure expertise ("Designed and deployed distributed veh... |
| Astrid Bergman | quiet_builder | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate's evidence is entirely technical implementation: 'Architected real-time transaction reconciliation engi... |
| Ewan Brackenridge | quiet_builder | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows strong technical depth in infrastructure and AI integration—'Built an agentic system for automated... |
| Hugo Lindqvist | quiet_builder | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provided is entirely technical and infrastructure-focused with no mention of client engagement, cross-fu... |
| Sana Qureshi | quiet_builder | advance | reject ⚠ | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence provided contains zero quotes demonstrating client-facing communication, cross-functional collaboration ... |
| Grace Okonkwo | wrong_domain | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows zero instances of explaining technical work to non-technical audiences, client engagement, or cros... |
| Imani Robinson | wrong_domain | reject | reject | 0.7 | 2.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The evidence shows internal technical work (SQL, Python, dashboards) but contains zero explicit signal of explaining ... |
| Nadia Haddad | wrong_domain | reject | reject | 0.7 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] The candidate's evidence describes systems administration, helpdesk operations, and infrastructure management—'Manage infrastructure and systems support for 120+ inte... |
| Marcus Feldman | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] The candidate's entire profile is research-focused: "ML systems researcher" designing compiler frameworks, publishing... |
| Ravi Chandrasekar | academic_researcher | reject | reject | 0.3 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] Zero evidence of client engagement, cross-functional collaboration with sales/delivery teams, or translation of techn... |
| Nia Carrington | wrong_domain | reject | reject | 0.3 | 1.0 | no | [production_reality] No rationale returned. \| [technical_integration] No rationale returned. \| [client_communication] This candidate's entire work history is in supply chain operations and logistics, with no evidence of AI/ML/GenAI sys... |
