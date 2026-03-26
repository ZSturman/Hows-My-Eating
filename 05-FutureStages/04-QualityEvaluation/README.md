# Eating Quality Evaluation

## Overview

This stage transforms raw eating metrics into **interpretable quality scores** backed by nutritional science and behavioral research, providing actionable feedback for healthier eating habits.

## Status: 📋 TODO - Not Yet Implemented

This stage requires bite segmentation (Stage 02) and meal structure analysis (Stage 03) to be completed first.

## Motivation

Raw metrics like "2.5 bites/minute" are not immediately meaningful to users. This stage translates measurements into:
- **Quality scores**: 0-100 scale for eating pace, thoroughness, consistency
- **Health implications**: "Your fast eating pace may reduce satiety signals"
- **Comparisons**: "This meal was 30% faster than your usual lunch"
- **Trends**: "You've been eating more mindfully this week (+15%)"

The goal is to make eating behavior **visible, understandable, and improvable**.

## Proposed Quality Dimensions

### 1. Eating Pace Quality

**Metric**: `pace_score` (0-100)

Based on bites per minute and meal duration:
- **Optimal**: 3-5 bites/min, 15-25 min/meal → Score: 90-100
- **Acceptable**: 2-3 or 5-7 bites/min, 10-15 or 25-30 min → Score: 70-89
- **Fast**: >8 bites/min or <10 min/meal → Score: <50
- **Very slow**: <2 bites/min or >40 min/meal → Score: 60-80 (not harmful but unusual)

**Feedback Examples**:
- Score 95: "Excellent pace! You're giving your body time to feel full."
- Score 45: "This meal was quite fast. Try setting your fork down between bites."

### 2. Chew Thoroughness

**Metric**: `chew_quality_score` (0-100)

Based on estimated chews per bite:
- **Thorough**: 20-40 chews/bite → Score: 90-100
- **Adequate**: 10-20 chews/bite → Score: 70-89
- **Rushed**: <10 chews/bite → Score: <60

**Calculation**:
- Use peak detection within each bite to estimate chew cycles
- Average across all bites in meal
- Compare to recommended range (varies by food type)

**Feedback Examples**:
- Score 85: "Good chewing! This aids digestion and satiety."
- Score 55: "Try chewing each bite 25-30 times for better digestion."

### 3. Eating Consistency

**Metric**: `consistency_score` (0-100)

Based on regularity of bite intervals:
- **Steady rhythm**: Low variability (CV < 0.4) → Score: 90-100
- **Moderate**: CV 0.4-0.7 → Score: 70-89
- **Irregular**: CV > 0.7 (distracted eating) → Score: <60

**Feedback Examples**:
- Score 92: "You maintained a steady eating rhythm—great mindfulness!"
- Score 58: "Irregular pace suggests distractions. Try eating without screens."

### 4. Meal Mindfulness

**Metric**: `mindfulness_score` (0-100)

Composite score combining:
- Absence of long interruptions (>60 sec)
- Steady pace throughout meal (no acceleration at end)
- Appropriate duration for meal size

**Indicators of mindful eating**:
- No "front-loading" (rushing at start)
- Pauses are brief and intentional (sips, not phone)
- Pace doesn't increase toward end (sign of impatience)

**Feedback Examples**:
- Score 88: "Mindful eating detected—no signs of distraction."
- Score 50: "Detected acceleration toward end of meal. Finish with awareness."

## Scientific Foundations

### Mastication Research

1. **Mioche et al. (2004)**: "Variations in human masseter and temporalis muscle activity related to food texture during free and side-imposed mastication"
   - Chewing patterns vary by food hardness
   - Inadequate chewing reduces nutrient absorption
   - [DOI: 10.1016/j.archoralbio.2004.05.001](https://doi.org/10.1016/j.archoralbio.2004.05.001)

2. **Zhu & Hollis (2014)**: "Increasing the number of chews before swallowing reduces meal size in normal-weight, overweight, and obese adults"
   - 40 chews/bite reduces intake by ~12% vs. 15 chews/bite
   - Improved satiety hormones (GLP-1, CCK)
   - [DOI: 10.1016/j.physbeh.2014.03.002](https://doi.org/10.1016/j.physbeh.2014.03.002)

3. **Cassady et al. (2009)**: "Mastication of almonds: effects of lipid bioaccessibility, appetite, and hormone response"
   - Thorough chewing increases caloric extraction
   - Affects gut hormone release and satiety
   - [DOI: 10.3945/ajcn.2008.26669](https://doi.org/10.3945/ajcn.2008.26669)

### Eating Rate & Health Outcomes

1. **Ohkuma et al. (2015)**: Meta-analysis linking fast eating to obesity
   - 2x increased obesity risk for fast vs. slow eaters
   - Mechanism: Bypasses satiety signals (20-min delay)

2. **Shah et al. (2014)**: "Slower eating speed lowers energy intake in normal-weight but not overweight/obese subjects"
   - Slower eating reduces intake by 10-15% (88 fewer kcal/meal)
   - Effect mediated by fullness ratings

## Implementation Checklist

### Phase 1: Score Computation
- [ ] Implement `pace_score` calculation with research-backed thresholds
- [ ] Implement `chew_quality_score` (requires chew count estimation)
- [ ] Implement `consistency_score` from inter-bite interval variance
- [ ] Implement `mindfulness_score` composite metric
- [ ] Create overall `eating_quality_score` weighted average

### Phase 2: Contextual Adjustment
- [ ] Adjust scores by food type (soup vs. steak requires different pace)
- [ ] Adjust by meal type (breakfast naturally faster than dinner)
- [ ] Personalize to user's baseline (compare to their history, not just global norms)
- [ ] Add confidence intervals (low-quality data → lower confidence)

### Phase 3: Feedback Generation
- [ ] Create feedback message templates for each score range
- [ ] Generate actionable improvement suggestions
- [ ] Highlight positive behaviors (reinforcement)
- [ ] Avoid punitive language (growth mindset framing)

### Phase 4: Longitudinal Tracking
- [ ] Track scores over time (daily, weekly, monthly averages)
- [ ] Detect improvement trends ("Your pace score improved 12% this week!")
- [ ] Identify regression patterns (alert: "You've been rushing lunches lately")
- [ ] Generate monthly eating behavior summary report

## Expected Output Format

```json
{
  "meal_id": "meal_20250115_lunch",
  "quality_assessment": {
    "overall_score": 72,
    "overall_category": "good",
    "dimensions": {
      "pace": {
        "score": 68,
        "category": "acceptable",
        "metric_value": 6.2,
        "metric_unit": "bites/min",
        "feedback": "A bit fast for lunch. Try slowing down to 4-5 bites/min.",
        "recommendation": "Set your fork down between bites and chew each bite 25 times."
      },
      "thoroughness": {
        "score": 78,
        "category": "good",
        "metric_value": 18,
        "metric_unit": "chews/bite",
        "feedback": "Decent chewing, but could be more thorough.",
        "recommendation": "Aim for 25-30 chews per bite for optimal digestion."
      },
      "consistency": {
        "score": 85,
        "category": "excellent",
        "metric_value": 0.38,
        "metric_unit": "CV",
        "feedback": "Steady eating rhythm—great mindfulness!",
        "recommendation": "Keep up the consistent pace."
      },
      "mindfulness": {
        "score": 60,
        "category": "fair",
        "feedback": "Pace accelerated toward end of meal.",
        "recommendation": "Practice finishing meals with the same awareness as you started."
      }
    },
    "comparison": {
      "vs_your_average": -8,
      "vs_your_recent": -12,
      "interpretation": "This meal was 8% lower quality than your typical lunch."
    },
    "improvement_potential": 23,
    "top_priority": "Slow down eating pace"
  }
}
```

## Integration Points

- **Input**: Meal-level metrics from Stage 03
- **Output**: Quality scores and feedback for Stage 05 (real-time feedback)
- **UI Display**: Score visualizations, progress charts, trend graphs
- **Notifications**: Alerts when quality drops below personal baseline

## Hardware Requirements

**REQUIRED**: AirPods Pro or AirPods Max (same as previous stages)

## Estimated Implementation Effort

- **Score Algorithm Development**: 5-7 days
- **Feedback System**: 3-4 days
- **Longitudinal Tracking**: 3-4 days
- **UI/UX Integration**: 5-6 days
- **User Testing & Refinement**: 5-7 days
- **Total**: ~4-5 weeks

## Success Criteria

- **Score validity**: Correlates with expert nutritionist ratings (r > 0.7)
- **User comprehension**: >80% of users understand their scores
- **Actionability**: >70% of users can identify specific improvement actions
- **Engagement**: Users check scores after >50% of meals
- **Behavior change**: Measurable improvement in scores over 4-week period

## Ethical Considerations

- **Avoid eating disorders**: No harsh language, no punishment framing
- **Body positivity**: Focus on health behaviors, not weight outcomes
- **User autonomy**: Allow disabling of feedback/notifications
- **Privacy**: All data stays on-device, no cloud storage without consent
- **Medical disclaimer**: Not a replacement for professional nutritional advice

## Next Stage

See [05-RealtimeFeedback](../05-RealtimeFeedback/) for delivering interventions during eating to enable real-time behavior modification.
