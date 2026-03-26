# Project History

This directory contains the initial prototype and development evolution of ChewSense, preserved to document the iterative engineering process.

## InitialPrototype/

The `InitialPrototype/` folder (originally "Hows My Eating") contains the **first working version** of the chewing detection system. This early work demonstrates:

- **Initial exploration**: Experimental approaches to motion-based eating detection
- **Iteration process**: Multiple versions (V1, Stage2-New, etc.) showing refinement
- **Learning journey**: Technical notes documenting problem-solving and decisions
- **Foundation building**: Core concepts that informed the current architecture

### Why Keep This?

1. **Demonstrates depth of work**: Shows the project evolved through substantial R&D, not just a quick implementation
2. **Engineering process**: Documents decision-making, dead ends, and breakthroughs
3. **Portfolio value**: Illustrates iterative development skills and technical problem-solving
4. **Reference material**: May contain ideas or approaches useful for future enhancements

### What Changed?

**From Initial Prototype → Current System**:
- **Data collection**: Manual recording → Dedicated iOS app with sync
- **Labeling**: Post-hoc annotation → Real-time video-synchronized marking
- **Training**: Ad-hoc scripts → Orchestrated pipeline with W&B tracking
- **Deployment**: Notebook-based → Professional CoreML export + real-time app
- **Architecture**: Experimental → Production-ready with clear lifecycle stages

## Development Timeline

### Phase 1: Initial Exploration (Early 2024)
- Proof of concept: Can AirPods motion detect chewing?
- Manual data collection and labeling
- Simple ML models (logistic regression, basic neural nets)
- Result: **Yes, detectable!**

### Phase 2: Iteration & Refinement (Mid 2024)
- Multiple architectural experiments (see InitialPrototype/ versions)
- Feature engineering trials
- Labeling workflow improvements
- Result: **Identified optimal approach**

### Phase 3: Production System (Late 2024)
- Built dedicated data collection iOS app
- Implemented soft-label generation for smooth training targets
- Created end-to-end pipeline with proper orchestration
- Added experiment tracking (W&B)
- Published data collection app to App Store

### Phase 4: Future Vision (2025+)
- Planned hierarchical analysis (bites → meals → quality → feedback)
- Comprehensive documentation and staging
- Open-source preparation
- Research reproducibility focus

## Key Learnings

1. **Hard labels insufficient**: Binary 0/1 labels caused unstable training. Soft labels with temporal ramps solved this.

2. **Feature selection critical**: Initial attempts with raw accelerometer data failed. Engineered features (magnitude, RMS, frequency components) essential.

3. **Temporal smoothing required**: Raw model predictions too noisy for UI. State machine with hysteresis provides stable user experience.

4. **Data quality matters**: Synchronized video labeling far superior to post-hoc annotation from memory.

5. **End-to-end thinking**: Early prototypes had gaps between components. Unified pipeline reduces errors and improves reproducibility.

## Project Evolution Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Proof of Concept                                        │
│ - Manual data collection                                         │
│ - Jupyter notebooks for analysis                                 │
│ - Basic binary classification                                    │
│ - Result: "It works!"                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ Phase 2: Iteration (InitialPrototype/)                           │
│ - Multiple architecture experiments                              │
│ - Feature engineering                                            │
│ - Labeling workflow improvements                                 │
│ - Result: "Here's the best approach"                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ Phase 3: Production System (Current Repo)                        │
│ - Dedicated iOS data collection app (App Store)                  │
│ - End-to-end Python pipeline with W&B                            │
│ - Real-time iOS/macOS inference app                              │
│ - Comprehensive documentation                                    │
│ - Result: "Professional, reproducible system"                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ Phase 4: Future Stages (Planned)                                 │
│ - Hierarchical analysis (chews → bites → meals)                  │
│ - Quality metrics and feedback                                   │
│ - Behavior change interventions                                  │
│ - Result: "Complete eating behavior system"                      │
└─────────────────────────────────────────────────────────────────┘
```

## Comparison: Then vs. Now

| Aspect | Initial Prototype | Current System |
|--------|------------------|----------------|
| **Data Collection** | Manual, ad-hoc | Dedicated iOS app (App Store) |
| **Labeling** | Post-hoc memory | Real-time video sync |
| **Training** | Jupyter notebooks | Orchestrated pipeline + W&B |
| **Model** | Hard labels, basic | Soft labels, refined architecture |
| **Deployment** | None | CoreML export + real-time app |
| **Testing** | Offline only | Real-time iOS/macOS |
| **Documentation** | Scattered notes | Comprehensive README system |
| **Reproducibility** | Low | High (version control, W&B) |
| **Future Vision** | Unclear | Explicit roadmap (5 stages) |

## Lessons for Future Projects

1. **Start scrappy, evolve systematically**: Proof of concept validates idea; production system delivers value
2. **Document decisions**: Future you (or others) will thank you
3. **Iterate with purpose**: Each version should answer specific questions
4. **Plan for productionization early**: Don't wait until "it works" to think about deployment
5. **Keep history**: Shows depth of work and engineering maturity

---

**The InitialPrototype represents 6+ months of R&D**. The current system is the distilled result of that exploration, but the history demonstrates the depth of work invested.

This is engineering as it really happens: not a straight line, but a deliberate iterative process toward a well-designed solution.
