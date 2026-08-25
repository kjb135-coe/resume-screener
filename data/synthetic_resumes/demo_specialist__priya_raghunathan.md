# Priya Raghunathan
AI Engineer | Machine Learning Systems
(415) 847–3622 | priya.raghunathan@email.com | San Francisco, CA

## Professional Experience

**Senior ML Engineer, Luminous Media Labs** | San Francisco, CA | March 2024 – Present

At Luminous Media Labs, a content intelligence startup, I lead the development of our next-generation video understanding platform that leverages multi-agent frameworks to analyze and contextualize entertainment media. My core focus is building systems that extract narrative structure, sentiment arcs, and cultural references from video content using orchestrated LLM agents working in concert with fine-tuned vision models.

I architected our agentic reasoning layer using a custom implementation of tool-use patterns with Claude and GPT-4, enabling agents to iteratively refine scene analysis by querying a vector store of entertainment domain knowledge. The system coordinates five specialized agents—one for dialogue extraction, one for visual theme detection, one for historical context, one for emotional beat mapping, and one for cross-reference synthesis—each with distinct prompts and access to different tool suites. I implemented retrieval-augmented generation across all agents to ground their outputs in our proprietary database of 500K+ movie and TV scenes, reducing hallucination rates on factual claims by 34 percentage points on our test benchmark.

I designed and executed a comprehensive evaluation framework for the agents using 2,400 manually annotated scenes across drama, comedy, and documentary content. We measure both task-specific metrics (scene classification F1 of 0.89, emotional arc continuity at 92% agreement with human coders) and cross-agent consistency scores. Latency optimization brought end-to-end agent inference from 18 seconds to 4.2 seconds per scene through strategic caching and parallel agent execution. I open-sourced the evaluation harness as a reference implementation, which has accumulated 2,800+ GitHub stars and sparked a discussion series on agent evaluation best practices that I presented at MLOps.community in June 2026.

**Machine Learning Engineer, Narrative AI** | Oakland, CA | August 2023 – February 2024

I joined Narrative AI as an early ML hire tasked with building the inference backbone for a screenplay analysis engine targeting screenwriters and studios. The initial mandate was to fine-tune open-source LLMs on a corpus of professionally written scripts to capture stylistic patterns and structural adherence to three-act narrative principles.

I curated and processed 8,000 feature film and television scripts using LlamaIndex to create a domain-specific retrieval corpus, then fine-tuned Mistral 7B and Llama 2 70B models using QLoRA on AWS SageMaker. The fine-tuned Mistral model achieved 78% accuracy on a held-out test set of 400 scripts when predicting structural breakdown points (act transitions, plot turns), compared to 61% for the base model. I implemented a RAG pipeline where user queries about script structure were enriched by retrieving semantically similar scenes from our dataset before being passed to the fine-tuned model, increasing relevance scores by 27 points on our internal rubric. Response latency measured at the application level was 2.8 seconds for typical queries.

I documented the entire pipeline in a technical blog post ("Fine-tuning LLMs for Narrative Intelligence," Medium, November 2023) that reached 12K reads and generated substantive feedback from screenwriting technologists. I also gave a workshop at the San Francisco AI Meetup on practical fine-tuning workflows that attracted 140 attendees.

**AI Research Intern, Creative Systems Lab** | Berkeley, CA | June 2022 – July 2023

During my transition from graduate study to industry, I contributed to a research effort within Creative Systems Lab focused on understanding how transformer models represent narrative concepts. I trained several variants of BERT on a 50K-sentence dataset of plot descriptions, each variant using different masking strategies to isolate how models capture causal relationships between story events. The best-performing variant achieved 84% accuracy on a custom narrative causality benchmark we developed, where the baseline was 52%. I implemented attention visualization tooling that revealed interpretable patterns in how attention heads aligned with narrative dependency structures, work that appeared in a workshop paper at AAAI 2023 and has been cited in three subsequent papers on narrative understanding.

## Education

**Master of Science, Computer Science** | University of California, Berkeley | May 2022
Specialization: Machine Learning; Thesis on fine-grained evaluation metrics for generative language models

**Bachelor of Science, Computer Science** | California State University, Sacramento | May 2020

## Technical Skills

Advanced proficiency in LLM agent orchestration, retrieval-augmented generation (RAG), fine-tuning on consumer hardware, multi-modal embeddings, prompt engineering, evaluation framework design, and benchmark construction. Languages: Python, SQL. Frameworks: PyTorch, HuggingFace Transformers, LlamaIndex, LangChain, Anthropic SDK. Cloud: AWS SageMaker, EC2. Version control and collaboration tools standard across the field.
