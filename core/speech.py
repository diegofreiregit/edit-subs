from faster_whisper import WhisperModel


_model_cache: dict = {}


def _get_model(model_size: str) -> WhisperModel:
    if model_size not in _model_cache:
        _model_cache[model_size] = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )
    return _model_cache[model_size]


def find_first_speech(
    wav_path: str,
    segment_start_sec: float,
    model_size: str = "tiny",
    min_silence_duration_ms: int = 500,
    speech_pad_ms: int = 400,
    min_word_confidence: float = 0.7,
) -> tuple[float, str]:
    """
    Transcribe wav_path and return the absolute timestamp (in seconds)
    and the actual first spoken word that meets the confidence threshold.

    segment_start_sec is added back so the returned timestamp is
    relative to the start of the full video, not the extracted segment.

    Raises RuntimeError if no speech is detected.
    """
    model = _get_model(model_size)

    segments, _ = model.transcribe(
        wav_path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": min_silence_duration_ms,
            "speech_pad_ms": speech_pad_ms,
        },
        beam_size=1,
    )

    for segment in segments:
        if segment.words is None:
            continue
        for word in segment.words:
            if word.probability >= min_word_confidence and word.word.strip():
                absolute_ts = segment_start_sec + word.start
                return absolute_ts, word.word

    raise RuntimeError(
        "No speech detected in the selected range.\n"
        "Try a wider time window or a different segment."
    )
