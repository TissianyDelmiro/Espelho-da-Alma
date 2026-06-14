# -*- coding: utf-8 -*-
"""
Espelho da Alma — app Gradio (4 seções, inspirado no design Figma).

Seções: Espelho (home/orbe) · Oráculo (cartas) · Diário (IA) · Essência (mapa).
A IA roda só no Diário. Localmente usa Ollama; no Space, transformers/GPU.
"""

import json
import random
import urllib.request
from datetime import datetime, timezone

import gradio as gr

from prompt import montar_mensagens_diario, polir
from imagem import gerar_poster

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen2.5:7b"

# ===========================================================================
# Conteúdo (vindo do seu Figma)
# ===========================================================================
ORACULO = [
    {"simbolo": "☽", "nome": "A Lua Interior", "elemento": "Água", "cor": "#7c3aed",
     "mensagem": "Seus sentimentos mais profundos pedem atenção. O que você esconde na escuridão de si mesmo é também o que carrega maior poder transformador.",
     "chaves": ["intuição", "ciclos", "revelação"]},
    {"simbolo": "⊕", "nome": "O Espelho Partido", "elemento": "Terra", "cor": "#c9a84c",
     "mensagem": "A fragmentação que você sente não é fraqueza — é a alma se expandindo além dos limites que lhe foram impostos. Integre os cacos.",
     "chaves": ["sombra", "integração", "completude"]},
    {"simbolo": "✦", "nome": "Estrela do Abismo", "elemento": "Éter", "cor": "#9b59b6",
     "mensagem": "Das profundezas do desconhecido nasce a mais rara luz. Confie no caminho mesmo quando ele se oculta de seus olhos.",
     "chaves": ["fé", "mistério", "guia"]},
    {"simbolo": "⌖", "nome": "O Limiar", "elemento": "Fogo", "cor": "#e74c3c",
     "mensagem": "Você está entre dois mundos. Não temas a transição — ela é o próprio ritual de sua evolução.",
     "chaves": ["mudança", "portal", "coragem"]},
    {"simbolo": "∞", "nome": "Serpente Ouroboros", "elemento": "Ar", "cor": "#27ae60",
     "mensagem": "O que termina em você é o começo de algo que ainda não tem nome. O ciclo eterno é sua natureza mais verdadeira.",
     "chaves": ["renascimento", "eternidade", "padrão"]},
    {"simbolo": "◈", "nome": "O Véu Rasgado", "elemento": "Luz", "cor": "#f39c12",
     "mensagem": "A verdade que você busca já mora em você. O véu entre o consciente e o oculto afina-se a cada respiração consciente.",
     "chaves": ["clareza", "despertar", "verdade"]},
]

PROMPTS_DIARIO = [
    "O que a sua sombra está tentando te dizer hoje?",
    "Qual parte de você está pedindo para ser vista e aceita?",
    "Que emoção você tem evitado sentir? O que ela guarda?",
    "Se sua alma pudesse falar em uma única frase agora, o que diria?",
    "Qual crença antiga já não te serve mais?",
    "O que você perdoaria em si mesmo se soubesse que é seguro fazê-lo?",
    "Que versão sua está querendo emergir neste ciclo?",
    "Onde em seu corpo você carrega tensão não expressa?",
]

ESSENCIA = [
    {"nome": "Sombra", "valor": 72, "cor": "#7c3aed", "simbolo": "◐", "desc": "Aspectos inconscientes a integrar"},
    {"nome": "Luz", "valor": 58, "cor": "#c9a84c", "simbolo": "◑", "desc": "Qualidades conscientes expressas"},
    {"nome": "Intuição", "valor": 84, "cor": "#9b59b6", "simbolo": "◈", "desc": "Canal de percepção extra-sensorial"},
    {"nome": "Ancoragem", "valor": 45, "cor": "#27ae60", "simbolo": "⊕", "desc": "Conexão com o plano material"},
    {"nome": "Transmutação", "valor": 63, "cor": "#e74c3c", "simbolo": "∆", "desc": "Capacidade de transformar experiências"},
]

_FASES = [
    (0.0625, "Lua Nova", "🌑", "Sementes de intenção são plantadas no silêncio.", 0, "Intenção"),
    (0.1875, "Lua Crescente", "🌒", "A vontade desperta. O que você inicia hoje ganha raízes.", 25, "Expansão"),
    (0.3125, "Quarto Crescente", "🌓", "Decisões pedem coragem. Aja com clareza.", 50, "Ação"),
    (0.4375, "Lua Gibosa Crescente", "🌔", "A manifestação se aproxima. Refine seus desejos.", 75, "Refinamento"),
    (0.5625, "Lua Cheia", "🌕", "Tudo que estava oculto agora se revela. Momento de colheita.", 100, "Revelação"),
    (0.6875, "Lua Gibosa Minguante", "🌖", "O que não serve mais pede para ser liberado.", 75, "Gratidão"),
    (0.8125, "Quarto Minguante", "🌗", "Introspecção profunda. Escute o silêncio interior.", 50, "Liberação"),
    (0.9375, "Lua Minguante", "🌘", "O ciclo se encerra. Gratidão e desapego.", 25, "Descanso"),
]


def fase_lua():
    conhecida = datetime(2024, 1, 11, 11, 57, tzinfo=timezone.utc)
    lun = 29.53059 * 86400
    idade = ((datetime.now(timezone.utc) - conhecida).total_seconds() % lun + lun) % lun
    pct = idade / lun
    for limite, nome, simbolo, desc, ilum, energia in _FASES:
        if pct < limite:
            return nome, simbolo, desc, ilum, energia
    return "Lua Nova", "🌑", "Sementes de intenção são plantadas no silêncio.", 0, "Intenção"


# ===========================================================================
# Geração do Diário (IA) via Ollama
# ===========================================================================
def gerar_reflexao_stream(pergunta, texto):
    mensagens = montar_mensagens_diario(pergunta, texto, "pt")
    payload = {
        "model": MODELO, "messages": mensagens, "stream": True, "keep_alive": "30m",
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 160, "num_ctx": 2048},
    }
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    acumulado = ""
    with urllib.request.urlopen(req, timeout=300) as resp:
        for linha in resp:
            if not linha.strip():
                continue
            dado = json.loads(linha.decode("utf-8"))
            acumulado += dado.get("message", {}).get("content", "")
            yield acumulado


# ===========================================================================
# Construtores de HTML
# ===========================================================================
HEADER_HTML = """
<header class="topbar">
  <div class="marca-grupo">
    <span class="marca-star">✦</span>
    <span class="marca">ESPELHO DA ALMA</span>
  </div>
  <nav class="nav-grupo">
    <button id="nav_esp" class="navitem ativo">ESPELHO</button>
    <button id="nav_ora" class="navitem">ORÁCULO</button>
    <button id="nav_dia" class="navitem">DIÁRIO</button>
    <button id="nav_ess" class="navitem">ESSÊNCIA</button>
  </nav>
</header>
"""

HERO_HTML = """
<div class="hero">
  <div class="hero-label">✦ PORTAL MÍSTICO ✦</div>
  <div class="hero-title">Espelho da Alma</div>
  <div class="hero-sub">O que você verá hoje?</div>
  <div class="orb">
    <div class="orb-glow"></div><div class="orb-core"></div>
    <div class="orb-ring"></div><div class="orb-dots"></div>
  </div>
  <div class="hero-quote">"O espelho não mente, mas raramente mostramos a nós mesmos o suficiente para ele revelar o que há além da superfície."</div>
</div>
"""

CARD_VERSO = """
<div class="card-wrap"><div class="card-back">
  <div class="card-back-star">✦</div>
  <div class="card-back-label">TOQUE PARA REVELAR</div>
</div></div>
"""


def render_card(c):
    kws = "".join(
        f'<span class="kw" style="color:{c["cor"]};border-color:{c["cor"]}55">{k.upper()}</span>'
        for k in c["chaves"]
    )
    return f"""
<div class="card-wrap"><div class="card-front" style="border-color:{c['cor']}55;
     background:linear-gradient(160deg,#1a1029 0%,#0d0818 60%,{c['cor']}18 100%)">
  <div class="card-brand">ESPELHO DA ALMA</div>
  <div class="card-symbol" style="color:{c['cor']};filter:drop-shadow(0 0 16px {c['cor']})">{c['simbolo']}</div>
  <div class="card-name">{c['nome']}</div>
  <div class="card-elem">{c['elemento']}</div>
  <div class="card-msg">"{c['mensagem']}"</div>
  <div class="card-kws">{kws}</div>
</div></div>
<div class="card-fullmsg">"{c['mensagem']}"</div>
"""


# JS que sorteia e desenha a carta no navegador (instantâneo + giro), sem servidor
JS_TIRAR_CARTA = (
    "() => {"
    "  const cartas = " + json.dumps(ORACULO, ensure_ascii=False) + ";"
    "  const c = cartas[Math.floor(Math.random()*cartas.length)];"
    "  const kws = c.chaves.map(k => `<span class=\"kw\" style=\"color:${c.cor};border-color:${c.cor}55\">${k.toUpperCase()}</span>`).join('');"
    "  const html = `<div class=\"card-wrap\"><div class=\"card-front\" style=\"border-color:${c.cor}55;background:linear-gradient(160deg,#1a1029 0%,#0d0818 60%,${c.cor}18 100%)\">"
    "    <div class=\"card-brand\">ESPELHO DA ALMA</div>"
    "    <div class=\"card-symbol\" style=\"color:${c.cor};filter:drop-shadow(0 0 16px ${c.cor})\">${c.simbolo}</div>"
    "    <div class=\"card-name\">${c.nome}</div>"
    "    <div class=\"card-elem\">${c.elemento}</div>"
    "    <div class=\"card-msg\">\"${c.mensagem}\"</div>"
    "    <div class=\"card-kws\">${kws}</div>"
    "  </div></div><div class=\"card-fullmsg\">\"${c.mensagem}\"</div>`;"
    "  const area = document.getElementById('card_area');"
    "  if (area) { area.innerHTML = html; }"
    "}"
)


def render_essencia():
    # valores "energéticos" do dia: estáveis dentro do mesmo dia, mudam a cada dia
    dia = datetime.now(timezone.utc).date().toordinal()
    barras = ""
    for i, t in enumerate(ESSENCIA):
        rnd = random.Random(dia * 31 + i)
        valor = rnd.randint(38, 92)
        barras += f"""
        <div class="ess-linha">
          <div class="ess-topo">
            <span><span class="ess-sim" style="color:{t['cor']};filter:drop-shadow(0 0 4px {t['cor']})">{t['simbolo']}</span>
            <span class="ess-nome">{t['nome']}</span></span>
            <span class="ess-val" style="color:{t['cor']}">{valor}%</span>
          </div>
          <div class="ess-trilho"><div class="ess-fill" style="width:{valor}%;
               background:linear-gradient(90deg,{t['cor']}44,{t['cor']});box-shadow:0 0 8px {t['cor']}66"></div></div>
        </div>"""
    nome, simbolo, desc, ilum, energia = fase_lua()
    return f"""
<div class="ess-grid">
  <div class="painel">
    <div class="painel-titulo">ESSÊNCIA DA ALMA</div>
    {barras}
    <div class="ess-rodape">Estes valores refletem o estado energético do momento presente — eles se transformam a cada ciclo.</div>
  </div>
  <div class="painel lua-painel">
    <div class="painel-titulo">FASE DA LUA</div>
    <div class="lua-simbolo">{simbolo}</div>
    <div class="lua-nome">{nome}</div>
    <div class="ess-trilho" style="margin:6px 0"><div class="ess-fill" style="width:{ilum}%;
         background:linear-gradient(90deg,rgba(201,168,76,.4),rgba(201,168,76,.9))"></div></div>
    <div class="lua-desc">{desc}</div>
    <div class="lua-energia">{energia.upper()}</div>
  </div>
</div>
"""


def cabecalho(label, titulo, sub):
    return f"""
<div class="sec-head">
  <div class="sec-label">✦ {label} ✦</div>
  <div class="sec-titulo">{titulo}</div>
  <div class="sec-sub">{sub}</div>
</div>
"""


# ===========================================================================
# CSS
# ===========================================================================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Lora:ital,wght@0,400;0,500;1,400;1,500&family=IM+Fell+English:ital@0;1&display=swap');

html, gradio-app, .gradio-container, .gradio-container .fillable, .app { background: transparent !important; }
/* reserva o espaço da barra de rolagem sempre -> largura constante (sem "pulo") */
html { overflow-y: scroll !important; overflow-x: hidden !important; }
html, body, gradio-app, .gradio-container, .gradio-container .fillable, .app, main {
    scrollbar-gutter: stable !important; }
body, gradio-app, .gradio-container, .app { overflow-x: hidden !important; }
.gradio-container { max-width: 980px !important; margin: 0 auto !important; font-family: 'Lora', serif !important; }
body {
    background:
        radial-gradient(ellipse 60% 40% at 20% 20%, rgba(124,58,237,0.06) 0%, transparent 100%),
        radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.05) 0%, transparent 100%),
        #07040f !important;
    background-attachment: fixed !important;
}
footer { display: none !important; }

/* scrollbars sem setas */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-button { display: none !important; height: 0 !important; width: 0 !important; }
::-webkit-scrollbar-track { background: transparent !important; }
::-webkit-scrollbar-thumb { background: rgba(201,168,76,.25) !important; border-radius: 8px !important; }
* { scrollbar-width: thin; scrollbar-color: rgba(201,168,76,.25) transparent; }
.gradio-container textarea::-webkit-scrollbar { width: 6px; }

/* loader -> 🔮 */
.gradio-container .wrap.default, .gradio-container .loading-wrap { background: transparent !important; backdrop-filter: none !important; }
.gradio-container .wrap.default > *, .gradio-container .loading-wrap > *,
.gradio-container .wrap.default svg, .gradio-container .loading-wrap svg { display: none !important; }
.gradio-container .wrap.default::after, .gradio-container .loading-wrap::after {
    content: "🔮"; display:block; font-size:44px; line-height:1; animation: pulsar 1.4s ease-in-out infinite; }
@keyframes pulsar { 0%,100%{opacity:.4;transform:scale(.88);} 50%{opacity:1;transform:scale(1.12);} }

/* estrelas */
body::before, body::after { content:""; position:fixed; inset:0; z-index:0; pointer-events:none; background-repeat:repeat; }
body::before {
    background-image:
        radial-gradient(1px 1px at 25px 35px, #e8dff5, transparent),
        radial-gradient(1px 1px at 120px 80px, #c9a84c, transparent),
        radial-gradient(1px 1px at 200px 150px, #e8dff5, transparent),
        radial-gradient(1px 1px at 80px 220px, #c8b8e8, transparent),
        radial-gradient(1px 1px at 280px 60px, #e8dff5, transparent),
        radial-gradient(1px 1px at 170px 280px, #c9a84c, transparent);
    background-size: 320px 320px; animation: subir 150s linear infinite, piscar 5s ease-in-out infinite; opacity:.55; }
body::after {
    background-image:
        radial-gradient(2px 2px at 60px 120px, #e8dff5, transparent),
        radial-gradient(1.5px 1.5px at 240px 200px, #c9a84c, transparent),
        radial-gradient(1.5px 1.5px at 150px 40px, #e8dff5, transparent);
    background-size: 440px 440px; animation: subir 260s linear infinite, piscar 8s ease-in-out infinite; opacity:.4; }
@keyframes subir { from{background-position:0 0;} to{background-position:0 -1600px;} }
@keyframes piscar { 0%,100%{opacity:.3;} 50%{opacity:.7;} }
.gradio-container > * { position: relative; z-index: 1; }

/* transição suave entre seções: fade leve + escalonamento bem curto (sem buraco vazio) */
@keyframes secaoEntra { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }
/* cabeçalho aparece primeiro */
.secao.anim .sec-head,
.secao.anim .hero-label, .secao.anim .hero-title, .secao.anim .hero-sub, .secao.anim .orb {
    animation: secaoEntra .45s ease both; }
/* conteúdo logo em seguida (escalonamento sutil de ~0,18s) */
.secao.anim .hero-quote,
.secao.anim #card_area, .secao.anim #ora_btn_row,
.secao.anim #diario_card,
.secao.anim .ess-grid {
    animation: secaoEntra .5s ease .18s both; }

/* ===== NAV (HTML puro, FIXA na tela inteira, igual ao Figma) ===== */
.topbar { position:fixed; top:0; left:0; right:0; z-index:100;
    display:flex; align-items:center; justify-content:space-between;
    padding:0 32px; height:62px;
    background:rgba(7,4,15,0.92); backdrop-filter:blur(16px);
    border-bottom:1px solid rgba(201,168,76,0.1); }
/* espaço pro conteúdo não ficar embaixo da barra fixa */
.gradio-container { padding-top:74px !important; }
.marca-grupo { display:flex; align-items:center; gap:12px; }
.marca-star { color:#c9a84c; font-size:18px; filter:drop-shadow(0 0 8px rgba(201,168,76,.6)); }
.marca { font-family:'Cinzel',serif; font-size:13px; letter-spacing:.28em; color:#c9a84c;
    white-space:nowrap; text-shadow:0 0 8px rgba(201,168,76,.4); }
.nav-grupo { display:flex; gap:4px; }
.navitem { font-family:'Cinzel',serif; font-size:10px; letter-spacing:.2em; padding:6px 14px;
    border-radius:40px; background:transparent; border:1px solid transparent; color:#9b8ab8;
    cursor:pointer; transition:color .3s ease, background .3s ease, border-color .3s ease;
    white-space:nowrap; box-sizing:border-box; }
.navitem:hover { color:#c9a84c; }
.navitem.ativo { background:rgba(201,168,76,.1); border-color:rgba(201,168,76,.5); color:#c9a84c; }

/* cabeçalhos de seção */
.sec-head { text-align:center; margin: 30px 0 26px; }
.sec-label { font-family:'Cinzel',serif; font-size:10px; letter-spacing:.35em; color:rgba(201,168,76,.6); margin-bottom:10px; }
.sec-titulo { font-family:'Cinzel',serif; font-size:30px; color:#e8dff5; letter-spacing:.1em; }
.sec-sub { font-family:'Lora',serif; font-size:14px; color:#9b8ab8; font-style:italic; margin-top:8px; }

/* ===== HERO / ORBE ===== */
.hero { text-align:center; min-height:74vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.hero-label { font-family:'Cinzel',serif; color:rgba(201,168,76,.6); letter-spacing:.4em; font-size:11px; margin-bottom:14px; }
.hero-title { font-family:'Cinzel',serif; color:#e8dff5; font-size:clamp(34px,6vw,64px); font-weight:700;
    letter-spacing:.08em; line-height:1.2; }
.hero-sub { font-family:'IM Fell English',serif; font-style:italic; color:#9b8ab8; font-size:18px; margin-top:6px; }
.hero-quote { font-family:'Lora',serif; max-width:480px; margin:38px auto 0; color:#7c6a99; font-style:italic; font-size:15px; line-height:1.9; }

.orb { position:relative; width:280px; height:280px; margin:44px auto 8px; }
.orb-glow { position:absolute; inset:-46px; border-radius:50%;
    background:radial-gradient(circle, rgba(124,58,237,.4) 0%, rgba(201,168,76,.1) 45%, transparent 70%); filter:blur(8px); animation:pulso 5s ease-in-out infinite; }
.orb-core { position:absolute; inset:20px; border-radius:50%;
    background:radial-gradient(circle at 36% 33%, #f3dca6 0%, #c79bff 20%, #7a4cc0 46%, #371b66 74%, #1c0f38 100%);
    box-shadow: inset -12px -16px 44px rgba(0,0,0,.55), inset 10px 12px 34px rgba(255,222,150,.22), 0 0 55px rgba(124,58,237,.5); }
.orb-ring { position:absolute; inset:6px; border-radius:50%;
    background:conic-gradient(from 0deg, transparent 0 6%, #e7c87a 13%, transparent 27% 55%, #c9a84c 67%, transparent 82% 100%);
    -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 5px), #000 calc(100% - 4px));
            mask:radial-gradient(farthest-side, transparent calc(100% - 5px), #000 calc(100% - 4px));
    animation:girarRing 16s linear infinite; }
.orb-dots { position:absolute; top:50%; left:50%; width:4px; height:4px; border-radius:50%; background:#e9c879;
    box-shadow:
        0 -128px 3px -1px rgba(233,200,121,.85),64px -111px 3px -1px rgba(233,200,121,.85),
        111px -64px 3px -1px rgba(233,200,121,.85),128px 0 3px -1px rgba(233,200,121,.85),
        111px 64px 3px -1px rgba(233,200,121,.85),64px 111px 3px -1px rgba(233,200,121,.85),
        0 128px 3px -1px rgba(233,200,121,.85),-64px 111px 3px -1px rgba(233,200,121,.85),
        -111px 64px 3px -1px rgba(233,200,121,.85),-128px 0 3px -1px rgba(233,200,121,.85),
        -111px -64px 3px -1px rgba(233,200,121,.85),-64px -111px 3px -1px rgba(233,200,121,.85);
    animation:girarDots 22s linear infinite; }
@keyframes girarRing { to{transform:rotate(360deg);} }
@keyframes girarDots { from{transform:translate(-50%,-50%) rotate(0);} to{transform:translate(-50%,-50%) rotate(360deg);} }
@keyframes pulso { 0%,100%{opacity:.7;} 50%{opacity:1;} }

/* ===== ORÁCULO ===== */
.card-wrap { display:flex; justify-content:center; margin: 6px auto; }
.card-back, .card-front { width:240px; min-height:360px; border-radius:16px; }
.card-back { background:linear-gradient(135deg,#1e1335 0%,#0f0820 50%,#1a0e30 100%);
    border:1px solid rgba(201,168,76,.25); display:flex; flex-direction:column; align-items:center; justify-content:center; }
.card-back-star { font-size:48px; color:rgba(201,168,76,.4); margin-bottom:8px; }
.card-back-label { font-family:'Cinzel',serif; font-size:11px; color:rgba(201,168,76,.5); letter-spacing:.2em; }
.card-front { border:1px solid; padding:24px; display:flex; flex-direction:column; align-items:center;
    justify-content:space-between; gap:10px; animation: girarCarta .8s ease both; }
@keyframes girarCarta { 0%{opacity:.15; transform:rotateY(0deg) scale(.88);} 100%{opacity:1; transform:rotateY(360deg) scale(1);} }
.card-brand { font-family:'Cinzel',serif; font-size:10px; color:rgba(201,168,76,.6); letter-spacing:.3em; }
.card-symbol { font-size:56px; line-height:1; }
.card-name { font-family:'Cinzel',serif; font-size:14px; color:#e8dff5; letter-spacing:.1em; margin-top:6px; }
.card-elem { font-family:'Lora',serif; font-size:11px; color:#9b8ab8; font-style:italic; }
.card-msg { font-family:'Lora',serif; font-size:12px; color:#c8b8e8; text-align:center; line-height:1.7; font-style:italic; }
.card-kws { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
.kw { font-family:'Cinzel',serif; font-size:9px; border:1px solid; border-radius:20px; padding:2px 8px; letter-spacing:.15em; }
.card-fullmsg { font-family:'Lora',serif; max-width:400px; margin:22px auto 0; text-align:center;
    font-size:15px; color:#c8b8e8; line-height:1.9; font-style:italic; animation: surgir .8s ease both; }

/* ===== DIÁRIO ===== */
#diario_card {
    background:linear-gradient(135deg,#110c1e 0%,#0d0818 100%) !important;
    border:1px solid rgba(201,168,76,.15) !important; border-radius:20px !important;
    padding:32px !important; width:min(600px, 92vw) !important; margin:0 auto !important;
    box-sizing:border-box; }
/* o conteúdo do cartão também não pode esticar a largura */
#diario_card > *, #diario_card .block, #diario_card .form { width:100% !important; }
/* centraliza o cartão (largura fixa) na seção */
#sec_dia { align-items:center !important; }
#diario_card .block, #diario_card .form, #diario_card > div, #diario_card > div > div {
    width:100% !important; }
#diario_card textarea { width:100% !important; min-height:170px !important; box-sizing:border-box; }
.diario-card-label { font-family:'Cinzel',serif; font-size:10px; letter-spacing:.3em;
    color:rgba(201,168,76,.6); margin-bottom:16px; }
#diario_botoes { justify-content:flex-end !important; gap:12px !important; }
#diario_botoes button { flex:0 0 auto !important; width:auto !important; min-width:0 !important; }
/* altura fixa p/ a pergunta (cabe 2 linhas) -> cartão não "salta" ao trocar */
#prompt_dia { text-align:left !important; margin-bottom:6px !important;
    min-height:76px !important; height:76px !important; display:flex !important; align-items:center !important;
    overflow:hidden !important; }
#prompt_dia, #prompt_dia * { scrollbar-width:none !important; }
#prompt_dia::-webkit-scrollbar, #prompt_dia *::-webkit-scrollbar { display:none !important; }
#prompt_dia *, #prompt_dia .prose { min-height:0 !important; }
#prompt_dia p { font-family:'IM Fell English',serif !important; font-style:italic; font-size:19px !important;
    color:#e8dff5 !important; line-height:1.6 !important; margin:0 !important; }
#sec_dia textarea {
    background:rgba(201,168,76,.04) !important; border:1px solid rgba(201,168,76,.15) !important;
    border-radius:12px !important; color:#c8b8e8 !important; font-family:'Lora',serif !important;
    font-size:14px !important; line-height:1.8 !important; }
#sec_dia textarea:focus { border-color:rgba(201,168,76,.4) !important; box-shadow:none !important; }
#reflexao textarea {
    background:rgba(10,7,21,.5) !important; color:#c8b8e8 !important; text-align:center !important;
    font-family:'Lora',serif !important; font-style:italic; font-size:17px !important; line-height:1.9 !important;
    border:1px solid rgba(201,168,76,.18) !important; border-radius:16px !important; animation: surgir .7s ease both; }
@keyframes surgir { from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:none;} }

/* botões dourados */
#btn_consultar button, #btn_outra button, #btn_refletir button {
    font-family:'Cinzel',serif !important; font-size:11px !important; letter-spacing:.22em !important;
    border-radius:40px !important; transition:all .3s ease !important; }
#btn_refletir button { background:#c9a84c !important; color:#07040f !important; border:none !important; }
#btn_refletir button:hover { filter:brightness(1.08); transform:translateY(-2px); }
#btn_consultar button, #btn_outra button { background:transparent !important; color:#c9a84c !important;
    border:1px solid rgba(201,168,76,.35) !important; }
#btn_consultar button:hover, #btn_outra button:hover { background:rgba(201,168,76,.1) !important; }

/* ===== ESSÊNCIA ===== */
.ess-grid { display:flex; flex-wrap:wrap; gap:24px; justify-content:center; align-items:flex-start; }
.painel { padding:30px; background:linear-gradient(135deg,#110c1e 0%,#0d0818 100%);
    border:1px solid rgba(201,168,76,.15); border-radius:20px; }
.ess-grid .painel:first-child { width:380px; max-width:90vw; }
.painel-titulo { font-family:'Cinzel',serif; font-size:10px; letter-spacing:.3em; color:rgba(201,168,76,.6); margin-bottom:22px; }
.ess-linha { margin-bottom:18px; }
.ess-topo { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.ess-sim { font-size:14px; margin-right:8px; }
.ess-nome { font-family:'Cinzel',serif; font-size:11px; color:#e8dff5; letter-spacing:.1em; }
.ess-val { font-family:'Lora',serif; font-size:12px; font-style:italic; }
.ess-trilho { width:100%; height:3px; background:rgba(255,255,255,.05); border-radius:3px; overflow:hidden; }
.ess-fill { height:100%; border-radius:3px; animation: encher 1.2s ease-out both; }
@keyframes encher { from{width:0 !important;} }
.ess-rodape { margin-top:26px; padding-top:20px; border-top:1px solid rgba(201,168,76,.1);
    font-family:'Lora',serif; font-size:12px; color:#7c6a99; font-style:italic; text-align:center; line-height:1.7; }
.lua-painel { display:flex; flex-direction:column; align-items:center; gap:14px; min-width:220px; text-align:center; }
.lua-simbolo { font-size:72px; line-height:1; animation: pulso 4s ease-in-out infinite; filter:drop-shadow(0 0 16px rgba(201,168,76,.5)); }
.lua-nome { font-family:'Cinzel',serif; font-size:13px; color:#e8dff5; letter-spacing:.1em; }
.lua-desc { font-family:'Lora',serif; font-size:12px; color:#9b8ab8; font-style:italic; line-height:1.6; }
.lua-energia { font-family:'Cinzel',serif; font-size:10px; color:#c9a84c; border:1px solid rgba(201,168,76,.25);
    border-radius:20px; padding:4px 14px; letter-spacing:.2em; }

@media (max-width: 640px) {
    .marca { font-size:10px; letter-spacing:.15em; }
    #nav_esp button, #nav_ora button, #nav_dia button, #nav_ess button { font-size:8px !important; padding:5px 9px !important; }
    .hero-title { font-size:38px; }
    .orb { width:200px; height:200px; }
}

/* ===== CORREÇÕES: sobrescreve o estilo padrão (cinza) dos botões do Gradio ===== */
#nav_esp, #nav_ora, #nav_dia, #nav_ess,
#nav_esp button, #nav_ora button, #nav_dia button, #nav_ess button {
    background:transparent !important; background-image:none !important;
    border:1px solid transparent !important; color:#9b8ab8 !important; box-shadow:none !important;
    font-family:'Cinzel',serif !important; font-size:10px !important; letter-spacing:.2em !important;
    border-radius:40px !important; padding:6px 14px !important; min-height:0 !important; }
#nav_esp.ativo, #nav_ora.ativo, #nav_dia.ativo, #nav_ess.ativo,
#nav_esp.ativo button, #nav_ora.ativo button, #nav_dia.ativo button, #nav_ess.ativo button {
    background:rgba(201,168,76,.12) !important; border-color:rgba(201,168,76,.5) !important; color:#c9a84c !important; }

#ora_btn_row { justify-content:center !important; }
#btn_consultar { flex:0 0 auto !important; width:auto !important; min-width:0 !important; max-width:280px !important; }
#btn_consultar, #btn_consultar button, #btn_outra, #btn_outra button {
    background:transparent !important; background-image:none !important; color:#c9a84c !important;
    border:1px solid rgba(201,168,76,.35) !important; box-shadow:none !important;
    font-family:'Cinzel',serif !important; letter-spacing:.22em !important; font-size:11px !important;
    border-radius:40px !important; }
#btn_refletir, #btn_refletir button {
    background:#c9a84c !important; background-image:none !important; color:#07040f !important;
    border:none !important; box-shadow:none !important;
    font-family:'Cinzel',serif !important; letter-spacing:.22em !important; font-size:11px !important;
    border-radius:40px !important; }

/* remove as caixas cinzas internas do Diário (deixa só o cartão dourado) */
#diario_card .block, #diario_card .form, #diario_card .gr-group, #diario_card .styler,
#diario_card > div, #diario_card > div > div {
    background:transparent !important; border:none !important; box-shadow:none !important; }
#diario_card { background:linear-gradient(135deg,#110c1e 0%,#0d0818 100%) !important;
    border:1px solid rgba(201,168,76,.15) !important; }

/* botão Compartilhar (dourado, centralizado) + pôster */
#share_row { justify-content:center !important; }
#btn_compartilhar { flex:0 0 auto !important; width:auto !important; min-width:0 !important;
    background:#c9a84c !important; background-image:none !important; color:#07040f !important;
    border:none !important; box-shadow:none !important; font-family:'Cinzel',serif !important;
    letter-spacing:.2em !important; font-size:11px !important; border-radius:40px !important; }
#poster_out { max-width:420px !important; margin:16px auto !important; }
"""


# ===========================================================================
# Interface
# ===========================================================================
def construir():
    with gr.Blocks(title="Espelho da Alma") as demo:
        prompt_idx = gr.State(0)
        reflexao_st = gr.State("")  # guarda o texto da reflexão (robusto p/ o pôster)

        # ----- NAV (HTML puro, igual ao Figma) -----
        gr.HTML(HEADER_HTML)

        # ----- SEÇÃO: ESPELHO (home) -----
        with gr.Column(visible=True, elem_id="sec_esp", elem_classes=["secao"]) as sec_esp:
            gr.HTML(HERO_HTML)

        # ----- SEÇÃO: ORÁCULO -----
        with gr.Column(visible=True, elem_id="sec_ora", elem_classes=["secao"]) as sec_ora:
            gr.HTML(cabecalho("CONSULTA", "O Oráculo", "Uma mensagem do inconsciente coletivo para você"))
            card_html = gr.HTML(CARD_VERSO, elem_id="card_area")
            with gr.Row(elem_id="ora_btn_row"):
                btn_consultar = gr.Button("CONSULTAR O ORÁCULO", elem_id="btn_consultar")

        # ----- SEÇÃO: DIÁRIO -----
        with gr.Column(visible=True, elem_id="sec_dia", elem_classes=["secao"]) as sec_dia:
            gr.HTML(cabecalho("INTROSPECÇÃO", "Diário da Alma",
                              "Palavras escritas no limiar entre o consciente e o oculto"))
            with gr.Group(elem_id="diario_card"):
                gr.HTML('<div class="diario-card-label">DIÁRIO DA ALMA</div>')
                prompt_dia = gr.Markdown(f"_{PROMPTS_DIARIO[0]}_", elem_id="prompt_dia")
                txt_dia = gr.Textbox(show_label=False, lines=8,
                                     placeholder="Deixe as palavras fluir sem julgamento...")
                with gr.Row(elem_id="diario_botoes"):
                    btn_outra = gr.Button("OUTRA PERGUNTA", elem_id="btn_outra")
                    btn_refletir = gr.Button("RECEBER REFLEXÃO", elem_id="btn_refletir")
            reflexao = gr.Textbox(show_label=False, lines=6, interactive=False,
                                  elem_id="reflexao", container=False, visible=False)
            with gr.Row(elem_id="share_row"):
                btn_compartilhar = gr.Button("📤 Compartilhar", elem_id="btn_compartilhar", visible=False)
            poster_out = gr.Image(show_label=False, type="pil", visible=False,
                                  container=False, elem_id="poster_out")

        # ----- SEÇÃO: ESSÊNCIA -----
        with gr.Column(visible=True, elem_id="sec_ess", elem_classes=["secao"]) as sec_ess:
            gr.HTML(cabecalho("MAPEAMENTO", "Mapa da Essência",
                              "O estado energético da sua alma neste momento"))
            essencia_html = gr.HTML(render_essencia(), elem_id="essencia_area")

        # ----- navegação 100% no navegador (instantânea): liga os itens da barra HTML -----
        JS_NAV_INIT = """
        () => {
          window.trocarSecao = function(secId, navId){
            ['sec_esp','sec_ora','sec_dia','sec_ess'].forEach(function(s){var e=document.getElementById(s); if(e) e.style.display='none';});
            var a=document.getElementById(secId);
            if(a){ a.style.display='block'; a.classList.remove('anim'); void a.offsetWidth; a.classList.add('anim'); }
            ['nav_esp','nav_ora','nav_dia','nav_ess'].forEach(function(n){var x=document.getElementById(n); if(x) x.classList.remove('ativo');});
            var b=document.getElementById(navId); if(b) b.classList.add('ativo');
            window.scrollTo({top:0,behavior:'smooth'});
          };
          [['nav_esp','sec_esp'],['nav_ora','sec_ora'],['nav_dia','sec_dia'],['nav_ess','sec_ess']].forEach(function(p){
            var el=document.getElementById(p[0]);
            if(el && !el._ligado){ el._ligado=true; el.addEventListener('click', function(){ window.trocarSecao(p[1], p[0]); }); }
          });
          ['sec_ora','sec_dia','sec_ess'].forEach(function(s){var e=document.getElementById(s); if(e) e.style.display='none';});
          var h=document.getElementById('sec_esp'); if(h) h.classList.add('anim');
        }
        """
        demo.load(None, js=JS_NAV_INIT)
        # recalcula a Essência (valores do dia) a cada visita
        demo.load(render_essencia, outputs=essencia_html)

        # ----- Oráculo: tirar carta (instantâneo, no navegador, com giro) -----
        btn_consultar.click(None, js=JS_TIRAR_CARTA)

        # ----- Diário: outra pergunta -----
        def outra_pergunta(idx):
            novo = (idx + 1) % len(PROMPTS_DIARIO)
            return novo, gr.update(value=f"_{PROMPTS_DIARIO[novo]}_"), "", gr.update(visible=False, value="")

        btn_outra.click(
            outra_pergunta, inputs=prompt_idx,
            outputs=[prompt_idx, prompt_dia, txt_dia, reflexao],
            show_progress="hidden",
        ).then(
            lambda: ("", gr.update(visible=False), gr.update(visible=False, value=None)),
            outputs=[reflexao_st, btn_compartilhar, poster_out],
            show_progress="hidden",
        )

        def _reflexao_valida(txt):
            return bool(txt) and "🔮" not in txt and len(txt.strip()) > 30 \
                and not txt.startswith("O espelho ficou")

        # ----- Diário: receber reflexão (IA) — controla reflexão, estado, botão e pôster -----
        def refletir(idx, texto):
            esconde = (gr.update(visible=False), gr.update(visible=False, value=None))
            if not texto.strip():
                yield (gr.update(visible=True, value="🔮  escreva algo primeiro — deixe as palavras fluírem."),
                       "", *esconde)
                return
            yield (gr.update(visible=True, value="🔮  a alma está ouvindo você..."), "", *esconde)
            pergunta = PROMPTS_DIARIO[idx]
            ultimo = ""
            try:
                for parcial in gerar_reflexao_stream(pergunta, texto):
                    ultimo = parcial
                    yield (gr.update(visible=True, value=parcial), "", *esconde)
            except Exception:
                yield (gr.update(visible=True, value="O espelho ficou turvo por um instante. Tente de novo."),
                       "", *esconde)
                return
            final = polir(ultimo, "pt")
            yield (gr.update(visible=True, value=final), final,
                   gr.update(visible=_reflexao_valida(final)), gr.update(visible=False, value=None))

        def criar_poster(idx, ref_txt):
            if not _reflexao_valida(ref_txt):
                return gr.update(visible=False)
            img = gerar_poster(ref_txt, PROMPTS_DIARIO[idx], "pt")
            return gr.update(value=img, visible=True)

        btn_refletir.click(
            refletir, inputs=[prompt_idx, txt_dia],
            outputs=[reflexao, reflexao_st, btn_compartilhar, poster_out],
        )

        btn_compartilhar.click(
            criar_poster, inputs=[prompt_idx, reflexao_st], outputs=poster_out,
            show_progress="hidden",
        ).then(
            fn=None,
            js="""() => {
                let t = 0;
                const rolar = () => {
                    const el = document.querySelector('#poster_out');
                    if (el && el.offsetHeight > 50) {
                        el.scrollIntoView({behavior: 'smooth', block: 'center'});
                    } else if (t++ < 25) { setTimeout(rolar, 150); }
                };
                setTimeout(rolar, 150);
            }""",
        )

    return demo


if __name__ == "__main__":
    construir().launch(css=CSS, theme=gr.themes.Base())
