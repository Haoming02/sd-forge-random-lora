import os.path
import random
from json import load

import gradio as gr
from modules import paths, scripts, shared
from modules.processing import StableDiffusionProcessing, fix_seed
from modules.ui_components import InputAccordion


class RandomLoraInjector(scripts.Script):
    subfolders: dict[str, tuple[str]]

    def __init__(self):
        if not getattr(RandomLoraInjector, "subfolders", None):
            RandomLoraInjector.get_subfolders()

    def title(self):
        return "Random LoRA"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        lora_folders = tuple(RandomLoraInjector.subfolders.keys())

        with InputAccordion(False, label=self.title()) as enabled:
            selected_folder = gr.Dropdown(
                label="Select Subfolder for Random LoRA",
                value=lora_folders[0],
                choices=lora_folders,
            )
            weight_override = gr.Slider(
                label="LoRA Weight Override",
                value=0.0,
                minimum=-2.0,
                maximum=2.0,
                step=0.1,
            )

        selected_folder.do_not_save_to_config = True
        weight_override.do_not_save_to_config = True

        return [enabled, selected_folder, weight_override]

    @classmethod
    def get_subfolders(cls):
        mappings = {}

        lora_folder: str = getattr(shared.cmd_opts, "lora_dir", os.path.join(paths.models_path, "Lora"))
        model_folder: str = os.path.dirname(lora_folder)

        for file in shared.walk_files(lora_folder, allowed_extensions=[".pt", ".ckpt", ".safetensors"]):
            assert os.path.isfile(file)
            path = os.path.relpath(file, model_folder)

            while True:
                path = path.rsplit(os.sep, 1)[0]
                mappings[path] = mappings.get(path, []) + [file]
                if os.sep not in path:
                    break

        cls.subfolders = {folder: tuple(mappings[folder]) for folder in sorted(mappings.keys())}

    @staticmethod
    def find_metadata(path: str) -> dict:
        json_file = os.path.splitext(path)[0] + ".json"
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                metadata = load(f)
            return metadata
        except Exception:
            return {}

    @staticmethod
    def inject_lora(
        p: StableDiffusionProcessing,
        lora_name: str,
        positive: str,
        negative: str,
        weight: float,
    ):
        w = weight or getattr(shared.opts, "extra_networks_default_multiplier", 1.0)

        if positive:
            p.prompt += f", {positive}"

        p.prompt += f" <lora:{lora_name}:{w}>"

        if negative:
            p.negative_prompt += f", {negative}"

    def setup(
        self,
        p: StableDiffusionProcessing,
        enabled: bool,
        selected_folder: str,
        weight_override: float,
    ):
        if not enabled:
            return

        fix_seed(p)
        random.seed(p.seed)

        files: tuple[str] = RandomLoraInjector.subfolders[selected_folder]
        lora: str = files[random.randint(1, len(files)) - 1]
        metadata: dict = RandomLoraInjector.find_metadata(lora)

        RandomLoraInjector.inject_lora(
            p,
            os.path.splitext(os.path.basename(lora))[0],
            metadata.get("activation text", None),
            metadata.get("negative text", None),
            weight_override or metadata.get("preferred weight", 0.0),
        )
