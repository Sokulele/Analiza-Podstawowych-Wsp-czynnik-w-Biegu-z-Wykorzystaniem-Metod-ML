"""Etap 7 — moduł rekomendacji biegowych.

Reguły kodowane ręcznie na podstawie literatury biomechanicznej (NIE uczone z danych).
Czyta JSON-y wygenerowane przez `src/coefficients/analyze.py`
(temporal, spatial, symmetry, meta) i zwraca listę rekomendacji.
"""
from .rules import (
    Recommendation,
    generate_recommendations,
)

__all__ = ["Recommendation", "generate_recommendations"]
