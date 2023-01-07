from hashids import Hashids


class BetterHashids:
    def __init__(self, hashids: Hashids):
        self.hashids = hashids

    def encode(self, value: int) -> str:
        return self.hashids.encode(value)
