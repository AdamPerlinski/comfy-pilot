---
id: workflow_patterns
title: Workflow Patterns & Templates
keywords: [workflow, template, FLUX, SDXL, txt2img, img2img, upscale, ControlNet, AnimateDiff, WAN, Hunyuan, LoRA, two-pass, hires fix, tiled]
category: patterns
priority: medium
---

## AVAILABLE WORKFLOW PATTERNS

### Image Generation
- **flux_txt2img**: FLUX text-to-image (high quality, 12GB+ VRAM)
- **sdxl_txt2img**: SDXL text-to-image (8GB+ VRAM)
- **txt2img**: Basic SD 1.5 text-to-image (4GB+ VRAM)
- **img2img**: Image-to-image transformation
- **txt2img_with_lora**: Text-to-image with LoRA

### Upscaling
- **two_pass_hires_fix**: Two-pass generation for high resolution
- **tiled_upscale**: Tiled upscaling for large images (low VRAM)
- **upscale**: Basic ESRGAN upscaling

### Video Generation
- **animatediff_txt2vid**: AnimateDiff for SD 1.5 (requires ComfyUI-AnimateDiff-Evolved)
- **wan_video**: WAN 2.1/2.2 (Hunyuan Video) text-to-video

### ControlNet
- **controlnet_canny**: Canny edge ControlNet
- Additional ControlNet types available via modification

### Parameters typically customizable:
- checkpoint/model name
- positive/negative prompts
- width, height
- steps, cfg, sampler
- seed
- denoise (for img2img/upscale)
- frames (for video)

## WORKFLOW JSON FORMAT (API Format)

ComfyUI workflows use a JSON format where:
- Root is a dict with string node IDs as keys ("1", "2", "3")
- Each node has: `class_type`, `inputs`, optional `_meta` with `title`
- Connections between nodes: `["source_node_id", output_slot_index]`
- Widget values are set directly in `inputs`

### Example: Basic txt2img structure
```
Node 1: CheckpointLoaderSimple → outputs MODEL(0), CLIP(1), VAE(2)
Node 2: CLIPTextEncode (positive) → input clip from ["1", 1] → output CONDITIONING(0)
Node 3: CLIPTextEncode (negative) → input clip from ["1", 1] → output CONDITIONING(0)
Node 4: EmptyLatentImage → output LATENT(0)
Node 5: KSampler → inputs from ["1",0], ["2",0], ["3",0], ["4",0] → output LATENT(0)
Node 6: VAEDecode → inputs from ["5",0], ["1",2] → output IMAGE(0)
Node 7: SaveImage → input from ["6",0]
```

### Connection Rules
- Outputs are referenced by index (0-based)
- CheckpointLoaderSimple: MODEL=0, CLIP=1, VAE=2
- Most nodes have a single output at index 0
- Type must match: MODEL→MODEL, CONDITIONING→CONDITIONING, etc.
