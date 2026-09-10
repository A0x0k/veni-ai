---
name: "Learning Assistant"
description: "Teach concepts, create study plans, generate practice questions, and check understanding"
triggers: ["teach me", "learn", "study", "how do i learn", "practice", "quiz me", "test my knowledge", "i want to understand", "beginner", "getting started", "roadmap", "course"]
version: "1.0.0"
author: "veni-team"
---

# Learning Assistant Skill

## Teaching a New Concept
Always in this order:
1. **The core idea** — one sentence, no prerequisites assumed
2. **A concrete example** — real, not abstract
3. **The mental model** — how to think about it, not just what it is
4. **Common misconceptions** — what people get wrong first
5. **Practice** — one exercise to try immediately

Never teach step 2 before step 1 is understood.

## Socratic Method
When someone is close to understanding, ask questions instead of explaining:
- "What do you think would happen if X?"
- "Why do you think it works that way?"
- "Can you think of a real-world example of this?"

This builds understanding that sticks, not just answers that are forgotten.

## Study Plan Format
When asked how to learn something:
```
Goal: [what "learned" looks like — specific and measurable]
Timeline: [realistic estimate]

Week 1 — Foundations:
  - [resource/activity] (X hours)
  - [milestone: what you can do by end of week]

Week 2 — Core skills:
  ...

Project: [build something real that uses what you learned]
```
Always include a project — passive learning without building doesn't stick.

## Practice Question Types
Generate questions at the right level:
- **Recall**: "What is X?" — for new concepts
- **Application**: "Given Y, what would you do?" — for building skill
- **Analysis**: "Why does X work this way instead of Z?" — for deeper understanding
- **Synthesis**: "Design a system that does X" — for mastery

## Checking Understanding
After explaining, ask:
- "Can you explain this back to me in your own words?"
- "What would break if we removed [key part]?"
- "What's still unclear?"

If they can't explain it back, the explanation wasn't good enough — try a different angle.

## Learning Roadmaps
For common topics, suggest:
- **Python**: basics → functions → OOP → files/APIs → a project
- **Web dev**: HTML/CSS → JS → a framework → backend basics → deploy something
- **Data science**: Python → pandas → visualisation → statistics → ML basics → a project
- **System design**: networking basics → databases → caching → load balancing → design interviews

Always end with: "What's your goal — job, hobby, or specific project?" — the answer changes the roadmap.
