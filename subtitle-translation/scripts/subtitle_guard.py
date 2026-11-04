#!/usr/bin/env python3
"""Local, conservative SRT/WebVTT text extraction and lossless skeleton checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from dataclasses import dataclass


class GuardError(ValueError):
    pass


@dataclass
class Cue:
    id: str
    start: int
    end: int
    text: str


# Tags include WebVTT voice/class/ruby tags and inline timestamps. Entities and
# SRT-style override blocks remain opaque; this is not a general ASS parser.
PROTECTED = re.compile(r"<[^>\r\n]+>|\{\\[^}\r\n]*\}|&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]*);")
PLACEHOLDER = re.compile(r"⟦P[0-9]+⟧")
SRT_TIME = r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9],[0-9]{3}"
VTT_TIME = r"(?:[0-9]{2,}:)?[0-5][0-9]:[0-5][0-9]\.[0-9]{3}"


def require(condition, message):
    if not condition:
        raise GuardError(message)


def milliseconds(stamp):
    parts = stamp.replace(",", ".").split(":")
    seconds, fraction = parts.pop().split(".")
    minutes = int(parts.pop())
    hours = int(parts.pop()) if parts else 0
    return ((hours * 60 + minutes) * 60 + int(seconds)) * 1000 + int(fraction)


def parse(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError("Input must be UTF-8; obtain approval before transcoding.") from exc
    require("\r" not in text.replace("\r\n", ""), "Bare CR line endings are unsupported.")
    require("\x00" not in text, "NUL bytes are unsupported.")
    require(not PLACEHOLDER.search(text), "Source collides with reserved placeholder syntax.")
    fmt = Path(path).suffix.lower().lstrip(".")
    require(fmt in {"srt", "vtt"}, "Only .srt and .vtt inputs are supported.")
    # Keep character offsets and raw line endings; never normalize the skeleton.
    lines = []
    offset = 0
    for line in text.splitlines(keepends=True):
        body = line.removesuffix("\n").removesuffix("\r")
        require("\n" not in body and "\r" not in body, "Unexpected line ending.")
        lines.append((offset, offset + len(body), body))
        offset += len(line)
    # Python splitlines also recognizes Unicode separators: reject rather than
    # accidentally interpreting visible dialogue as structural delimiters.
    require(all(not any(c in body for c in "\v\f\x1c\x1d\x1e\x85\u2028\u2029")
                for _, _, body in lines), "Unsupported Unicode/control line separator.")
    blocks = []
    current = []
    for line in lines:
        if not line[2].strip(" \t"):
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    require(bool(blocks), "Empty subtitle file.")
    if fmt == "vtt":
        header = blocks.pop(0)
        require(re.fullmatch(r"\ufeff?WEBVTT(?:[ \t].*)?", header[0][2]) is not None,
                "Missing WebVTT header.")
        require(all("-->" not in item[2] for item in header), "Missing blank line after WebVTT header.")
    cues = []
    for block in blocks:
        first = block[0][2]
        if fmt == "vtt" and (first == "NOTE" or first.startswith(("NOTE ", "NOTE\t"))
                              or first in {"STYLE", "REGION"}):
            continue
        if fmt == "srt":
            require(re.fullmatch(r"\ufeff?[0-9]+", first) is not None,
                    "SRT block must begin with a numeric index.")
            timing_index = 1
            stamp = SRT_TIME
        else:
            timing_index = 0 if "-->" in first else 1
            stamp = VTT_TIME
        require(len(block) > timing_index + 1, "Cue has no timing line or payload.")
        timing = block[timing_index][2]
        match = re.fullmatch(rf"[ \t]*({stamp})[ \t]+-->[ \t]+({stamp})(?:[ \t]+[^\r\n]*)?", timing)
        require(match is not None, f"Unsupported timing line: {timing!r}")
        require(milliseconds(match[1]) < milliseconds(match[2]), f"Non-positive cue duration: {timing}")
        payload = block[timing_index + 1:]
        require(all("-->" not in item[2] for item in payload), "Timing arrow inside payload is unsupported.")
        start, end = payload[0][0], payload[-1][1]
        cues.append(Cue(f"c{len(cues) + 1:06d}", start, end, text[start:end]))
    require(bool(cues), "No translatable cues found.")
    return raw, text, fmt, cues


def protect(text):
    tokens = []

    def replace(match):
        token = f"⟦P{len(tokens):04d}⟧"
        tokens.append(match[0])
        return token

    return PROTECTED.sub(replace, text.replace("\r\n", "\n")), tokens


def skeleton(text, cues):
    chunks = []
    cursor = 0
    for cue in cues:
        chunks.append(text[cursor:cue.start])
        cursor = cue.end
    chunks.append(text[cursor:])
    return chunks


def verify(source, target):
    _, original, fmt, before = parse(source)
    _, translated, target_fmt, after = parse(target)
    require(fmt == target_fmt, "Format changed.")
    require(len(before) == len(after), "Cue count changed.")
    require(skeleton(original, before) == skeleton(translated, after),
            "Non-payload bytes changed (timings, IDs, metadata, separators, or line endings).")
    for old, new in zip(before, after):
        require(re.findall(r"\r\n|\n", old.text) == re.findall(r"\r\n|\n", new.text),
                f"{old.id}: payload line endings/count changed.")
        require(PROTECTED.findall(old.text) == PROTECTED.findall(new.text),
                f"{old.id}: protected tags/entities changed.")
    return len(before)


def publish(path, data):
    """Publish complete bytes without replacing an existing path, even in a race."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".subtitle-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # atomic no-clobber publication on local filesystems
    finally:
        os.unlink(temporary)


def extract(source, output):
    raw, _, fmt, cues = parse(source)
    document = {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "format": fmt,
        "cues": [{"id": cue.id, "text": protect(cue.text)[0]} for cue in cues],
    }
    publish(output, (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return len(cues)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def render(source, translations, output):
    raw, text, _, cues = parse(source)
    document = json.loads(Path(translations).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(document, dict), "Translations must be a JSON object.")
    require(document.get("source_sha256") == hashlib.sha256(raw).hexdigest(), "Source fingerprint mismatch.")
    entries = document.get("translations")
    require(isinstance(entries, list), "Expected a translations array.")
    require(all(isinstance(entry, dict) and isinstance(entry.get("text"), str) for entry in entries),
            "Each translation must contain id and string text.")
    require([entry.get("id") for entry in entries] == [cue.id for cue in cues],
            "Cue IDs must match exactly, once each, in source order.")
    chunks = []
    cursor = 0
    for cue, entry in zip(cues, entries):
        protected, tokens = protect(cue.text)
        translated = entry["text"]
        prefix = f"{cue.id}: "
        require("\r" not in translated, prefix + "Use LF in intermediate JSON.")
        require(not any(c in translated for c in "\x00\v\f\x1c\x1d\x1e\x85\u2028\u2029\ufeff"),
                prefix + "Forbidden control character or BOM.")
        require(len(translated.split("\n")) == len(protected.split("\n")), prefix + "Payload line count changed.")
        require(all(line.strip() for line in translated.split("\n")), prefix + "Blank payload line.")
        require("-->" not in translated, prefix + "New timing arrow.")
        require(not PROTECTED.search(translated) and "<" not in translated and "{\\" not in translated,
                prefix + "New markup/entity; use existing placeholders only.")
        for old_line, new_line in zip(protected.split("\n"), translated.split("\n")):
            require(PLACEHOLDER.findall(old_line) == PLACEHOLDER.findall(new_line),
                    prefix + "Protected placeholders changed, reordered, or moved between lines.")
        restored = PLACEHOLDER.sub(lambda match: tokens[int(match[0][2:-1])], translated)
        # Restore each original newline, even in a file with mixed endings.
        endings = iter(re.findall(r"\r\n|\n", cue.text))
        restored = re.sub("\n", lambda _: next(endings), restored)
        chunks.extend((text[cursor:cue.start], restored))
        cursor = cue.end
    chunks.append(text[cursor:])
    candidate = "".join(chunks).encode("utf-8")
    output = Path(output)
    require(output.suffix.lower() == Path(source).suffix.lower(), "Output extension must match input.")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(suffix=output.suffix, dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(candidate)
        verify(source, temp)
        publish(output, candidate)
    finally:
        os.unlink(temp)
    return len(cues)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, arguments in (("extract", ("source", "output")),
                            ("render", ("source", "translations", "output")),
                            ("verify", ("source", "target"))):
        command = commands.add_parser(name)
        for argument in arguments:
            command.add_argument(argument)
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        count = globals()[command](**args)
    except (GuardError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {command}; {count} cues. Structural checks only; semantic review is separate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
