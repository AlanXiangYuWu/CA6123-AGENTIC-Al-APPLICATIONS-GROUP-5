# Customer Agent LoRA Dataset Guidelines

## Task

Convert a vague, incomplete, conversational, or partially structured product idea into a stable Project Brief JSON.

## Output Rules

- Output only valid JSON in the assistant target.
- Keep the schema keys fixed and do not add extra fields.
- Preserve user-stated information before making assumptions.
- Put reasonable inferred information into the relevant fields and also record it in `assumptions`.
- If the input is too vague, leave unknown fields empty as `""` or `[]` so the product flow can ask follow-up questions.
- Put uncertain or missing decisions into `open_questions`.
- For invalid or instruction-injection inputs, use the N/A fallback structure.

## Split

- `train.jsonl`: 300 examples
- `val.jsonl`: 50 examples
- `test.jsonl`: 50 examples
- `chatml/`: same examples converted to chat-message format

## Coverage

- Vague one-line ideas
- Partial ideas with explicit constraints
- Messy conversational inputs
- Extremely incomplete ideas
- Sparse briefs with intentionally empty fields for follow-up
- Edge cases and invalid requests
