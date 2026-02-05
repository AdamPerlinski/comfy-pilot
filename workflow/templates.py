"""Pre-built workflow templates for common tasks."""

from typing import Dict, Any


class WorkflowTemplates:
    """Pre-built workflow templates for common ComfyUI tasks.

    All templates are in ComfyUI API format (not UI format).
    """

    @staticmethod
    def txt2img(
        checkpoint: str = "",
        positive_prompt: str = "",
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seed: int = 0,
    ) -> Dict[str, Any]:
        """Basic text-to-image workflow template.

        Args:
            checkpoint: Checkpoint filename (e.g., "v1-5-pruned.safetensors")
            positive_prompt: Positive prompt text
            negative_prompt: Negative prompt text
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of sampling steps
            cfg: CFG scale
            sampler: Sampler name (euler, euler_ancestral, dpm_2, etc.)
            scheduler: Scheduler name (normal, karras, exponential, etc.)
            seed: Random seed (0 for random)

        Returns:
            ComfyUI workflow dict in API format
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": checkpoint
                },
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["1", 1]
                },
                "_meta": {"title": "Positive Prompt"}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                },
                "_meta": {"title": "Negative Prompt"}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "_meta": {"title": "Empty Latent"}
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                },
                "_meta": {"title": "KSampler"}
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                },
                "_meta": {"title": "VAE Decode"}
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["6", 0],
                    "filename_prefix": "comfy_pilot"
                },
                "_meta": {"title": "Save Image"}
            }
        }

    @staticmethod
    def img2img(
        checkpoint: str = "",
        positive_prompt: str = "",
        negative_prompt: str = "",
        denoise: float = 0.75,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seed: int = 0,
    ) -> Dict[str, Any]:
        """Image-to-image workflow template.

        Requires an input image to be connected to the LoadImage node.
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": checkpoint
                },
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": ""
                },
                "_meta": {"title": "Load Image"}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["1", 1]
                },
                "_meta": {"title": "Positive Prompt"}
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                },
                "_meta": {"title": "Negative Prompt"}
            },
            "5": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["2", 0],
                    "vae": ["1", 2]
                },
                "_meta": {"title": "VAE Encode"}
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0]
                },
                "_meta": {"title": "KSampler"}
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["1", 2]
                },
                "_meta": {"title": "VAE Decode"}
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["7", 0],
                    "filename_prefix": "comfy_pilot_i2i"
                },
                "_meta": {"title": "Save Image"}
            }
        }

    @staticmethod
    def upscale(
        upscale_model: str = "RealESRGAN_x4plus.pth",
    ) -> Dict[str, Any]:
        """Simple upscale workflow using ESRGAN models."""
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": ""
                },
                "_meta": {"title": "Load Image"}
            },
            "2": {
                "class_type": "UpscaleModelLoader",
                "inputs": {
                    "model_name": upscale_model
                },
                "_meta": {"title": "Load Upscale Model"}
            },
            "3": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["2", 0],
                    "image": ["1", 0]
                },
                "_meta": {"title": "Upscale Image"}
            },
            "4": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["3", 0],
                    "filename_prefix": "comfy_pilot_upscale"
                },
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== FLUX ====================

    @staticmethod
    def flux_txt2img(
        unet: str = "flux1-dev.safetensors",
        clip_l: str = "clip_l.safetensors",
        t5xxl: str = "t5xxl_fp16.safetensors",
        vae: str = "ae.safetensors",
        positive_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        guidance: float = 3.5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """FLUX text-to-image workflow.

        Requires: FLUX UNET, CLIP-L, T5-XXL, FLUX VAE
        VRAM: 12GB+ (fp8), 24GB+ (fp16)
        """
        return {
            "1": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": unet,
                    "weight_dtype": "fp8_e4m3fn"
                },
                "_meta": {"title": "Load FLUX UNET"}
            },
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": clip_l,
                    "clip_name2": t5xxl,
                    "type": "flux"
                },
                "_meta": {"title": "Load CLIP"}
            },
            "3": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": vae},
                "_meta": {"title": "Load VAE"}
            },
            "4": {
                "class_type": "CLIPTextEncodeFlux",
                "inputs": {
                    "clip": ["2", 0],
                    "clip_l": positive_prompt,
                    "t5xxl": positive_prompt,
                    "guidance": guidance
                },
                "_meta": {"title": "FLUX Text Encode"}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "_meta": {"title": "Empty Latent"}
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["4", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler"}
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["3", 0]
                },
                "_meta": {"title": "VAE Decode"}
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["7", 0],
                    "filename_prefix": "flux"
                },
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== SDXL ====================

    @staticmethod
    def sdxl_txt2img(
        checkpoint: str = "",
        positive_prompt: str = "",
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg: float = 7.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """SDXL text-to-image workflow.

        VRAM: 8GB minimum, 12GB+ recommended
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load SDXL Checkpoint"}
            },
            "2": {
                "class_type": "CLIPTextEncodeSDXL",
                "inputs": {
                    "clip": ["1", 1],
                    "text_g": positive_prompt,
                    "text_l": positive_prompt,
                    "width": width,
                    "height": height,
                    "crop_w": 0,
                    "crop_h": 0,
                    "target_width": width,
                    "target_height": height
                },
                "_meta": {"title": "Positive SDXL"}
            },
            "3": {
                "class_type": "CLIPTextEncodeSDXL",
                "inputs": {
                    "clip": ["1", 1],
                    "text_g": negative_prompt,
                    "text_l": negative_prompt,
                    "width": width,
                    "height": height,
                    "crop_w": 0,
                    "crop_h": 0,
                    "target_width": width,
                    "target_height": height
                },
                "_meta": {"title": "Negative SDXL"}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "_meta": {"title": "Empty Latent"}
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler"}
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                },
                "_meta": {"title": "VAE Decode"}
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["6", 0],
                    "filename_prefix": "sdxl"
                },
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== TWO-PASS / HIRES FIX ====================

    @staticmethod
    def two_pass_hires(
        checkpoint: str = "",
        positive_prompt: str = "",
        negative_prompt: str = "",
        initial_width: int = 768,
        initial_height: int = 768,
        final_width: int = 1536,
        final_height: int = 1536,
        first_pass_steps: int = 20,
        second_pass_steps: int = 15,
        second_pass_denoise: float = 0.5,
        cfg: float = 7.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """Two-pass generation with hires fix.

        Pass 1: Generate at lower resolution
        Pass 2: Upscale latent and refine
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Positive Prompt"}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Negative Prompt"}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": initial_width,
                    "height": initial_height,
                    "batch_size": 1
                },
                "_meta": {"title": "Initial Latent (Pass 1)"}
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": first_pass_steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler Pass 1"}
            },
            "6": {
                "class_type": "LatentUpscale",
                "inputs": {
                    "samples": ["5", 0],
                    "upscale_method": "bilinear",
                    "width": final_width,
                    "height": final_height,
                    "crop": "disabled"
                },
                "_meta": {"title": "Upscale Latent"}
            },
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["6", 0],
                    "seed": seed,
                    "steps": second_pass_steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": second_pass_denoise
                },
                "_meta": {"title": "KSampler Pass 2 (Hires)"}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"images": ["8", 0], "filename_prefix": "hires"},
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== TILED (LOW VRAM) ====================

    @staticmethod
    def tiled_upscale(
        checkpoint: str = "",
        upscale_model: str = "RealESRGAN_x4plus.pth",
        positive_prompt: str = "",
        negative_prompt: str = "",
        denoise: float = 0.35,
        tile_size: int = 512,
        steps: int = 15,
        cfg: float = 7.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """Tiled upscaling for large images with low VRAM.

        Uses VAEEncodeTiled and VAEDecodeTiled for memory efficiency.
        """
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": ""},
                "_meta": {"title": "Load Input Image"}
            },
            "2": {
                "class_type": "UpscaleModelLoader",
                "inputs": {"model_name": upscale_model},
                "_meta": {"title": "Load Upscale Model"}
            },
            "3": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["2", 0],
                    "image": ["1", 0]
                },
                "_meta": {"title": "Upscale 4x"}
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["4", 1]},
                "_meta": {"title": "Positive"}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["4", 1]},
                "_meta": {"title": "Negative"}
            },
            "7": {
                "class_type": "VAEEncodeTiled",
                "inputs": {
                    "pixels": ["3", 0],
                    "vae": ["4", 2],
                    "tile_size": tile_size
                },
                "_meta": {"title": "VAE Encode Tiled"}
            },
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["4", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["7", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": denoise
                },
                "_meta": {"title": "KSampler (Refine)"}
            },
            "9": {
                "class_type": "VAEDecodeTiled",
                "inputs": {
                    "samples": ["8", 0],
                    "vae": ["4", 2],
                    "tile_size": tile_size
                },
                "_meta": {"title": "VAE Decode Tiled"}
            },
            "10": {
                "class_type": "SaveImage",
                "inputs": {"images": ["9", 0], "filename_prefix": "upscaled"},
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== VIDEO - ANIMATEDIFF ====================

    @staticmethod
    def animatediff_txt2vid(
        checkpoint: str = "",
        motion_module: str = "mm_sd_v15_v2.ckpt",
        positive_prompt: str = "",
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        frames: int = 16,
        steps: int = 20,
        cfg: float = 7.5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """AnimateDiff text-to-video workflow.

        Requires: ComfyUI-AnimateDiff-Evolved custom node
        Uses SD 1.5 checkpoints with motion modules
        VRAM: 8GB+ for 16 frames
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load SD 1.5 Checkpoint"}
            },
            "2": {
                "class_type": "ADE_AnimateDiffLoaderWithContext",
                "inputs": {
                    "model": ["1", 0],
                    "context_options": ["3", 0],
                    "motion_model": motion_module,
                    "beta_schedule": "autoselect"
                },
                "_meta": {"title": "AnimateDiff Loader"}
            },
            "3": {
                "class_type": "ADE_AnimateDiffUniformContextOptions",
                "inputs": {
                    "context_length": 16,
                    "context_stride": 1,
                    "context_overlap": 4,
                    "closed_loop": False
                },
                "_meta": {"title": "Context Options"}
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Positive Prompt"}
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Negative Prompt"}
            },
            "6": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": frames
                },
                "_meta": {"title": "Empty Latent (Frames)"}
            },
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["6", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler"}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": 8,
                    "loop_count": 0,
                    "filename_prefix": "animatediff",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True
                },
                "_meta": {"title": "Save Video"}
            }
        }

    # ==================== VIDEO - WAN / HUNYUAN ====================

    @staticmethod
    def wan_hunyuan_video(
        positive_prompt: str = "",
        width: int = 848,
        height: int = 480,
        frames: int = 81,
        steps: int = 30,
        cfg: float = 6.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """WAN 2.1/2.2 (Hunyuan Video) text-to-video workflow.

        Requires: ComfyUI-HunyuanVideoWrapper custom node
        VRAM: 12GB+ (fp8), 24GB+ (fp16)
        Resolution: 848x480 or 1280x720
        """
        return {
            "1": {
                "class_type": "HyVideoModelLoader",
                "inputs": {
                    "model": "hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors",
                    "base_precision": "fp8_e4m3fn",
                    "quantization": "disabled"
                },
                "_meta": {"title": "Load Hunyuan Model"}
            },
            "2": {
                "class_type": "HyVideoVAELoader",
                "inputs": {
                    "model_name": "hunyuan_video_vae_fp32.safetensors",
                    "precision": "fp16"
                },
                "_meta": {"title": "Load Video VAE"}
            },
            "3": {
                "class_type": "DownloadAndLoadHyVideoTextEncoder",
                "inputs": {
                    "llm_model": "Kijai/llava-llama-3-8b-text-encoder-tokenizer",
                    "clip_model": "openai/clip-vit-large-patch14",
                    "precision": "fp16"
                },
                "_meta": {"title": "Load Text Encoders"}
            },
            "4": {
                "class_type": "HyVideoTextEncode",
                "inputs": {
                    "text_encoders": ["3", 0],
                    "prompt": positive_prompt
                },
                "_meta": {"title": "Encode Text"}
            },
            "5": {
                "class_type": "EmptyHyVideoLatentVideo",
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": frames,
                    "batch_size": 1
                },
                "_meta": {"title": "Empty Video Latent"}
            },
            "6": {
                "class_type": "HyVideoSampler",
                "inputs": {
                    "model": ["1", 0],
                    "hyvid_embeds": ["4", 0],
                    "samples": ["5", 0],
                    "steps": steps,
                    "embedded_guidance_scale": cfg,
                    "flow_shift": 7.0,
                    "seed": seed
                },
                "_meta": {"title": "Video Sampler"}
            },
            "7": {
                "class_type": "HyVideoDecode",
                "inputs": {
                    "vae": ["2", 0],
                    "samples": ["6", 0],
                    "enable_vae_tiling": True
                },
                "_meta": {"title": "Decode Video"}
            },
            "8": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["7", 0],
                    "frame_rate": 24,
                    "filename_prefix": "hunyuan_video",
                    "format": "video/h264-mp4"
                },
                "_meta": {"title": "Save Video"}
            }
        }

    # ==================== CONTROLNET ====================

    @staticmethod
    def controlnet_canny(
        checkpoint: str = "",
        controlnet_model: str = "control_v11p_sd15_canny.pth",
        positive_prompt: str = "",
        negative_prompt: str = "",
        controlnet_strength: float = 1.0,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """ControlNet Canny edge workflow.

        Requires: ControlNet Auxiliary Preprocessors custom node
        """
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "class_type": "ControlNetLoader",
                "inputs": {"control_net_name": controlnet_model},
                "_meta": {"title": "Load ControlNet"}
            },
            "3": {
                "class_type": "LoadImage",
                "inputs": {"image": ""},
                "_meta": {"title": "Load Reference Image"}
            },
            "4": {
                "class_type": "CannyEdgePreprocessor",
                "inputs": {
                    "image": ["3", 0],
                    "low_threshold": 100,
                    "high_threshold": 200,
                    "resolution": 512
                },
                "_meta": {"title": "Canny Edge Detection"}
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Positive Prompt"}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["1", 1]},
                "_meta": {"title": "Negative Prompt"}
            },
            "7": {
                "class_type": "ControlNetApply",
                "inputs": {
                    "conditioning": ["5", 0],
                    "control_net": ["2", 0],
                    "image": ["4", 0],
                    "strength": controlnet_strength
                },
                "_meta": {"title": "Apply ControlNet"}
            },
            "8": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
                "_meta": {"title": "Empty Latent"}
            },
            "9": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["7", 0],
                    "negative": ["6", 0],
                    "latent_image": ["8", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler"}
            },
            "10": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["9", 0], "vae": ["1", 2]},
                "_meta": {"title": "VAE Decode"}
            },
            "11": {
                "class_type": "SaveImage",
                "inputs": {"images": ["10", 0], "filename_prefix": "controlnet"},
                "_meta": {"title": "Save Image"}
            }
        }

    # ==================== LORA ====================

    @staticmethod
    def txt2img_with_lora(
        checkpoint: str = "",
        lora_name: str = "",
        lora_strength: float = 0.8,
        positive_prompt: str = "",
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """Text-to-image with LoRA."""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": ["1", 0],
                    "clip": ["1", 1],
                    "lora_name": lora_name,
                    "strength_model": lora_strength,
                    "strength_clip": lora_strength
                },
                "_meta": {"title": "Load LoRA"}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["2", 1]},
                "_meta": {"title": "Positive Prompt"}
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["2", 1]},
                "_meta": {"title": "Negative Prompt"}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
                "_meta": {"title": "Empty Latent"}
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0
                },
                "_meta": {"title": "KSampler"}
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
                "_meta": {"title": "VAE Decode"}
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {"images": ["7", 0], "filename_prefix": "lora"},
                "_meta": {"title": "Save Image"}
            }
        }
