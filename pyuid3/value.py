# AUTOGENERATED! DO NOT EDIT! File to edit: src/value.ipynb (unless otherwise specified).

__all__ = ['Value']

# Cell
class Value:
    def __init__(self, name: str, confidence: float):
        self.confidence = confidence
        self.name = name

    def get_name(self) -> str:
        return self.name

    def get_confidence(self) -> float:
        return self.confidence

    def __str__(self) -> str:
        return self.get_name() + '[' + str(round(self.get_confidence() * 100.0) / 100.0) + ']'

    def __eq__(self, other: 'Value') -> bool:
        return self.name == other.get_name()
