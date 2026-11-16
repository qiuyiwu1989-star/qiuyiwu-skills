#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe.py — faster-whisper 转录（毫秒级时间戳）

用法:
  python3 transcribe.py <audio-or-model> <audio> <out.txt> [--ms] [--model-dir DIR] [--lang zh]

输出（默认，秒+毫秒）:
  [00:00:00.000-00:00:03.780] 文本
同时写 <out>.srt（毫秒标准 SRT，可导剪映/Arctee）。

模型目录须含 model.bin（faster-whisper 格式）。默认 $HOME/.openclaw/models/faster-whisper-medium
"""
import sys, os, argparse, time

def fmt_ts(t, sep=":"):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}" if sep == ":" else f"{h:02d}:{m:02d}:{int(s):02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="模型名或本地目录")
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--ms", action="store_true", help="输出 hh:mm:ss.mmm 时间轴")
    ap.add_argument("--beam", type=int, default=5)
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    model_path = args.model
    if not os.path.isdir(model_path):
        model_path = os.path.expanduser("~/.openclaw/models/faster-whisper-medium")
    t0 = time.time()
    model = WhisperModel(model_path, device="cpu", compute_type="int8", cpu_threads=8)
    segments, info = model.transcribe(args.audio, language=args.lang, beam_size=args.beam,
                                      vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
    print(f"[{time.time()-t0:.0f}s] lang={info.language} dur={info.duration:.1f}s", flush=True)

    def ts(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    srt = open(args.out + ".srt", "w", encoding="utf-8")
    n = 0
    prev_texts = []   # 末尾若干段文本（去标点）用于重复检测
    dup_flags = []    # (段号, 时间) 重复位置

    def norm(s):
        return "".join(ch for ch in s if ch.isalnum() or '\u4e00' <= ch <= '\u9fff')

    with open(args.out, "w", encoding="utf-8") as f:
        for seg in segments:
            n += 1
            line = f"[{ts(seg.start)}-{ts(seg.end)}] {seg.text.strip()}"
            f.write(line + "\n")
            a = f"{int(seg.start//3600):02d}:{int(seg.start%3600//60):02d}:{int(seg.start%60):02d},{int(seg.start%1*1000):03d}"
            b = f"{int(seg.end//3600):02d}:{int(seg.end%3600//60):02d}:{int(seg.end%60):02d},{int(seg.end%1*1000):03d}"
            srt.write(f"{n}\n{a} --> {b}\n{seg.text.strip()}\n\n")
            # 重复检测：当前段与往前 3~12 段中某段 exact 相同（且长度>=8字）
            cur = norm(seg.text)
            if len(cur) >= 8:
                for back in range(3, 13):
                    if len(prev_texts) >= back and prev_texts[-back] == cur:
                        dup_flags.append((n, ts(seg.start), seg.text.strip()[:30]))
                        break
            prev_texts.append(cur)
            if n % 50 == 0:
                f.flush(); srt.flush()
                print(f"  seg {n} @ {seg.end:.0f}s/{info.duration:.0f}s [{time.time()-t0:.0f}s]", flush=True)
    srt.close()
    print(f"DONE {n} segments in {time.time()-t0:.0f}s -> {args.out} (+.srt)", flush=True)
    if dup_flags:
        print(f"\n⚠️  检测到 {len(dup_flags)} 处疑似整段重复（whisper 解码回环，建议核对/重跑）:", flush=True)
        for n2, t, txt in dup_flags:
            print(f"   seg#{n2} @{t}  {txt}", flush=True)
    else:
        print("✓ 未检测到整段重复", flush=True)

if __name__ == "__main__":
    main()
