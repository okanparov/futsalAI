"""0-99 rating system.

Girdi: 0-1 araliginda normalize edilmis bilesenler; eksik (None/yok) bilesenler
atlanir, kalan agirliklar yeniden normalize edilir.
"""

OVERALL_WEIGHTS = {
    "defensive": 0.30, "offensive": 0.25, "positioning": 0.20,
    "ball_interaction": 0.15, "physical": 0.10,
}

POSITION_WEIGHTS = {
    "kaleci": {"shot_saves": 0.40, "pass_accuracy": 0.30, "distribution": 0.20, "positioning": 0.10},
    "defans": {"tackles_won": 0.35, "interceptions": 0.25, "pass_accuracy": 0.20, "positioning": 0.20},
    "orta saha": {"pass_accuracy": 0.30, "ball_recovery": 0.25, "positioning": 0.25, "tackles_interceptions": 0.20},
    "forvard": {"shots_on_target": 0.35, "pass_accuracy": 0.20, "ball_control": 0.25, "positioning": 0.20},
}

# Normalizasyon referanslari (futsal icin kaba degerler, ayarlanabilir)
REFERENCE_DISTANCE_M = 3000.0


def normalize_distance(distance_m, reference=REFERENCE_DISTANCE_M):
    return max(0.0, min(1.0, distance_m / reference))


def weighted_score(components, weights):
    """Mevcut bilesenler uzerinden agirlikli ortalama (0-1); hic yoksa None."""
    avail = {k: w for k, w in weights.items() if components.get(k) is not None}
    total = sum(avail.values())
    if total == 0:
        return None
    return sum(components[k] * w for k, w in avail.items()) / total


class RatingSystem:
    def calculate(self, components, position=None):
        """components: dict 0-1. position verilirse pozisyon agirliklari, yoksa genel formul.
        Donus: int 0-99 ya da hesaplanamazsa None."""
        weights = POSITION_WEIGHTS.get((position or "").lower(), OVERALL_WEIGHTS)
        score = weighted_score(components, weights)
        if score is None:
            return None
        return int(round(max(0.0, min(1.0, score)) * 99))

    def from_match_stats(self, summary, position=None):
        """StatsCalculator.summary ciktisindan reyting. Su an yalnizca
        konumlanma (saha kapsami) ve fiziksel (mesafe) mevcut."""
        components = {
            "positioning": summary.get("coverage"),
            "physical": normalize_distance(summary.get("distance_covered", 0.0)),
        }
        return self.calculate(components, position)
