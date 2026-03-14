"""Face detection and speaker spatial mapping for interview mode.

Algorithm: In a 2-person interview, we only need to find ONE face to determine
the split. If a face is detected on the right side, the other speaker must be
on the left side (and vice versa). This works for any single-camera interview
regardless of face angle (frontal, profile, or partially obscured).
"""
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FaceRegion:
    speaker_label: str  # "Speaker A"
    x: int
    y: int
    w: int
    h: int  # bounding box in source frame


def detect_speaker_faces(
    video_path: str,
    speaker_count: int,
    sample_count: int = 20,
) -> list[FaceRegion]:
    """Detect speaker positions for interview split-screen.

    For 2-speaker interviews: detects at least one face and infers the other
    speaker's position on the opposite side of the frame. Returns exactly 2
    FaceRegions (left speaker, right speaker) or empty list if detection fails.

    For 3+ speakers: requires all faces to be detected (original clustering).
    """
    try:
        os.environ.setdefault("OPENCV_OPENCL_RUNTIME", "disabled")
        import cv2
    except ImportError:
        logger.warning("opencv not installed — skipping face mapping")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("Cannot open video for face mapping: %s", video_path)
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    if frame_width == 0 or frame_height == 0 or total_frames == 0:
        cap.release()
        return []

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Sample frames evenly
    frame_step = max(1, total_frames // sample_count)
    detections: list[tuple[int, int, int, int]] = []
    frames_with_faces = 0
    total_sampled = 0

    frame_idx = 0
    while frame_idx < total_frames and total_sampled < sample_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        total_sampled += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
        )
        if len(faces) > 0:
            frames_with_faces += 1
            for (x, y, w, h) in faces:
                detections.append((int(x), int(y), int(w), int(h)))
        frame_idx += frame_step

    cap.release()

    if total_sampled == 0 or not detections:
        return []

    detection_rate = frames_with_faces / total_sampled
    if detection_rate < 0.3:
        logger.info("Face detection rate too low (%.0f%%) — skipping split-screen", detection_rate * 100)
        return []

    if speaker_count == 2:
        return _infer_two_speakers(detections, frame_width, frame_height, total_sampled)

    # 3+ speakers: require all faces detected (original approach)
    return _detect_all_speakers(detections, speaker_count, frame_width, total_sampled)


def _infer_two_speakers(
    detections: list[tuple[int, int, int, int]],
    frame_width: int,
    frame_height: int,
    total_sampled: int,
) -> list[FaceRegion]:
    """For 2-speaker interviews: always return left/right crop positions.

    Strategy: In any 2-person interview, one speaker is on the left side and
    one on the right. We place virtual "face regions" at the 1/3 and 2/3 marks
    of the frame — this guarantees distinct crops regardless of actual face
    positions, camera angle, or whether faces are frontal/profile.

    Face detection is used ONLY to validate there's a person in the frame
    (detection_rate > 30% checked by caller) and to set appropriate face size
    for crop calculations.
    """
    # Use the largest detected face to determine a reasonable face size
    largest = max(detections, key=lambda d: d[2] * d[3])
    face_w = largest[2]
    face_h = largest[3]
    face_y = largest[1]

    # Place speakers at 1/3 and 2/3 of frame width
    # This guarantees non-overlapping crops for any interview layout
    left_center_x = frame_width // 3
    right_center_x = (frame_width * 2) // 3

    left_face = FaceRegion(
        speaker_label="Speaker A",
        x=left_center_x - face_w // 2,
        y=face_y,
        w=face_w,
        h=face_h,
    )
    right_face = FaceRegion(
        speaker_label="Speaker B",
        x=right_center_x - face_w // 2,
        y=face_y,
        w=face_w,
        h=face_h,
    )

    logger.info(
        "Interview split: left at x=%d, right at x=%d (frame=%dpx, face=%dpx)",
        left_center_x, right_center_x, frame_width, face_w,
    )
    return [left_face, right_face]


def _detect_all_speakers(
    detections: list[tuple[int, int, int, int]],
    speaker_count: int,
    frame_width: int,
    total_sampled: int,
) -> list[FaceRegion]:
    """For 3+ speakers: require all faces to be reliably detected."""
    x_centers = [(d[0] + d[2] // 2, d) for d in detections]
    x_centers.sort(key=lambda t: t[0])

    clusters = _cluster_by_gaps(x_centers, speaker_count, frame_width)
    if len(clusters) < speaker_count:
        logger.info(
            "Found %d face clusters but expected %d — skipping split-screen",
            len(clusters), speaker_count,
        )
        return []

    min_detections = max(3, int(total_sampled * 0.25))
    valid_clusters = [c for c in clusters if len(c) >= min_detections]
    if len(valid_clusters) < speaker_count:
        logger.info(
            "Only %d clusters with enough detections (need %d) — skipping",
            len(valid_clusters), min_detections,
        )
        return []

    results = []
    for i, cluster in enumerate(valid_clusters[:speaker_count]):
        label = f"Speaker {chr(65 + i)}"
        sorted_by_x = sorted(cluster, key=lambda d: d[0])
        mid = len(sorted_by_x) // 2
        median_det = sorted_by_x[mid]
        results.append(FaceRegion(
            speaker_label=label,
            x=median_det[0], y=median_det[1],
            w=median_det[2], h=median_det[3],
        ))
    return results


def _cluster_by_gaps(
    x_centers: list[tuple[int, tuple]],
    target_count: int,
    frame_width: int,
) -> list[list[tuple]]:
    """Cluster face detections by finding natural gaps in X-center positions."""
    if not x_centers:
        return []
    if target_count <= 1:
        return [[d for _, d in x_centers]]

    gaps: list[tuple[int, int]] = []
    for i in range(1, len(x_centers)):
        gap = x_centers[i][0] - x_centers[i - 1][0]
        gaps.append((gap, i))

    gaps.sort(key=lambda g: g[0], reverse=True)
    split_indices = sorted([g[1] for g in gaps[: target_count - 1]])

    clusters: list[list[tuple]] = []
    prev = 0
    for idx in split_indices:
        cluster = [d for _, d in x_centers[prev:idx]]
        if cluster:
            clusters.append(cluster)
        prev = idx
    last = [d for _, d in x_centers[prev:]]
    if last:
        clusters.append(last)

    return clusters
