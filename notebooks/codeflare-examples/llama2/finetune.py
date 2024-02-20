from os import environ, listdir, path, unlink
from shutil import rmtree

from datasets import load_dataset
from peft import (
    prepare_model_for_kbit_training, LoraConfig, get_peft_model, PeftModel
)
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, Trainer,
    TrainingArguments, DataCollatorForLanguageModeling
)

models_cache_folder = '/models'
dataset_id = environ.get('dataset_id', 'Abirate/english_quotes')

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=[
        "self_attn.q_proj",
        "self_attn.k_proj",
        "self_attn.v_proj",
        "self_attn.o_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)


def finetune():
    tokenizer, model = _load_artifacts(models_cache_folder)
    training_data = _load_training_data(dataset_id, tokenizer)
    _run_training(model, training_data, tokenizer)
    new_model = _merge_models(model, models_cache_folder)
    _clean_folder(models_cache_folder)
    _save_artifacts(tokenizer, new_model, models_cache_folder)


def _clean_folder(folder):
    print(f'Cleaning folder {folder}')

    for filename in listdir(folder):
        file_path = path.join(folder, filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def _load_artifacts(models_cache_folder):
    print(f'Loading artifacts from {models_cache_folder}.')
    tokenizer = AutoTokenizer.from_pretrained(models_cache_folder)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        models_cache_folder, quantization_config=bnb_config, device_map={"": 0}
    )
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    _print_trainable_parameters(model)

    return tokenizer, model


def _print_trainable_parameters(model):
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
        f"trainable params: {trainable_params} || all params: {all_param} || "
        f"trainable%: {100 * trainable_params / all_param}"
    )


def _load_training_data(dataset_id, tokenizer):
    print(f'Loading dataset {dataset_id}.')
    data = load_dataset(dataset_id)
    data = data.map(lambda samples: tokenizer(samples["quote"]), batched=True)

    return data["train"]


def _run_training(model, training_data, tokenizer):
    print('Setting up training.')
    trainer = Trainer(
        model=model,
        train_dataset=training_data,
        args=TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=2,
            max_steps=10,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=1,
            output_dir="outputs",
            optim="paged_adamw_8bit",
            ddp_find_unused_parameters=False
        ),
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    model.config.use_cache = False
    print('Running training.')
    # This invokes distributed training on the Ray cluster through HF Trainer
    trainer.train()


def _merge_models(model, models_cache_folder):
    print('Merging models.')
    original_model = AutoModelForCausalLM.from_pretrained(
        models_cache_folder,
        device_map='cpu',
        trust_remote_code=True,
        torch_dtype=torch.float16,
        cache_dir="cache_dir"
    )
    model = PeftModel.from_pretrained(
        original_model,
        model,
    )
    model = model.merge_and_unload()

    return model


def _save_artifacts(tokenizer, model, folder_name):
    print(f'Serializing artifacts to {folder_name}.')
    model.save_pretrained(folder_name)
    tokenizer.save_pretrained(folder_name)


if __name__ == '__main__':
    finetune()