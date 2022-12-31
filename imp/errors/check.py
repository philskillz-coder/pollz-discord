from typing import Dict, Any

class BetterCheckException(Exception):
    def __init__(self, **content):
        self.content: Dict[str, Any] = content

class HandeledCheckException(BetterCheckException):
    def __init__(self, original: BetterCheckException, **content):
        self.original = original
        super().__init__(**content)
