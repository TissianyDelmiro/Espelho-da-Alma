---
title: Espelho da Alma
emoji: 🔮
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: 6.17.3
python_version: "3.12"
app_file: app.py
pinned: true
short_description: Mystical mirror for the soul — oracle, journal, inner map
tags:
- thousand-token-wood
- off-brand
- tiny-titan
models:
- Qwen2.5-3B-Instruct
---

> **Track:** Thousand Token Wood &nbsp;·&nbsp; **Badges:** Off Brand (custom UI), Tiny Titan (3B model)
>
> 🎬 **Demo video:** _(add link)_ &nbsp;·&nbsp; 📱 **Social post:** _(add link)_


# 🔮 Espelho da Alma · Mirror of the Soul

A **mystical portal for self-reflection**, in four spaces. The interface is in
Portuguese (that's where the magic lands for its audience); this page is in
English for the judges.

> *"The mirror does not lie, but we rarely show ourselves enough for it to
> reveal what lies beneath the surface."*

## The four spaces

- **🪞 Espelho** (Mirror) — the home: a glowing, rotating orb and a welcome.
- **🃏 Oráculo** (Oracle) — draw one of six hand-written cards (The Inner Moon,
  The Broken Mirror, Star of the Abyss…), each with a symbol, element and
  message. Instant, like tarot.
- **📓 Diário** (Journal) — **this is where the AI lives.** You write freely in
  response to a "shadow" prompt, and the *voice of the soul* answers with a
  short, intimate reflection — written live, token by token.
- **🌙 Essência** (Essence) — an "energy map": five traits whose values shift
  each day, plus the **real current moon phase** (computed astronomically).

## What makes it special

- **The model runs inside this Space** — Qwen2.5-3B via **transformers** on a
  free **ZeroGPU**. **No external LLM / cloud API is called**; the whole
  experience is self-hosted.
- **Custom interface**, built from a Figma design: animated starfield, a CSS
  orb that spins, flipping oracle cards, a gold-on-black mystical theme,
  staggered section transitions — fully responsive.

## The craft behind the Diário

The magic isn't the model — it's the prompt. Three rules make a small model
feel like it *knows* you:

1. **Literal echo** — it reuses your exact words, transformed, never swapped
   for generic synonyms.
2. **Concrete image** — banned vague words ("deep", "sensitive", "intense");
   only scenes, objects, textures.
3. **Declare, don't analyze** — second person, present tense, no hedging.

Built for the Hugging Face *Build Small* hackathon.
