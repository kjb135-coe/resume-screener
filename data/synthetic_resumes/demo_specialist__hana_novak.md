# Hana Novak
**Senior ML Engineer — Healthcare AI**

(216) 555-0847 | hana.novak@protonmail.com | Cleveland, OH | github.com/hanovak

---

## EXPERIENCE

**Senior Machine Learning Engineer** | Meridian Health Systems | Cleveland, OH | *Jan 2024 – Present*

- Architected multi-agent framework for clinical decision support using LangGraph and Claude API; agents coordinate information retrieval, evidence synthesis, and confidence scoring across medical literature and structured guidelines
- Developed fine-tuned medical language model (based on Llama 2 70B) on 450K+ de-identified clinical notes; achieved 94.2% F1 on named entity recognition task (disease, medication, procedure extraction) against held-out eval set of 5K annotated examples
- Implemented RAG pipeline integrating 200K+ clinical research papers via vector embeddings (E5-large); reduced hallucination rate from 12% baseline to 3.2% on biomedical question-answering eval set (n=2K questions)
- Built evaluation framework comparing 7 LLM variants (GPT-4, Claude 3 Opus, Llama 2, Mixtral) on 8 medical reasoning benchmarks; documented comparative latency and accuracy trade-offs in internal whitepaper
- Optimized token efficiency of clinical documentation summarization pipeline; reduced avg tokens per note from 1240 to 847 through prompt engineering and few-shot selection, lowering API costs by 32%
- Published technical blog post on retrieval strategies for medical domain adaptation that received 1.8K GitHub stars on associated evaluation dataset

**ML Engineer** | Precision Biotech Innovations | Columbus, OH | *Aug 2022 – Dec 2023*

- Developed end-to-end RAG system for drug interaction prediction by combining structured pharmacokinetic data with unstructured clinical trial summaries; achieved 91.7% accuracy on curated eval set of 3K known interactions
- Fine-tuned DistilBERT on protein sequence classification task (functional vs. non-functional mutations); model reached 89.4% balanced accuracy across 8K labeled examples after hyperparameter search
- Designed multi-agent framework where specialized agents handle literature search, data validation, and risk assessment independently; coordinated via supervisor agent using chain-of-thought prompting
- Implemented semantic similarity matching for clinical trial eligibility criteria using dense passage retrieval; reduced candidate pool to 2.2% of original size while maintaining 98.1% recall on validation cohort
- Contributed to open-source biomedical NLP toolkit (200+ GitHub stars); wrote 3 tutorial notebooks demonstrating fine-tuning workflows for clinical NER tasks
- Presented "Scaling RAG for Domain-Specific Applications" at ML Systems Workshop 2023; slides referenced in 4 subsequent conference talks

**Data Science Intern** | CareFlow Analytics | Pittsburgh, PA | *Jun 2022 – Aug 2022*

- Built classification model predicting adverse event severity from unstructured clinical notes using BERT embeddings and logistic regression; achieved 87.3% AUC on test set (n=1.2K)
- Performed error analysis on model predictions; identified 15% class imbalance issue and experimented with SMOTE oversampling, improving minority class recall from 68% to 81%
- Automated data preprocessing pipeline for structured EHR tables using pandas and Polars; processed 2.3M patient records with 94% data completeness after validation

---

## SKILLS

- **LLM & Inference**: Claude API, GPT-4, Llama 2, Mixtral, prompt engineering, function calling, multi-turn reasoning
- **RAG & Vector Search**: LangChain, LlamaIndex, Pinecone, FAISS, embedding models (E5, BGE), semantic search
- **Agents & Orchestration**: LangGraph, CrewAI, multi-agent design patterns, supervisor agents, tool use
- **Model Adaptation**: Fine-tuning (LoRA, QLoRA), domain-specific pretraining, transfer learning, eval set construction
- **Evaluation & Benchmarking**: Custom eval frameworks, automated scoring, latency profiling, comparative LLM analysis
- **Data & ML**: PyTorch, HuggingFace Transformers, scikit-learn, pandas, numpy, SQL
- **Infrastructure**: Docker, AWS (SageMaker, S3), Linux, Git, Weights & Biases

---

## EDUCATION

**M.S. in Computer Science** | Case Western Reserve University | Cleveland, OH | 2022
- Thesis: "Domain Adaptation of Transformer Models for Biomedical Text Classification"

**B.S. in Computer Science** | Ohio State University | Columbus, OH | 2020

---

## PUBLICATIONS & CONTRIBUTIONS

- "Retrieval Strategies for Medical Domain RAG" — Technical Blog, Medium, *Mar 2025* (1.8K stars on eval dataset)
- Open-source Biomedical NLP Toolkit — Maintainer, 200+ GitHub stars
- "Scaling RAG for Domain-Specific Applications" — ML Systems Workshop 2023
