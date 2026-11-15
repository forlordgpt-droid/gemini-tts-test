# Gemini 3.8 Flash-Lite TTS via GitHub Actions

This project generates the speech **"Yes this is working"** using Kie.ai's `google/gemini-3-8-flash-lite-tts` model, then saves the resulting WAV file as a GitHub Actions artifact.

## Setup

1. Go to **Settings → Secrets and variables → Actions → New repository secret**.
2. Add the secret **`KIE_API_KEY`**, with your Kie.ai API key as the value. Never commit your `.env` file or API key.
3. Go to **Actions → Generate Gemini 3.8 Flash-Lite TTS → Run workflow**.
4. Leave the text as **Yes this is working**, and click **Run workflow**.
5. When the workflow finishes, open the run and download the **gemini-tts-wav** artifact containing `yes_this_is_working.wav`.

The workflow is manually triggered only. Generating speech may consume Kie.ai credits.

API: https://docs.kie.ai/market/google/gemini-3-8-flash-lite-tts
