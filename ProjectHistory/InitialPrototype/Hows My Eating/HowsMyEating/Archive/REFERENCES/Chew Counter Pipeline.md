## Collect Data
## Sync Data
## Noise reduction
### Audio:
- ...
### Motion:
#### Identify artifacts:
- Walking
- Talking
- Head moving
#### Apply band-pass filter
- Butterworth
- Chebyshev
#### Thresholding
#### Peak Detection
#### Smoothing

## Segment
- Divide into 5-sec chunks
## Feature Extraction
### Audio:
- RMS
- Zero-cross
- Spectral
### Motion:
- Mean acceleration
- Standard deviation
- Peak count

## Data fusion
- Combine audio and motion into single vector. One for each segment

## Normalize
## Classification
- ANN
- SVm 