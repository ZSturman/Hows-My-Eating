# ChewSense Dataset

This dataset contains motion sensor data collected from AirPods for chewing detection.

## Dataset Statistics

- **Total Sessions**: 24
- **Eating Sessions**: 0
- **Not-Eating Sessions**: 24
- **Total Duration**: 0.99 hours
- **Total Samples**: 176,880

## Data Collection

Data is collected using the ChewSense Data Collection app (available on the [App Store](https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802)).

Each session consists of:
- **CSV file**: Motion sensor data (accelerometer and gyroscope) with labels
- **Video file**: Synchronized video recording (excluded from git, see .gitignore)

## Sessions

| Session Name | Label | Date | Duration (min) | Total Samples | Eating | Not-Eating |
|-------------|-------|------|----------------|---------------|--------|------------|
| Eating-20251123-055649 | Unknown | Unknown | 3.0 | 9,024 | 5,363 | 3,661 |
| Eating-20251126-052803 | Unknown | Unknown | 4.9 | 14,390 | 8,702 | 5,688 |
| Eating-20251127-055805 | Unknown | Unknown | 2.3 | 6,865 | 4,702 | 2,163 |
| Eating-20251203-061305 | Unknown | Unknown | 2.2 | 6,542 | 5,271 | 1,271 |
| Eating-20251203-061529 | Unknown | Unknown | 1.1 | 3,188 | 2,320 | 868 |
| Eating-20251203-061652 | Unknown | Unknown | 1.2 | 3,492 | 2,459 | 1,033 |
| Eating-20251203-061809 | Unknown | Unknown | 1.2 | 3,598 | 2,499 | 1,099 |
| Not-eating-20251203-095215 | Not | eati-ng- 20:25:12 | 1.5 | 4,340 | 0 | 4,340 |
| Not-eating-20251209-050952 | Not | eati-ng- 20:25:12 | 2.1 | 6,191 | 0 | 6,191 |
| Not-eating-20251209-051208 | Not | eati-ng- 20:25:12 | 2.7 | 8,185 | 0 | 8,185 |
| Not-eating-20251211-150638 | Not | eati-ng- 20:25:12 | 2.2 | 6,525 | 0 | 6,525 |
| Not-eating-20251211-165249 | Not | eati-ng- 20:25:12 | 1.4 | 4,211 | 0 | 4,211 |
| Not-eating-20251211-165415 | Not | eati-ng- 20:25:12 | 2.2 | 6,458 | 0 | 6,458 |
| Not-eating-20251211-165632 | Not | eati-ng- 20:25:12 | 2.7 | 8,059 | 0 | 8,059 |
| Not-eating-20251211-204838 | Not | eati-ng- 20:25:12 | 2.6 | 7,727 | 0 | 7,727 |
| Not-eating-20251212-061659 | Not | eati-ng- 20:25:12 | 0.5 | 1,442 | 0 | 1,442 |
| Not-eating-20251212-175356 | Not | eati-ng- 20:25:12 | 2.4 | 6,985 | 0 | 6,985 |
| Not-eating-20251212-181452 | Not | eati-ng- 20:25:12 | 0.0 | 0 | 0 | 0 |
| Not-eating-20251212-181501 | Not | eati-ng- 20:25:12 | 8.2 | 24,344 | 0 | 24,344 |
| Not-eating-20251212-182314 | Not | eati-ng- 20:25:12 | 2.0 | 6,045 | 0 | 6,045 |
| Not-eating-20251212-182518 | Not | eati-ng- 20:25:12 | 3.2 | 9,487 | 0 | 9,487 |
| Not-eating-20251212-182831 | Not | eati-ng- 20:25:12 | 4.8 | 14,454 | 0 | 14,454 |
| Not-eating-20251212-183323 | Not | eati-ng- 20:25:12 | 2.4 | 7,097 | 0 | 7,097 |
| Not-eating-20251212-183548 | Not | eati-ng- 20:25:12 | 2.8 | 8,231 | 0 | 8,231 |

## Data Format

Each CSV file contains the following columns:
- `timestamp`: Device timestamp (seconds since boot)
- `ax`, `ay`, `az`: Accelerometer data (g)
- `gx`, `gy`, `gz`: Gyroscope data (rad/s)
- `label`: Boolean label (true = eating, false = not eating)

## Collection Protocol

- **Eating sessions**: User performs actual eating activities while wearing AirPods, marking chewing periods with the app
- **Not-eating sessions**: User performs various daily activities (talking, walking, working, etc.) without eating

## Data Quality

- All sessions use AirPods Pro or AirPods Max with motion sensors
- Synchronized video allows for precise labeling verification
- Motion data sampled at ~50 Hz (actual rate varies slightly)

## Usage

To add new data:
1. Use the ChewSense Data Collection app to record sessions
2. Export sessions and place in `data/raw_sessions/`
3. Run `python main.py` to process and transform new data
4. Regenerate this file with: `python scripts/generate_dataset_metadata.py`

---

*Last updated: 2026-01-05 18:09:15*
