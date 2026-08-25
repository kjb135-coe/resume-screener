# Mateo Guzman
Senior Software Engineer, Biotech Infrastructure
(210) 814-2937 | mateo.guzman@emailpro.com | Austin, TX

## Core Skills
**Languages & Frameworks:** Python, Go, TypeScript, PostgreSQL, Redis  
**LLM & Agents:** LangChain, Claude API, Anthropic SDK, prompt engineering, retrieval-augmented generation  
**Infrastructure:** Kubernetes, Docker, AWS (EC2, Lambda, RDS, S3), Terraform, CI/CD pipelines  
**Data & Integration:** Apache Airflow, REST APIs, gRPC, ETL pipelines, data validation workflows  
**Healthcare Tech:** HIPAA compliance patterns, HL7 message handling, clinical data standards

## Professional Experience

**Senior Backend Engineer** | Meridian Therapeutics Platform | Austin, TX | Jan 2023 – Present

Architected and deployed an agentic system for automated drug compound screening that processes 50,000+ chemical structures daily. Built multi-turn agent workflows using Claude API with function calling to orchestrate property predictions, toxicity assessments, and binding affinity simulations. System integrates with 12 external computational chemistry APIs via a custom abstraction layer and routes requests through a load-balanced pool of 40 GPU-accelerated workers.

Engineered the core data pipeline infrastructure handling genomic sequencing outputs and clinical trial metadata. Implemented a Kubernetes-native ETL framework using Airflow that processes 2TB+ monthly of patient genotype and phenotype data. Built RAG system with vector embeddings to enable researchers to query historical trial results—currently serving 150+ daily queries from internal research teams with 94% relevance ratings.

Designed and maintained the centralized API gateway for all biomarker validation services. Implemented request routing, rate limiting, and versioning to support 8 downstream microservices across a 30-person engineering org. Wrote Go services handling HL7 v2 parsing and normalization of incoming clinical data from partner hospitals, processing 10,000+ daily messages with 99.98% uptime.

**Backend Engineer** | ClinicalDM Systems | Houston, TX | Jun 2021 – Dec 2022

Developed core extraction and transformation layer for electronic health record aggregation platform used by 45 clinical research sites. Built Python-based ETL workers that ingested structured and unstructured clinical notes, applied entity extraction heuristics, and populated analytics database serving 300+ concurrent researcher queries. Optimized query performance through strategic indexing, reducing median latency from 12s to 2.3s.

Implemented prompt-based document classification pipeline using GPT-3.5 to automatically categorize clinical documents into treatment types. Fine-tuned classification accuracy to 91% through iterative prompt refinement and built feedback loops for edge cases. System processed 15,000+ monthly documents with minimal manual review overhead.

Contributed to infrastructure migration from single-tenant monolith to multi-tenant Kubernetes architecture. Provisioned containerized deployment pipeline with Terraform, implemented namespace-level isolation for HIPAA compliance, and established monitoring dashboards for 12 production services.

**Software Engineer** | Vertex Data Labs | Austin, TX | Aug 2019 – May 2021

Built data validation and quality assurance framework for bioinformatics workflows. Wrote distributed validators in Python that ran post-processing checks on 500+ genomic datasets weekly. Developed internal libraries for common ETL patterns and API integrations to reduce engineering toil.

## Education
B.S. Computer Science | University of Texas at Austin | 2019
