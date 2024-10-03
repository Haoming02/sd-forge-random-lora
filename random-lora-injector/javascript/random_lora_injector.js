function updateRandomLoraUI(data) {
    gradioApp().querySelector('#random_lora_injector_selected_folder').updateChoices(data.subfolders);
    gradioApp().querySelector('#random_lora_injector_cache_status').value = data.cache_status;
    gradioApp().querySelector('#random_lora_injector_debug_info').value = data.debug_info;
}

// You can add more client-side functionality here if needed