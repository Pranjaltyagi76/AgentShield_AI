"""Assemble reviewed public browser captures into an explicitly edited walkthrough.

Requires Python 3.12+ and FFmpeg with libx264/libass on PATH.
No network, credentials, browser automation, or runtime benchmark execution.
Run from repository root: python docs/portfolio/build_walkthrough.py
"""

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parents[1] / ".cache" / "portfolio-video"
DURATION = 8
CAPTIONS = [
    "AgentShield AI: a synthetic agent-security harness. This saved sample is historical.",
    "Free hosting can sleep. Retry is explicit; the saved sample remains accessible.",
    "Start a temporary guest workspace. No account or inference API key is required.",
    "Select the shared hardened behavior v2 and the twelve-case Core v2 suite.",
    "Launch the actual persisted run. The queue records ordered execution evidence.",
    "Observed hardened run: 12 of 12 evaluated; 12 passed. These are scripted results.",
    "Run the vulnerable profile against the same pinned suite and execution limits.",
    "Observed vulnerable run: 12 of 12 evaluated; 6 passed. Failures follow evidence.",
    "Open a finding at its exact event. The private answer marker is redacted for display.",
    "AS-006: the gateway blocks a prohibited destination. No mock execution follows.",
    "AS-011: an allowed guide lookup has a recorded mock result and benign-task check.",
    "Compare vulnerable to hardened: six improved, six unchanged. Coverage stays visible.",
    "Download authenticated HTML and JSON reports from retained evidence.",
    "History stores report metadata. Exports regenerate while source records remain.",
    "API and database connected. Gemini disabled. Custom authoring and settings page remain open.",
]


def timestamp(seconds, separator):
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}000"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    frames = json.loads((ROOT / "captures" / "frames.json").read_text(encoding="utf-8"))
    if len(frames) != len(CAPTIONS):
        raise ValueError("Every reviewed capture requires an explicit caption")
    concat = []
    cues = []
    for index, (frame, caption) in enumerate(zip(frames, CAPTIONS, strict=True)):
        image = ROOT / "captures" / frame["file"]
        if not image.is_file():
            raise FileNotFoundError(image)
        concat.extend([f"file '{image.as_posix()}'", f"duration {DURATION}"])
        start, end = index * DURATION, (index + 1) * DURATION
        wrapped = textwrap.fill(caption, width=72)
        cues.append((index + 1, start, end, wrapped))
    concat.append(f"file '{image.as_posix()}'")
    (CACHE / "frames.txt").write_text("\n".join(concat) + "\n", encoding="utf-8")
    srt = "\n\n".join(
        f"{number}\n{timestamp(start, ',')} --> {timestamp(end, ',')}\n{caption}"
        for number, start, end, caption in cues
    )
    (CACHE / "captions.srt").write_text(srt + "\n", encoding="utf-8")
    vtt = "WEBVTT\n\n" + "\n\n".join(
        f"{timestamp(start, '.')} --> {timestamp(end, '.')}\n{caption}"
        for _, start, end, caption in cues
    )
    (ROOT / "walkthrough.vtt").write_text(vtt + "\n", encoding="utf-8")
    environment = os.environ.copy()
    font_option = ""
    if os.name == "nt":
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        shutil.copyfile(fonts / "arial.ttf", CACHE / "header.ttf")
        config = CACHE / "fonts.conf"
        config.write_text(
            "<fontconfig><dir>"
            + escape(fonts.as_posix())
            + "</dir><cachedir>"
            + escape((CACHE / "font-cache").as_posix())
            + "</cachedir></fontconfig>",
            encoding="utf-8",
        )
        environment["FONTCONFIG_FILE"] = str(config)
        font_option = "fontfile=header.ttf:"
    # Relative subtitle filename avoids Windows drive-colon filter escaping.
    filters = (
        "scale=1000:800:force_original_aspect_ratio=decrease:in_range=pc:out_range=tv,"
        "format=yuv420p,setparams=range=limited,"
        "pad=1024:960:(ow-iw)/2:40:color=0x10221b,"
        "drawtext="
        + font_option
        + "text='AgentShield AI | Edited browser captures | 18 Nov 2026':"
        "fontcolor=white:fontsize=19:x=20:y=10,"
        "subtitles=captions.srt:force_style='FontName=Arial,FontSize=8,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H0010221B,"
        "BorderStyle=3,Outline=1,Shadow=0,MarginV=8'"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(CACHE / "frames.txt"),
            "-vf",
            filters,
            "-r",
            "10",
            "-t",
            str(len(frames) * DURATION),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(ROOT / "walkthrough.mp4"),
        ],
        cwd=CACHE,
        env=environment,
        check=True,
    )
    print(f"Created {len(frames) * DURATION}-second captioned edited walkthrough")


if __name__ == "__main__":
    main()
