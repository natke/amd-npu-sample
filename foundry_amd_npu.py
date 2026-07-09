"""Download and run an AMD NPU model with the Foundry Local Python SDK.

Requires: pip install foundry-local-sdk-winml  (on Windows with an AMD NPU machine).
"""

import time

from foundry_local_sdk import Configuration, FoundryLocalManager

ALIAS = "qwen2.5-0.5b"  # any alias with an AMD NPU variant in the catalog


def step(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> None:
    step("Initializing Foundry Local Manager (starts daemon)...")
    FoundryLocalManager.initialize(Configuration(app_name="AmdNpuExample"))
    manager = FoundryLocalManager.instance
    step("Manager initialized.")

    step("Discovering execution providers...")
    for ep in manager.discover_eps():
        step(f"  - {ep.name} (registered: {ep.is_registered})")

    step("Downloading and registering EPs (this can take a while on first run)...")
    result = manager.download_and_register_eps(
        progress_callback=lambda ep, pct: print(f"    {ep}: {pct:5.1f}%", end="\r", flush=True)
    )
    print()
    step(f"EP registration: success={result.success} status={result.status} "
         f"registered={result.registered_eps} failed={result.failed_eps}")

    step(f"Looking up model alias '{ALIAS}'...")
    model = manager.catalog.get_model(ALIAS)
    if model is None:
        raise SystemExit(f"Alias '{ALIAS}' not found in catalog.")

    step("Available variants:")
    for v in model.variants:
        rt = v.info.runtime
        step(f"  - {v.id}  device={rt.device_type if rt else '?'}  "
             f"ep={rt.execution_provider if rt else '?'}  cached={v.is_cached}")

    npu_variant = next(
        (v for v in model.variants
         if v.info.runtime
         and v.info.runtime.device_type == "NPU"
         and "vitis" in v.info.runtime.execution_provider.lower()),
        None,
    )
    if npu_variant is None:
        raise SystemExit(f"No AMD NPU variant available for '{ALIAS}'.")
    step(f"Selected variant: {npu_variant.id}")
    model.select_variant(npu_variant)

    if not model.is_cached:
        step("Downloading model...")
        model.download(progress_callback=lambda p: print(f"    {p:5.1f}%", end="\r", flush=True))
        print()
        step("Download complete.")
    else:
        step("Model already cached.")

    step("Loading model (first NPU load can take minutes)...")
    t0 = time.time()
    model.load()
    step(f"Model loaded in {time.time() - t0:.1f}s.")

    try:
        step("Sending chat request...")
        t0 = time.time()
        response = model.get_chat_client().complete_chat(
            messages=[{"role": "user", "content": "Say hello from the AMD NPU."}]
        )
        step(f"Response received in {time.time() - t0:.1f}s:")
        print(response.choices[0].message.content)
    finally:
        step("Unloading model...")
        model.unload()
        step("Done.")


if __name__ == "__main__":
    main()

