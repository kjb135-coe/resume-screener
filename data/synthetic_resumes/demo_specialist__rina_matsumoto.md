# Rina Matsumoto
Senior ML Engineer – Infrastructure & Developer Tools
(503) 284-7621 | rina.matsumoto@outlook.com | Portland, OR | github.com/rinamatsumoto

---

## Core Competencies
**ML/AI:** Retrieval-Augmented Generation (RAG), multi-agent frameworks, LLM fine-tuning, prompt engineering, vector databases, semantic search, agentic reasoning loops, function calling, tool use orchestration  
**Frameworks & Libraries:** LangChain, LlamaIndex, AutoGen, Pydantic, OpenAI API, Anthropic API, Cohere, HuggingFace Transformers, vLLM, Ray, FastAPI  
**Infrastructure & Tools:** Docker, Kubernetes, PostgreSQL, Pinecone, Weaviate, Redis, Apache Kafka, MLflow, Weights & Biases, GitHub Actions  
**Evaluation & Monitoring:** RAGAS framework, custom eval harnesses, benchmark construction, latency profiling, token cost optimization  
**Languages:** Python, TypeScript, SQL, Bash

---

## Professional Experience

**Senior ML Engineer – Developer Experience**  
*Tessera Labs, Portland, OR* | Mar 2024 – Present

- Architected and maintained an open-source LLM toolkit for building multi-agent applications, now at 4.2K GitHub stars and 180+ contributors; designed TypeScript and Python SDKs with unified abstractions for agent state management and tool execution
- Built comprehensive evaluation framework for agent reasoning quality, implementing RAGAS metrics and custom recall/precision benchmarks; measured 87% semantic correctness on internal eval set of 500 queries against baseline of 61%
- Developed RAG infrastructure component supporting multiple retrieval strategies (dense, sparse, hybrid); optimized vector search latency to <45ms p99 for 10M-token corpus using Weaviate clustering and query rewriting
- Designed and shipped fine-tuning pipeline orchestration using Ray distributed training; reduced wall-clock time for instruction-tuned models from 8 hours to 2.5 hours on 4xA100 setup through batch scheduling improvements
- Led technical blog series on agentic reasoning patterns, published five posts on agent memory architectures, tool-use optimization, and LLM routing strategies; accumulated 12K+ views and cited by community projects

**ML Infrastructure Engineer**  
*Zenith AI, Seattle, WA* | Jul 2023 – Feb 2024

- Owned development of internal LLM serving infrastructure; built multi-model endpoint abstraction supporting OpenAI, Anthropic, and open-weight model inference with automatic rate-limit handling and request queuing via Kafka
- Implemented function-calling orchestration layer enabling tool composition across 40+ API integrations; benchmarked at 78% tool selection accuracy on held-out test set of 200 complex multi-step tasks
- Constructed evaluation harness for LLM output quality using custom metrics (BLEU, semantic similarity via embeddings, token-level accuracy); integrated with CI/CD to track model performance across versions
- Optimized prompt templates and context management strategies, reducing average token usage by 32% across production query workloads while maintaining ROUGE-L score of 0.71 on benchmark tasks
- Mentored three junior engineers on LLM fundamentals, vector database design, and debugging agentic failures; conducted internal workshop on RAG system architecture

**ML Engineer**  
*Cascade AI, Eugene, OR* | Jan 2023 – Jun 2023

- Developed end-to-end RAG system for technical documentation retrieval using LlamaIndex, PostgreSQL with pgvector, and semantic chunking; achieved 83% MRR@10 on 5K-document test collection
- Fine-tuned open-weight LLMs (Llama 2, Mistral) on domain-specific instruction sets using LoRA; validated improvements through offline benchmarks showing 14-point increase in task-specific accuracy
- Built agent framework supporting multi-turn conversation state and tool memory; implemented reasoning chain evaluation using custom scoring rubric applied to 300-example validation set
- Contributed to internal MLflow tracking infrastructure, implementing automated experiment logging and model registry workflows; reduced setup friction for team onboarding

---

## Education

**M.S. Computer Science** – University of Washington, Seattle, WA | 2022  
Focus: Machine Learning, Natural Language Processing

**B.S. Computer Science** – Reed College, Portland, OR | 2020

---

## Technical Publications & Community
- "Building Reliable Tool-Use Agents" – Published on Towards Data Science (Jul 2025)  
- Speaker, LLM Infrastructure Summit – "Observability Patterns for Multi-Agent Systems" (Nov 2025)  
- Core contributor to LlamaIndex framework; PRs focused on hybrid retrieval and prompt optimization
