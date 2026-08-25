"""Archetype specs for the synthetic corpus. See docs/corpus_design.md.

Each spec pairs a target label with explicit per-dimension levels and
concrete instructions about what the resume must and must not contain.
The label is an INPUT to generation, never inferred from the output --
that is what keeps the ground truth independent of the scorer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Archetype:
    key: str
    label: str  # advance | hold | reject
    count: int
    production_reality: str  # high | medium | low
    technical_integration: str
    client_communication: str
    years: str  # target total experience, explicit so dates match the label
    brief: str
    must_include: tuple[str, ...]
    must_avoid: tuple[str, ...]


ARCHETYPES: tuple[Archetype, ...] = (
    Archetype(
        key="production_generalist",
        label="advance",
        count=7,
        production_reality="high",
        technical_integration="high",
        client_communication="high",
        years="4-7 years",
        brief=(
            "An AI engineer who has shipped agent-based systems to "
            "production and also works directly with customers or "
            "non-technical stakeholders. The unambiguous yes."
        ),
        must_include=(
            "at least two systems described as live in production with concrete scale figures",
            "ownership language: on-call, monitoring, incident response, or iterating after launch",
            "agentic work described concretely -- tool calling, memory, orchestration",
            "integration into a real business system or third-party API",
            "at least one instance of presenting to non-technical stakeholders or working with clients",
        ),
        must_avoid=(
            "academic publications as a headline",
            "any suggestion the work was a prototype",
        ),
    ),
    Archetype(
        key="quiet_builder",
        label="advance",
        count=7,
        production_reality="high",
        technical_integration="high",
        client_communication="low",
        years="4-8 years",
        brief=(
            "Same production and technical strength as the generalist, but "
            "entirely heads-down. No client-facing or cross-functional "
            "evidence whatsoever. Tests that a missing communication signal "
            "is treated as a non-differentiator, not a disqualifier."
        ),
        must_include=(
            "production systems with real users and concrete scale figures",
            "deep agentic or LLM engineering described concretely",
            "infrastructure, API, or platform integration work",
        ),
        must_avoid=(
            "ANY mention of presentations, stakeholders, clients, customers, sales, or cross-team work",
            "workshops, mentoring, or writing documentation for other audiences",
        ),
    ),
    Archetype(
        key="adjacent_shipper",
        label="advance",
        count=6,
        production_reality="high",
        technical_integration="medium",
        client_communication="medium",
        years="6-9 years",
        brief=(
            "Came from ML infrastructure, data platform, or backend "
            "engineering, and has genuinely shipped LLM or agent systems in "
            "the last one to two years. Deep production credibility, "
            "moderate agentic depth. Tests whether transferable production "
            "experience is credited rather than pattern-matching on titles."
        ),
        must_include=(
            "a longer history of shipping non-AI production systems",
            "a recent, real, deployed LLM or agent project with users",
            "cloud infrastructure and API integration work",
        ),
        must_avoid=("framing the AI work as experimental or exploratory",),
    ),
    Archetype(
        key="demo_specialist",
        label="hold",
        count=7,
        production_reality="low",
        technical_integration="high",
        client_communication="medium",
        years="3-6 years",
        brief=(
            "Technically impressive and completely current -- RAG, "
            "multi-agent frameworks, fine-tuning, evals -- but nothing has "
            "ever reached real users. THE most important discriminator in "
            "the corpus.\n\n"
            "Critically: this person does NOT know their work reads as "
            "demo-stage. They write with total confidence, the way an "
            "ambitious engineer actually writes. The demo-stage reality must "
            "be inferable ONLY from what is absent -- no users, no uptime, "
            "no operational ownership -- never from a self-applied label. A "
            "resume that announces its own weakness is not a realistic test "
            "case."
        ),
        must_include=(
            "genuinely current and sophisticated AI techniques described competently and confidently",
            (
                "impressive-sounding metrics that are all OFFLINE: benchmark scores, "
                "eval-set accuracy, latency measured locally, improvements over a baseline"
            ),
            "artifacts that stand in for adoption: GitHub stars, demo links, blog posts, talks",
            "roles that are plausibly real jobs with normal titles and normal date ranges",
        ),
        must_avoid=(
            (
                "the words prototype, POC, proof of concept, hackathon, demo, side project, "
                "experiment, pilot, or research project ANYWHERE -- this person would never "
                "describe their own work that way"
            ),
            "any disclaimer such as 'not deployed', 'internal only', or 'not for production use'",
            (
                "ANY production signal: real user or customer counts, request volume from live "
                "traffic, uptime, SLAs, on-call, incident response, monitoring, or revenue impact"
            ),
            "any statement that a system was launched, rolled out, adopted, or is in use by anyone",
        ),
    ),
    Archetype(
        key="production_light_ai",
        label="hold",
        count=7,
        production_reality="high",
        technical_integration="low",
        client_communication="medium",
        years="5-8 years",
        brief=(
            "Strong, real production engineering history -- APIs, "
            "distributed systems, cloud, on-call -- with only peripheral AI "
            "exposure. The mirror image of the demo specialist: catches a "
            "scorer that rewards shipping without checking it is AI work."
        ),
        must_include=(
            "substantial production engineering with scale and reliability detail",
            "at most one small, peripheral AI touch -- calling an LLM API once, or a simple classifier",
        ),
        must_avoid=(
            "agent frameworks, orchestration, tool calling, or memory systems",
            "any suggestion of depth in LLM engineering",
        ),
    ),
    Archetype(
        key="early_career",
        label="hold",
        count=6,
        production_reality="medium",
        technical_integration="medium",
        client_communication="low",
        years="1-3 years",
        brief=(
            "Real contributions to production systems, but narrow scope and "
            "clearly not owning systems yet. Below the posting's 3-6+ year "
            "band without being unqualified. Genuinely ambiguous by "
            "construction, which is why hold is the right label."
        ),
        must_include=(
            "a junior or mid-level title, and dates consistent with 1-3 years total",
            "real contribution to a shipped system, but as a contributor rather than an owner",
            "some genuine LLM or AI exposure, modest in scope",
        ),
        must_avoid=("system ownership, architectural leadership, or on-call ownership",),
    ),
    Archetype(
        key="keyword_stuffer",
        label="reject",
        count=7,
        production_reality="low",
        technical_integration="low",
        client_communication="low",
        years="4-7 years",
        brief=(
            "Dense skills sections naming every fashionable tool, but every "
            "bullet is a noun phrase with no verb describing what was built. "
            "Titles inflated relative to described substance. Tests the "
            "rubric's rule that a named tool without a sentence describing "
            "what it did is not evidence."
        ),
        must_include=(
            "a very long skills section naming many current AI tools and frameworks",
            (
                "bullets that are noun phrases or bare tool lists, NEVER sentences describing "
                "an action taken or an outcome achieved"
            ),
            "a senior-sounding title that the described substance does not support",
        ),
        must_avoid=(
            "any concrete metric, percentage, or scale figure",
            "any sentence explaining what the person actually did or built",
        ),
    ),
    Archetype(
        key="wrong_domain",
        label="reject",
        count=7,
        production_reality="medium",
        technical_integration="low",
        client_communication="low",
        years="4-8 years",
        brief=(
            "Competent and legitimately experienced, in something else "
            "entirely: frontend, data analytics, IT operations, or QA. May "
            "mention AI once in passing. Should be the cheapest rejection in "
            "the corpus."
        ),
        must_include=(
            "a coherent, real career in a clearly non-AI-engineering discipline",
            "at most one passing mention of AI, if any",
        ),
        must_avoid=("LLM, agent, or generative AI engineering work of any substance",),
    ),
    Archetype(
        key="academic_researcher",
        label="reject",
        count=6,
        production_reality="low",
        technical_integration="medium",
        client_communication="low",
        years="4-7 years including PhD",
        brief=(
            "PhD or research-track. Publications, citations, benchmark "
            "results, novel architectures. Real intellectual depth, but no "
            "production deployment, no business integration, no client work. "
            "Rejected for FIT, not for quality -- the posting wants a "
            "solutions engineer. If these score advance, the scorer is "
            "rewarding prestige over role match."
        ),
        must_include=(
            "publications with venues and citation counts",
            "benchmark or evaluation results on academic datasets",
            "research-track titles: PhD candidate, postdoc, research scientist",
        ),
        must_avoid=(
            "production deployment, business system integration, or commercial users",
            "on-call, monitoring, or operational ownership",
        ),
    ),
)


# Names are drawn independently of label so no name pattern predicts the
# verdict. We are not currently testing for name-based bias -- that is a
# documented limitation, not a solved problem.
NAMES: tuple[str, ...] = (
    "Priya Raghunathan", "Marcus Feldman", "Yuki Tanaka", "Dele Adeyemi",
    "Sofia Marchetti", "Aleksandr Volkov", "Grace Okonkwo", "Tomas Herrera",
    "Nadia Haddad", "Ewan Brackenridge", "Mei-Lin Chow", "Rafael Duarte",
    "Ingrid Solberg", "Omar Benali", "Claire Fontaine", "Devon Whitaker",
    "Anjali Deshmukh", "Kwame Asante", "Larissa Petrov", "Hugo Lindqvist",
    "Fatima Zahra", "Bennett Cross", "Rina Matsumoto", "Cormac Delaney",
    "Zainab Iqbal", "Theo Vandenberg", "Camila Restrepo", "Isaac Mwangi",
    "Wren Sutcliffe", "Hana Novak", "Julius Amankwah", "Elena Vasquez",
    "Rohan Malhotra", "Astrid Bergman", "Malik Johnson", "Chiara Bellini",
    "Tobias Reinhardt", "Amara Nwosu", "Lucas Ferreira", "Signe Aalborg",
    "Ravi Chandrasekar", "Beatrix Hollowell", "Jonah Steinberg", "Nia Carrington",
    "Emil Kowalczyk", "Sana Qureshi", "Dashiell Monroe", "Freya Ashcombe",
    "Andres Villalobos", "Keiko Yamashita", "Bruno Salvatore", "Imani Robinson",
    "Lars Thorvaldsen", "Vera Klimenko", "Oscar Nakamura", "Delphine Aubert",
    "Tariq Mansour", "Rosalind Pike", "Mateo Guzman", "Saoirse Lachlan",
)
