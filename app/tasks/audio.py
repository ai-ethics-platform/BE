"""
# app/tasks/audio.py
Celery task : 여러 사용자 음성 트랙을 ffmpeg로 하나의 wav로 합치기
"""
# app/tasks/audio.py
import subprocess
from pathlib import Path
from celery import shared_task


@shared_task(name="audio.mix_tracks")
def mix_tracks(recording_paths: list[str], output_path: str) -> str:
    """Mix N audio tracks into one WAV using ffmpeg.

    Parameters
    ----------
    recording_paths : list[str]
        리스트 길이는 2개 이상이어야 합니다.
    output_path : str
        결과 WAV 저장 경로(확장자는 자유). 부모 디렉터리가 없으면 생성됩니다.
    """
    if len(recording_paths) < 2:
        raise ValueError("Need at least two tracks to mix")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = (
        ["ffmpeg", "-y"]                                # -y: overwrite
        + sum([["-i", p] for p in recording_paths], []) # -i path … 반복
        + [
            "-filter_complex",
            f"amix=inputs={len(recording_paths)}:normalize=0",
            output_path,
        ]
    )
    subprocess.run(cmd, check=True)
    return output_path
