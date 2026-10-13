# Demo media

| File | What it is |
|---|---|
| `applyops-walkthrough.mp4` | About seven-minute walkthrough in ten chapters. **Subtitles only, no audio** |
| `walkthrough-transcript.md` | The subtitles as text, by chapter, with timestamps |
| `demo.gif` | Short loop for the README: an overclaiming letter is blocked |
| `../images/*.png` | The three screenshots used in the README |

## How these were made (and what they are not)

* Every command shown was **really executed** (in PowerShell, with the same `$c` variable that is typed on screen)
  against the fictional sample data in `examples/sample_candidate`, and its real output was captured.
* The captured text is replayed in a terminal-styled web page that was recorded with a browser automation tool.
  So the images and video are **not** raw recordings of a Windows Terminal window: they are faithful replays of
  real output. The typing is animated with uneven speed, pauses and the occasional corrected typo so that it is
  easy to follow; the commands themselves are exactly what was run.
* Long outputs are shortened where marked (for example the `pip install` result shows only its final line).
* There is no narration: the video has no audio track.
* Only fictional data appears: Alex Rivera, Acme Logistics, `example` links.
* ApplyOps does not generate resumes or PDFs yet (see the [roadmap](../ROADMAP.md)), so none are shown.

To re-create them, run the commands in the README on the sample candidate and capture the output.
