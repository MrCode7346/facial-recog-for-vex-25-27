print("importing modules...")
import os
import time
import struct
import mmap
import torch
import torch.nn as nn
import torch.nn.functional as F
import gradio as gr
from tqdm import tqdm
import sentencepiece as spm

print("imported modules...")

device = (
    'cuda' if torch.cuda.is_available()
    else 'xpu' if hasattr(torch, "xpu") and torch.xpu.is_available()
    else 'mps' if torch.backends.mps.is_available()
    else 'cpu'
)
print(f"Training on: {device}")

batch_size = 8          # Reduced from 16
block_size = 64         # Reduced from 128
max_iters = 1_000_000
learning_rate = 3e-4
n_embd = 128            # Reduced from 256
n_head = 4              # Reduced from 8
n_layer = 4             # Reduced from 6
dropout = 0.2

checkpoint_path = "./checkpoint.pt"
final_model_path = "./nikunj-llm-gpt-final.pt"
instruct_model_path = "./nikunj-llm-gpt-instruct.pt"
instruction_checkpoint_path = "./instruction-checkpoint.pt"

data_dir = "./content/data"
instruction_file = "./content/data/instructions.txt"
tokenizer_path = "./content/data/tokenizer.model"

print("Loading SentencePiece tokenizer...")

sp = spm.SentencePieceProcessor()
sp.load(tokenizer_path)

def encode(text):
    return sp.encode(text, out_type=int)

def decode(tokens):
    return sp.decode(tokens)

vocab_size = sp.get_piece_size()
print(f"Loaded SentencePiece tokenizer with vocab size: {vocab_size}")

def load_instruction_data():
    with open(instruction_file, "r", encoding="utf-8") as f:
        text = f.read()
    return torch.tensor(encode(text), dtype=torch.long)

instruction_data = load_instruction_data()

def get_instruction_batch():
    data = instruction_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    return x.to(device), y.to(device)

BIN_FILE = "./content/data/openwebtext.bin"
META_FILE = "./content/data/openwebtext.meta"

print("Loading mmap dataset...")

with open(META_FILE, "r") as f:
    total_tokens = int(f.read().strip())

with open(BIN_FILE, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

def get_token(idx):
    return struct.unpack_from("<I", mm, idx * 4)[0]

def get_pretraining_batch():
    ix = torch.randint(total_tokens - block_size - 1, (batch_size,))
    x = torch.zeros((batch_size, block_size), dtype=torch.long)
    y = torch.zeros((batch_size, block_size), dtype=torch.long)

    for b in range(batch_size):
        start = ix[b].item()
        for t in range(block_size):
            x[b, t] = get_token(start + t)
            y[b, t] = get_token(start + t + 1)

    return x.to(device), y.to(device)

class Head(nn.Module):
    def __init__(self, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)
        q = self.query(x)
        wei = q @ k.transpose(-2, -1) * (k.shape[-1] ** -0.5)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        v = self.value(x)
        return wei @ v

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(num_heads * head_size, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))

class FeedForward(nn.Module):
    def __init__(self, n_embd):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        head_size = n_embd // n_head
        self.sa = MultiHeadAttention(n_head, head_size)
        self.ffwd = FeedForward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = self.ln1(x + self.sa(x))
        return self.ln2(x + self.ffwd(x))

class GPTLanguageModel(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok_emb = self.token_embedding_table(idx)
        pos_emb = self.position_embedding_table(torch.arange(T, device=idx.device))
        x = tok_emb + pos_emb
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(B*T, -1), targets.view(B*T))
        return logits, loss

    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        idx = idx.to(next(self.parameters()).device)
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -block_size:]
            logits, _ = self.forward(idx_cond)
            logits = logits[:, -1, :] / temperature
            if top_k is not None:
                values, indices = torch.topk(logits, top_k)
                logits = torch.full_like(logits, float('-inf'))
                logits.scatter_(1, indices, values)
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx

model = GPTLanguageModel(vocab_size).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

def train_model():
    start_iter = 0

    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        start_iter = checkpoint['iter']
        print(f"Resumed from checkpoint at step {start_iter}")

    for iter in tqdm(range(start_iter, max_iters), desc="Pretraining"):
        xb, yb = get_pretraining_batch()
        logits, loss = model(xb, yb)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if iter % 100 == 0 and iter > 0:
            torch.save({
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'iter': iter
            }, checkpoint_path)

    torch.save(model.state_dict(), final_model_path)
    print("Pretraining complete.")

def instruction_tune():
    print("Loading pretrained model...")
    start_iter = 0

    if os.path.exists(final_model_path):
        model.load_state_dict(torch.load(final_model_path, map_location=device))
        print("Loaded pretrained model.")

    local_optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    steps = 100_000

    for step in tqdm(range(start_iter, steps), desc="Instruction tuning"):
        xb, yb = get_instruction_batch()
        logits, loss = model(xb, yb)
        local_optimizer.zero_grad()
        loss.backward()
        local_optimizer.step()

        if step % 100 == 0:
            torch.save({
                'model': model.state_dict(),
                'optimizer': local_optimizer.state_dict(),
                'iter': step
            }, instruction_checkpoint_path)

    torch.save(model.state_dict(), instruct_model_path)
    print("Instruction tuning complete!")

# ============================================================
# RUN TRAINING PIPELINE
# ============================================================
if os.path.exists(instruct_model_path):
    model.load_state_dict(torch.load(instruct_model_path, map_location=device))
    model.eval()
    print("Loaded instruction-tuned model.")
elif os.path.exists(final_model_path):
    model.load_state_dict(torch.load(final_model_path, map_location=device))
    model.eval()
    print("Loaded pretrained model. Starting instruction tuning...")
    instruction_tune()
else:
    print("No models found. Starting full training pipeline...")
    train_model()
    instruction_tune()

model.eval()

# ============================================================
# CHAT FUNCTION
# ============================================================
def chat_fn(user_input):
    prompt = f"<|user|> {user_input}\n<|assistant|>"
    context = torch.tensor(encode(prompt), dtype=torch.long).unsqueeze(0).to(device)

    output = model.generate(context, max_new_tokens=300, temperature=0.8)
    generated_tokens = output[0].tolist()[len(context[0]):]
    response = decode(generated_tokens)

    if "<|end|>" in response:
        response = response.split("<|end|>")[0]

    return response.strip()

# ============================================================
# GRADIO UI
# ============================================================
demo = gr.Interface(
    fn=chat_fn,
    inputs=gr.Textbox(lines=2, placeholder="Type your message here...", label="👤 You"),
    outputs=[gr.Textbox(label="🤖 Model Response")],
    title="🧠🐍 PyBrain",
    description="Chat with your custom GPT model."
)

demo.launch(share=False)
