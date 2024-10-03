import os
import json
import random
import time
import gradio as gr
from modules import scripts, shared, processing

# Path to cache directory
CACHE_DIR = os.path.join(scripts.basedir(), "random-lora-injector", "cache")

class RandomLoraInjector(scripts.Script):
    def __init__(self):
        self.base_dir = "models/Lora"
        self.subfolders = self.get_subfolders(self.base_dir)
        self.lora_cache = {}
        self.cache_status = "No folder cached"
        self.debug_info = ""

    def title(self):
        return "Random LoRA Injector"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("Random LoRA Injector", open=False):
                enabled = gr.Checkbox(label="Enable Random LoRA Injector", value=False)
                selected_folder = gr.Dropdown(label="Select Subfolder for Random LoRA", choices=self.subfolders)
                cache_button = gr.Button(label="Cache Selected Folder")
                force_recache = gr.Checkbox(label="Force Recache", value=False)
                show_lora_name = gr.Checkbox(label="Display LoRA Name in Info", value=False)
                weight_override = gr.Number(label="LoRA Weight Override", value=1, minimum=0.01, step=0.01)
                cache_status = gr.Textbox(label="Cache Status", interactive=False)
                debug_info = gr.Textbox(label="Debug Info", interactive=False)

        cache_button.click(
            fn=self.populate_cache,
            inputs=[selected_folder, force_recache],
            outputs=[cache_status, debug_info]
        )

        return [enabled, selected_folder, show_lora_name, weight_override, cache_status, debug_info]

    def get_subfolders(self, folder):
        subfolders = []
        for root, dirs, files in os.walk(folder):
            subfolders.append(root)
        return sorted(subfolders)

    def get_all_lora_files(self, folder):
        lora_files = []
        for root, dirs, files in os.walk(folder):
            lora_files.extend([os.path.join(root, f) for f in files if f.endswith(('.safetensors', '.pt'))])
        return lora_files

    def get_cache_file_path(self, folder):
        folder_name = os.path.basename(folder)
        safe_folder_name = ''.join(c for c in folder_name if c.isalnum() or c in (' ', '_', '-'))
        return os.path.join(CACHE_DIR, f"{safe_folder_name}_cache.json")

    def load_cache(self, folder):
        cache_file = self.get_cache_file_path(folder)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache for {folder}: {e}")
        return None

    def save_cache(self, folder, cache_data):
        cache_file = self.get_cache_file_path(folder)
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving cache for {folder}: {e}")

    def extract_metadata_from_json(self, lora_file):
        json_file = os.path.splitext(lora_file)[0] + ".json"
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('activation text')
        except Exception as e:
            print(f"Error reading JSON metadata for {lora_file}: {e}")
        return None

    def populate_cache(self, folder, force_recache=False):
        existing_cache = self.load_cache(folder)
        if existing_cache and not force_recache:
            self.lora_cache[folder] = existing_cache
            self.cache_status = f"Loaded existing cache for {folder}"
            return self.cache_status, ""

        start_time = time.time()
        lora_count = 0
        new_cache = []
        
        try:
            lora_files = self.get_all_lora_files(folder)
            for lora_file in lora_files:
                activation_text = self.extract_metadata_from_json(lora_file)
                if activation_text:
                    lora_name = os.path.splitext(os.path.basename(lora_file))[0]
                    new_cache.append({
                        "file": lora_file,
                        "name": lora_name,
                        "prompt": f"<lora:{lora_name}:1>",
                        "activation_text": activation_text
                    })
                    lora_count += 1
            
            self.lora_cache[folder] = new_cache
            self.save_cache(folder, new_cache)
            duration = time.time() - start_time
            self.cache_status = f"Cached {lora_count} LoRAs in {duration:.1f} seconds"
        except Exception as e:
            self.cache_status = f"Error caching folder: {str(e)}"
        
        return self.cache_status, "Cache updated"

    def get_random_lora_from_cache(self, folder):
        if folder in self.lora_cache and self.lora_cache[folder]:
            return random.choice(self.lora_cache[folder])
        return None

    def inject_lora_into_prompt(self, original_prompt: str, lora_name: str, activation_text: str, weight: float) -> str:
        if not original_prompt:
            return f"<lora:{lora_name}:{weight}>, {activation_text}"
        
        parts = original_prompt.split(',')
        lora_parts = [p.strip() for p in parts if p.strip().startswith('<lora:')]
        non_lora_parts = [p.strip() for p in parts if not p.strip().startswith('<lora:')]
        
        lora_prompt_with_weight = f"<lora:{lora_name}:{weight}>"
        
        final_parts = [lora_prompt_with_weight] + lora_parts + [activation_text] + non_lora_parts
        return ', '.join(part for part in final_parts if part)

    def process(self, p, enabled, selected_folder, show_lora_name, weight_override, cache_status, debug_info):
        if not enabled or not selected_folder:
            return p

        if selected_folder not in self.lora_cache:
            self.populate_cache(selected_folder)

        random_lora = self.get_random_lora_from_cache(selected_folder)
        if not random_lora:
            debug_info = f"No valid LoRA files found in cache for folder: {selected_folder}"
            return p

        lora_name = random_lora["name"]
        activation_text = random_lora["activation_text"]

        debug_info = f"Selected LoRA: {lora_name}\nWeight: {weight_override}\nActivation: {activation_text}\n\n"

        original_prompt = p.prompt
        original_negative_prompt = p.negative_prompt

        p.all_prompts = []
        p.all_negative_prompts = []
        
        for i in range(p.batch_size * p.n_iter):
            modified_prompt = self.inject_lora_into_prompt(original_prompt, lora_name, activation_text, weight_override)
            p.all_prompts.append(modified_prompt)
            p.all_negative_prompts.append(original_negative_prompt)

            debug_info += f"Batch {i + 1} Prompt: {modified_prompt}\n"

        p.prompt = p.all_prompts[0]

        if show_lora_name:
            if not hasattr(p, 'extra_generation_params'):
                p.extra_generation_params = {}
            p.extra_generation_params["Chosen LoRA"] = lora_name

        return p

    def run(self, p, *args):
        enabled, selected_folder, show_lora_name, weight_override, cache_status, debug_info = args
        
        if not enabled:
            return processing.process_images(p)

        p = self.process(p, enabled, selected_folder, show_lora_name, weight_override, cache_status, debug_info)
        processed = processing.process_images(p)
        
        if not hasattr(processed, 'info'):
            processed.info = ""
        processed.info += f"\n\nRandom LoRA Injector Debug Info:\n{debug_info}"
        
        return processed