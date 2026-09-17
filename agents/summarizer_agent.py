"""Summarizer agent: produces structured summaries of a topic from indexed notes."""
import config
from groq import Groq

MODEL = config.GROQ_MODEL


class SummarizerAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def summarize(self, topic, k=6):
        chunks = self.vectorstore.search(topic, k=k)
        if not chunks:
            return "_No content found on that topic in your notes._"
        material = "\n\n".join(c["text"] for c in chunks)
        prompt = (
            f"You are a study summarizer. Create a clear, structured summary of the "
            f"following material about **{topic}**.\n\n"
            "Structure the summary as:\n"
            "1. A one-sentence definition/overview\n"
            "2. Key points (as bullet points)\n"
            "3. Important terms in **bold**\n"
            "4. A short 'Why it matters' section\n\n"
            f"Material:\n{material}\n\nSummary:"
        )
        resp = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=700,
        )
        return resp.choices[0].message.content
