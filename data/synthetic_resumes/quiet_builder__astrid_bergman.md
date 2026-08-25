# Astrid Bergman
Senior Backend Engineer, Payments Infrastructure
astrid.bergman@mailbox.io | (206) 447-3821 | Seattle, WA

## Experience

**Senior Backend Engineer** | Nexus Financial Systems | Seattle, WA | Jan 2024 – Present
- Architected real-time transaction reconciliation engine processing 2.3M+ daily settlement records across 47 payment corridors; reduced reconciliation latency from 4.2 hours to 18 minutes through async worker pool redesign
- Implemented agentic settlement workflow using Claude API with tool use for dispute resolution, enabling autonomous handling of 73% of chargeback cases without manual intervention; integrated with Kafka topic for asynchronous processing of 8,000+ daily events
- Built gRPC service layer for card processor integrations (Visa, Mastercard networks); designed protobuf schemas handling 1.4M transactions/day with <50ms p99 latency
- Decomposed legacy monolithic ledger system into 12 microservices using event sourcing; maintained ACID guarantees across distributed transactions via Postgres SERIALIZABLE isolation with WAL streaming
- Deployed custom token vaulting system on AWS KMS with envelope encryption; PCI DSS 3.2 compliant storage reducing breach surface area by 94%

**Backend Engineer** | Compass Payments Ltd. | Vancouver, BC | Jul 2022 – Dec 2023
- Engineered LLM-powered transaction categorization agent using GPT-4 fine-tuned embeddings; classified 156M historical transactions with 96.8% merchant category accuracy, enabling improved spend analytics
- Extended Stripe API client library to support webhook retry logic with exponential backoff; handled burst loads of 18,000 events/second during peak settlement windows
- Implemented Kubernetes-native scaling controller for payment processing pods; reduced cold-start latency for transaction authorization from 340ms to 89ms through preemptive scheduling
- Maintained PostgreSQL multi-master replication cluster across 3 availability zones; implemented automated failover reducing RTO to <90 seconds for critical payment rails
- Built internal CLI tool for bulk transaction remediation using Python asyncio; processed 2.1M records in parallel, reducing operations team manual work by 11 hours per month

**Software Engineer** | Currencyflow Systems | Toronto, ON | Mar 2021 – Jun 2022
- Developed HTTP/2 reverse proxy for PCI-compliant routing of card data between acquiring banks and payment gateways; zero data loss across 340M annual requests
- Designed schema migrations framework using Liquibase for Postgres supporting zero-downtime schema evolution across sharded ledger tables; executed 23 production deployments with zero rollbacks
- Implemented distributed tracing infrastructure using Jaeger; reduced p99 transaction latency investigation time from 6 hours to 8 minutes by correlating logs across 34 microservices
- Built Redis-backed rate limiter for merchant API endpoints supporting dynamic quota assignment; prevented 8 denial-of-service incidents affecting customer merchant tiers

**Junior Backend Engineer** | Vertex Payment Solutions | Montreal, QC | Jun 2020 – Feb 2021
- Contributed to core settlement processing service written in Go; optimized SQL query patterns reducing database CPU utilization by 31%
- Developed batch reconciliation scripts for FX settlement matching; identified and corrected 12,400 unmatched transactions worth $2.8M CAD
- Implemented structured logging using JSON format with correlation IDs across payment rails; improved incident triage speed for production issues

## Skills
- **Languages:** Go, Python, Java, SQL
- **Infrastructure:** Kubernetes, Docker, AWS (EC2, RDS, Lambda, KMS), Postgres, Redis, Kafka
- **APIs & Protocols:** REST, gRPC, Protocol Buffers, AMQP, WebSockets
- **Specialization:** Payment systems, transaction processing, LLM integration, distributed systems, event streaming

## Education
**Bachelor of Science, Computer Science** | University of British Columbia | Vancouver, BC | 2020
