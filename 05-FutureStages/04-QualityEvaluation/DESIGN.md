# Chewing Quality Evaluation - Technical Design

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   MealMetrics + BiteEvents                       │
│               (from MealAnalyzer + BiteDetector)                 │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ChewQualityEvaluator                          │
│                                                                  │
│  ┌──────────────┐   ┌────────────────┐   ┌───────────────────┐  │
│  │    Pace      │   │  Thoroughness  │   │    Rhythm         │  │
│  │   Evaluator  │   │   Evaluator    │   │   Evaluator       │  │
│  └──────────────┘   └────────────────┘   └───────────────────┘  │
│         │                   │                     │              │
│         ▼                   ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    ChewQualityMetrics                        ││
│  │                                                              ││
│  │  Scores: 0-100 for each category                            ││
│  │  Ratings: EXCELLENT / GOOD / FAIR / NEEDS_IMPROVEMENT       ││
│  │  Recommendations: Personalized suggestions                   ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Health Guidelines Reference

### Chewing Recommendations
| Source | Recommendation |
|--------|----------------|
| Mindful eating | 20-30 chews per bite |
| Dental health | Thorough chewing for digestion |
| Weight management | Slow eating (20+ min meals) |

### Optimal Pace
| Metric | Target Range | Source |
|--------|--------------|--------|
| Meal duration | 20-30 minutes | Mindful eating guidelines |
| Inter-bite interval | 5-15 seconds | Eating pace research |
| Chews per bite | 20-30 | Mastication research |

## Scoring System

### Pace Score (30% of total)
```python
def score_pace(avg_ibi: float) -> float:
    """Score eating pace (higher = better)."""
    TARGET_MIN = 5.0   # seconds
    TARGET_MAX = 15.0  # seconds
    
    if TARGET_MIN <= avg_ibi <= TARGET_MAX:
        return 100.0
    elif avg_ibi < TARGET_MIN:
        # Too fast: 0 at 0s, 100 at 5s
        return max(0, (avg_ibi / TARGET_MIN) * 100)
    else:
        # Too slow: gradually decrease (but slow is generally okay)
        return max(50, 100 - (avg_ibi - TARGET_MAX) * 2)
```

### Thoroughness Score (40% of total)
```python
def score_thoroughness(bites: List[BiteEvent]) -> float:
    """Score chewing thoroughness."""
    chew_counts = [b.chew_count for b in bites if b.chew_count]
    
    if not chew_counts:
        return 50.0  # Unknown, neutral score
    
    avg_chews = np.mean(chew_counts)
    TARGET_MIN = 20
    TARGET_MAX = 30
    
    if TARGET_MIN <= avg_chews <= TARGET_MAX:
        return 100.0
    elif avg_chews < TARGET_MIN:
        return max(0, (avg_chews / TARGET_MIN) * 100)
    else:
        return max(80, 100 - (avg_chews - TARGET_MAX) * 2)
```

### Rhythm Score (30% of total)
```python
def score_rhythm(ibis: np.ndarray) -> float:
    """Score eating rhythm consistency."""
    cv = np.std(ibis) / np.mean(ibis)  # Coefficient of variation
    
    # Lower CV = more consistent = better
    if cv < 0.3:
        return 100.0
    elif cv < 0.5:
        return 80.0
    elif cv < 0.7:
        return 60.0
    else:
        return 40.0
```

## Rating Thresholds

| Score | Rating |
|-------|--------|
| 85-100 | EXCELLENT |
| 70-84 | GOOD |
| 50-69 | FAIR |
| 0-49 | NEEDS_IMPROVEMENT |

## Recommendation Engine

Based on weak areas, generate personalized suggestions:

```python
RECOMMENDATIONS = {
    FeedbackArea.PACE: {
        "low": "Try to slow down between bites. Put your utensil down after each bite.",
        "high": "Your pace is good, but try to stay consistent throughout the meal."
    },
    FeedbackArea.THOROUGHNESS: {
        "low": "Try chewing each bite 20-30 times before swallowing.",
        "high": "Great job chewing thoroughly!"
    },
    FeedbackArea.RHYTHM: {
        "low": "Try to maintain a more consistent eating pace.",
        "high": "Your eating rhythm is excellent."
    }
}
```

## Output Format

```json
{
  "overall_score": 78,
  "overall_rating": "GOOD",
  "categories": {
    "pace": {
      "score": 85,
      "rating": "EXCELLENT",
      "avg_ibi": 8.2,
      "details": "Your eating pace is in the optimal range"
    },
    "thoroughness": {
      "score": 65,
      "rating": "FAIR",
      "avg_chews_per_bite": 15,
      "rushed_bites_percent": 22,
      "details": "Some bites could use more chewing"
    },
    "rhythm": {
      "score": 82,
      "rating": "GOOD",
      "consistency_score": 0.72,
      "details": "Your eating pace is fairly consistent"
    }
  },
  "recommendations": [
    "Try chewing each bite 20-30 times before swallowing.",
    "You're doing great with pace - keep it up!"
  ]
}
```

## Integration

- Input: `MealMetrics`, `List[BiteEvent]`
- Output: `ChewQualityMetrics`
- UI Integration: Display scores, ratings, and recommendations
- Tracking: Store historical quality metrics for trend analysis
