# Mateo Guzman
Senior Backend Engineer | Healthcare Systems
(210) 445-8923 | mateo.guzman@mailbox.com | Austin, TX

## Core Skills
**Languages & Frameworks:** Python, Go, TypeScript, PostgreSQL, FastAPI, gRPC  
**Infrastructure & Cloud:** AWS (EC2, RDS, Lambda, SQS), Kubernetes, Docker, Terraform, CloudFormation  
**AI/ML & Integration:** LLM orchestration, prompt engineering, vector embeddings, RAG pipelines, semantic search, OpenAI/Anthropic APIs, agent state management  
**Databases & Caching:** PostgreSQL optimization, Redis, DynamoDB, Elasticsearch  
**Observability:** DataDog, CloudWatch, structured logging, distributed tracing

## Professional Experience

**Senior Backend Engineer** | Nexus Clinical Systems | Austin, TX | March 2023 – Present
- Architected and deployed multi-turn agentic system for clinical trial matching, processing 8,000+ patient records monthly through fine-grained eligibility criteria. System uses hierarchical prompting with GPT-4 to reduce false positives from 34% to 7% through iterative refinement loops.
- Built embeddings-based semantic search pipeline ingesting 150,000+ clinical protocol documents into Pinecone, enabling sub-100ms retrieval for trial candidate recommendations across 12 specialties.
- Designed internal LLM gateway abstracting multiple provider APIs (OpenAI, Anthropic, local Llama deployments) with token-level cost tracking and fallback routing, serving 200+ daily inference requests with 99.4% uptime.
- Engineered real-time HL7/FHIR data ingestion pipeline in Go processing 500+ inbound patient records per minute, normalizing disparate EHR formats into canonical schema with full audit trail.
- Optimized PostgreSQL queries for patient cohort analysis, reducing query time from 45s to 1.2s through strategic indexing and materialized views, enabling interactive filtering on 2.3M patient records.

**Backend Engineer II** | Meridian Health Analytics | Denver, CO | August 2021 – February 2023
- Developed prompt chaining system for automated adverse event classification from unstructured clinical notes, reducing manual review workload by 60% across 50,000+ monthly submissions.
- Implemented distributed task queue using Celery and RabbitMQ for asynchronous biomarker analysis, handling 25,000+ jobs daily with <5% failure rate and full idempotency guarantees.
- Migrated monolithic Django application to microservices architecture using gRPC, reducing P99 latency from 8.2s to 1.1s for real-time lab result processing.
- Built data validation and reconciliation layer reconciling claims data across three major insurance provider APIs, identifying and flagging 12,000+ monthly discrepancies with root-cause tracing.

**Junior Backend Engineer** | VistaCore Systems | Denver, CO | June 2020 – July 2021
- Built REST API endpoints for medication interaction checking, consuming external pharmacokinetics database and serving 30,000+ daily requests with sub-50ms latency.
- Wrote data migration scripts consolidating 15 years of historical patient records (420M rows) into unified PostgreSQL schema with zero-downtime cutover.
- Debugged and optimized Redis caching strategy for frequently accessed clinical guidelines, improving hit rate from 52% to 87%.

## Education
**B.S. Computer Science** | University of Colorado Boulder | Boulder, CO | 2020
