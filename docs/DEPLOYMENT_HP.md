# CortexMesh — Guia de Conexão HP DL360

## Arquitetura do Cluster

```
┌─────────────────────────────────────────────────────────────┐
│                        MAC (Admin)                          │
│                   i5-7360U / 8GB RAM                        │
│              CortexMesh Dashboard (porta 8585)              │
│         Envia instruções → HP executa → Retorna             │
└───────────────────────────┬─────────────────────────────────┘
                            │ SSH / Cockpit
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    HP DL360 Gen8 (Host)                     │
│                2x Xeon E5-2450L / 64GB ECC                  │
│                    3.5TB SAS RAID                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              VM Cockpit (99% hardware)              │   │
│  │                                                     │   │
│  │  Colibri Engine v1.12.0                            │   │
│  │  GLM-5.2 (744B) — ./coli serve :8001              │   │
│  │  Kimi K3 (2.8T) — ./coli serve :8002              │   │
│  │  CortexMesh Controller — porta 8000                │   │
│  │  Agent Nous — orquestração local                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Cisco C240   │  │ PC Windows   │  │  Mac Admin   │     │
│  │ Worker       │  │ GPU Worker   │  │  (fora)      │     │
│  │ 64GB RAM     │  │ RTX 4060 8GB │  │              │     │
│  │ Colibri      │  │ Colibri CUDA │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Conexão Inicial

### 1. Acessar HP via SSH

```bash
# Do Mac, conectar ao HP
ssh ubuntu@<IP_DO_HP>

# Verificar recursos
free -h                    # RAM
df -h                      # Disco
lscpu | grep "CPU(s)"      # CPUs
lsblk                      # Discos
```

### 2. Acessar VM via Cockpit

```bash
# Cockpit roda na porta 9090 do HP
# Acessar pelo navegador: http://<IP_DO_HP>:9090

# Ou via CLI, listar VMs
virsh list --all

# Conectar à VM
virsh console <nome-da-vm>
```

### 3. Dentro da VM — Verificar Colibri

```bash
# Verificar Colibri
which coli
coli --version

# Modelos disponíveis
ls -la /nvme/models/          # ou caminho dos modelos

# Serviços rodando
ss -tlnp | grep coli
ss -tlnp | grep cortex
```

---

## Comandos de Controle

### Colibri — GLM-5.2 (744B)
```bash
# Iniciar servidor GLM-5.2
COLI_MODEL=/nvme/models/glm52_i4 ./coli serve \
  --host 0.0.0.0 --port 8001 --model-id glm-5.2-colibri

# Testar
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-5.2","messages":[{"role":"user","content":"Oi"}]}'
```

### Colibri — Kimi K3 (2.8T)
```bash
COLI_MODEL=/nvme/models/kimi_k3 ./coli serve \
  --host 0.0.0.0 --port 8002 --model-id kimi-k3
```

### Fine-Tuning LoRA (Colab GPU T4)
```python
# Este roda no Colab, não no HP
# GPU T4 = 15GB VRAM — suporta modelos até 7B-14B

from transformers import TrainingArguments
from peft import LoraConfig

training_args = TrainingArguments(
    output_dir="./glm-code-lora",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    fp16=True,
    save_steps=100,
)

lora_config = LoraConfig(
    r=64,
    lora_alpha=128,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

---

## Distribuição de Experts

### HP DL360 (64GB RAM)
- Armazena modelos no disco 3.5TB
- Carrega experts na RAM via Colibri streaming
- CPU faz inference quando GPU não disponível

### PC Windows (RTX 4060 8GB)
- Colibri CUDA backend
- Experts na VRAM (até ~14B Q4)
- Fallback: RAM (16GB) → disco

### Cisco C240 (64GB RAM)
- Mesmo papel do HP mas sem armazenamento principal
- Experts em RAM via Colibri

---

## Configuração CortexMesh (VM do HP)

```bash
# No CortexMesh, registrar os nós:
# 1. HP = Controller + Storage
# 2. PC = GPU Worker
# 3. Cisco = CPU Worker
# 4. Mac = Client Only

# Cada nó roda o agente CortexMesh:
cortexctl agent --controller http://<IP_HP>:8000 --token <TOKEN>
```

---

## Fluxo de Trabalho

1. **Mac** envia instrução → **HP VM** recebe
2. **HP VM** decide: treinar ou inferir?
3. Se **treinar** → usa Colab GPU T4 (LoRA) ou CPU do HP
4. Se **inferir** → Colibri distribui experts (HP RAM + PC GPU + Cisco RAM)
5. Resultado volta para **Mac**

---

## Troubleshooting

```bash
# Verificar RAM disponível
free -h

# Verificar GPU (PC apenas)
nvidia-smi

# Verificar Colibri ativo
curl http://localhost:8001/api/health
curl http://localhost:8002/api/health

# Verificar CortexMesh
curl http://localhost:8000/api/v1/health

# Logs do Colibri
journalctl -u colibri-glm52 -f
journalctl -u colibri-kimi -f

# Logs do CortexMesh
journalctl -u cortexmesh -f

# Verificar rede entre nós
ping <IP_CISCO>
ping <IP_PC>
```

---

## Contato

Este documento é usado pelo agente no Mac para se comunicar com o HP.

Para executar comandos no HP, o Mac envia instruções via SSH ou Cockpit.
