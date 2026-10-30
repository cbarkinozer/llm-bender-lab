"""New CPU reference composition; RoPE is applied before transposing heads."""
import torch
from torch import nn
from torch.nn import functional as F
from _7_RMSNorm.pytorch import RMSNorm
from _4_RoPE.pytorch import RoPE

class TinyModel(nn.Module):
    def __init__(self, vocab_size, hidden_dim, num_heads, max_length):
        super().__init__()
        if hidden_dim%num_heads or (hidden_dim//num_heads)%2: raise ValueError('Incompatible dimensions')
        self.config=dict(vocab_size=vocab_size,hidden_dim=hidden_dim,num_heads=num_heads,max_length=max_length)
        self.embedding=nn.Embedding(vocab_size,hidden_dim)
        self.norm=RMSNorm(hidden_dim)
        self.qkv=nn.Linear(hidden_dim,3*hidden_dim,bias=False)
        self.projection=nn.Linear(hidden_dim,hidden_dim,bias=False)
        self.rope=RoPE(hidden_dim//num_heads,max_length)
        self.ff=nn.Sequential(nn.Linear(hidden_dim,2*hidden_dim),nn.GELU(),nn.Linear(2*hidden_dim,hidden_dim))
        self.out=nn.Linear(hidden_dim,vocab_size,bias=False)
    def forward(self, tokens):
        b,s=tokens.shape; h=self.config['num_heads']; d=self.config['hidden_dim']//h
        if s>self.config['max_length']: raise ValueError('Sequence too long')
        x=self.embedding(tokens); q,k,v=self.qkv(self.norm(x)).chunk(3,dim=-1)
        q=self.rope(q.reshape(b,s,h,d)).transpose(1,2)
        k=self.rope(k.reshape(b,s,h,d)).transpose(1,2)
        v=v.reshape(b,s,h,d).transpose(1,2)
        attended=F.scaled_dot_product_attention(q,k,v,is_causal=True).transpose(1,2).reshape(b,s,h*d)
        x=x+self.projection(attended); x=x+self.ff(self.norm(x))
        return self.out(x)
    def save(self, path): torch.save({'config':self.config,'state':self.state_dict()},path)
    @classmethod
    def load(cls, path):
        saved=torch.load(path,map_location='cpu',weights_only=True)
        model=cls(**saved['config']); model.load_state_dict(saved['state']); return model

def train_demo(tokens, *, seed, steps, learning_rate):
    torch.manual_seed(seed)
    model=TinyModel(8,8,2,16)
    optimizer=torch.optim.AdamW(model.parameters(),lr=learning_rate)
    losses=[]
    for _ in range(steps):
        optimizer.zero_grad()
        logits=model(tokens[:,:-1]); loss=F.cross_entropy(logits.reshape(-1,8),tokens[:,1:].reshape(-1))
        losses.append(loss.item()); loss.backward(); optimizer.step()
    return {'model':model,'losses':losses}

def generate(model, prompt, *, max_new_tokens):
    if max_new_tokens<0: raise ValueError('Nonnegative token budget required')
    result=list(prompt)
    model.eval()
    with torch.no_grad():
        for _ in range(max_new_tokens): result.append(int(model(torch.tensor([result]))[0,-1].argmax()))
    return result
