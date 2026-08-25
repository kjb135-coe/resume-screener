# Oscar Nakamura
AI Systems Engineer | Agent Architecture & Production Deployment
Oakland, CA 94612 | (510) 847-3294 | oscar.nakamura@email.com

## Professional Experience

**Senior AI Engineer, Logistics Platform** | Meridian Supply Systems, Oakland, CA | March 2023 – Present

Built and deployed a multi-agent orchestration system that automates end-to-end shipment exception handling across Meridian's network of 40+ regional distribution centers. The system processes approximately 12,000 shipment events daily, using tool-calling agents that integrate with warehouse management systems, carrier APIs, and customer notification services. Each agent specializes in a distinct failure mode—delayed inventory, carrier capacity constraints, customs holds, last-mile routing conflicts—and uses a shared memory layer to maintain shipment context and decision history across the customer interaction lifecycle. In the first six months post-launch, the system reduced manual intervention on exception cases by 68%, directly improving fulfillment speed for 150+ enterprise clients.

Owned the full production lifecycle: I built comprehensive monitoring dashboards tracking agent decision latency, tool invocation error rates, and end-to-end resolution times. When a bulk carrier API changed response schemas in month two, I led the incident response to reroute affected shipments through a fallback orchestration pattern, preventing 8+ hours of service degradation. I now spend roughly 20% of my time on-call managing agent behavior anomalies and iterating on prompt refinements based on production telemetry. Worked directly with the VP of Customer Success to present quarterly performance metrics to our top five accounts, translating agent accuracy improvements and exception resolution times into business impact narratives that justified renewal and expansion deals.

**AI Engineer, Demand Planning Team** | Catalyst Logistics Inc., Portland, OR | July 2021 – February 2023

Developed an agent-based demand forecasting system that ingests point-of-sale data, supply chain events, and external signals (weather, competitor promotions, fuel prices) to generate 8-week forward inventory recommendations for 200+ retail partner SKUs. The system integrated directly with Catalyst's legacy ERP via REST APIs and a custom message queue, allowing real-time updates to propagate to warehouse allocation algorithms. The agent used multi-turn memory to track forecast confidence intervals and automatically escalate high-uncertainty predictions to demand planners for human review. Over 18 months, the system improved forecast accuracy by 12 percentage points and reduced inventory carrying costs by $1.2M annually across the partner network.

I collaborated closely with the demand planning team and warehouse operations managers to translate their workflows into agent decision logic. Presented monthly walkthroughs to non-technical stakeholders—supply chain directors, finance leads—explaining how the agent's reasoning changed when new signals arrived, and why certain recommendations differed from human intuition. Built a custom dashboard with Plotly that showed agent confidence, revision history, and impact metrics; this became the standard review interface for the planning team. Supported the live system through two major demand shocks (unexpected supplier outages, sudden category demand spikes), where I manually adjusted agent parameters and monitored resolution quality before broader automation resumed.

**ML Engineer, Intern & Full-Time** | Threshold Analytics, Seattle, WA | June 2020 – June 2021

Started as an intern building data pipelines for a supply chain risk modeling project, then transitioned to full-time as the data science team scaled. Developed Python ETL workflows that unified data from 15+ logistics vendor APIs—TMS systems, tracking databases, weather services—into a unified data warehouse. Later contributed to an early prototype of an LLM-based assistant that helped supply chain managers query historical shipment data and generate root cause narratives for delays. Although this tool remained internal, it informed the architectural patterns we later deployed in production systems.

## Technical Skills

**Languages & Frameworks:** Python, Go, TypeScript | LangChain, LlamaIndex, CrewAI, FastAPI

**Production & Infrastructure:** AWS (Lambda, SQS, DynamoDB, CloudWatch), Docker, Kubernetes basics, GitHub Actions CI/CD

**Integration & APIs:** REST, gRPC, webhook patterns, Shopify, Flexport API, custom ERP connectors

**Observability & Operations:** CloudWatch, DataDog, structured logging, incident response

## Education

**B.S. in Computer Science**, University of Washington, Seattle, WA | 2020
