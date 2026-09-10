# Architecture: Veni-AI

Veni-AI is a modular terminal-native AI assistant. Its architecture is built for extensibility, safety, and agentic autonomy.

## 🧱 Modular Design
The system is divided into key subsystems:

1.  **Core Controller:** Manages the LLM lifecycle, session state, and conversation pruning.
2.  **Skill System (Agentic Routing):**
    - A dynamic routing engine that maps natural language intent to specific tools (skills).
    - Skills are loosely coupled; activating a skill only loads necessary context, keeping the LLM prompt lean.
3.  **Persona Engine:** Modifies system prompts and behavioral rules for the agent at runtime, enabling context-specific handling (e.g., "Critic" vs "Teacher").
4.  **Safety Layer:** A pre-execution middleware that validates shell commands against a blacklist and triggers approval prompts for destructive operations.

## 🧩 Why this Architecture?
By using a **Skill-based routing system** instead of a single massive prompt, Veni-AI maintains high performance and reduces hallucination risk, as the LLM only operates within the context of the currently active skills.
