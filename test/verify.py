import torch
import os
import argparse
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
import json

import re


def parse_element_letter(response):
    """Extract the ELEMENT letter from agent response."""
    match = re.search(r"ELEMENT:\s*([A-P]|None)", response)
    return match.group(1) if match else None


def lookup_element(letter, grounding_prompt):
    """Find the web element description for a given letter in the grounding prompt."""
    if letter is None or letter == "None":
        return "None"
    pattern = rf"^{letter}\.\s*(.+)$"
    match = re.search(pattern, grounding_prompt, re.MULTILINE)
    return match.group(1).strip() if match else "Not found"


def run_inference(model, processor, prompt, image, device="cuda:0"):
    inputs = processor(prompt, [image], return_tensors='pt').to(device)
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=False,
        eos_token_id=processor.tokenizer.eos_token_id,
    )
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    return response


def main():
    parser = argparse.ArgumentParser(description="Compare agent responses on clean vs. perturbed images.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to Phi-3 Vision model weights")
    parser.add_argument("--conv-path", type=str, required=True, help="Path to conversation JSON file")
    parser.add_argument("--clean-image", type=str, required=True, help="Path to clean screenshot")
    parser.add_argument("--perturbed-image", type=str, required=True, help="Path to perturbed screenshot")
    args = parser.parse_args()

    # Load model
    print("Loading model...")
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, trust_remote_code=True, torch_dtype="auto"
    ).cuda()

    # Load conversation data
    with open(args.conv_path, "r", encoding="utf-8") as f:
        conv_data = json.load(f)
    system_prompt = conv_data["system"]
    user_request = conv_data["user"][0]
    grounding_prompt = conv_data["user"][1]
    assistant_answer = conv_data["assistant"]

    # Build prompt (same for both images)
    chat = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"<|image_1|>\n{user_request}"},
        {"role": "assistant", "content": assistant_answer},
        {"role": "user", "content": grounding_prompt}
    ]
    prompt = processor.tokenizer.apply_chat_template(
        chat, tokenize=False, add_generation_prompt=True
    )
    if prompt.endswith('<|endoftext|>'):
        prompt = prompt.rstrip('<|endoftext|>')

    print("=" * 60)
    print("PROMPT (identical for both runs)")
    print("=" * 60)
    print(prompt)
    print("=" * 60)

    # Load images
    clean_image = Image.open(args.clean_image).convert("RGB")
    perturbed_image = Image.open(args.perturbed_image).convert("RGB")

    # Run inference on clean image
    print(f"\n[1/2] Running inference on CLEAN image: {args.clean_image}")
    clean_response = run_inference(model, processor, prompt, clean_image)
    print(f">>> Clean Response:\n{clean_response}")

    # Run inference on perturbed image
    print(f"\n[2/2] Running inference on PERTURBED image: {args.perturbed_image}")
    perturbed_response = run_inference(model, processor, prompt, perturbed_image)
    print(f">>> Perturbed Response:\n{perturbed_response}")

    # Parse element letters and look up web elements
    clean_letter = parse_element_letter(clean_response)
    perturbed_letter = parse_element_letter(perturbed_response)
    clean_element = lookup_element(clean_letter, grounding_prompt)
    perturbed_element = lookup_element(perturbed_letter, grounding_prompt)

    # Summary comparison
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"Clean image:        {os.path.basename(args.clean_image)}")
    print(f"  Selected element: [{clean_letter}] {clean_element}")
    print(f"Perturbed image:    {os.path.basename(args.perturbed_image)}")
    print(f"  Selected element: [{perturbed_letter}] {perturbed_element}")
    print("-" * 60)
    if clean_letter == perturbed_letter:
        print("Result: Same element selected. Perturbation had no effect.")
    else:
        print(f"Result: Selection changed from [{clean_letter}] to [{perturbed_letter}].")
        print(f"The adversarial perturbation redirected the agent's grounded selection,")
        print(f"where [{perturbed_letter}] is the attacker-controlled element.")
    print("=" * 60)

if __name__ == "__main__":
    main()