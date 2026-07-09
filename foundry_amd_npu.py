"""Download and run an AMD NPU model with the Foundry Local Python SDK.

Requires: pip install foundry-local-sdk  (on Windows with an AMD NPU machine).
"""

from foundry_local_sdk import Configuration, FoundryLocalManager

ALIAS = "qwen2.5-0.5b"  # any alias with an AMD NPU variant in the catalog


def main() -> None:
    FoundryLocalManager.initialize(Configuration(app_name="AmdNpuExample"))
    manager = FoundryLocalManager.instance

    # Make sure the AMD NPU EP (VitisAI) is downloaded and registered.
    manager.download_and_register_eps()

    # Get the model and pick the AMD NPU variant.
    model = manager.catalog.get_model(ALIAS)
    if model is None:
        raise SystemExit(f"Alias '{ALIAS}' not found in catalog.")

    npu_variant = next(
        (v for v in model.variants
         if v.info.runtime
         and v.info.runtime.device_type == "NPU"
         and "vitis" in v.info.runtime.execution_provider.lower()),
        None,
    )
    if npu_variant is None:
        raise SystemExit(f"No AMD NPU variant available for '{ALIAS}'.")

    model.select_variant(npu_variant)

    if not model.is_cached:
        print(f"Downloading {model.id} ...")
        model.download(progress_callback=lambda p: print(f"  {p:5.1f}%", end="\r"))
        print()

    model.load()
    try:
        response = model.get_chat_client().complete_chat(
            messages=[{"role": "user", "content": "Say hello from the AMD NPU."}]
        )
        print(response.choices[0].message.content)
    finally:
        model.unload()


if __name__ == "__main__":
    main()
