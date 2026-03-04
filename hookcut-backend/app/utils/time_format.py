def timestamp_to_seconds(ts: str) -> float:
    """
    Convert timestamp string to seconds.
    Supports: "M:SS", "MM:SS", "H:MM:SS", "SS", and composite markers.
    """
    ts = ts.strip().replace(" [composite]", "")
    # Handle composite timestamps like "1:30+3:45"
    if "+" in ts:
        return timestamp_to_seconds(ts.split("+")[0])

    parts = ts.split(":")
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp format: {ts}")


def parse_composite_timestamps(start_time: str, end_time: str) -> list[tuple[float, float]]:
    """
    Parse composite hook timestamps into list of (start_seconds, end_seconds) pairs.
    Example: start="1:30+3:45", end="1:55+4:10" -> [(90, 115), (225, 250)]
    """
    if "+" not in start_time:
        return [(timestamp_to_seconds(start_time), timestamp_to_seconds(end_time))]

    starts = start_time.replace(" [composite]", "").split("+")
    ends = end_time.replace(" [composite]", "").split("+")

    if len(starts) != len(ends):
        raise ValueError(
            f"Composite timestamp mismatch: {len(starts)} starts vs {len(ends)} ends"
        )

    return [
        (timestamp_to_seconds(s.strip()), timestamp_to_seconds(e.strip()))
        for s, e in zip(starts, ends)
    ]
