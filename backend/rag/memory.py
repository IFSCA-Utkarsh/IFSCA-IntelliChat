import asyncio
from typing import List

class AsyncConversationMemory:
    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.history: List[str] = []
        self.lock = asyncio.Lock()

    async def add_exchange(self, question: str):
        async with self.lock:
            self.history.append(question)
            if len(self.history) > self.max_turns:
                self.history.pop(0)

    async def get_history_text(self) -> str:
        async with self.lock:
            return "\n".join(self.history) if self.history else "None"

    async def clear(self):
        async with self.lock:
            self.history.clear()