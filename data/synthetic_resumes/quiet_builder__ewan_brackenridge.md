# Ewan Brackenridge
Senior Infrastructure Engineer | Developer Tools
Portland, OR 97214 | (503) 284-1962 | ewan.brackenridge@mailbox.io

## Professional Experience

**Senior Infrastructure Engineer** | Vertex Systems | Portland, OR | March 2023 – Present

Built and maintained the deployment pipeline infrastructure supporting Vertex's internal developer platform, serving approximately 180 engineers across the organization. Implemented a custom agent framework in Python that monitors production deployments in real-time, using Claude's API to analyze logs and metrics, automatically identifying failure patterns and suggesting rollback decisions. The system processes approximately 2,400 deployments monthly and has reduced mean time to recovery by 34% through intelligent alerting logic. Architected a multi-region Kubernetes orchestration layer that handles failover across AWS, GCP, and on-premises infrastructure with sub-second decision latency. Designed and deployed a service mesh integration using Envoy proxies that intercepts all internal API traffic, applying rate limiting, retry logic, and request transformation rules at the infrastructure level without requiring application code changes.

**Platform Engineer** | Cascade Labs | Seattle, WA | July 2022 – February 2023

Developed internal tools and infrastructure supporting the core data pipeline. Implemented a custom API gateway using Rust that sits between 40+ microservices and handles request routing, authentication token validation, and payload transformation. Built an agentic system for automated incident remediation that uses LLM reasoning to execute pre-approved infrastructure operations—the system successfully handled 280+ incidents autonomously in its first six months of production, reducing on-call burden by approximately 18 hours per week. Integrated with Anthropic's API to create dynamic debugging workflows that analyze system state and suggest infrastructure adjustments. Optimized the database query layer to handle 85,000 requests per second at peak traffic, reducing p99 latencies from 620ms to 140ms through connection pooling and intelligent caching strategies.

**Backend Infrastructure Specialist** | TenThousand | Seattle, WA | January 2021 – June 2022

Owned the infrastructure modernization effort for TenThousand's legacy monolith, migrating services to a distributed architecture running on Docker and Kubernetes. Created an observability platform that ingests approximately 4.2 billion log lines daily, built a custom metrics aggregation system using PromQL and Grafana dashboards. Developed tooling in Go to automate certificate rotation, secrets management, and network policy enforcement across 200+ production containers. Implemented a circuit breaker pattern library used by 35+ internal services to prevent cascade failures during high-load periods.

**Junior Systems Engineer** | Drift Technologies | Portland, OR | August 2019 – December 2020

Worked on infrastructure provisioning and cloud resource optimization. Built Terraform modules for repeatable infrastructure-as-code deployments and wrote monitoring scripts that tracked resource utilization across 120+ production EC2 instances, identifying cost optimization opportunities that reduced monthly cloud spend by $18,000.

## Technical Skills
Python, Rust, Go, Kubernetes, Docker, Terraform, AWS (EC2, S3, Lambda, RDS), GCP, Envoy, PostgreSQL, API integration, LLM engineering, Prometheus, Grafana, Linux systems administration
