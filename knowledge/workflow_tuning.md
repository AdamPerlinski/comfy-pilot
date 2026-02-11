---
id: workflow_tuning
title: Workflow Tuning & Troubleshooting
keywords: [denoise, CFG, steps, sampler, scheduler, blurry, artifacts, faces, hands, upscale, img2img, video, flickering, ControlNet, quality, style, resolution]
category: tuning
priority: medium
---

## COMMON ISSUES & FIXES

### "Image is too similar to original" (img2img)
**Problem**: Denoise too low
**Fixes**:
- Increase denoise: 0.3→0.5 (subtle change) or 0.5→0.75 (major change)
- denoise=0.3: Minor tweaks, keeps composition
- denoise=0.5: Balanced transformation
- denoise=0.7: Significant changes
- denoise=1.0: Completely new image (ignores input)

### "Image doesn't match prompt at all"
**Problem**: Denoise too high or CFG wrong
**Fixes**:
- Lower denoise for img2img (0.4-0.6)
- Adjust CFG: too low (1-4) = ignores prompt, too high (15+) = artifacts
- Sweet spot: CFG 6-8 for most models
- Check negative prompt isn't blocking desired content

### "Image is blurry/lacks detail"
**Problem**: Not enough steps, wrong sampler, or resolution too low
**Fixes**:
- Increase steps: 20→30→40
- Use better sampler: euler→dpmpp_2m_sde
- Add detail LoRA (Detail Tweaker)
- Use two-pass/hires fix
- Check VAE - use external VAE (vae-ft-mse-840000)
- Add to prompt: "highly detailed, sharp focus, 8k"

### "Colors are washed out/dull"
**Problem**: Bad VAE or wrong model
**Fixes**:
- Use external VAE: vae-ft-mse-840000-ema-pruned
- For SDXL: sdxl_vae.safetensors
- Increase CFG slightly (7→8)
- Add "vibrant colors, vivid" to prompt

### "Artifacts/noise in image"
**Problem**: CFG too high or wrong sampler
**Fixes**:
- Lower CFG: 12→7
- Use RescaleCFG node
- Try different sampler: euler_ancestral, dpmpp_2m
- Add "noise, grain, artifacts" to negative prompt

### "Faces look bad/distorted"
**Problem**: Model limitation or resolution
**Fixes**:
- Use face restoration: CodeFormer, GFPGAN
- Use ADetailer/Impact Pack face detailer
- Generate at higher resolution
- Use face-specific LoRA
- Add "detailed face, clear face" to prompt
- Add "deformed face, ugly face" to negative

### "Hands look wrong"
**Problem**: Common SD issue
**Fixes**:
- Use hand detailer (Impact Pack)
- Add "detailed hands, correct fingers" to prompt
- Add "bad hands, extra fingers, mutated hands" to negative
- Use ControlNet with hand reference
- Use hand-fix LoRA

### "Text in image is unreadable"
**Problem**: SD models bad at text
**Fixes**:
- Use FLUX (much better at text)
- Use SD3 (improved text)
- Use ControlNet with text image
- Post-process: add text after generation

### "Composition is wrong"
**Problem**: Model doesn't understand layout
**Fixes**:
- Use ControlNet (depth, canny, pose)
- Use regional prompting
- Use img2img with rough sketch
- Be more specific in prompt about positions
- Use IP-Adapter for composition reference

### "Style is inconsistent"
**Problem**: Random variations
**Fixes**:
- Lock seed for consistency
- Use same LoRA with consistent strength
- Use style reference (IP-Adapter)
- Add specific style tags consistently

## PARAMETER EFFECTS GUIDE

### Denoise (img2img, upscale)
```
0.0-0.2: Almost no change, color correction only
0.2-0.4: Subtle changes, keeps structure
0.4-0.6: Balanced - good for refinement
0.6-0.8: Major changes, new details
0.8-1.0: Almost complete regeneration
```

**Recommendations**:
- Face fix: 0.3-0.4
- Style transfer: 0.5-0.7
- Upscale refinement: 0.3-0.5
- Major rework: 0.7-0.9

### CFG Scale (Classifier-Free Guidance)
```
1-3:   Creative, ignores prompt somewhat
4-6:   Balanced, good for artistic
7-9:   Standard, follows prompt well (RECOMMENDED)
10-12: Strict, may oversaturate
13-20: Very strict, artifacts likely
```

**Model-specific**:
- FLUX: Uses guidance in encoder, CFG=1.0 in sampler
- SDXL: 6-8 typical
- SD1.5: 7-9 typical
- Turbo/Lightning: 1-2 only

### Steps
```
1-4:   Turbo/Lightning models only
10-15: Fast preview, lower quality
20-30: Standard quality (RECOMMENDED)
30-50: Diminishing returns, slower
50+:   Usually unnecessary
```

**Model-specific**:
- FLUX: 20-30 steps
- SDXL: 25-40 steps
- SD1.5: 20-30 steps
- Turbo: 4 steps
- Lightning: 4-8 steps

### Sampler Choice
```
Fast & Good:
- euler: Fast, good quality
- dpmpp_2m: Balanced, popular choice
- dpmpp_2m_sde: High quality, bit slower

High Quality:
- dpmpp_sde: Very high quality
- dpmpp_2m_sde_karras: Excellent for detail
- dpm_2_ancestral: Good variation

Stable/Consistent:
- ddim: Stable, deterministic
- uni_pc: Fast, stable

For Turbo/Lightning:
- euler, euler_ancestral
```

### Scheduler
```
normal:      Standard, safe choice
karras:      Better for detailed images (RECOMMENDED)
exponential: Good for some models
sgm_uniform: For SGM-based models
simple:      For FLUX
beta:        Alternative option
```

### Resolution Effects
```
Lower than native: Blurry, distorted
Native resolution: Best quality
Higher than native: May tile, artifacts (use two-pass)

Native resolutions:
- SD1.5: 512x512
- SDXL: 1024x1024
- FLUX: 1024x1024 (flexible)
```

## IMG2IMG TUNING

### "Result too similar to input"
Increase denoise progressively:
```
Current → Try
0.3     → 0.5
0.5     → 0.65
0.65    → 0.8
```

### "Result ignores input completely"
Decrease denoise:
```
Current → Try
0.8     → 0.6
0.6     → 0.45
0.45    → 0.35
```

### "Want to keep composition but change style"
- denoise: 0.4-0.6
- Use style LoRA
- Add style keywords to prompt
- Consider IP-Adapter for style

### "Want to keep colors but change content"
- denoise: 0.6-0.8
- Use ControlNet (canny/depth) to keep structure
- Strong prompt for new content

### "Inpainting doesn't blend well"
- Increase feathering/blur on mask edges
- Use "only masked" option
- Increase denoise slightly
- Match prompt to surrounding area

### Optimal img2img Settings by Task
```
Photo restoration: denoise 0.3-0.4, keep details
Style transfer:    denoise 0.5-0.6, change look
Major edits:       denoise 0.7-0.8, new content
Face swap prep:    denoise 0.3-0.4, subtle blend
Colorization:      denoise 0.2-0.3, minimal change
```

## VIDEO TUNING

### "Video is too short"
**AnimateDiff**:
- Increase batch_size in EmptyLatentImage: 16→24→32
- More frames = more VRAM needed
- 16 frames ≈ 8GB, 32 frames ≈ 12GB+

**WAN/Hunyuan**:
- Increase length in EmptyHyVideoLatentVideo: 49→81→129
- length=81 ≈ 3.3 seconds at 24fps
- length=129 ≈ 5.3 seconds at 24fps

**Frame count guide**:
```
Frames  Duration@8fps  Duration@24fps  VRAM (approx)
16      2 sec          0.7 sec         6-8GB
24      3 sec          1 sec           8-10GB
32      4 sec          1.3 sec         10-12GB
48      6 sec          2 sec           12-16GB
64      8 sec          2.7 sec         16-20GB
```

### "Video has flickering"
**Fixes**:
- Use context options with overlap (AnimateDiff)
  - context_overlap: 4→8
- Enable temporal consistency in sampler
- Use consistent seed
- Add motion LoRA for smoother motion
- Reduce CFG slightly

### "Motion is too subtle/static"
**AnimateDiff**:
- Use different motion module: mm_sd_v15_v2→mm_sd_v15_v3
- Increase motion scale if available
- Add motion keywords: "dynamic, moving, action"

**WAN/Hunyuan**:
- Increase flow_shift: 7→9
- More descriptive motion in prompt
- Longer generation (more frames)

### "Motion is too chaotic/jittery"
**Fixes**:
- Decrease motion scale
- Use uniform context with more overlap
- Lower CFG: 8→6
- Increase steps
- Use motion LoRA trained for smooth motion

### "Video quality is low"
**Fixes**:
- Increase steps: 20→30
- Use higher resolution (if VRAM allows)
- Use better base checkpoint
- Enable VAE tiling for decode
- Post-process with video upscaler

### "Video loops awkwardly"
**Fixes**:
- Enable closed_loop in context options
- Use pingpong=True in video output
- Generate extra frames, trim in post

### Frame Rate Adjustment
```
VHS_VideoCombine settings:
- frame_rate=8:  Slow motion feel, smoother for few frames
- frame_rate=12: Standard animation
- frame_rate=24: Cinematic, needs more frames
- frame_rate=30: Smooth, gaming feel
```

## QUALITY IMPROVEMENT TRICKS

### General Quality Boost
1. **Two-pass generation**:
   - First pass: native resolution
   - Second pass: 1.5-2x with denoise 0.4-0.5

2. **Better sampler combo**:
   - sampler: dpmpp_2m_sde
   - scheduler: karras
   - steps: 30+

3. **Add quality prompts**:
   - Positive: "masterpiece, best quality, highly detailed, sharp"
   - Negative: "worst quality, low quality, blurry, artifacts"

4. **Use FreeU** (if available):
   - Enhances details without extra compute
   - Typical: b1=1.3, b2=1.4, s1=0.9, s2=0.2

### Detail Enhancement
1. **Detail LoRA**: Add at 0.3-0.5 strength
2. **Increase resolution** with two-pass
3. **Use upscale model** + img2img refinement
4. **Add sharpening** in post (ImageSharpen node)

### Photorealistic Improvements
1. Use realistic checkpoint (Juggernaut XL, RealVisXL)
2. Add "photo, photograph, realistic, raw photo" to prompt
3. Use negative: "painting, drawing, illustration, anime"
4. CFG 6-7 (not too high)
5. Consider adding film grain for authenticity

### Anime/Illustration Improvements
1. Use anime checkpoint (Pony, MeinaMix)
2. Add style tags: "anime, illustration, cel shading"
3. Use quality tags for Pony: "score_9, score_8_up"
4. Clean negative: "photo, realistic, 3d"

### Fixing Specific Areas
1. **Inpaint** problem areas with mask
2. Use **ADetailer** for faces/hands automatically
3. **Regional prompting** for specific parts
4. **ControlNet** to preserve good parts while regenerating

## STYLE ADJUSTMENT TRICKS

### "Want more contrast"
- Add "high contrast, dramatic lighting" to prompt
- Increase CFG slightly: 7→9
- Use post-processing: adjust levels

### "Want softer/dreamier look"
- Add "soft lighting, dreamy, ethereal, bokeh" to prompt
- Lower CFG: 7→5
- Use gaussian blur lightly in post
- Lower sharpness

### "Want more vibrant colors"
- Add "vibrant, colorful, saturated" to prompt
- Use SDXL or FLUX (better colors)
- Check VAE (use good external VAE)
- Post-process: increase saturation

### "Want muted/vintage colors"
- Add "muted colors, vintage, film" to prompt
- Add "oversaturated, neon" to negative
- Use film grain LoRA
- Post-process: decrease saturation

### "Want specific art style"
- Use style LoRA
- Use IP-Adapter with reference image
- Add artist name (if model knows it)
- Be specific: "oil painting style, impressionist, baroque"

### "Want consistent style across images"
- Lock seed
- Use same LoRA + strength
- Use same prompts structure
- Consider fine-tuning LoRA for your style
- Use IP-Adapter style reference

### Color Temperature
- Warm: "warm lighting, golden hour, amber tones"
- Cool: "cool lighting, blue tones, moonlight"
- Neutral: "neutral lighting, white balance"

## CONTROLNET TUNING

### "ControlNet effect too strong"
- Lower strength: 1.0→0.7→0.5
- Use control_end_percent < 1.0 (stop earlier)
- Softer preprocessor settings

### "ControlNet effect too weak"
- Increase strength: 0.7→0.9→1.0
- Better preprocessor settings
- Higher resolution preprocessor
- control_start_percent=0.0 (start from beginning)

### "Pose not matching reference"
- Use OpenPose with face+hands
- Higher resolution preprocessing
- Check skeleton overlay matches intent
- strength 0.8-1.0 for strict matching

### "Edges too strict/artificial"
- Lower Canny thresholds: 100/200→50/150
- Use SoftEdge instead of Canny
- Lower strength: 0.8→0.6
- HED preprocessor for softer edges

### "Depth not working well"
- Try different depth estimator: MiDaS→Zoe→LeReS
- Increase preprocessor resolution
- Use depth_leres for detailed scenes
- Adjust strength based on scene complexity

### ControlNet Strength Guide
```
0.3-0.5: Subtle guidance, creative freedom
0.5-0.7: Balanced control (RECOMMENDED)
0.7-0.9: Strong adherence to control
0.9-1.0: Strict following (may look stiff)
```

### Multi-ControlNet Tips
- Total strength shouldn't exceed 1.5-2.0
- Primary control: 0.6-0.8
- Secondary control: 0.3-0.5
- Use different control_end_percent for layering

## UPSCALE TUNING

### "Upscaled image too smooth/plastic"
- Increase denoise in refinement pass: 0.2→0.35
- Use detail-preserving upscaler (RealESRGAN, SwinIR)
- Add detail LoRA in refinement
- Sharpen in post-processing

### "Upscaled image has artifacts"
- Lower denoise: 0.5→0.3
- Use better upscale model
- Tile with overlap to reduce seams
- Reduce tile size if OOM

### "Upscale changed the style"
- Lower denoise: 0.4→0.25
- Use same checkpoint as original
- Match prompt exactly
- Use ControlNet tile for structure preservation

### "Upscale has visible seams" (tiled)
- Increase tile overlap: 32→64→128
- Use Ultimate SD Upscale (better seam handling)
- Lower denoise at seams
- seam_fix_mode options

### Upscale Model Recommendations
```
General:        RealESRGAN_x4plus
Anime:          RealESRGAN_x4plus_anime_6B
Faces:          GFPGAN, CodeFormer (face-specific)
Detail:         SwinIR, ESRGAN_4x
Fast:           RealESRGAN_x2plus (2x only)
```

### Recommended Upscale Workflow
1. Generate at native resolution
2. Upscale with model (4x)
3. VAEEncodeTiled (tile_size=512)
4. KSampler (denoise=0.3, steps=15)
5. VAEDecodeTiled
6. Optional: Sharpen/enhance

### Tile Size vs VRAM
```
Tile Size   VRAM Needed   Quality
256         4GB           Lower
512         6-8GB         Good (RECOMMENDED)
768         10-12GB       Better
1024        12-16GB       Best
```
