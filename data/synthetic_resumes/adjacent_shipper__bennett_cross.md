# Bennett Cross
Senior Software Engineer, Platform Infrastructure
Portland, OR | (503) 447-8192 | bcross@emailaddr.com | linkedin.com/in/bennettcross

## Professional Summary

Infrastructure and backend engineer with 8 years of production systems experience, including 18 months shipping LLM-powered features at scale. Deep expertise in cloud architecture, API design, and data pipeline reliability. Recently led the architecture and deployment of an agent-based document processing system serving 2,000+ daily users across financial services clients. Proven track record translating ML research into operationalized, monitored production systems.

## Experience

**Senior Platform Engineer** | Cascadia Data Systems | Portland, OR | January 2025 – Present

- Architected and deployed a multi-agent document analysis service for compliance workflows, integrating Claude API with internal document retrieval system; system processes 15,000+ documents monthly with 99.2% uptime SLA
- Built request queuing and rate-limiting layer using Redis and gRPC to manage API costs while maintaining sub-second latencies; reduced per-request inference cost by 34% through intelligent batching
- Designed monitoring and observability stack using Datadog and custom metrics; implemented alerting for model drift and API failures, enabling rapid diagnosis of production issues
- Mentored 3 engineers on LLM integration patterns; documented decision tree for fallback strategies when models refuse requests or return malformed outputs
- Managed vendor relationships with ML API providers; negotiated tiered pricing and established SLAs for response time and availability

**Backend Engineer, ML Infrastructure** | Zenith Labs | Seattle, WA | August 2022 – December 2024

- Owned the data ingestion and feature serving platform supporting a 40-person ML team; architecture processed 2TB daily of training data across 12 microservices running on Kubernetes
- Led migration of feature store from DynamoDB to PostgreSQL with column-oriented indexes; improved query latency by 60% and reduced infrastructure costs by 28%
- Built Python SDK for internal ML model deployment; abstracted Kubernetes complexity and enabled 15+ data scientists to deploy models without DevOps assistance
- Implemented streaming aggregation pipeline using Kafka and Flink for real-time feature computation; powering recommendation models serving 3M+ users across mobile and web
- Developed comprehensive API testing framework using pytest and property-based testing; caught 11 critical data serialization bugs before production deployment
- Contributed to cost optimization initiative that reduced cloud spend by $180K annually through reserved instance planning and workload consolidation

**Software Engineer** | Pivot Systems | Denver, CO | March 2021 – July 2022

- Developed core backend services for multi-tenant SaaS platform serving HR automation; 25,000+ employees across 60+ companies used the system daily
- Designed REST API for task scheduling engine; handled 500K+ requests per day with p99 latency under 200ms using PostgreSQL connection pooling and query optimization
- Implemented webhook delivery system with exponential backoff and dead-letter queue; achieved 99.8% successful delivery rate for critical events
- Collaborated with frontend team on API contract design and documentation; reduced integration time by 40% for new customer onboarding
- Debugged complex production incidents involving race conditions and distributed transaction consistency; documented postmortems and implemented preventative monitoring

**Software Engineer** | Rapid Tech | Denver, CO | June 2019 – February 2021

- Built and maintained event processing pipeline handling 50M+ events daily for analytics platform; architecture scaled across 3 AWS regions with automated failover
- Developed client libraries in Python and Go for event ingestion; adopted by 8 internal teams and 12 external partners
- Optimized database queries for reporting layer; improved dashboard load times from 8 seconds to 1.2 seconds through strategic indexing and query rewriting
- Owned on-call rotation for production infrastructure; maintained 99.7% uptime SLA across all services

**Junior Backend Engineer** | Insight Digital Solutions | Boise, ID | July 2018 – May 2019

- Implemented REST endpoints for customer data management service; handled authentication, validation, and database persistence
- Wrote unit and integration tests achieving 78% code coverage
- Participated in weekly code reviews and infrastructure planning meetings

## Technical Skills

**Languages & Frameworks:** Python, Go, SQL, TypeScript, Rust (learning)

**Infrastructure & Cloud:** AWS (EC2, S3, Lambda, RDS, SQS), Kubernetes, Docker, Terraform, PostgreSQL, Redis, Kafka

**ML & API Integration:** LLM API integrations (Claude, GPT-4), vector databases, prompt engineering, retrieval-augmented generation (RAG), function calling

**Tools & Practices:** Git, CI/CD pipelines, gRPC, REST APIs, Datadog, PagerDuty, agile methodologies

## Education

**Bachelor of Science in Computer Science** | University of Oregon | Eugene, OR | Graduated 2018
