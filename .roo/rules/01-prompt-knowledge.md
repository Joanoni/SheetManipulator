# 2026-03-15 STANDARDS FOR PROMPT ENGINEERING & SEMANTIC MARKDOWN

# 2026 FRONTIER PROMPT ENGINEERING STANDARDS

## Core Architecture
<architecture>
* **Semantic Hierarchy:** Models prioritize content based on header depth. Use H1 for global context and H2/H3 for operational segments.
* **Hybrid Delimiters:** Use XML-style tags to encapsulate variable content and instructions. This prevents "Context Bleed" and ensures strict adherence to section boundaries.
</architecture>

## Markdown Best Practices
<markdown_rules>
* **Tables:** Use for all comparative data or feature mapping. Grid-based logic is processed with higher fidelity than prose.
* **Horizontal Rules (---):** Use to force a state reset between instructions and output examples.
* **Bold Emphasis:** Reserved for critical constraints and non-optional logic.
</markdown_rules>

## Advanced XML Tagging
<tagging_standards>
* `<context>`: High-level background and situational data.
* `<rules>`: Hard constraints that the model must not violate.
* `<thinking>`: Explicitly request this tag for complex reasoning before the final answer (Chain of Thought).
* `<output_format>`: Exact structural requirements for the response.
</tagging_standards>