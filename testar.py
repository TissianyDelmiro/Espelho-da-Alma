# -*- coding: utf-8 -*-
"""
Testar o "cérebro" do Espelho da Alma contra um modelo local (Ollama).

Uso:
    python testar.py                          # 3 respostas de exemplo, em PT
    python testar.py --idioma en              # em inglês
    python testar.py --modelo qwen2.5:7b      # escolhe o modelo
    python testar.py --interativo             # você responde no terminal

Pré-requisito: Ollama rodando, com o modelo já baixado:
    ollama pull qwen2.5:7b
"""

import argparse
import json
import random
import sys
import urllib.request

# Windows: o terminal usa cp1252 por padrão e quebra com acentos / caracteres
# especiais. Forçamos UTF-8 na saída pra poder imprimir o retrato em português.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from prompt import BARALHO, montar_mensagens

OLLAMA_URL = "http://localhost:11434/api/chat"

# Pares pergunta→resposta que JÁ COMBINAM (corrige o bug antigo de sortear
# perguntas e colar respostas que não tinham nada a ver). No modo automático
# sorteamos 3 destes pares, então a resposta sempre responde a pergunta.
PARES_TESTE = {
    "pt": {
        "Que cor tem o seu cansaço hoje?": "Cinza-fosco, igual céu antes da chuva.",
        "O que sobra de você quando o dia acaba?": "Um copo de água pela metade e a TV ligada sem som.",
        "Que peso você carrega que ninguém vê?": "O de fingir que está tudo bem pra não preocupar ninguém.",
        "Que cheiro tem a sua infância?": "Terra molhada e café passado na cozinha da minha avó.",
        "O que te faz acordar às 3 da manhã sem motivo?": "A lista de tudo que eu ainda não resolvi.",
        "Qual verdade você sabe mas finge que não sabe?": "Que eu preciso ir embora de um lugar que já acabou.",
    },
    "en": {
        "What color is your tiredness today?": "Matte gray, like the sky before rain.",
        "What is left of you when the day is over?": "A half-glass of water and the TV on with no sound.",
        "What weight do you carry that no one sees?": "Pretending I'm fine so no one worries about me.",
        "What does your childhood smell like?": "Wet earth and coffee brewing in my grandmother's kitchen.",
        "What wakes you at 3 a.m. for no reason?": "The list of everything I still haven't sorted out.",
        "What truth do you know but pretend you don't?": "That I need to leave a place that's already over.",
    },
}


def gerar(mensagens, modelo, temperatura=0.8):
    """Chama o Ollama e devolve o texto do retrato."""
    payload = {
        "model": modelo,
        "messages": mensagens,
        "stream": False,
        # temperatura alta = criatividade; um pouco mais baixa segura a gramática
        "options": {"temperature": temperatura, "top_p": 0.95},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    return dados["message"]["content"].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="qwen2.5:7b")
    ap.add_argument("--idioma", default="pt", choices=["pt", "en"])
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--interativo", action="store_true")
    args = ap.parse_args()

    idioma = args.idioma

    if args.interativo:
        # sorteia 3 perguntas do baralho e você responde
        perguntas = random.sample(BARALHO[idioma], 3)
        cabecalho = "🔮 O Espelho da Alma pergunta:" if idioma == "pt" else "🔮 The Mirror of the Soul asks:"
        print(f"\n{cabecalho}\n")
        respostas = []
        for p in perguntas:
            print(f"  {p}")
            respostas.append(input("  → ").strip())
            print()
    else:
        # modo automático: sorteia 3 PARES que já combinam
        pares = PARES_TESTE[idioma]
        perguntas = random.sample(list(pares.keys()), 3)
        respostas = [pares[p] for p in perguntas]

    print(f"\n[modelo: {args.modelo} | idioma: {idioma}]  gerando o retrato...\n")
    mensagens = montar_mensagens(perguntas, respostas, idioma=idioma)

    try:
        retrato = gerar(mensagens, args.modelo, temperatura=args.temp)
    except urllib.error.URLError:
        print("❌ Não consegui falar com o Ollama. Ele está rodando? (ollama serve)")
        return

    print("─" * 60)
    for p, r in zip(perguntas, respostas):
        print(f"  {p}\n  → {r}\n")
    print("─" * 60)
    print(f"\n{retrato}\n")
    print("─" * 60)


if __name__ == "__main__":
    main()
