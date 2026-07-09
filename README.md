# AMD NPU Foundry Local sample

Minimal Python sample that downloads and runs an AMD NPU (VitisAI) model
using the [Foundry Local](https://github.com/microsoft/Foundry-Local) Python SDK.

## Prerequisites

- Windows on an AMD Ryzen AI (XDNA NPU) machine
- Python 3.11+

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python foundry_amd_npu.py
```

Edit `ALIAS` in `foundry_amd_npu.py` to any model alias in the catalog that
has an AMD NPU variant (check with `foundry model list --variants` — look for
`NPU / VitisAIExecutionProvider`).

## Alternative: direct ORT-GenAI (no Foundry Local)

`genai_amd_npu.py` bypasses Foundry Local and runs a locally-cached model
directly with `onnxruntime-genai-winml`. Useful for bisecting ORT / ORT-GenAI
versions against the AMD NPU EP without the Foundry Core in the way.

```powershell
python -m venv .venv-genai
.\.venv-genai\Scripts\Activate.ps1
pip install -r requirements-genai.txt

# Point at a model folder that has genai_config.json (VitisAI EP)
python genai_amd_npu.py --model "C:\path\to\model" --prompt "hello"

# Pin specific versions to bisect:
pip install "onnxruntime-genai-winml==0.13.2"
pip install "onnxruntime-genai-winml==0.14.1"
```

Add `--force-vitis` to override the providers listed in `genai_config.json`.

