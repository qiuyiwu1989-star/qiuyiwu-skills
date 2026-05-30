#!/usr/bin/env python3
"""
小米 MIMO TTS 语音生成 — 项目无关版本

用法：
  单段：
    python3 generate.py --text "(知性) 这是一段讲稿。" --out ./out.m4a [--voice 茉莉]
  批量 JSON：
    python3 generate.py --json ./narrations.json --out-dir ./output/audio [--targets ID1 ID2] [--force]

JSON 输入格式：
  {
    "卡片ID": {
      "narration": "(知性 干练 醇厚) 文本...",
      "voice": "茉莉"      # 可选，默认 茉莉
    },
    ...
  }

环境变量：
  MIMO_API_KEY      必须 — 小米 MIMO API key
  MIMO_API_URL      可选 — 默认 https://api.xiaomimimo.com/v1/chat/completions
  MIMO_MODEL        可选 — 默认 mimo-v2.5-tts
"""
import os, sys, json, base64, time, re, urllib.request, urllib.error, argparse, shutil, struct

DEFAULT_DIRECTOR_PROMPT = (
    "以资深认知导览员的口吻讲解，温暖知性，像一位认真讲到自己得意论点的老师；"
    "语速适中偏慢；核心判断放缓加重；不要播音腔，要有思考的停顿和呼吸。"
)

API_URL = os.environ.get("MIMO_API_URL", "https://api.xiaomimimo.com/v1/chat/completions")
MODEL   = os.environ.get("MIMO_MODEL", "mimo-v2.5-tts")

STYLE_TAG_RE = re.compile(r"^\s*(\([^)]+\)|\[[^\]]+\])+")


def extract_style_prefix(text):
    """从讲稿开头提取风格标签序列（一个或多个连续的 (风格) [锚点]）。只取 (风格)。"""
    m = STYLE_TAG_RE.match(text)
    if not m:
        return ""
    prefix_text = m.group(0)
    style_tags = re.findall(r"\([^)]+\)", prefix_text)
    return "".join(style_tags)


def split_text(text, max_chars=400, min_chars=200, inject_style=True):
    """按句切片，每段 < max_chars。最后段短于 min_chars 则合并到上段。
    每个 chunk 自动注入风格标签（防止后段语气机械化）。"""
    style_prefix = extract_style_prefix(text) if inject_style else ""
    chunks = []
    buf = ""
    for sentence in re.split(r"(?<=[。！？\n])", text):
        s = sentence.strip()
        if not s:
            continue
        if len(buf) + len(s) > max_chars and buf:
            chunks.append(buf)
            buf = s
        else:
            buf += s
    if buf:
        chunks.append(buf)
    # 末段过短 → 合并
    if len(chunks) >= 2 and len(chunks[-1]) < min_chars:
        chunks[-2] = chunks[-2] + chunks[-1]
        chunks = chunks[:-1]
    # 给除第一段外的所有段补回风格前缀
    if style_prefix and len(chunks) > 1:
        for i in range(1, len(chunks)):
            if not chunks[i].startswith("("):
                chunks[i] = style_prefix + chunks[i]
    return chunks


def call_tts(text, api_key, voice="茉莉", director_prompt=DEFAULT_DIRECTOR_PROMPT, timeout=120):
    """单次 TTS 调用，返回 wav bytes。"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user",      "content": director_prompt},
            {"role": "assistant", "content": text},
        ],
        "audio": {"format": "wav", "voice": voice},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    r = json.loads(body)
    audio_b64 = r["choices"][0]["message"]["audio"]["data"]
    return base64.b64decode(audio_b64)


def find_data_chunk(buf):
    i = 12
    while i < len(buf):
        chunk_id = buf[i:i+4]
        chunk_size = struct.unpack("<I", buf[i+4:i+8])[0]
        if chunk_id == b"data":
            return i, chunk_size
        i += 8 + chunk_size
    return None, 0


def concat_wavs(wav_bytes_list, out_path, gap_ms=80, silence_threshold=600):
    """把多段 wav 拼成一个。复用第一段 header，trim 头尾静音，段间插入 gap_ms 真静音。"""
    if not wav_bytes_list:
        return
    first = wav_bytes_list[0]
    header_end, _ = find_data_chunk(first)
    if header_end is None:
        open(out_path, "wb").write(b"".join(wav_bytes_list))
        return

    # 解析格式参数
    fmt_i = 12
    sample_rate, channels, bits = 24000, 1, 16
    while fmt_i < header_end:
        chunk_id = first[fmt_i:fmt_i+4]
        chunk_size = struct.unpack("<I", first[fmt_i+4:fmt_i+8])[0]
        if chunk_id == b"fmt ":
            channels    = struct.unpack("<H", first[fmt_i+10:fmt_i+12])[0]
            sample_rate = struct.unpack("<I", first[fmt_i+12:fmt_i+16])[0]
            bits        = struct.unpack("<H", first[fmt_i+22:fmt_i+24])[0]
            break
        fmt_i += 8 + chunk_size
    bytes_per_sample = channels * bits // 8

    keep_silence_samples = int(sample_rate * gap_ms / 1000)
    keep_silence = b"\x00" * (keep_silence_samples * bytes_per_sample) if gap_ms > 0 else b""

    def trim_silence(pcm):
        if bits != 16:
            return pcm
        n_samples = len(pcm) // bytes_per_sample
        max_lookback = int(sample_rate * 1.5)
        start = 0
        for s in range(min(n_samples, max_lookback)):
            off = s * bytes_per_sample
            val = struct.unpack("<h", pcm[off:off+2])[0]
            if abs(val) > silence_threshold:
                start = s
                break
        end = n_samples
        for s in range(min(n_samples, max_lookback)):
            idx = n_samples - 1 - s
            off = idx * bytes_per_sample
            val = struct.unpack("<h", pcm[off:off+2])[0]
            if abs(val) > silence_threshold:
                end = idx + 1
                break
        pad = int(sample_rate * 0.03)  # 30ms 过渡，防 click
        start = max(0, start - pad)
        end   = min(n_samples, end + pad)
        return pcm[start * bytes_per_sample : end * bytes_per_sample]

    pcm_parts = []
    for i, wb in enumerate(wav_bytes_list):
        di, ds = find_data_chunk(wb)
        if di is None:
            continue
        pcm = wb[di + 8 : di + 8 + ds]
        pcm = trim_silence(pcm)
        pcm_parts.append(pcm)
        if i < len(wav_bytes_list) - 1 and keep_silence:
            pcm_parts.append(keep_silence)

    total_pcm = b"".join(pcm_parts)
    header = first[:header_end]
    new_riff_size = len(header) - 8 + 8 + len(total_pcm)
    new_data_chunk = b"data" + struct.pack("<I", len(total_pcm)) + total_pcm
    new_buf = bytearray(header) + new_data_chunk
    new_buf[4:8] = struct.pack("<I", new_riff_size)
    open(out_path, "wb").write(bytes(new_buf))


def find_audio_encoder():
    """检测 afconvert（macOS）或 ffmpeg。"""
    if shutil.which("afconvert"):
        return "afconvert"
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    return None


def wav_to_m4a(wav_path, m4a_path, bitrate_kbps=96):
    """wav → m4a（AAC + faststart）"""
    encoder = find_audio_encoder()
    if encoder == "afconvert":
        rc = os.system(
            f'afconvert -f mp4f -d aac@44100 -b {bitrate_kbps * 1000} "{wav_path}" "{m4a_path}" > /dev/null 2>&1'
        )
    elif encoder == "ffmpeg":
        rc = os.system(
            f'ffmpeg -y -loglevel error -i "{wav_path}" -c:a aac -b:a {bitrate_kbps}k -movflags +faststart "{m4a_path}"'
        )
    else:
        print("ERROR: neither afconvert (macOS) nor ffmpeg found. Install ffmpeg: brew install ffmpeg / apt install ffmpeg", file=sys.stderr)
        return False
    return rc == 0


def process_one(narration, out_m4a_path, api_key, voice="茉莉",
                director_prompt=DEFAULT_DIRECTOR_PROMPT,
                gap_ms=80, max_chars=400, retries=3, bitrate_kbps=96,
                wav_tmp_dir=None, label="", force=False):
    """处理一段讲稿 → 一个 m4a 文件。返回 True/False。"""
    if os.path.exists(out_m4a_path) and not force:
        print(f"  skip {label} (exists: {out_m4a_path})", file=sys.stderr)
        return True

    out_dir = os.path.dirname(os.path.abspath(out_m4a_path)) or "."
    os.makedirs(out_dir, exist_ok=True)
    if wav_tmp_dir is None:
        wav_tmp_dir = os.path.join(out_dir, "_wav")
    os.makedirs(wav_tmp_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(out_m4a_path))[0]
    wav_path = os.path.join(wav_tmp_dir, f"{base}.wav")

    chunks = split_text(narration, max_chars=max_chars)
    print(f"  {label or base} [{voice}]: {len(narration)} chars → {len(chunks)} TTS calls", file=sys.stderr)

    wavs = []
    for i, chunk in enumerate(chunks):
        expected_kb = len(chunk) * 10  # 24kHz 16bit mono ≈ 10 KB/字
        for attempt in range(retries):
            try:
                wav = call_tts(chunk, api_key=api_key, voice=voice, director_prompt=director_prompt)
                actual_kb = len(wav) // 1024
                if actual_kb > max(5000, expected_kb * 3):
                    print(f"    [{i+1}/{len(chunks)}] anomaly {actual_kb} KB (expected ~{expected_kb}), retry {attempt+1}/{retries}", file=sys.stderr)
                    time.sleep(2)
                    continue
                wavs.append(wav)
                print(f"    [{i+1}/{len(chunks)}] {actual_kb} KB ✓", file=sys.stderr)
                time.sleep(0.5)
                break
            except Exception as e:
                print(f"    [{i+1}/{len(chunks)}] ERROR attempt {attempt+1}/{retries}: {e}", file=sys.stderr)
                time.sleep(2)
        else:
            print(f"    [{i+1}/{len(chunks)}] FAILED after {retries} retries", file=sys.stderr)
            return False

    concat_wavs(wavs, wav_path, gap_ms=gap_ms)

    if not wav_to_m4a(wav_path, out_m4a_path, bitrate_kbps=bitrate_kbps):
        print(f"    conversion failed: {wav_path} → {out_m4a_path}", file=sys.stderr)
        return False

    sz_m4a = os.path.getsize(out_m4a_path)
    print(f"  ✓ {label or base}: {sz_m4a // 1024} KB → {out_m4a_path}", file=sys.stderr)
    return True


def main():
    ap = argparse.ArgumentParser(description="小米 MIMO TTS 语音生成")
    # 输入方式（二选一）
    ap.add_argument("--text", help="单段文本（直接传字符串）")
    ap.add_argument("--json", help="批量 JSON 文件：{id: {narration, voice}}")
    # 输出
    ap.add_argument("--out", help="单段模式输出 m4a 路径")
    ap.add_argument("--out-dir", help="批量模式输出目录")
    # 可选过滤
    ap.add_argument("--targets", nargs="*", help="批量模式：只跑这些 ID")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的输出文件")
    # 配置
    ap.add_argument("--voice", default="茉莉", help="音色（默认 茉莉）")
    ap.add_argument("--director", default=DEFAULT_DIRECTOR_PROMPT, help="Director prompt")
    ap.add_argument("--max-chars", type=int, default=400, help="单段最大字数（默认 400）")
    ap.add_argument("--gap-ms", type=int, default=80, help="段间停顿 ms（默认 80，0=无停顿）")
    ap.add_argument("--no-silence-gap", action="store_true", help="等同于 --gap-ms 0")
    ap.add_argument("--retries", type=int, default=3, help="单段重试次数（默认 3）")
    ap.add_argument("--bitrate", type=int, default=96, help="m4a 码率 kbps（默认 96）")

    args = ap.parse_args()

    api_key = os.environ.get("MIMO_API_KEY", "").strip()
    if not api_key:
        print("ERROR: MIMO_API_KEY 环境变量未设置。\n  export MIMO_API_KEY=sk-xxxxxxxx", file=sys.stderr)
        sys.exit(1)

    if args.no_silence_gap:
        args.gap_ms = 0

    if args.text:
        if not args.out:
            print("ERROR: --text 必须配 --out 输出路径", file=sys.stderr)
            sys.exit(1)
        ok = process_one(
            args.text, args.out, api_key,
            voice=args.voice, director_prompt=args.director,
            gap_ms=args.gap_ms, max_chars=args.max_chars,
            retries=args.retries, bitrate_kbps=args.bitrate,
            force=args.force, label="single",
        )
        sys.exit(0 if ok else 1)

    if args.json:
        if not args.out_dir:
            print("ERROR: --json 必须配 --out-dir 输出目录", file=sys.stderr)
            sys.exit(1)
        with open(args.json, encoding="utf-8") as f:
            data = json.load(f)
        targets = args.targets or list(data.keys())
        os.makedirs(args.out_dir, exist_ok=True)
        ok_count = 0
        for cid in targets:
            if cid not in data:
                print(f"  skip {cid} (not in json)", file=sys.stderr)
                continue
            entry = data[cid]
            narration = entry.get("narration") or entry.get("text") or ""
            if not narration:
                print(f"  skip {cid} (empty narration)", file=sys.stderr)
                continue
            voice = entry.get("voice", args.voice)
            out_path = os.path.join(args.out_dir, f"{cid}.m4a")
            if process_one(
                narration, out_path, api_key,
                voice=voice, director_prompt=args.director,
                gap_ms=args.gap_ms, max_chars=args.max_chars,
                retries=args.retries, bitrate_kbps=args.bitrate,
                force=args.force, label=cid,
            ):
                ok_count += 1
        print(f"\n完成 {ok_count}/{len(targets)} 张", file=sys.stderr)
        sys.exit(0 if ok_count == len(targets) else 1)

    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
