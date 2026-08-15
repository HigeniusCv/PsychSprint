"""Llama-3.1 chat template, applied by US, not by the server.

/chat/completions is never used: the base model must be scored on the
byte-identical string, so both models go through /completion with this
rendered template. <|begin_of_text|> is deliberately omitted -- the server
auto-inserts BOS when the model's add_bos_token metadata is true (Llama-3.1:
true); including it literally would double the BOS (DECISIONS.md D-008).
"""
LLAMA3_TEMPLATE = (
    "<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
    "<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
)


def render(system, user):
    return LLAMA3_TEMPLATE.format(system=system, user=user)
