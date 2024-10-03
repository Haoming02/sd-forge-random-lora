# Random LoRA Injector Extension for Stable Diffusion WebUI

This extension for the Automatic1111 Stable Diffusion WebUI allows you to randomly inject LoRA models into your prompts, adding variety and unpredictability to your generated images.

## Features

- Randomly selects a LoRA from a specified folder
- Injects the selected LoRA and its activation text into your prompt
- Caches LoRA information for faster subsequent use
- Allows custom weight override for LoRA application
- Displays debug information for transparency

## Installation

1. Clone this repository into the `extensions` folder of your Stable Diffusion WebUI installation:
   ```
   git clone https://github.com/yourusername/sd-webui-random-lora-injector.git
   ```
2. Restart your Stable Diffusion WebUI.

## Usage

1. In the Stable Diffusion WebUI, look for the "Random LoRA Injector" accordion in the main interface.
2. Enable the Random LoRA Injector by checking the "Enable Random Character LoRA" box.
3. Select the folder containing your LoRA models from the dropdown menu.
4. Click "Cache Selected Folder" to load the LoRAs (only needed once per folder, unless you add new LoRAs).
5. Optionally, adjust the LoRA Weight Override if you want to change the default strength.
6. Generate your image as usual. The extension will randomly select and inject a LoRA from the chosen folder into your prompt.

## Notes

- This extension expects LoRA models to have accompanying JSON files with the same name, containing an "activation text" field.
- The injected LoRA and its activation text will be added to the beginning of your prompt.
- Debug information, including the selected LoRA and modified prompt, will be displayed in the generation info.

## Support

If you encounter any issues or have suggestions for improvements, please open an issue on the GitHub repository.

Enjoy adding random LoRA flavor to your generations!
