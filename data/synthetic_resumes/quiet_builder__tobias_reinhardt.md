# Tobias Reinhardt
Senior Backend Engineer | E-Commerce Infrastructure
(717) 483-2941 | tobias.reinhardt@email.com | Pittsburgh, PA

## Core Skills
**Languages & Frameworks:** Python, Go, Java, TypeScript | Django, FastAPI, gRPC | PostgreSQL, Redis, DynamoDB, Elasticsearch
**ML & Agents:** LLM integration, prompt engineering, RAG systems, agentic workflows, LangChain, vector databases, inference optimization
**Infrastructure & Cloud:** AWS (EC2, Lambda, SQS, RDS, S3), Kubernetes, Docker, Terraform, CI/CD pipelines, monitoring & observability
**APIs & Integration:** REST, GraphQL, webhook systems, third-party payment gateways, inventory management APIs, real-time event streaming
**Databases & Performance:** Query optimization, sharding strategies, connection pooling, caching layers, replication

## Professional Experience

### Senior Backend Engineer – Catalogix Solutions
**June 2023 – Present** | Chicago, IL

Built and maintained core backend systems serving 2.3M SKUs across 47,000+ daily transactions on the Catalogix e-commerce platform. Architected and deployed production LLM-powered product description generation system processing 180K+ merchandise items monthly with average latency of 340ms per item.

- Designed agentic workflow using Claude API and LangChain that autonomously categorizes products, extracts attributes, and generates SEO-optimized descriptions; integrated with PostgreSQL backend to persist 2.1M processed records; reduced manual categorization workload by 94%
- Engineered distributed cache layer using Redis Cluster across 6 nodes handling 45K requests/second peak load; implemented cache warming strategies for high-velocity product ingestion reducing P99 latency from 2.8s to 640ms
- Developed real-time inventory synchronization service consuming events from 23 upstream supplier systems via Kafka, maintaining 99.94% accuracy on stock levels across 1.2M active items; implemented dead-letter queues and replay mechanisms for failed event processing
- Built GraphQL API gateway in Go handling 38K concurrent connections, serving product catalog queries to mobile and web clients; optimized resolver queries reducing N+1 problems through dataloader implementation, cut average response time by 61%
- Implemented LLM-based dynamic pricing recommendation engine analyzing historical sales velocity, competitor pricing feeds, and demand signals; pipeline processes 8.7M data points daily, generating price recommendations for 340K items; integrated with order management system via gRPC
- Migrated legacy monolithic inventory system to microservices architecture across 12 Kubernetes namespaces; wrote Terraform modules for infrastructure-as-code managing 200+ AWS resources; reduced deployment time from 45 minutes to 6 minutes

### Backend Engineer – RetailLink Technologies
**August 2021 – May 2023** | Austin, TX

Engineered payment processing and fulfillment subsystems for RetailLink's multi-vendor marketplace supporting 15K+ sellers and 890K daily orders. Contributed to production systems handling $42M in monthly transaction volume.

- Developed asynchronous order processing pipeline using Python workers and Celery, processing 18K orders/hour with idempotency guarantees; integrated with Stripe, PayPal, and 7 regional payment gateways; maintained transaction accuracy audits at 99.998%
- Built seller rating aggregation service consuming 1.2M+ monthly reviews; implemented vector embeddings (using Sentence-BERT) for semantic review analysis to surface actionable feedback patterns; stored embeddings in Pinecone, enabling similarity search for fraud detection
- Engineered database sharding strategy for user profiles table (800M+ records) across 16 PostgreSQL instances; designed consistent hashing layer and implemented migration tooling; reduced query latency from 1.2s to 85ms for profile lookups
- Created internal monitoring dashboards using Prometheus and Grafana tracking 250+ operational metrics across payment flows, inventory, and fulfillment; configured alerting thresholds reducing mean-time-to-incident-detection by 73%
- Optimized Elasticsearch cluster (24 nodes, 18TB index) supporting full-text product search for 22M catalog items; implemented custom analyzers for e-commerce domain, improved search relevance scoring by 34%

### Junior Backend Engineer – DataFlow Systems
**March 2021 – July 2021** | Denver, CO

Developed backend features for supply chain analytics platform serving enterprise retail clients.

- Built ETL pipeline ingesting 3.2M daily records from client warehouse systems via REST APIs; implemented validation, transformation, and incremental loading logic reducing data latency from 6 hours to 45 minutes
- Contributed to API design and implementation for real-time demand forecasting module accepting time-series data and returning predictions via REST endpoints; deployed across 8 production servers

## Education
**Bachelor of Science, Computer Science** – University of Colorado Boulder | Graduated May 2021
