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

`genai_amd_npu.py` bypasses Foundry Local and runs the same model directly
with `onnxruntime-genai-winml`. Uses the same `ALIAS` and prompt as
`foundry_amd_npu.py` and looks up the cached model folder in the Foundry
Local model cache. Run `foundry_amd_npu.py` first so the AMD NPU variant is
downloaded.

Useful for bisecting ORT / ORT-GenAI versions against the AMD NPU EP without
the Foundry Core in the way.

```powershell
python -m venv .venv-genai
.\.venv-genai\Scripts\Activate.ps1
pip install -r requirements-genai.txt

# Install the ONNX Runtime version you want to test against
# (windowsml does NOT install onnxruntime unless you use its [with-ort] extra,
# so we install it explicitly to control the version we're bisecting.)
pip install "onnxruntime==1.26.0"

python genai_amd_npu.py

# To bisect, uninstall and reinstall with a different version:
pip install --force-reinstall "onnxruntime==1.23.2"
pip install --force-reinstall "onnxruntime-genai-winml==0.13.2"
```

