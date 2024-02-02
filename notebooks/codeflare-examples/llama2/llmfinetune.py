from huggingface_hub import HfApi, HfFolder
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
import transformers
from peft import PeftModel

#get your HF token :)
token = ""
HfFolder.save_token(token)

# model_id = "meta-llama/Llama-2-7b-chat-hf" ## "Trelis/Llama-2-7b-chat-hf-sharded-bf16" is an alternative if you don't have access via Meta on HuggingFace
# model_id = "meta-llama/Llama-2-13b-chat-hf"
model_id = "Trelis/Llama-2-7b-chat-hf-sharded-bf16"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map={"":0})



model.gradient_checkpointing_enable()
model = prepare_model_for_kbit_training(model)


def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
    )

config = LoraConfig(
    r=8,
    lora_alpha=32,
    # target_modules=["query_key_value"],
    target_modules=["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj"], #specific to Llama models.
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, config)
print_trainable_parameters(model)    

data = load_dataset("Abirate/english_quotes")
data = data.map(lambda samples: tokenizer(samples["quote"]), batched=True)

tokenizer.pad_token = tokenizer.eos_token # </s>

trainer = transformers.Trainer(
    model=model,
    train_dataset=data["train"],
    args=transformers.TrainingArguments(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        warmup_steps=2,
        max_steps=10,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=1,
        output_dir="outputs",
        optim="paged_adamw_8bit",
        ddp_find_unused_parameters=False # this makes the job run on CF fine. credits @Michael Clifford
 
    ),
    data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
)
model.config.use_cache = False  # silence the warnings. Please re-enable for inference!
trainer.train()

base_model_name = model_id.split("/")[-1]

# Define the save and push paths
adapter_model = f"mamurak/{base_model_name}-fine-tuned-adapters"  #adjust 'avijra' to your HuggingFace organisation
new_model = f"mamurak/{base_model_name}-fine-tuned" #adjust 'avijra' to your HuggingFace organisation

# Save the model
model.save_pretrained(adapter_model, push_to_hub=True, use_auth_token=True)

# Push the model to the hub
model.push_to_hub(adapter_model, use_auth_token=True)
cache_dir="cache_dir"
# reload the base model (you might need a pro subscription for this because you may need a high RAM environment for the 13B model since this is loading the full original model, not quantized)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map='cpu', trust_remote_code=True, torch_dtype=torch.float16, cache_dir=cache_dir)

# load perf model with new adapters
model = PeftModel.from_pretrained(
    model,
    adapter_model,
)

model = model.merge_and_unload() # merge adapters with the base model.

model.push_to_hub(new_model, use_auth_token=True, max_shard_size="5GB")

#Push the tokenizer
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
tokenizer.push_to_hub(new_model, use_auth_token=True)
