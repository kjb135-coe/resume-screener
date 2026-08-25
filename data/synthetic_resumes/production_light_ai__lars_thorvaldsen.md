# Lars Thorvaldsen
Production Engineering Manager | Supply Chain Systems  
Portland, OR 47203 | (503) 886-4127 | lars.thorvaldsen@email.com

## Professional Summary

Production engineering leader with 7 years building and operating mission-critical logistics and supply-chain systems at scale. Proven track record shipping reliable infrastructure serving 2M+ daily transactions across warehousing, fulfillment, and last-mile operations. Deep expertise in distributed systems reliability, on-call management, and cross-functional collaboration with operations and product teams. Known for pragmatic solutions that balance velocity with operational resilience in high-stakes environments.

## Experience

**Senior Production Engineer, Meridian Logistics** | Portland, OR | March 2023 – Present
- Led redesign of order-routing microservices handling 180K shipments daily across 12 regional distribution centers; reduced latency p99 from 850ms to 280ms and improved system availability to 99.97%
- Owned on-call rotation for critical fulfillment APIs serving 1,200+ carrier integrations; established SLO framework and alerting strategy that reduced incident mean-time-to-resolution from 45 minutes to 12 minutes
- Drove migration of legacy monolithic warehouse management system to containerized services on Kubernetes; coordinated with warehouse operations, carrier partners, and product to execute zero-downtime cutover for $120M annual fulfillment volume
- Implemented comprehensive observability stack (Prometheus, Jaeger, ELK) capturing end-to-end traces from order ingestion through dock scanning; identified and remediated three critical bottlenecks in peak-load scenarios
- Managed 4-person on-call team; established runbooks and automation to handle 95% of alerts without human intervention

**Production Engineer II, Bruin Supply Chain Solutions** | Seattle, WA | July 2021 – February 2023
- Architected real-time inventory synchronization service connecting 40+ warehouse facilities to central fulfillment hub; handled eventual consistency challenges across distributed datacenters with <5 minute reconciliation window
- Reduced database query latency by 60% through indexing analysis and connection pooling optimization; enabled product team to ship inventory forecasting feature impacting $8M in working capital efficiency
- Built canary deployment pipeline for supply-chain APIs using traffic shadowing; caught regression in demand-forecasting logic before production impact
- Managed PostgreSQL replication and failover for time-series shipment tracking data; implemented automated backup validation reducing RTO from 6 hours to 12 minutes
- On-call for carrier integration layer; developed troubleshooting guides and dashboards used by 15-person carrier operations team

**Software Engineer, Logistics, Titan Fulfillment** | Seattle, WA | November 2019 – June 2021
- Built rate-shopping API that queried carrier pricing endpoints and persisted results for 50K+ daily shipments; integrated with cost-estimation system across 8 fulfillment centers
- Developed small pilot using third-party text classification API to auto-categorize carrier exception messages (delivery delays, address corrections) for 2-3% improvement in manual triage efficiency; learned lessons about reliability of external APIs in production workflows
- Implemented cache-warming strategy for common carrier zone lookups; reduced query load on carrier master data service by 40%
- Owned on-call responsibilities for order tracking API; debugged complex issues involving multiple datacenters and carrier API timeouts

**Associate Software Engineer, Apex Transportation** | Portland, OR | June 2018 – October 2019
- Developed backend services for last-mile delivery routing and proof-of-delivery tracking; supported 200K+ deliveries monthly
- Implemented rate-limiting and retry logic for third-party carrier API calls to handle transient failures
- Participated in on-call rotation for customer-facing APIs

## Technical Skills

**Platforms & Infrastructure:** Kubernetes, Docker, AWS (EC2, RDS, S3, Lambda), PostgreSQL, Redis, gRPC, REST APIs

**Observability & Reliability:** Prometheus, Grafana, Jaeger, ELK Stack, PagerDuty, incident management, SLO/SLI definition

**Languages:** Go, Python, Java, SQL

**Practices:** Production readiness reviews, chaos engineering, capacity planning, load testing, deployment automation

## Education

**Bachelor of Science, Computer Science**  
University of Washington | Seattle, WA | 2018
