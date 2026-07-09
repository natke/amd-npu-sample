"""Run an AMD NPU (VitisAI) ONNX model directly with ONNX Runtime GenAI.

Bypasses the Foundry Local SDK/Core so you can bisect ORT / ORT-GenAI / EP
versions independently.

Point --model at a Foundry Local model cache folder that contains a
`genai_config.json` configured for VitisAIExecutionProvider — e.g. the
folder Foundry Local downloads under:
  %LOCALAPPDATA%\Microsoft\FoundryLocal\models\<model-id>\
"""

import argparse
import sys
import time

import onnxruntime_genai as og


def step(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True,
                    help="Path to the model folder (contains genai_config.json)")
    ap.add_argument("--prompt", default="Say hello from the AMD NPU.")
    ap.add_argument("--max-length", type=int, default=128)
    ap.add_argument("--force-vitis", action="store_true",
                    help="Override providers in genai_config.json and force VitisAI")
    args = ap.parse_args()

    step(f"onnxruntime-genai version: {og.__version__}")
    step(f"Loading model config from {args.model} ...")
    config = og.Config(args.model)

    if args.force_vitis:
        step("Forcing VitisAIExecutionProvider ...")
        config.clear_providers()
        config.append_provider("VitisAI")

    step("Building model (first NPU compile can take minutes) ...")
    t0 = time.time()
    model = og.Model(config)
    step(f"Model built in {time.time() - t0:.1f}s.")

    tokenizer = og.Tokenizer(model)
    tokenizer_stream = tokenizer.create_stream()

    input_tokens = tokenizer.encode(args.prompt)

    params = og.GeneratorParams(model)
    params.set_search_options(max_length=args.max_length)

    step(f"Prompt: {args.prompt!r}")
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

    total = time.time() - t0
    step(f"First token: {first_token_time:.2f}s  Total: {total:.2f}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
