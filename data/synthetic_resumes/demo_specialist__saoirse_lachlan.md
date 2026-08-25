# Saoirse Lachlan
**ML Engineer, Supply Chain & Logistics**

Portland, OR | (503) 447-2891 | saoirse.lachlan@mailbox.io | github.com/slachlan

---

## Experience

**Senior ML Engineer** | Nexus Logistics Systems | Portland, OR | March 2024 – Present

Designed and implemented a multi-agent retrieval-augmented generation system to optimize supply chain document analysis and route planning. Built a framework combining Claude 3.5 Sonnet with custom agents that parse warehouse manifests, shipping regulations, and inventory datasets to generate dynamic logistics recommendations. Implemented semantic search over vectorized regulatory documents using pgvector and Anthropic's embeddings API, achieving 94% retrieval accuracy on a curated eval set of 500 supply chain queries. Developed a specialized fine-tuning pipeline for logistics terminology, improving F1 scores on downstream entity recognition tasks from 0.71 to 0.89 using domain-specific training data. Engineered an agentic workflow that chains document retrieval, constraint validation, and cost optimization in sequence, reducing latency per inference from 8.2 seconds to 2.1 seconds through prompt caching and batched API calls. Published technical deep-dive on arXiv examining retrieval quality trade-offs in supply chain LLM applications, which garnered 340 GitHub stars on the accompanying implementation repository.

**ML Engineer** | Helix Freight Analytics | Seattle, WA | June 2023 – February 2024

Developed a fine-tuned language model for carrier performance prediction and shipment anomaly detection in freight networks. Adapted open-source models using logistics-specific datasets containing 50,000 carrier interactions and delivery event sequences, achieving 87% accuracy on held-out test benchmarks for predicting delivery delays. Implemented a multi-modal evaluation framework combining latency profiling, token efficiency metrics, and domain-specific accuracy measures to compare model variants. Built retrieval pipelines to ground predictions in historical carrier data and regulatory constraints, incorporating recent logistics policy changes through continuous vector store updates. Created end-to-end inference infrastructure using Ray for distributed model serving and eval harness automation, processing 2M+ simulated supply chain scenarios to validate model robustness. Presented findings at MLOps.community on practical challenges of fine-tuning for regulated logistics domains.

**Data Engineer** | Clearpath Logistics | Vancouver, BC | August 2022 – May 2023

Constructed data processing and feature engineering pipelines for predictive models supporting warehouse operations and transportation planning. Built ETL workflows in Python and dbt to aggregate shipment records, GPS telemetry, and warehouse sensors into feature stores optimized for model training. Developed evaluation datasets and benchmark suites for testing ML models against logistics KPIs including delivery window accuracy and resource utilization forecasts. Collaborated with operations teams to identify high-value prediction targets and ensure feature definitions aligned with domain requirements. Automated recurring data quality checks and implemented monitoring dashboards for upstream data freshness.

## Technical Skills

**ML Frameworks & LLM Tools:** LangChain, LlamaIndex, Anthropic API, fine-tuning pipelines, RAG systems, multi-agent orchestration, prompt engineering, evaluation frameworks

**Data & Infrastructure:** PostgreSQL with pgvector, Python, SQL, dbt, Airflow, Ray, Docker

**Specializations:** Supply chain optimization, logistics NLP, domain-specific model adaptation, retrieval evaluation, inference optimization
