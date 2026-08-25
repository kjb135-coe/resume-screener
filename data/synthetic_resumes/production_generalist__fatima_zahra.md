# Fatima Zahra
AI Systems Engineer | Agent Architecture & Production Deployment
Denver, CO | (720) 445-8291 | fatima.zahra@email.com

## Professional Summary

AI engineer with 6 years building and operating production agent systems in government and public sector contexts. Proven track record shipping multi-agent orchestration platforms that serve thousands of users daily, with direct responsibility for system reliability, stakeholder communication, and post-launch iteration. Deep expertise in LLM integration, tool-calling architectures, API orchestration, and translating technical constraints to non-technical audiences.

## Experience

**Senior AI Systems Engineer** | Colorado Department of Natural Resources | Denver, CO | March 2022 – Present

Led design and deployment of an intelligent permitting agent for water rights allocation, now processing 12,000+ monthly requests from ranchers, farmers, and municipal water authorities.

- Architected multi-agent system with specialized orchestration layer: intake agent handles document classification and extraction, compliance agent evaluates against state regulations via custom rulebase APIs, and approval agent interfaces with legacy permitting database. Each agent maintains conversation memory across 5+ turn interactions to handle complex multi-year water agreements.
- Implemented tool-calling framework integrating 14 external APIs including USGS water data feeds, municipal records systems, and the state's GIS platform. Built fallback logic and retry handlers to manage 99.2% uptime across systems with variable latency.
- On-call for incident response and monitoring using CloudWatch dashboards; resolved 23 production incidents in 2025 (avg. resolution time 47 minutes). Implemented structured logging that reduced mean time to diagnosis by 62%.
- Presented quarterly performance metrics and system roadmap to executive stakeholders in the state water board, translating agent behavior and model confidence thresholds into policy language for non-technical directors.
- Iterated system after launch based on user feedback: added explanation generation so farmers could understand denial reasons, reduced false rejections by 18% through fine-tuning prompt engineering, extended memory window to handle seasonal permit renewals.

**AI Engineer** | Utah State Health Department, Bureau of Data Services | Salt Lake City, UT | July 2019 – February 2022

Developed and shipped a complaint triage and routing agent handling public health complaints across 40+ agencies in the state, now live with 8,000+ annual interactions.

- Built agentic workflow that classifies incoming complaints using Claude API with custom few-shot examples, extracts jurisdiction-relevant entities, checks historical complaint patterns in PostgreSQL, and routes to appropriate agency via email and webhook integrations. System handles 99% of routing autonomously with human review fallback.
- Managed full lifecycle from pre-launch load testing (stress tested to 500 req/sec) through monitoring and on-call support. Caught and resolved memory leak in agent orchestration layer affecting throughput; improved mean response time from 8.2 seconds to 2.1 seconds.
- Conducted user training sessions with complaint specialists across 12 health departments, demonstrating agent capabilities and collecting feedback on classification accuracy. Created documentation translating technical system architecture into workflows for non-technical staff.
- Deployed agentic system on AWS using ECS with auto-scaling; managed container orchestration and CI/CD pipeline improvements that reduced deployment time from 90 to 15 minutes.

**Machine Learning Engineer** | Regional Planning Commission, Salt Lake City, UT | September 2018 – June 2019

Developed early prototypes and conducted feasibility studies for AI-driven public engagement (not production).

**Data Analyst** | Utah Department of Human Services | Salt Lake City, UT | June 2017 – August 2018

## Technical Skills

**Agent & LLM Systems:** Tool-calling design, multi-agent orchestration, prompt engineering, memory management (conversation history, context windows), function calling with structured outputs, fallback strategies

**Cloud & Infrastructure:** AWS (ECS, Lambda, CloudWatch, RDS), Docker, Kubernetes basics, CI/CD (GitHub Actions), monitoring and alerting

**Integrations & APIs:** REST API design and consumption, webhook handling, database connectivity (PostgreSQL, legacy systems), third-party API orchestration, error handling and retry logic

**Languages:** Python (primary), SQL, Bash

**Stakeholder Communication:** Executive briefings, non-technical documentation, user training, requirements translation

## Education

**M.S. in Computer Science** | University of Colorado Boulder | Boulder, CO | 2017
Thesis: Scalable Data Processing in Distributed Systems

**B.A. in Mathematics** | University of Utah | Salt Lake City, UT | 2015
