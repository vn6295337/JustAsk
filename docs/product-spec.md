# JustAsk Product Spec

Draft · 2026-11-07

---

## 1. Users and Use Cases

- **Who:** interviewers, plus the owner during demos.
- **Where:** mainly India.
- **How many:** a handful at a time.
- **Device:** Android phone.
- **Use:** type a question, get an answer. No setup.

---

## 2. Hard Rules

- **Free forever:** use only free tiers and free models. Never call a paid model.
- **No signup:** no accounts, no login.
- **Honest privacy:**
  - Tell users that questions go to outside AI providers, and that those providers may keep, read or train on them.
  - A phone ID and the network address (IP address) are held briefly in memory, only to apply usage limits.
- **18+ only:** the user confirms their age on first use.
- **Nothing personal kept on our server:** no questions, answers or IP addresses in logs.

### Not in Scope

- Accounts or login
- Paid models, paid hosting or buying credits
- Chat history in the cloud, or sync between devices
- Users in Europe (EU and nearby countries), the UK or Switzerland, because Gemini's free tier is not allowed there
- Images, files or voice
- AI that takes actions; it only answers

---

## 3. Features

| Feature | What it does |
|---|---|
| Ask | Type a question, tap Send. |
| Streamed answer | Words appear as the model writes them. |
| Automatic model choice | The app picks the best free model available. The user never picks. |
| Free-quota switching | When a model's free quota (its allowed questions per minute or per day) runs out, switch to the next suitable model that still has quota. Small models are fine. OpenRouter free models are the last resort. |
| "Capacity used up" message | When every free quota is used up: "Free capacity used up. Try again after (time)." |
| Daily limit per phone | 100 questions per phone per day, then "Daily limit reached." |
| First-use notice | A privacy notice and "I am 18 or older." The user accepts once. |
| Install page | The download page lists the app's permissions (internet and network status only), links a VirusTotal scan of the app file and links the source code. Check the built file's permissions before each release, because libraries can add some. |
| Out-of-date warning | The app says answers may not cover recent events. |
| Local history | Chat history stays on the phone. The user can clear it. |
| Offline questions | When offline, save the question and send it when the phone is back online. |
| Saved answers | A repeated question gets its saved answer instantly. News answers expire quickly. |

### Behind-the-Scenes Tools

- **Model registry:** keeps the list of free models and their limits up to date.
- **Dashboard:** shows which free models exist and how the list changes.

---

## 4. Quality Targets

| Area | Target |
|---|---|
| First word of the answer | Within 5 seconds, when the server is awake |
| First question after the server has been idle | Can be slower. The app shows "Waking up…" |
| Uptime | Best effort |
| Capacity | A handful of users at a time |
| Monthly cost | $0 |
| Model list freshness | Updated at least weekly. Alert the owner if an update fails. |
| Security | Provider keys exist only on the server. Only the owner can change model rankings or limits. |

---

## 5. Provider Landscape

| | Gemini (Google) | Groq | OpenRouter (free models) |
|---|---|---|---|
| Free limit | Set per model. See "Gemini Free Limits" below. | Set per model. See "Groq Free Limits" below. | No purchase needed. 20 per minute and 50 per day, shared across all free models. Rises to 1,000 per day after a one-time purchase of $10 in credits. |
| Uses your questions | Yes, on the free tier. People at Google may read them. | Keeps logs up to 30 days unless "Zero Data Retention" is turned on. Training use not stated. | Depends on the model host. A setting can block hosts that collect data. |
| Age rule | 18+ only. Not for apps likely used by under-18s. | Not checked | Not checked |
| Region rule | Free tier not allowed for users in Europe (EU and nearby countries), the UK or Switzerland | Not checked | Not checked |
| Shows remaining quota | Not checked | With every answer | Through account info, or when a request fails |
| Small free models | 3.1 Flash Lite, 3.5 Flash Lite, Gemma 4 | gpt-oss-20b | LFM2.5-2.6B, Gemma 4. See "OpenRouter Free Models" below. |
| Recent changes | Gemini 2.0 Flash models passed their shutdown date (June 2026). 2.5 Flash and 2.5 Pro are closed to new users and retire December 2026. | Llama models became Enterprise-only, meaning available only under paid contracts (Aug 2026). Compound, Groq's web-search system, was shut down (Sep 2026). | Not checked |

### Gemini Free Limits

From the owner's Google AI Studio project, 2026-11-08. Text models only.

| Model | Questions per minute | Tokens per minute | Questions per day |
|---|---|---|---|
| Gemini 3.8 Flash | 5 | 250K | 20 |
| Gemini 3.6 Flash | 5 | 250K | 20 |
| Gemini 3 Flash | 5 | 250K | 20 |
| Gemini 2.5 Flash (retires Dec 2026) | 5 | 250K | 20 |
| Gemini 3.5 Flash Lite | 15 | 250K | 500 |
| Gemini 3.1 Flash Lite | 15 | 250K | 500 |
| Gemini 2.5 Flash Lite | 10 | 250K | 20 |
| Gemma 4 31B | 30 | 16K | 14,400 |
| Gemma 4 26B | 30 | 16K | 14,400 |

- **Not free on this project (limit 0):** Gemini 2 Flash, 2 Flash Lite, 2.5 Pro, 3.1 Pro, 4 Argon.
- **Daily total:**
  - Flash and Flash Lite models: about 1,100 questions.
  - Gemma: 28,800 questions.
- **Gemma's real limit is tokens:** 16K tokens per minute is about 16 questions per minute per model, at about 1,000 tokens per question.
- **Google Search (web search):**
  - Free for Gemini 2.5 models, up to 1,500 per day.
  - Not free for Gemini 3 and newer.
  - The real cap is the model's own daily limit: 20 per day.

### Groq Free Limits

From the Groq rate-limits page (free plan table), 2026-11-10. Text models only.

| Model | Questions per minute | Questions per day | Tokens per minute | Tokens per day |
|---|---|---|---|---|
| openai/gpt-oss-120b | 30 | 1,000 | 8K | 200K |
| openai/gpt-oss-20b | 30 | 1,000 | 8K | 200K |
| qwen/qwen3.8-27b | 30 | 1,000 | 8K | 200K |

- **Tokens run out before questions.**
  - At about 1,500 tokens per question (gpt-oss "thinking" text counts too), 200K tokens per day is about 130 questions per model.
  - 8K tokens per minute is about 5 questions per minute per model.
- **Daily total:** about 400 questions across the 3 models, not 3,000.
- **Left out:** speech models (Orpheus, Whisper) and safety checkers (Prompt Guard 2, gpt-oss-safeguard-20b). They don't write answers.

### OpenRouter Free Models

From the OpenRouter models page, 2026-11-08. Text models only. "Weekly tokens" shows how busy each model is across all OpenRouter users.

| Model | Weekly tokens | Note |
|---|---|---|
| NVIDIA Nemotron 3 Ultra | 3.2T | Busiest |
| NVIDIA Nemotron 3.5 Super VL | 3.14T | Also reads images |
| NVIDIA Nemotron 3.5 Lightning | 1.24T | |
| Dots Studio Dots3-Note Preview | 794B | Preview |
| Cohere North Mini Code | 224B | Built for code |
| NVIDIA Nemotron 3 Nano Omni | 134B | Also reads images and audio |
| XingChen Xing4.0 29B A4B | 108B | |
| Recursive Flint | 99.2B | |
| LiquidAI LFM2.5-2.6B | 12B | Small model |
| Respan Span-01 Lite | 1.23B | |
| Google Gemma 4 26B A4B | 1.12B | Also free on Gemini directly |
| Google Gemma 4 31B | 637M | Also free on Gemini directly |

- **Left out:** embedding, rerank and speech models. They don't write answers.
- **Notes come from model names and the page labels.** Not checked further.
- **More models don't add capacity.** The free limit (20 per minute, 50 per day) is shared across all free models. Extra models are backups for when one model's host is busy.
- **Gemma 4 has two separate free quotas:** one on Gemini, one on OpenRouter.
- **A negative account balance blocks free models too** (error 402). New accounts get a small free allowance, so a paid model called by mistake can succeed and use it up.
  - Only call model IDs that end in ":free".
  - If a free model returns error 402, stop using OpenRouter and alert the owner.
- **Data use:** not checked per model. Blocking hosts that collect data may remove some models from this list.

---

## 6. Lessons from the Current Build

| What went wrong | Requirement |
|---|---|
| The model list stopped updating in May 2026, and nobody noticed. | Alert the owner when an update fails. Each provider updates on its own, so one failure doesn't stop the others. |
| Groq and Google retired the app's default models. | No hard-coded model names. Check each provider's live model list. |
| Every question tried the same used-up model first. | Remember which free quotas are used up, and skip them until they reset. |
| One user could use up all the free quota. | A daily limit per phone, plus a limit per IP address. |
| Anyone with the public database key could change rankings and limits. | Only the owner can change rankings and limits. |
| The privacy claims ("no data collection") were not true. | Privacy wording must match what the providers actually do. |
| Each free server took about 1 minute to wake up after being idle. | Show "Waking up…" while the server starts. |
| The app followed a fixed ranking even when a model's quota was used up. | Model choice follows the owner's ranking and skips models whose quota is used up. |
| Empty answers counted as successes. | An empty or blocked answer counts as a failure, and the app switches models. |
| A partial model-list update could delete good data. | Don't replace the model list if the new one is much smaller than the old one. |
| The offline sync re-sent questions and multiplied usage. | Send each saved question once. Give up after 3 failed tries. Saved questions count toward the daily limit. |
| Saved answers could be wrong (two different questions matched) or out of date (kept 7 days). | Match the exact question. Keep news answers about 1 hour and other answers up to 7 days. |

---

## 7. Success Measures

| Measure | Formula | Target |
|---|---|---|
| Answer success | Questions answered / questions asked | ≥ 90% |
| Fast first word | Answers whose first word arrives within 5 seconds / all answers (server awake) | ≥ 80% |
| Quota switch success | Questions answered after a quota switch / questions that hit a used-up quota | ≥ 90% |
| Wasted calls | Calls to quotas already known to be used up / all calls | Near 0 |
| Paid calls | Count of calls to paid models | 0 |

---

## 8. Top Risks

| Risk | Impact | Response |
|---|---|---|
| Providers change free limits or remove models without notice | The app stops answering | Check live model lists, and alert on update failure |
| Free capacity runs out during an interview | The demo fails | Daily limit per phone. Check remaining quota before each interview. |
| Android warns about, or blocks, an app installed from outside the Play Store | The interviewer can't install the app | Test the install on 2 or 3 phones. Send a short install note with the link. |

---

## 9. Open Decisions

| Decision | Default | Reason |
|---|---|---|
| Does the 5-second target include the first question after the server has been idle? | No | Including it needs a keep-awake setup. |
| Daily limit per phone | 100 questions | Stops one person or script from using up everyone's free quota. |
| How interviewers install the app | An Android app file (APK) shared through a GitHub Releases link | Free. Doesn't depend on Expo Go supporting this app's Expo version. |
| Live web search for news | Keep, limited to about 20 per day | Gemini 2.5 Flash Lite with Google Search is free. When that runs out, answer without search and show the out-of-date warning. Google's display rules for search results not checked. || One server instead of two | Yes | Two free servers double the wake-up wait. |
| Web version as the no-install option | Yes | For interviewers who won't install an app file. Whether chat history storage works in a browser is not checked. |