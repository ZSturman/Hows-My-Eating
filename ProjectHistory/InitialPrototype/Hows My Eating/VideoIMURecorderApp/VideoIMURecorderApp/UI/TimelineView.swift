//
//  TimelineView.swift
//  VideoTimelineTest
//
//  Created by Zachary Sturman on 11/13/25.
//

import Foundation
import SwiftUI

struct MarkerShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        // Simple upward-pointing triangle
        path.move(to: CGPoint(x: rect.midX, y: rect.maxY))        // bottom center (apex)
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY))     // top right
        path.addLine(to: CGPoint(x: rect.minX, y: rect.minY))     // top left
        path.closeSubpath()
        return path
    }
}

struct TimelineView: View {
    @ObservedObject var viewModel: VideoEditorViewModel
    var markersEnabled: Bool = true
    @GestureState private var scrubStartTime: Double? = nil

    var body: some View {
        GeometryReader { geo in
            let markerHeight: CGFloat = 24
            let timelineHeight = max(geo.size.height - markerHeight, 0)

            ZStack {
                // Center playhead spanning markers + thumbnails
                Rectangle()
                    .fill(Color.white)
                    .frame(width: 2, height: geo.size.height)
                    .position(x: geo.size.width / 2.0, y: geo.size.height / 2.0)

                VStack(spacing: 0) {
                    // Marker row above the thumbnail strip
                    ZStack {
                        ForEach(viewModel.segments) { segment in
                            segmentView(
                                segment: segment,
                                width: geo.size.width,
                                height: markerHeight
                            )
                        }

                        ForEach(viewModel.markers) { marker in
                            markerView(
                                marker: marker,
                                width: geo.size.width,
                                height: markerHeight
                            )
                        }
                    }
                    .frame(height: markerHeight)

                    // Thumbnails row
                    ZStack {
                        HStack(spacing: 0) {
                            ForEach(viewModel.thumbnails) { thumb in
                                ZStack {
                                    if let image = thumb.image {
                                        Image(uiImage: image)
                                            .resizable()
                                            .scaledToFill()
                                    } else {
                                        Color.black
                                    }
                                }
                                .frame(
                                    width: geo.size.width / CGFloat(max(viewModel.framesVisible, 1)),
                                    height: timelineHeight
                                )
                                .clipped()
                            }
                        }
                        .offset(x: geo.size.width / 2.0 - filmstripX(for: viewModel.currentTime, width: geo.size.width))
                        .contentShape(Rectangle())
                        .gesture(scrubGesture(width: geo.size.width))
                    }
                    .frame(height: timelineHeight)
                }
            }
        }
    }

    // MARK: - Gestures

    // Map a time in seconds to a normalized 0...1 position along the full filmstrip.
    private func normalizedPosition(for time: Double) -> Double {
        let total = max(viewModel.duration, 0.0001)
        let clamped = min(max(time, 0.0), total)
        return clamped / total
    }

    private func filmstripX(for time: Double, width: CGFloat) -> CGFloat {
        CGFloat(normalizedPosition(for: time)) * width
    }

    private func scrubGesture(width: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 0)
            .updating($scrubStartTime) { value, state, _ in
                if state == nil {
                    state = viewModel.currentTime
                }
                guard let startTime = state, viewModel.duration > 0 else { return }

                let fraction = Double(value.translation.width / width)
                // Dragging right (positive translation) should move the video content
                // to the right, which means we go earlier in time.
                let newTime = startTime - fraction * viewModel.duration
                viewModel.seek(to: newTime)
            }
    }

    // MARK: - Marker drawing

    private func xFor(time: Double, width: CGFloat) -> CGFloat {
        let centerX = width / 2.0
        let currentX = filmstripX(for: viewModel.currentTime, width: width)
        let markerX  = filmstripX(for: time, width: width)
        return centerX + (markerX - currentX)
    }

    @ViewBuilder
    private func segmentView(segment: Segment,
                             width: CGFloat,
                             height: CGFloat) -> some View {
        let startX  = xFor(time: segment.startTime, width: width)
        let endX    = xFor(time: segment.endTime, width: width)
        let lineWidth = max(endX - startX, 1)

        Rectangle()
            .fill(segment.isChewing ? Color.green.opacity(0.6) : Color.blue.opacity(0.4))
            .frame(width: lineWidth, height: 4)
            .position(
                x: startX + lineWidth / 2.0,
                y: height - 4
            )
    }

    @ViewBuilder
    private func markerView(marker: VideoMarker,
                            width: CGFloat,
                            height: CGFloat) -> some View {
        let x = xFor(time: marker.time, width: width)
        let isSelected = marker.id == viewModel.selectedMarkerID

        MarkerShape()
            .fill(isSelected ? Color.red : Color.yellow)
            .frame(width: 14, height: 18)
            .position(x: x, y: height / 2.0)
            .gesture(
                DragGesture()
                    .onChanged { value in
                        guard markersEnabled else { return }
                        let clampedX = min(max(value.location.x, 0), width)
                        let centerX = width / 2.0
                        let total = viewModel.duration
                        guard total > 0 else { return }

                        // invert xFor to compute the marker's new time
                        let deltaFraction = Double((clampedX - centerX) / width)
                        let newTime = viewModel.currentTime + deltaFraction * total
                        viewModel.updateMarker(marker, to: newTime)
                    }
            )
            .onTapGesture {
                guard markersEnabled else { return }
                if viewModel.selectedMarkerID == marker.id {
                    viewModel.selectedMarkerID = nil
                } else {
                    viewModel.selectedMarkerID = marker.id
                }
            }
    }
}
