# Real-Time Feedback & Intervention

## Overview

The final stage: delivering **live, in-the-moment feedback** during eating to enable immediate behavior modification. This closes the loop from detection → analysis → quality assessment → **actionable intervention**.

## Status: 📋 TODO - Not Yet Implemented

This is the culmination of all previous stages and represents the full vision of ChewSense as a behavior-change tool.

## Motivation

Post-meal feedback ("You ate too fast 20 minutes ago") is interesting but limited. Real-time feedback during the meal:
- **Interrupts unhealthy patterns** before they complete
- **Reinforces positive behaviors** in the moment
- **Builds awareness** through immediate cause-effect
- **Enables habit formation** via timely reinforcement

**Example**: User eating quickly → Gentle haptic + notification at bite 10: "You're eating fast. Try slowing down." → User adjusts → Improved behavior that meal.

## Proposed Intervention Design

### When to Intervene?

**Triggering Conditions**:
1. **Fast eating detected**: Pace >7 bites/min for 3+ consecutive bites
2. **Insufficient chewing**: <12 chews/bite for 5+ consecutive bites
3. **Distracted eating**: Irregular pace pattern (CV > 0.8)
4. **Front-loading**: First 5 bites too rapid (<15 sec intervals)
5. **Meal completion**: Final bite → Provide summary

**Timing Principles**:
- **Early intervention**: Trigger within first 1/3 of meal when behavior is still malleable
- **Not too frequent**: Max 1 intervention per 3 minutes (avoid annoyance)
- **Context-aware**: Suppress if user explicitly swiped away previous feedback
- **Escalation**: Subtle first (haptic), then visual, then audio if ignored

### Intervention Modalities

#### 1. Haptic Feedback (Least Intrusive)
- **Gentle double-tap**: "You're doing great, keep it up"
- **Firm single pulse**: "Slow down reminder"
- **Triple tap**: "Check your pace"

**Pros**: Non-disruptive, private, immediate
**Cons**: Easy to ignore, limited information bandwidth

#### 2. Visual Notifications (Moderate)
- **Banner notification**: "Eating pace: Fast. Try slowing down."
- **Lock screen card**: Brief message with current pace
- **Apple Watch complication**: Live pace indicator

**Pros**: Clear message, user can dismiss
**Cons**: Requires looking at device (not always practical mid-meal)

#### 3. Audio Cues (Most Intrusive)
- **Gentle chime**: "Reminder: chew thoroughly"
- **Voice prompt**: "You're at 8 bites per minute. Slow to 5."
- **AirPods spatial audio**: Directional reminder (futuristic)

**Pros**: Doesn't require visual attention
**Cons**: Socially awkward in public, can be annoying

#### 4. Hybrid Approach (Recommended)
- **Default**: Haptic + visual
- **User config**: Enable/disable each modality
- **Smart mode**: Haptic-only in public (detected via location/calendar), visual at home

### Feedback Messages

**Positive Reinforcement** (when doing well):
- "Great pace! You're at 4 bites/min."
- "Thorough chewing detected—keep it up!"
- "Steady rhythm—mindful eating in action."

**Gentle Reminders** (when pace increases):
- "You've sped up a bit. Try slowing down."
- "Remember to chew each bite 25 times."
- "Take a breath between bites."

**Actionable Guidance** (when significantly off-track):
- "Current pace: 9 bites/min. Goal: 5 bites/min. Put your fork down."
- "Chew count low. Focus on texture and flavor."
- "Interrupted rhythm. Minimize distractions if possible."

**End-of-Meal Summary**:
- "Meal complete! Pace: 72/100, Thoroughness: 85/100. Nice job on chewing."
- "Finished in 8 minutes (goal: 15 min). Tomorrow, try slowing down."

## Technical Architecture

### Real-Time Processing Pipeline

```
AirPods Motion Data (50 Hz)
   ↓
Feature Extraction (0.75s windows, 0.1s step)
   ↓
Binary Chewing Detection (CoreML inference)
   ↓
Bite Segmentation (gap detection)
   ↓
Live Meal Analysis (pace, chew count, rhythm)
   ↓
Quality Assessment (score computation)
   ↓
Intervention Logic (trigger evaluation)
   ↓
Feedback Delivery (haptic/visual/audio)
```

**Latency Requirements**:
- Feature extraction to inference: <20ms
- Bite detection: <500ms after bite ends
- Intervention decision: <1 second
- Total loop: <2 seconds from behavior to feedback

### Intervention State Machine

```
States:
- IDLE: Not eating
- MONITORING: Eating in progress, observing
- WARNED: Intervention triggered, waiting for response
- REINFORCED: Positive behavior, providing encouragement
- SUPPRESSED: User dismissed feedback, temporarily silent

Transitions:
- IDLE → MONITORING: First bite detected
- MONITORING → WARNED: Unhealthy pattern detected
- WARNED → MONITORING: User adjusts behavior
- WARNED → SUPPRESSED: User dismisses notification
- MONITORING → REINFORCED: Healthy behavior detected
- REINFORCED → MONITORING: After positive feedback delivered
- MONITORING → IDLE: Meal ends (no bites for 10+ minutes)
```

## Scientific Foundations

### Just-In-Time Adaptive Interventions (JITAI)

1. **Nahum-Shani et al. (2018)**: "Just-in-Time Adaptive Interventions (JITAIs) in Mobile Health: Key Components and Design Principles"
   - Framework for delivering timely, context-sensitive interventions
   - Effectiveness depends on timing, relevance, and user burden
   - [DOI: 10.1007/s12160-016-9830-8](https://doi.org/10.1007/s12160-016-9830-8)

2. **Spruijt-Metz & Nilsen (2014)**: "Dynamic Models of Behavior for Just-in-Time Adaptive Interventions"
   - Real-time interventions more effective than delayed feedback
   - Requires balancing immediacy with user annoyance

### Behavior Change Techniques

1. **Michie et al. (2013)**: "The behavior change technique taxonomy (v1) of 93 hierarchically clustered techniques"
   - Relevant techniques: Self-monitoring, feedback, prompts/cues
   - [DOI: 10.1007/s12160-013-9486-6](https://doi.org/10.1007/s12160-013-9486-6)

2. **Fogg Behavior Model**: B = M × A × P (Motivation × Ability × Prompt)
   - Intervention = Prompt at high motivation + high ability moment
   - Timing is critical (mid-meal when user can still adjust)

## Implementation Checklist

### Phase 1: Intervention Logic
- [ ] Implement trigger conditions (fast pace, low chew count, etc.)
- [ ] Build intervention state machine
- [ ] Add cooldown timers (prevent spam)
- [ ] Create user preference system (enable/disable modalities)

### Phase 2: Feedback Delivery
- [ ] Integrate haptic feedback API (UIFeedbackGenerator)
- [ ] Implement local notifications (UNUserNotificationCenter)
- [ ] Add Apple Watch complications support
- [ ] Build in-app feedback overlay (non-intrusive)

### Phase 3: Message Generation
- [ ] Create message templates (positive, reminder, guidance)
- [ ] Implement dynamic message selection based on context
- [ ] Add personalization (use user's name, reference goals)
- [ ] Localization support (multi-language)

### Phase 4: User Control
- [ ] Build settings page (feedback preferences)
- [ ] Add "Do Not Disturb" mode (manual or scheduled)
- [ ] Implement dismissal tracking (learn when to stay quiet)
- [ ] Create feedback history log (review past interventions)

### Phase 5: Evaluation
- [ ] A/B test: Feedback vs. no feedback (measure behavior change)
- [ ] User satisfaction survey (annoyance vs. helpfulness)
- [ ] Measure adherence (% of meals with feedback enabled)
- [ ] Longitudinal study: Sustained behavior change over 8+ weeks

## Expected User Experience

**Scenario: Lunch on a busy workday**

```
12:30 PM - User starts eating while checking email
12:31 PM - ChewSense detects first bite
12:32 PM - Bite #5 detected, pace = 8.5 bites/min (fast)
12:33 PM - [Haptic + Notification] "You're eating quickly. Try slowing down."
12:33 PM - User sees notification, puts phone away
12:34 PM - Pace decreases to 5 bites/min
12:35 PM - [Haptic + Notification] "Great adjustment! Steady pace."
12:42 PM - Last bite detected
12:42 PM - [Summary] "Meal complete in 12 min. Pace: 75/100. Nice recovery!"
```

**Scenario: Dinner at home**

```
6:45 PM - User starts eating at dining table
6:46 PM - Steady pace detected (4 bites/min)
6:48 PM - [Haptic] "Excellent pace—keep it up!"
6:55 PM - Meal ends naturally
6:55 PM - [Summary] "Perfect dinner! Pace: 92/100, Thoroughness: 88/100."
```

## Integration Points

- **Input**: Real-time quality scores from Stage 04
- **Output**: Notifications to user, behavior change logs
- **Data storage**: Intervention history for analysis
- **HealthKit**: Export eating behavior metrics (with user permission)

## Hardware Requirements

**REQUIRED**: 
- AirPods Pro or AirPods Max (motion sensors)
- iPhone/Mac with notification support
- Optional: Apple Watch for richer feedback

## Estimated Implementation Effort

- **Intervention Logic**: 4-5 days
- **Feedback System**: 5-7 days
- **User Controls & Settings**: 3-4 days
- **Testing & Refinement**: 7-10 days
- **User Studies**: 4-6 weeks (ongoing)
- **Total**: ~4-6 weeks development + studies

## Success Criteria

- **Behavior change**: ≥15% improvement in quality scores over 4 weeks
- **User acceptance**: ≥70% enable feedback after trying it
- **Engagement**: ≥60% of meals with feedback active
- **Annoyance**: <20% find feedback "too intrusive"
- **Sustained use**: ≥50% still using after 8 weeks

## Privacy & Ethics

- **Data ownership**: All data stored locally by default
- **Consent**: Explicit opt-in for any data sharing
- **Transparency**: User can see all intervention logic and scores
- **Opt-out**: Easy to disable feedback without losing tracking
- **Eating disorders**: Screen for disordered eating patterns, provide resources
- **Medical advice**: Clear disclaimers that this is not medical device

## Future Enhancements

- **Social features**: Share goals with friends (opt-in)
- **Gamification**: Badges for streaks of mindful eating
- **Personalization**: ML learns optimal intervention timing per user
- **Integration**: Sync with nutrition apps (MyFitnessPal, Lose It!)
- **Wearable expansion**: Support for other devices (Samsung, Garmin, etc.)

## Conclusion

This final stage transforms ChewSense from a passive detection system into an active **behavior change partner**. By delivering timely, relevant, and respectful feedback, the system empowers users to develop healthier eating habits through awareness and gentle guidance.

---

**Full ChewSense Pipeline**: Binary Detection → Bite Segmentation → Meal Structure → Quality Evaluation → **Real-Time Feedback** ✅
