"""Retriever agent: RAG-based question answering."""
import config
from groq import Groq

MODEL = config.GROQ_MODEL


class RetrieverAgent:
    """Retrieves relevant chunks and answers a user question using an LLM."""

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def answer(self, question, k=4, history=None):
        """Answer a question grounded in retrieved chunks.

        Args:
            question: the user's question.
            k: number of chunks to retrieve.
            history: optional list of previous turns as dicts with "q" and "a"
                keys (e.g. {"q": "...", "a": "..."}). The last few turns are
                replayed to the LLM so follow-up questions work.
        """
        chunks = self.vectorstore.search(question, k=k)
        if not chunks:
            return "I couldn't find anything relevant in your uploaded notes.", []
        context = "\n\n---\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )
        messages = [
            {"role": "system", "content": (
                "You are a study assistant. Answer the student's latest question "
                "using ONLY the context provided in that message. If the context "
                "doesn't contain the answer, say so honestly. Earlier messages are "
                "previous turns of the conversation — use them to resolve follow-ups "
                "(e.g. 'explain that again', 'what about the second one')."
            )},
        ]
        for turn in (history or [])[-4:]:
            messages.append({"role": "user", "content": turn["q"]})
            messages.append({"role": "assistant", "content": turn["a"]})
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        })
        resp = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=500,
        )
        return resp.choices[0].message.content, chunks
