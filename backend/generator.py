from transformers import pipeline

# --------------------------------------------------
# Load a text-generation model
# --------------------------------------------------
# You can switch to 'gpt2-medium' for stronger responses if needed
generator = pipeline(
    "text-generation",
    model="distilgpt2"
)

# --------------------------------------------------
# Generate an answer using retrieved memories
# --------------------------------------------------
def generate_answer(query: str, retrieved_memories: list) -> str:
    """
    Combine retrieved memories and user query to generate a concise, natural answer.
    """
    if not retrieved_memories:
        return "I don't recall anything about that."

    # Combine memories into context
    context_text = "\n".join(retrieved_memories)

    # Clear prompt with instruction to be concise
   prompt = (
    "You are an AI assistant. Use the following memories to answer the question accurately.\n"
    f"Memories:\n{context_text}\n\n"
    f"Question: {query}\n"
    "Answer concisely in 1-2 sentences. "
    "If the memory contains the answer, provide it. "
    "Do not repeat the question. "
    "If unknown, say 'I don't recall'."
)


    # Generate response with limits to avoid repetition
    result = generator(
        prompt,
        max_length=100,       # limit token count
        do_sample=True,
        temperature=0.7,      # creativity control
        pad_token_id=50256    # ensures proper stopping for GPT-2 models
    )

    # Extract generated text
    text = result[0]["generated_text"]

    # Remove prompt from output
    answer = text.split("Answer:")[-1].strip()

    return answer
