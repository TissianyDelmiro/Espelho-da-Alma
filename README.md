<div align="center">

# 🔮 Espelho da Alma

**Um portal místico de autorreflexão, movido por um modelo de linguagem pequeno (3B) — rodando inteiramente self-hosted, sem nenhuma API de nuvem.**

[![Demo ao vivo](https://img.shields.io/badge/🤗%20Demo%20ao%20vivo-Hugging%20Face%20Space-c9a84c)](https://huggingface.co/spaces/build-small-hackathon/espelho-da-alma)
[![Modelo](https://img.shields.io/badge/Modelo-Qwen2.5--3B-7c3aed)](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
[![Execução](https://img.shields.io/badge/Execução-transformers%20·%20ZeroGPU-27ae60)]()
[![UI](https://img.shields.io/badge/UI-Gradio-f39c12)](https://www.gradio.app/)
[![Sem APIs de nuvem](https://img.shields.io/badge/Sem%20APIs%20de%20nuvem-self--hosted-9b59b6)]()

*Feito para o hackathon **Build Small** da Hugging Face — trilha: Thousand Token Wood.*

</div>

---
<img width="1920" height="945" alt="image" src="https://github.com/user-attachments/assets/86b2bc68-4330-4d98-b5a2-ac6aa33ae3ee" />
<img width="1920" height="945" alt="image" src="https://github.com/user-attachments/assets/edcdea69-4fcc-4a48-ae03-dec255c53b4e" />
<img width="1920" height="1616" alt="image" src="https://github.com/user-attachments/assets/e24453fa-16b8-497d-a964-99026b1ded16" />
<img width="1920" height="945" alt="image" src="https://github.com/user-attachments/assets/500c69fe-c520-407d-9201-d028861f9b08" />


> *"O espelho não mente, mas raramente mostramos a nós mesmos o suficiente para ele revelar o que há além da superfície."*

O **Espelho da Alma** transforma um modelo pequeno (3B) em algo delicado: um espelho
místico que reflete quem você é neste momento. A interface é em **português** (é onde a
magia toca o público).

Toda a experiência roda **sem nenhuma API de LLM/nuvem externa** — o modelo é servido
dentro do próprio app.

## ✨ As quatro seções

| Seção | O que faz | Usa IA? |
|-------|-----------|---------|
| 🪞 **Espelho** | A home — um orbe brilhante que **gira** lentamente, com as boas-vindas. | — |
| 🃏 **Oráculo** | Tire uma de seis cartas-arquétipo escritas à mão (A Lua Interior, O Espelho Partido, Estrela do Abismo…), cada uma com símbolo, elemento, palavras-chave e mensagem. A carta **vira** ao ser tirada — instantâneo, como tarô. | Não (curado) |
| 📓 **Diário** | **O coração.** Você escreve livremente respondendo a uma pergunta da "sombra", e a *voz da alma* devolve uma reflexão curta e íntima — surgindo **palavra por palavra**. Dá pra transformar num **pôster compartilhável**. | **Sim** |
| 🌙 **Essência** | Um "mapa de energia": cinco traços cujos valores mudam **a cada dia**, mais a **fase real da lua** (calculada astronomicamente). | Não (arte generativa) |

## 🧠 O segredo do Diário

A mágica não é o tamanho do modelo — é o **prompt**. Três regras fazem um modelo
pequeno parecer que *te conhece*:

1. **Eco literal** — ele reusa as suas palavras exatas, transformadas, nunca trocadas por sinônimos genéricos.
2. **Imagem concreta** — palavras vagas proibidas ("profundo", "sensível", "intenso"); só cenas, objetos, texturas.
3. **Afirme, não analise** — segunda pessoa, presente, sem rodeios.

Uma função leve `polir()` ainda limpa os deslizes típicos de modelo pequeno
(ex.: pronomes "tu/você") pra reflexão sair redonda.

## 🛠️ Tecnologias

- **UI:** [Gradio](https://www.gradio.app/) (Python) — tema 100% custom criado a partir de um
  design no Figma: céu de estrelas animado em CSS, orbe giratório em CSS/JS, cartas que viram,
  barra de navegação fixa, transições suaves entre seções, paleta dourado-sobre-quase-preto
  (fontes Cinzel · Lora · IM Fell English), layout responsivo.
- **Modelo:** [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) (≤ 4B parâmetros).
- **Inferência:** [`transformers`](https://github.com/huggingface/transformers) na **GPU grátis
  (ZeroGPU)** do Space — self-hosted, sem chaves de API. *(No desenvolvimento local uso o
  [Ollama](https://ollama.com/) com a mesma família de modelo.)*
- **Pôster:** [Pillow](https://python-pillow.org/) gera uma imagem 1080×1350 pra compartilhar.
- **Fase da lua:** Python puro, a partir de uma lua nova de referência.

## 📂 Estrutura do projeto

```
projeto/
├── app.py            # app Gradio — 4 seções, UI, CSS, eventos (local: Ollama)
├── prompt.py         # o "cérebro": baralho de perguntas, system prompts e a voz do Diário
├── imagem.py         # gerador do pôster compartilhável (Pillow)
├── testar.py         # CLI pra testar o prompt contra um modelo local
└── space/            # pacote de deploy do Hugging Face Space (motor: transformers + ZeroGPU)
    ├── app.py
    ├── prompt.py
    ├── imagem.py
    ├── requirements.txt
    └── README.md
```

## ▶️ Rodar localmente

Requer Python 3.10+ e [Ollama](https://ollama.com/).

```bash
# 1) suba um modelo local
ollama pull qwen2.5:3b      # ou qwen2.5:7b pra mais qualidade
ollama serve

# 2) instale as dependências e rode
pip install gradio pillow
python app.py               # abre em http://localhost:7860
```

## ☁️ Deploy (Hugging Face Space, ZeroGPU grátis)

A pasta `space/` é um Space Gradio autossuficiente. Ele usa `transformers` com o decorador
`@spaces.GPU` (ZeroGPU) e baixa o modelo do Hub na primeira execução — sem chaves de API,
sem serviços externos.

## 🏅 Hackathon

Feito para o **Build Small** da Hugging Face (trilha Thousand Token Wood), mirando os badges
**Off Brand** (interface custom) e **Tiny Titan** (modelo ≤ 4B).

## 🙏 Créditos

- [Qwen2.5](https://huggingface.co/Qwen) (Alibaba) · [Transformers](https://github.com/huggingface/transformers) e [Gradio](https://www.gradio.app/) (Hugging Face) · [ZeroGPU](https://huggingface.co/zero-gpu-explorers).

## 📜 Licença

MIT.
