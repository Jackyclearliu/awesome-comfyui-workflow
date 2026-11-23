# 4x Upscale on 8GB VRAM

Takes a 1024x1536 render to 4096x6144. One model load, one scale node, no manual tiling.

## Measured on

RTX 3070 Ti Laptop 8GB · Ryzen 7 6800H · 32GB RAM · Win 11 · ComfyUI 0.42.1

| Input | Output | Time |
|---|---|---|
| 1024x1536 | 4096x6144 (25 MP) | 14-16 s |
| 1024x1536 | 2048x3072 | ~18 s (includes model load) |

The upscale model is 64 MB. The 25 MP result is what pushes memory, and it completes on 8 GB.

## Install

1. Copy `upscale-4x-8gb.json` into `ComfyUI/user/default/workflows`.
2. Put `RealESRGAN_x4plus.safetensors` into `ComfyUI/models/upscale_models/`.
   It is a standard download; the workflow expects exactly that filename.
3. Open the workflow, choose your image in **LoadImage**, press Queue.

## The five nodes

| Node | What it does |
|---|---|
| LoadImage | your render |
| UpscaleModelLoader | Real-ESRGAN 4x+ |
| ImageUpscaleWithModel | the 4x pass |
| ImageScaleBy | `1.0` for true 4x, `0.5` for a 2x result with the model's detail and a quarter of the file size |
| SaveImage | writes the PNG |

The default is `1.0`. If you only need web-sized output, `0.5` is faster to store and looks nearly identical at screen size.

## Licensing

- **Real-ESRGAN 4x+ is BSD-3-Clause.** Commercial use of the output is fine.
- **4x-UltraSharp** gives crisper line art on anime images, but it is **CC-BY-NC-SA-4.0** — personal use only, no commercial output. If you swap it in, change the filename in UpscaleModelLoader and keep that limitation in mind.
- The workflow file is yours to use. Please don't resell the JSON itself.

## Notes

- Chaining it for 16x mostly adds runtime; 4x is where the model was trained.
- For batches, the model stays in memory after the first run, so each additional image costs only the upscale pass.
- Source PNGs at 4096x6144 are around 20-25 MB. Saving as JPEG q90 brings that to about 2.3 MB with no visible loss at normal viewing distance.

## Samples in this folder

- `samples/kitsune-4096x6144.jpg`, `samples/bookshop-4096x6144.jpg` — full-resolution output
- `compare/compare-*.jpg` — 256 px crops at 200%, original on the left, 4x on the right
