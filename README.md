# Red Teaming Framework for VLM Web Agents

A modular framework designed for red teaming and evaluating the robustness of Vision-Language Models (VLMs). This project specifically focuses on generating adversarial inputs and testing the security of web agents powered by multimodal models.

## Critical Prerequisites

**Before installing this framework, you must manually configure the base models.**

Due to conflicting library versions and environment requirements, you need to set up the environments for **MiniCPM-o**, **LLaVA**, and **Phi-3** separately and download their model weights to your local machine.

### 1. MiniCPM-o
* **Repo:** [OpenBMB/MiniCPM-o](https://github.com/OpenBMB/MiniCPM-o)
* **Setup:** Clone the repo, create a dedicated environment (e.g., `conda create -n minicpm`), and install dependencies.
* **Weights:** Download the official weights locally and record the path.

### 2. LLaVA
* **Repo:** [haotian-liu/LLaVA](https://github.com/haotian-liu/LLaVA)
* **Setup:** Clone the repo and create a dedicated environment (e.g., `conda create -n llava`).
* **Weights:** Download LLaVA-v1.5/v1.6 weights locally and record the path.

### 3. Phi-3 Vision
* **Repo:** [microsoft/Phi-3-Vision](https://huggingface.co/microsoft/Phi-3-vision-128k-instruct)
* **Setup:** Ensure you have the compatible `transformers` version installed in a dedicated environment.
* **Weights:** Download the `Phi-3-vision-128k-instruct` weights locally.
---

## Quick Verification (Phi-3 Vision)

We provide a minimal test to verify that the attack works as expected. The script runs inference on both clean and perturbed screenshots and compares the agent's selections side by side.

> **Note:** This test requires Phi-3 Vision (see Prerequisites §3). The provided test cases (perturbed images) were optimized for Phi-3; test data for other backbones can be generated using the training scripts in `scripts/`.

### Test Data

Pre-generated test cases are located in `test/`:

```
test/
├── clean_fix_slot/         # Clean screenshots with target in a fixed slot position
├── clean_multi_slot/       # Clean screenshots with target across multiple slot positions
├── perturbed_fix_slot/     # Perturbed screenshots (ε=16/255) with target in a fixed slot
├── perturbed_multi_slot/   # Perturbed screenshots (ε=16/255) with target across multiple slots
├── conv.json               # Conversation data (system prompt, user query, grounding prompt)
└── verify.py               # Runs inference on clean vs. perturbed and compares results

```

The `fix_slot` cases test companion variation (target position fixed, surrounding elements vary), while `multi_slot` cases test both companion variation and positional shift simultaneously.

### Running the Test

```bash
conda activate phi3vision

# Test with fixed slot position
python test/verify.py \
    --model-path /path/to/Phi-3-vision-128k-instruct \
    --conv-path test/conv.json \
    --clean-image test/clean_fix_slot/sample_0.png \
    --perturbed-image test/perturbed_fix_slot/sample_0.png

# Test with varying slot positions
python test/verify.py \
    --model-path /path/to/Phi-3-vision-128k-instruct \
    --conv-path test/conv.json \
    --clean-image test/clean_multi_slot/sample_0.png \
    --perturbed-image test/perturbed_multi_slot/sample_0.png
```

### Expected Output

The script runs inference on both image sets and prints a comparison table showing, for each test case, the element selected under clean vs. perturbed input. On clean screenshots the agent should select the best-matching candidate; on perturbed screenshots it should consistently select the attacker-controlled candidate.

---

## Workflow Example: LLaVA

After ensuring you have created a unique Conda environment for each model above, follow these steps to run the training workflow. We will use LLaVA as the primary example.

 You must clone the official LLaVA repository to your **home directory** (`~/`), as the scripts rely on local code references from this repository.

```bash
cd ~
git clone [https://github.com/haotian-liu/LLaVA.git](https://github.com/haotian-liu/LLaVA.git)
```

### 2. Configure the Training Script
Navigate to the training script located at: `scripts/LLaVA/train_with_mask.sh`

Open the file and configure each parameter's path (model paths, data paths, output directories) to match your local environment configuration.

### 3. Run the Script
Once the paths are configured, execute the script:

```bash
bash scripts/LLaVA/train_with_mask.sh
```
---
## Agent Framework Setup

To run end-to-end evaluation, you need to install the target agent frameworks.

### SeeAct
* **Repo:** [OSU-NLP-Group/SeeAct](https://github.com/OSU-NLP-Group/SeeAct)
* **Setup:** Clone the repo and follow the official installation instructions.
* **Usage:** Our evaluation uses the client-side asset replacement protocol described in the paper. See `scripts/seeact/` for evaluation scripts.

### VisualWebArena
* **Repo:** [web-arena-x/visualwebarena](https://github.com/web-arena-x/visualwebarena)
* **Setup:** Follow the official instructions to set up the sandbox environment, including deploying the OneStopShop shopping site.
* **Usage:** See `scripts/visualwebarena/` for evaluation scripts with both Accessibility Tree and Set-of-Mark observation modes.

