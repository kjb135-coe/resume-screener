# Theo Vandenberg
Production Engineer | Infrastructure & Payments
Denver, CO | (720) 445-8962 | theo.vandenberg@mailpoint.dev

## EXPERIENCE

**Senior Production Engineer** | Meridian Financial Systems | Denver, CO | Mar 2023 – Present
- Architected and operated payment processing infrastructure handling 2.3M transactions daily across 47 regions; designed circuit breaker patterns reducing cascading failures by 94%
- Led on-call rotation for critical payment APIs; maintained 99.97% uptime SLA through systematic reliability improvements and incident response automation
- Implemented distributed tracing (Jaeger) across microservices stack; reduced mean time to detect (MTTD) for payment delays from 18 minutes to 2 minutes
- Managed PostgreSQL cluster scaling supporting 15K concurrent connections; optimized query performance on transaction ledger reducing tail latency by 68%
- Deployed fraud detection classifier (simple logistic regression via AWS Lambda) to flag suspicious payment patterns; integrated lightweight model serving without adding measurable latency
- Oncall engineer responsible for 12 microservices; maintained runbooks and incident postmortems; reduced MTTR for payment gateway outages from 42 minutes to 9 minutes

**Platform Engineer** | Cascadia Payment Corp | Seattle, WA | Jan 2021 – Feb 2023
- Built Kubernetes cluster management platform supporting 800+ payment processing pods; automated node scaling based on transaction volume forecasts
- Designed and implemented API rate limiting service using token bucket algorithm; protected backend systems from abuse while maintaining sub-millisecond latency
- Owned database migration strategy for 60GB+ transaction history; zero-downtime migration using dual-write pattern with data validation across 50M+ records
- Established alerting and monitoring standards across platform; reduced alert fatigue by 71% through correlation-based grouping and anomaly detection thresholds
- Collaborated with payments product team on capacity planning; presented monthly forecasts to executive stakeholders
- Troubleshot complex distributed system failures in real-time; debugged race conditions in concurrent transaction processors

**Infrastructure Engineer** | Quantix Solutions | Portland, OR | Nov 2018 – Dec 2020
- Managed AWS infrastructure hosting core settlement systems; optimized costs by 32% through Reserved Instance strategy and spot instance automation
- Built observability platform for payment clearing house; ingested 800M+ metrics daily using Prometheus and Grafana
- Deployed Vault for secrets management across 200+ services; reduced credential rotation cycle from manual quarterly to automated weekly
- Developed disaster recovery procedures; tested quarterly failovers ensuring RPO under 15 minutes for transaction databases

## TECHNICAL SKILLS
- Languages: Go, Python, Bash
- Cloud & Infrastructure: AWS (EC2, RDS, Lambda, S3), Kubernetes, Docker, Terraform
- Observability: Prometheus, Grafana, Jaeger, ELK Stack
- Databases: PostgreSQL, Redis, DynamoDB
- Payments: Settlement systems, PCI compliance, ACH/wire protocols

## EDUCATION
B.S. Computer Science | University of Colorado Boulder | 2018
