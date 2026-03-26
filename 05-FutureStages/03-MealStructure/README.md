# Meal Structure Analysis

## Overview

This stage aggregates individual bites into **meal-level episodes** and analyzes eating patterns across the entire meal, including pace, consistency, and temporal structure.

## Status: 📋 TODO - Not Yet Implemented

This stage depends on bite segmentation (Stage 02) being completed first.

## Motivation

Meal-level analysis provides context that individual bites cannot:
- **Meal duration**: Total time from first to last bite
- **Eating pace**: Bites per minute, changes over time
- **Meal interruptions**: Long gaps suggesting conversation or breaks
- **Eating rhythm**: Regularity vs. irregularity of bite timing
- **Meal size proxy**: Total bite count and chewing duration

These insights enable:
- Comparison across meals (today vs. yesterday)
- Identification of rushed eating patterns
- Detection of mindful vs. distracted eating
- Longitudinal behavior tracking

## Proposed Technical Approach

### Algorithm: Meal Boundary Detection

**Method 1: Gap-Based Segmentation**
- Meal starts: First bite after long idle period (e.g., >10 minutes)
- Meal ends: Last bite before long idle period
- Simple, interpretable, no training required

**Method 2: Hidden Markov Model**
- States: {Pre-meal, Eating, Interruption, Post-meal}
- Emissions: Inter-bite intervals
- Learn transition probabilities from annotated meals
- More robust to variable-length breaks (phone call during meal)

**Method 3: Supervised Learning**
- Features: Inter-bite intervals, time of day, bite rate trend
- Labels: Meal boundaries from manual annotation
- Model: Sequence classifier (LSTM, CRF)
- Most flexible but requires substantial annotation effort

### Meal-Level Metrics

Once meals are segmented, compute:

1. **Duration Metrics**
   - `meal_duration`: First bite to last bite (seconds)
   - `active_eating_time`: Sum of all bite durations
   - `pause_time`: `meal_duration - active_eating_time`

2. **Pace Metrics**
   - `bites_per_minute`: `bite_count / (meal_duration / 60)`
   - `avg_inter_bite_interval`: Mean time between consecutive bites
   - `pace_variability`: Standard deviation of inter-bite intervals

3. **Pattern Metrics**
   - `eating_rhythm_score`: How regular are bite intervals? (inverse of CV)
   - `front_loading`: Ratio of early bites vs. late bites (rushed start?)
   - `interruption_count`: Number of gaps >30 seconds during meal

4. **Temporal Features**
   - `time_of_day`: Breakfast, lunch, dinner classification
   - `day_of_week`: Weekday vs. weekend patterns
   - `meal_number`: 1st, 2nd, 3rd meal of the day

## Scientific References

### Eating Pace Research

1. **Robinson et al. (2014)**: "Eating attentively: a systematic review and meta-analysis of the effect of food intake memory and awareness on eating"
   - Distracted eating leads to increased consumption
   - Slower eating associated with better satiety signals
   - [DOI: 10.3945/ajcn.114.086223](https://doi.org/10.3945/ajcn.114.086223)

2. **Ohkuma et al. (2015)**: "Association between eating rate and obesity: a systematic review and meta-analysis"
   - Fast eating strongly associated with obesity risk
   - Slower eaters consume 10-15% fewer calories on average
   - [DOI: 10.1038/ijo.2015.96](https://doi.org/10.1038/ijo.2015.96)

3. **Viskaal-van Dongen et al. (2011)**: "Eating rate of commonly consumed foods promotes food and energy intake"
   - Quantified eating rates for different food types
   - Eating rate influences satiety and fullness
   - [DOI: 10.1016/j.appet.2010.09.002](https://doi.org/10.1016/j.appet.2010.09.002)

### Key Findings

- **Recommended pace**: 10-20 minutes per meal minimum
- **Bite rate**: 3-5 bites/minute considered healthy
- **Fast eating threshold**: >8 bites/minute or <10 min/meal
- **Interruptions**: Normal meals have 1-2 brief pauses (sips, conversation)

## Implementation Checklist

### Phase 1: Meal Segmentation
- [ ] Implement gap-based meal boundary detection
- [ ] Add configurable `meal_gap_threshold` (default: 10 minutes)
- [ ] Create `Meal` data structure (start, end, bite_list)
- [ ] Handle edge cases (incomplete meals at session boundaries)

### Phase 2: Metric Computation
- [ ] Compute duration metrics per meal
- [ ] Compute pace metrics per meal
- [ ] Compute pattern metrics per meal
- [ ] Generate meal summary JSON

### Phase 3: Visualization
- [ ] Create bite timeline plot with meal boundaries
- [ ] Plot inter-bite interval distribution
- [ ] Show eating pace over time (within meal)
- [ ] Generate meal comparison charts (day-to-day)

### Phase 4: Advanced Analytics
- [ ] Detect anomalous eating patterns (too fast, irregular)
- [ ] Classify meal types (breakfast, lunch, dinner) by time and duration
- [ ] Track weekly eating behavior trends
- [ ] Generate personalized "eating profile" summary

## Expected Output Format

```json
{
  "session_date": "2025-01-15",
  "meals": [
    {
      "meal_id": "meal_001",
      "meal_type": "breakfast",
      "start_time": "08:15:30",
      "end_time": "08:28:45",
      "duration_sec": 795,
      "bite_count": 18,
      "bites_per_minute": 1.36,
      "avg_inter_bite_interval": 42.1,
      "pace_variability": 18.3,
      "interruption_count": 1,
      "eating_rhythm_score": 0.72,
      "pace_category": "slow",
      "notes": "Healthy pace, steady rhythm"
    },
    {
      "meal_id": "meal_002",
      "meal_type": "lunch",
      "start_time": "12:40:15",
      "end_time": "12:48:20",
      "duration_sec": 485,
      "bite_count": 22,
      "bites_per_minute": 2.72,
      "avg_inter_bite_interval": 21.0,
      "pace_variability": 9.4,
      "interruption_count": 0,
      "eating_rhythm_score": 0.89,
      "pace_category": "fast",
      "notes": "Fast eating detected - consider slowing down"
    }
  ],
  "daily_summary": {
    "total_meals": 2,
    "total_bites": 40,
    "avg_meal_duration": 640,
    "avg_pace": "moderate",
    "fast_meal_count": 1
  }
}
```

## Integration Points

- **Input**: Bite-level data from Stage 02
- **Output**: Meal-level summaries for Stage 04 (quality evaluation)
- **Real-time display**: Live meal timer and pace indicator in app
- **Historical tracking**: Store meal summaries for longitudinal analysis

## Hardware Requirements

**REQUIRED**: AirPods Pro or AirPods Max (same as previous stages)

## Estimated Implementation Effort

- **Algorithm Development**: 4-6 days
- **Metric Computation**: 2-3 days
- **Visualization Tools**: 3-4 days
- **Integration & Testing**: 2-3 days
- **Total**: ~2-3 weeks

## Success Criteria

- **Meal boundary accuracy**: >90% agreement with manual labels
- **Pace estimation**: Within ±0.5 bites/minute of video-measured pace
- **Pattern detection**: Correctly identifies "fast" vs. "slow" meals
- **Scalability**: Process 1 week of data (20+ meals) in <10 seconds

## Next Stage

See [04-QualityEvaluation](../04-QualityEvaluation/) for assessing eating quality and providing actionable feedback.
