from __future__ import annotations

import asyncio
import math
import re
import subprocess
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
GENERATED = ROOT / "generated"
OUTPUT = ROOT / "output"
LOGO = ROOT.parent / "dist" / "assets" / "agentproof-logo.png"
FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())

W, H = 1920, 1080
BG = "#090a0f"
PANEL = "#11141c"
PANEL_2 = "#171b25"
TEXT = "#f5f6f8"
MUTED = "#9ca4b5"
CORAL = "#ff593f"
CYAN = "#27d7e8"
GREEN = "#6ef0ae"
VIOLET = "#9d7cff"

FONT_REG = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
FONT_MONO = Path("C:/Windows/Fonts/consola.ttf")


SCENES = [
    {
        "key": "intro",
        "kicker": "AGENT TANK · FUTURE OF WORK",
        "title": "Did the agent\nearn the payment?",
        "subtitle": "Verifiable work. Automatic settlement.",
        "narration": "AI agents can work. But who decides whether the result actually earned the payment? AgentProof turns that question into a verifiable on-chain decision.",
    },
    {
        "key": "problem",
        "kicker": "THE MISSING TRUST LAYER",
        "title": "Autonomous work still\nhas a payment problem.",
        "subtitle": "Smart contracts cannot interpret open-ended deliverables. Centralized review is slow, opaque, and difficult for agents to trust.",
        "narration": "Traditional smart contracts cannot interpret requirements like, fix the bug without breaking the public API. Centralized marketplaces can review the work, but their decisions are slow, opaque, and hard for autonomous systems to compose with.",
    },
    {
        "key": "flow",
        "kicker": "THE AGENTPROOF PROTOCOL",
        "title": "From plain-language brief\nto final settlement.",
        "subtitle": "Four auditable stages. One deterministic case outcome.",
        "narration": "AgentProof creates a four-stage protocol. The client locks a brief, acceptance criteria, an assigned builder, and escrow. The builder submits public, content-addressed evidence. GenLayer validators evaluate every criterion, and the contract settles the result.",
    },
    {
        "key": "brief",
        "kicker": "01 · LOCK THE TERMS",
        "title": "The brief becomes\nthe source of truth.",
        "subtitle": "Immutable criteria · assigned builder · escrowed GEN",
        "shot": "brief.png",
        "narration": "In the live demo, the job brief and four acceptance criteria are locked before work begins. The client escrows GEN, the builder is fixed, and the terms cannot change after the case is created.",
    },
    {
        "key": "evidence",
        "kicker": "02 · FREEZE THE EVIDENCE",
        "title": "Evidence is data,\nnever instruction.",
        "subtitle": "Public URI · immutable content hash · prompt-injection boundary",
        "shot": "evidence.png",
        "narration": "The builder submits a public evidence bundle with an immutable content hash. Validators inspect the frozen artifact as untrusted data. Repository content can provide facts, but it can never override the adjudication instructions.",
    },
    {
        "key": "verdict",
        "kicker": "03 · GENLAYER CONSENSUS",
        "title": "Independent validators.\nOne auditable verdict.",
        "subtitle": "5 / 5 agree · 4 / 4 criteria passed · 92% confidence",
        "shot": "verdict.png",
        "narration": "GenLayer's non-comparative Equivalence Principle lets independent validators inspect the same evidence and converge on a reproducible verdict. Here, all five validators agree that all four criteria passed, with a compact consensus rationale.",
    },
    {
        "key": "settled",
        "kicker": "04 · SETTLE EXACTLY ONCE",
        "title": "Accepted work gets paid.\nRejected work gets refunded.",
        "subtitle": "Live Studio Devnet contract · 8 passing tests · double-settlement protection",
        "shot": "settled.png",
        "narration": "Settlement pays the builder on acceptance, or refunds the client on rejection. State changes before value transfer, and every case can settle only once. The live Studio Devnet contract exposes five methods and is backed by eight passing tests.",
    },
    {
        "key": "outro",
        "kicker": "LIVE NOW ON GENLAYER STUDIO DEVNET",
        "title": "AI agents can work.\nAgentProof decides\nif they earned the payment.",
        "subtitle": "agent-proof-coral.vercel.app  ·  github.com/Maje53/AgentProof",
        "narration": "AgentProof is live today on GenLayer Studio Devnet. Try the demo, inspect the public repository, and help build a future where autonomous work can earn autonomous payment.",
    },
]


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(str(path), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=face)[2] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def gradient_background() -> Image.Image:
    y, x = np.mgrid[0:H, 0:W]
    base = np.zeros((H, W, 3), dtype=np.float32)
    base[:] = np.array([9, 10, 15], dtype=np.float32)
    glow1 = np.exp(-(((x - 210) / 620) ** 2 + ((y - 120) / 520) ** 2))[:, :, None]
    glow2 = np.exp(-(((x - 1740) / 720) ** 2 + ((y - 900) / 650) ** 2))[:, :, None]
    base += glow1 * np.array([22, 5, 4]) + glow2 * np.array([4, 10, 22])
    rng = np.random.default_rng(53)
    base += rng.normal(0, 1.1, base.shape)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def rounded_paste(canvas: Image.Image, source: Image.Image, box: tuple[int, int, int, int], radius: int = 28) -> None:
    x1, y1, x2, y2 = box
    target = source.copy()
    target.thumbnail((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    layer = Image.new("RGB", (x2 - x1, y2 - y1), PANEL)
    ox = ((x2 - x1) - target.width) // 2
    oy = ((y2 - y1) - target.height) // 2
    layer.paste(target, (ox, oy))
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *layer.size), radius=radius, fill=255)
    canvas.paste(layer, (x1, y1), mask)


def brand_header(draw: ImageDraw.ImageDraw, canvas: Image.Image, index: int) -> None:
    logo = Image.open(LOGO).convert("RGB").resize((58, 58), Image.Resampling.LANCZOS)
    mask = Image.new("L", (58, 58), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 58, 58), radius=13, fill=255)
    canvas.paste(logo, (74, 54), mask)
    draw.text((150, 63), "AgentProof", font=font(30, bold=True), fill=TEXT)
    draw.text((150, 98), "VERIFIABLE AGENT WORK", font=font(13, mono=True), fill=MUTED)
    draw.text((1530, 68), "AGENT TANK 2026", font=font(18, mono=True), fill=CYAN)
    draw.text((1772, 69), f"{index + 1:02d}/08", font=font(17, mono=True), fill=MUTED)
    draw.line((74, 135, 1846, 135), fill="#292d39", width=2)


def footer(draw: ImageDraw.ImageDraw, scene: dict, index: int) -> None:
    draw.rounded_rectangle((74, 902, 1846, 1020), radius=20, fill="#11151de8", outline="#2a3040", width=2)
    face = font(25)
    lines = wrap(draw, scene["narration"], face, 1680)
    y = 922 if len(lines) <= 2 else 910
    for line in lines[:3]:
        draw.text((112, y), line, font=face, fill="#e3e6ec")
        y += 34
    segment = (W - 148) / len(SCENES)
    for i in range(len(SCENES)):
        color = CORAL if i <= index else "#2b303b"
        draw.rounded_rectangle((74 + i * segment, 1048, 74 + (i + 1) * segment - 8, 1058), radius=5, fill=color)


def render_intro(canvas: Image.Image, draw: ImageDraw.ImageDraw, scene: dict) -> None:
    logo = Image.open(LOGO).convert("RGB").resize((315, 315), Image.Resampling.LANCZOS)
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((140, 230, 550, 640), fill=(255, 76, 52, 62))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    canvas.paste(glow, (0, 0), glow)
    mask = Image.new("L", (315, 315), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 315, 315), radius=68, fill=255)
    canvas.paste(logo, (190, 282), mask)
    draw.text((640, 235), scene["kicker"], font=font(22, mono=True), fill=CYAN)
    y = 295
    for line in scene["title"].split("\n"):
        draw.text((640, y), line, font=font(86, bold=True), fill=TEXT if y < 360 else CORAL)
        y += 94
    draw.text((645, 525), scene["subtitle"], font=font(34), fill=MUTED)
    draw.rounded_rectangle((645, 605, 1160, 668), radius=31, fill=CORAL)
    draw.text((690, 620), "LIVE ON STUDIO DEVNET", font=font(22, bold=True, mono=True), fill="#110b0a")


def render_problem(canvas: Image.Image, draw: ImageDraw.ImageDraw, scene: dict) -> None:
    draw.text((86, 190), scene["kicker"], font=font(20, mono=True), fill=CORAL)
    y = 245
    for line in scene["title"].split("\n"):
        draw.text((82, y), line, font=font(70, bold=True), fill=TEXT)
        y += 80
    items = [
        ("01", "Subjective criteria", "Success cannot be reduced to a simple boolean oracle."),
        ("02", "Opaque review", "Agents cannot audit or compose with centralized decisions."),
        ("03", "Fragile settlement", "Payment still depends on trust, delay, and manual approval."),
    ]
    x = 82
    for number, title, body in items:
        draw.rounded_rectangle((x, 525, x + 550, 810), radius=24, fill=PANEL, outline="#2c313d", width=2)
        draw.text((x + 32, 555), number, font=font(20, mono=True), fill=CYAN)
        draw.text((x + 32, 610), title, font=font(34, bold=True), fill=TEXT)
        for j, line in enumerate(wrap(draw, body, font(25), 470)):
            draw.text((x + 32, 675 + j * 35), line, font=font(25), fill=MUTED)
        x += 594


def render_flow(canvas: Image.Image, draw: ImageDraw.ImageDraw, scene: dict) -> None:
    draw.text((84, 185), scene["kicker"], font=font(20, mono=True), fill=CYAN)
    draw.text((82, 235), scene["title"].split("\n")[0], font=font(65, bold=True), fill=TEXT)
    draw.text((82, 310), scene["title"].split("\n")[1], font=font(65, bold=True), fill=CORAL)
    steps = [
        ("01", "LOCK", "Brief + criteria\nBuilder + escrow", CORAL),
        ("02", "SUBMIT", "Public evidence\nContent hash", CYAN),
        ("03", "DECIDE", "Independent AI\nvalidator consensus", VIOLET),
        ("04", "SETTLE", "Pay builder\nor refund client", GREEN),
    ]
    x = 76
    for i, (num, title, body, color) in enumerate(steps):
        draw.rounded_rectangle((x, 475, x + 390, 790), radius=26, fill=PANEL, outline=color, width=3)
        draw.text((x + 30, 505), num, font=font(18, mono=True), fill=color)
        draw.text((x + 30, 565), title, font=font(38, bold=True), fill=TEXT)
        yy = 640
        for line in body.split("\n"):
            draw.text((x + 30, yy), line, font=font(26), fill=MUTED)
            yy += 38
        if i < 3:
            draw.line((x + 400, 632, x + 468, 632), fill="#565d6d", width=4)
            draw.polygon([(x + 468, 632), (x + 449, 620), (x + 449, 644)], fill="#565d6d")
        x += 466


def render_product(canvas: Image.Image, draw: ImageDraw.ImageDraw, scene: dict) -> None:
    shot = Image.open(ASSETS / scene["shot"]).convert("RGB")
    rounded_paste(canvas, shot, (65, 185, 1245, 850), radius=24)
    draw.rounded_rectangle((65, 185, 1245, 850), radius=24, outline="#343a49", width=3)
    x = 1300
    draw.text((x, 210), scene["kicker"], font=font(18, mono=True), fill=CYAN if scene["key"] != "settled" else GREEN)
    y = 265
    for line in scene["title"].split("\n"):
        draw.text((x, y), line, font=font(48, bold=True), fill=TEXT)
        y += 60
    y += 28
    for line in wrap(draw, scene["subtitle"], font(25), 520):
        draw.text((x, y), line, font=font(25), fill=MUTED)
        y += 38
    if scene["key"] == "brief":
        facts = [("STATE", "OPEN → SUBMITTED"), ("ESCROW", "1,250 GEN"), ("CRITERIA", "4 locked checks")]
    elif scene["key"] == "evidence":
        facts = [("SOURCE", "Public repository"), ("INTEGRITY", "SHA-256 hash"), ("BOUNDARY", "Untrusted input")]
    elif scene["key"] == "verdict":
        facts = [("VERDICT", "ACCEPT"), ("VALIDATORS", "5 / 5 agree"), ("CONFIDENCE", "92%")]
    else:
        facts = [("STATE", "SETTLED"), ("NETWORK", "Studio Devnet"), ("TESTS", "8 passing")]
    y += 32
    for label, value in facts:
        draw.rounded_rectangle((x, y, 1830, y + 72), radius=16, fill=PANEL_2, outline="#2c3240", width=2)
        draw.text((x + 20, y + 14), label, font=font(15, mono=True), fill=MUTED)
        draw.text((x + 190, y + 13), value, font=font(24, bold=True), fill=GREEN if scene["key"] in {"verdict", "settled"} else TEXT)
        y += 88


def render_outro(canvas: Image.Image, draw: ImageDraw.ImageDraw, scene: dict) -> None:
    logo = Image.open(LOGO).convert("RGB").resize((230, 230), Image.Resampling.LANCZOS)
    mask = Image.new("L", (230, 230), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 230, 230), radius=50, fill=255)
    canvas.paste(logo, (110, 260), mask)
    draw.text((420, 210), scene["kicker"], font=font(20, mono=True), fill=CYAN)
    y = 260
    for i, line in enumerate(scene["title"].split("\n")):
        draw.text((420, y), line, font=font(62, bold=True), fill=CORAL if i == 2 else TEXT)
        y += 72
    draw.rounded_rectangle((420, 540, 1800, 695), radius=24, fill=PANEL, outline="#303645", width=2)
    draw.text((460, 575), "LIVE DEMO", font=font(16, mono=True), fill=CYAN)
    draw.text((690, 568), "agent-proof-coral.vercel.app", font=font(29, bold=True), fill=TEXT)
    draw.text((460, 632), "SOURCE", font=font(16, mono=True), fill=VIOLET)
    draw.text((690, 625), "github.com/Maje53/AgentProof", font=font(29, bold=True), fill=TEXT)
    draw.text((112, 735), "0xD6f7eE8da1fc3510B8513b2724af86aC8B3f0f92", font=font(23, mono=True), fill=MUTED)


def render_scene(scene: dict, index: int) -> Path:
    canvas = gradient_background()
    draw = ImageDraw.Draw(canvas)
    brand_header(draw, canvas, index)
    if scene["key"] == "intro":
        render_intro(canvas, draw, scene)
    elif scene["key"] == "problem":
        render_problem(canvas, draw, scene)
    elif scene["key"] == "flow":
        render_flow(canvas, draw, scene)
    elif scene["key"] == "outro":
        render_outro(canvas, draw, scene)
    else:
        render_product(canvas, draw, scene)
    footer(draw, scene, index)
    output = GENERATED / f"scene-{index + 1:02d}-{scene['key']}.png"
    canvas.save(output, quality=95)
    return output


async def create_voice_segments() -> list[Path]:
    paths = []
    for index, scene in enumerate(SCENES):
        target = GENERATED / f"voice-{index + 1:02d}.mp3"
        communicator = edge_tts.Communicate(
            scene["narration"],
            voice="en-US-AvaMultilingualNeural",
            rate="-2%",
            volume="+0%",
            pitch="-2Hz",
        )
        await communicator.save(str(target))
        paths.append(target)
    return paths


def probe_duration(path: Path) -> float:
    result = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration for {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def write_srt(durations: list[float]) -> None:
    cursor = 0.0
    blocks = []
    for index, (scene, duration) in enumerate(zip(SCENES, durations), 1):
        blocks.append(f"{index}\n{srt_time(cursor)} --> {srt_time(cursor + duration)}\n{scene['narration']}\n")
        cursor += duration
    (OUTPUT / "agentproof-subtitles.srt").write_text("\n".join(blocks), encoding="utf-8")


def create_music(duration: float) -> Path:
    sample_rate = 44_100
    count = int(duration * sample_rate)
    t = np.arange(count, dtype=np.float64) / sample_rate
    pad = np.zeros(count, dtype=np.float64)
    chords = [(110.0, 164.81, 220.0), (98.0, 146.83, 196.0), (123.47, 185.0, 246.94), (110.0, 164.81, 220.0)]
    section = max(1.0, duration / len(chords))
    for i, chord in enumerate(chords):
        start = int(i * section * sample_rate)
        end = min(count, int((i + 1) * section * sample_rate))
        local = t[start:end]
        env = np.sin(np.linspace(0, math.pi, end - start)) ** 0.35
        wave_sum = sum(np.sin(2 * math.pi * f * local + i * 0.4) for f in chord) / len(chord)
        pad[start:end] += wave_sum * env
    pulse = np.sin(2 * math.pi * 55 * t) * (np.maximum(0, np.sin(2 * math.pi * 0.5 * t)) ** 12)
    shimmer = np.sin(2 * math.pi * 880 * t) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.08 * t))
    audio = 0.19 * pad + 0.035 * pulse + 0.012 * shimmer
    fade = min(sample_rate * 2, count // 4)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    stereo = np.column_stack((audio, np.roll(audio, 220)))
    pcm = np.int16(np.clip(stereo, -1, 1) * 32767)
    target = GENERATED / "original-ambient-score.wav"
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    return target


def write_concat(paths: list[Path], durations: list[float], name: str) -> Path:
    target = GENERATED / name
    lines = []
    for path, duration in zip(paths, durations):
        escaped = path.as_posix().replace("'", "'\\''")
        lines.extend([f"file '{escaped}'", f"duration {duration:.3f}"])
    escaped = paths[-1].as_posix().replace("'", "'\\''")
    lines.append(f"file '{escaped}'")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def write_audio_concat(paths: list[Path]) -> Path:
    target = GENERATED / "audio-concat.txt"
    lines = [f"file '{path.as_posix().replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'" for path in paths]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def encode_video(scene_paths: list[Path], voice_paths: list[Path], durations: list[float]) -> Path:
    visuals = write_concat(scene_paths, durations, "visuals-concat.txt")
    voices = write_audio_concat(voice_paths)
    music = create_music(sum(durations))
    target = OUTPUT / "agentproof-agent-tank-demo.mp4"
    command = [
        str(FFMPEG), "-y",
        "-f", "concat", "-safe", "0", "-i", str(visuals),
        "-f", "concat", "-safe", "0", "-i", str(voices),
        "-i", str(music),
        "-filter_complex", "[1:a]volume=1.15[voice];[2:a]volume=0.16[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(target),
    ]
    subprocess.run(command, check=True)
    return target


def main() -> None:
    for directory in (ASSETS, GENERATED, OUTPUT):
        directory.mkdir(parents=True, exist_ok=True)
    missing = [scene["shot"] for scene in SCENES if scene.get("shot") and not (ASSETS / scene["shot"]).exists()]
    if missing:
        raise SystemExit(f"Missing captured demo assets: {', '.join(missing)}")
    scene_paths = [render_scene(scene, i) for i, scene in enumerate(SCENES)]
    voice_paths = asyncio.run(create_voice_segments())
    durations = [probe_duration(path) for path in voice_paths]
    write_srt(durations)
    video = encode_video(scene_paths, voice_paths, durations)
    thumbnail = Image.open(scene_paths[0]).resize((1280, 720), Image.Resampling.LANCZOS)
    thumbnail.save(OUTPUT / "agentproof-thumbnail.png", quality=95)
    print(f"Video: {video}")
    print(f"Duration: {sum(durations):.1f}s")
    print(f"Subtitles: {OUTPUT / 'agentproof-subtitles.srt'}")


if __name__ == "__main__":
    main()
