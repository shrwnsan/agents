# Capture: patch → WebM/MP4 loop, headless

Production pick for accent motion: record the patch once in a headless browser,
ship the file, let visitors decode instead of simulate.

## The path that works: WebCodecs + a muxer, in-page

`MediaRecorder` on `canvas.captureStream()` produces **0-byte files** in
headless Chromium (compositor-dependent) — verified, not a codec-string problem.
Encode frames explicitly instead:

1. **Muxer.** UMD builds, pinned:
   - `webm-muxer` **5.1.4** (latest of the 5.x line) — global `WebMMuxer`
   - `mp4-muxer` **5.2.1** — global `Mp4Muxer`, IIFE at `/build/mp4-muxer.js`
2. **Codec.** `avc1` (H.264-in-MP4) is unsupported in this headless build; use
   VP9: codec string `vp09.00.10.08` with `webm-muxer`, or `avc1.640028` with
   `mp4-muxer` on builds that have it. Probe with `VideoEncoder.isConfigSupported`.
3. **Frames.** After a ~3 s warmup (feedback patches), sample the canvas at a
   fixed cadence — `createImageBitmap(canvas)` post-rAF captures the current
   buffer fine (12 fps sampling read well for slow drift patches; slow-motion
   playback at a slower rate is often the right look for ambient accents).
4. **Encode.** `new VideoEncoder({output: m.addVideoChunk, error})`, configure
   `{codec, width, height, bitrate, framerate}`, then per frame:
   `enc.encode(frame, {keyFrame: i % 24 === 0}); frame.close(); bmp.close();`,
   finally `await enc.flush(); muxer.finalize();`
5. **Get the file out.** `fetch('http://127.0.0.1:PORT/upload', {method:'POST',
   body: muxer.target.buffer})` to a local Node endpoint. Localhost HTTP inside
   the container is fine; the rig server must send
   `Access-Control-Allow-Origin: *` — the page's requests come from a null
   origin otherwise and the upload silently fails CORS.
6. **Verify the artifact.** File size (a 10 s 800×450 VP9 loop ≈ hundreds of
   KB; 0 B = the recorder path, not the encoder path), duration, and decode one
   frame back through `png-lum.mjs` for the luminance check.

## Seamless looping

Feedback patches are chaotic: the last frame will not equal the first. Options
in order of honesty:

- **Accept the cut** for very slow drifts (speed ≤ 0.02 reads as continuous).
- **Crossfade** the seam on the consumer side (two stacked elements alternating,
  short CSS/DOM opacity ramp) — no re-encode needed.
- Design the patch period-matched — only realistic for pure-procedural patches,
  where the micro-shader port ([micro-shader.md](micro-shader.md)) gives you
  exact control of the time term anyway.

## Shipping checklist for the loop

- [ ] `muted`, `autoplay`, `playsinline`, `loop` attributes on `<video>`.
- [ ] `prefers-reduced-motion` → static poster frame instead.
- [ ] Pause/play control for decorative motion; pause when off-screen.
- [ ] Under ~500 KB for an accent band; drop bitrate before resolution.
- [ ] Poster attribute set so layout doesn't flash.
