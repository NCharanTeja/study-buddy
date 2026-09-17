"""Quiz agent: generates practice questions from indexed notes."""
import config
from groq import Groq

MODEL = config.GROQ_MODEL


class QuizAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def generate(self, topic, n=5, k=6):
        chunks = self.vectorstore.search(topic, k=k)
        if not chunks:
            return "_No content found on that topic in your notes._"
        material = "\n\n".join(c["text"] for c in chunks)
        prompt = (
            f"Create a {n}-question practice quiz on **{topic}** using the material below.\n\n"
            "Requirements:\n"
            "- Mix multiple-choice (4 options) and short-answer questions\n"
            "- Number the questions\n"
            "- After all questions, add an '### Answers' section with correct answers "
            "and one-line explanations\n\n"
            f"Material:\n{material}\n\nQuiz:"
        )
        resp = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1200,
        )
        return resp.choices[0].message.content
