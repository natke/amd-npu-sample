"""Run an AMD NPU (VitisAI) ONNX model directly with ONNX Runtime GenAI.

Bypasses the Foundry Local SDK/Core so you can bisect ORT / ORT-GenAI / EP
versions independently. Uses the same alias as `foundry_amd_npu.py` and
looks for the model in the Foundry Local model cache — run that script
first (or `foundry model load <alias>`) so the AMD NPU variant is cached.

Locates the AMD NPU EP by scanning `C:\\Program Files\\WindowsApps` for the
`MicrosoftCorporationII.WinML.AMD.NPU.EP.*` MSIX package.
"""

import glob
import os
import sys
import time
from pathlib import Path

import onnxruntime_genai as og

ALIAS = "qwen2.5-0.5b"  # keep in sync with foundry_amd_npu.py
PROMPT = "Say hello from the AMD NPU."
MAX_LENGTH = 128
EP_NAME = "VitisAIExecutionProvider"
EP_DLL = "onnxruntime_providers_vitisai.dll"
EP_PKG_GLOB = r"C:\Program Files\WindowsApps\MicrosoftCorporationII.WinML.AMD.NPU.EP.*"

FOUNDRY_MODELS_DIR = Path.home() / ".foundry" / "cache" / "models" / "Microsoft"


def step(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def find_model_folder() -> Path:
    """Locate the AMD NPU (VitisAI) variant folder for ALIAS in the Foundry cache."""
    if not FOUNDRY_MODELS_DIR.is_dir():
        sys.exit(f"Foundry model cache not found at {FOUNDRY_MODELS_DIR}. "
                 f"Run foundry_amd_npu.py first to download the model.")
    for cfg in FOUNDRY_MODELS_DIR.rglob("genai_config.json"):
        name = str(cfg.parent).lower()
        if ALIAS.lower() in name and "vitis" in name:
            return cfg.parent
    sys.exit(f"No AMD NPU variant of '{ALIAS}' found in {FOUNDRY_MODELS_DIR}. "
             f"Run foundry_amd_npu.py first to download it.")


def find_ep_dll() -> Path:
    """Locate onnxruntime_providers_vitisai.dll in the AMD NPU EP MSIX package."""
    for pkg in glob.glob(EP_PKG_GLOB):
        for dll in Path(pkg).rglob(EP_DLL):
            return dll
    sys.exit(f"Could not find {EP_DLL} under {EP_PKG_GLOB}. "
             f"Is the AMD NPU EP installed via Windows Update / Foundry Local?")


def main() -> None:
    step(f"onnxruntime-genai version: {og.__version__}")

    model_path = find_model_folder()
    step(f"Model folder: {model_path}")

    ep_dll = find_ep_dll()
    step(f"EP library:    {ep_dll}")

    # Make sibling helper DLLs (e.g. onnxruntime_vitis_ai_custom_ops.dll) discoverable.
    os.add_dll_directory(str(ep_dll.parent))

    step(f"Registering EP: {EP_NAME}")
    og.register_execution_provider_library(EP_NAME, str(ep_dll))

    step("Building config (forcing VitisAI EP) ...")
    config = og.Config(str(model_path))
    config.clear_providers()
    config.append_provider(EP_NAME)

    step("Building model (first NPU compile can take minutes) ...")
    t0 = time.time()
    model = og.Model(config)
    step(f"Model built in {time.time() - t0:.1f}s.")

    tokenizer = og.Tokenizer(model)
    tokenizer_stream = tokenizer.create_stream()

    input_tokens = tokenizer.encode(PROMPT)

    params = og.GeneratorParams(model)
    params.set_search_options(max_length=MAX_LENGTH)

    step(f"Prompt: {PROMPT!r}")
    step("Generating ...")
    t0 = time.time()

    generator = og.Generator(model, params)
    generator.append_tokens(input_tokens)

    first_token_time = None
    print()
    while not generator.is_done():
        generator.generate_next_token()
        if first_token_time is None:
            first_token_time = time.time() - t0
        new_token = generator.get_next_tokens()[0]
        print(tokenizer_stream.decode(new_token), end="", flush=True)
    print()

    step(f"First token: {first_token_time:.2f}s  Total: {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()


