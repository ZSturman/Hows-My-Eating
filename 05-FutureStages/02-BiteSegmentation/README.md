# Bite Segmentation

## Overview

This stage focuses on extracting **individual bite events** from continuous chewing detection signals. Rather than binary chewing/not-chewing, this stage identifies discrete bite boundaries with temporal information.

## Status: 📋 TODO - Not Yet Implemented

This is a planned future capability that builds on the binary chewing detection foundation.

## Motivation

Understanding bite-level behavior unlocks:
- **Bite counting**: How many bites per meal?
- **Bite duration**: How long does each bite last?
- **Inter-bite intervals**: Time between bites (eating pace)
- **Bite patterns**: Rhythmic vs. irregular eating

These metrics are fundamental for understanding eating behavior and providing meaningful feedback.

## Proposed Technical Approach

### Algorithm: Temporal Clustering with Gap Detection

1. **Input**: Continuous chewing probability signal from binary detector
2. **Threshold**: Apply hysteresis to identify chewing periods
3. **Gap Detection**: Segment continuous chewing into bites when gaps exceed threshold
   - Typical inter-bite gap: 2-5 seconds
   - Configurable `min_gap_sec` parameter (start with 3.0 seconds)
4. **Bite Extraction**: Each segment becomes a bite event with:
   - `start_time`: Beginning of bite
   - `end_time`: End of bite
   - `duration`: `end_time - start_time`
   - `chew_count_estimate`: Number of individual chews (from peaks)
   - `confidence`: Average probability during bite

### Alternative Approaches

- **DBSCAN Clustering**: Cluster chewing timestamps with temporal distance metric
- **Hidden Markov Model**: Model state transitions (idle → bite → gap → bite → meal end)
- **Peak Detection**: Identify individual chew cycles within bite, then cluster into bites
- **Learning-based**: Train separate bite boundary detector (requires bite-level annotations)

### Validation Strategy

Annotate subset of data with manual bite labels (video review) to evaluate:
- **Bite count accuracy**: Predicted vs. actual bite count per meal
- **Boundary precision**: How close are predicted bite boundaries to ground truth?
- **Sensitivity analysis**: How does `min_gap_sec` affect performance?

## Scientific References

### Bite Detection in Literature

1. **Dong et al. (2012)**: "A New Method for Measuring Meal Intake in Humans via Automated Wrist Motion Tracking"
   - Used wrist-worn accelerometers to detect hand-to-mouth gestures
   - Achieved ~80% bite detection accuracy
   - [DOI: 10.1016/j.appet.2012.04.014](https://doi.org/10.1016/j.appet.2012.04.014)

2. **Fontana et al. (2015)**: "Automatic Ingestion Monitor: A Novel Wearable Device for Monitoring of Ingestive Behavior"
   - Sensor-based bite detection and classification
   - Focus on temporal patterns of eating
   - [DOI: 10.1109/TBME.2014.2383121](https://doi.org/10.1109/TBME.2014.2383121)

3. **Kyritsis et al. (2019)**: "Modeling Wrist Micromovements to Measure In-Meal Eating Behavior from Inertial Sensor Data"
   - IMU-based bite detection with high temporal resolution
   - Validated against video ground truth
   - [DOI: 10.1109/JBHI.2019.2892011](https://doi.org/10.1109/JBHI.2019.2892011)

### Key Findings from Literature

- Inter-bite intervals typically range from 2-8 seconds in healthy eating
- Bite duration averages 10-20 seconds including chewing and swallowing
- Faster eating (shorter intervals) associated with overconsumption
- Individual chew cycles occur at 1-2 Hz (60-120 chews/minute)

## Implementation Checklist

### Phase 1: Basic Segmentation
- [ ] Implement gap-based bite segmentation algorithm
- [ ] Add configurable `min_gap_sec` parameter
- [ ] Extract bite timestamps and durations
- [ ] Create `Bite` data structure (start, end, duration, confidence)

### Phase 2: Validation
- [ ] Annotate 10-20 meals with manual bite labels (video review)
- [ ] Compute bite count accuracy
- [ ] Measure temporal boundary precision
- [ ] Tune `min_gap_sec` parameter

### Phase 3: Integration
- [ ] Add bite segmentation to pipeline (`02-DataPipeline/scripts/segment_bites.py`)
- [ ] Update real-time app to display live bite count
- [ ] Export bite-level CSV (one row per bite)
- [ ] Create visualization tools (bite timeline plots)

### Phase 4: Advanced Features
- [ ] Estimate individual chew count within each bite (peak detection)
- [ ] Detect "sipping" vs. "chewing" bites (liquid vs. solid)
- [ ] Classify bite types (e.g., small/medium/large based on duration)

## Expected Output Format

```json
{
  "meal_id": "session_20251215_123456",
  "bites": [
    {
      "bite_id": 1,
      "start_time": 10.5,
      "end_time": 25.3,
      "duration": 14.8,
      "chew_count_estimate": 18,
      "avg_confidence": 0.87
    },
    {
      "bite_id": 2,
      "start_time": 30.1,
      "end_time": 42.7,
      "duration": 12.6,
      "chew_count_estimate": 15,
      "avg_confidence": 0.91
    }
  ]
}
```

## Hardware Requirements

**REQUIRED**: AirPods Pro or AirPods Max (same as binary detection)

## Estimated Implementation Effort

- **Algorithm Development**: 3-5 days
- **Validation Dataset Creation**: 2-3 days
- **Integration & Testing**: 2-3 days
- **Total**: ~1-2 weeks

## Success Criteria

- **Bite count accuracy**: ±10% of manual count
- **False positive rate**: <5% (spurious bites detected)
- **False negative rate**: <10% (missed bites)
- **Real-time capable**: Process 1 minute of data in <1 second

## Next Stage

See [03-MealStructure](../03-MealStructure/) for aggregating bites into meal-level analytics.
