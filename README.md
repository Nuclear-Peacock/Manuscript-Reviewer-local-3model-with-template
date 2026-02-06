Local Manuscript Reviewer (Radiology / Nuclear Medicine / Medical Education / AI)

A local-only manuscript review assistant that helps you generate a structured, human-style peer review.

✅ Runs on your computer (localhost only)

✅ Manuscripts stay on your PC

✅ Designed for radiology, nuclear medicine, medical education, and AI-in-radiology/education

⚠️ Privacy / confidentiality (please read)

No deployment needed. This tool is meant to run only on your computer.

Do not deploy this app.

Do NOT deploy to any server.

Do NOT use tunnels (ngrok / Cloudflare Tunnel / Streamlit Cloud).

Uploaded manuscripts are saved in private_inputs/ on your PC.

Outputs are saved in outputs/ on your PC.

If you are reviewing unpublished work, keeping this local helps protect confidentiality.

Windows (One-click UI Quickstart)

What you need (one time)

Python 3.10+

Download from the official Python website.

During install, check “Add Python to PATH.”

Ollama (local LLM runner)

Install Ollama.

Open Ollama once so it is running.

Start the UI

Start Ollama.

Double-click run_ui.bat.

Your browser should open automatically at:

http://127.0.0.1:8501

If the browser does not open, open Chrome/Edge and go to that address.

Stop the UI

Close the browser tab.

Go to the black terminal window and press Ctrl+C.

Using the UI

Upload your manuscript PDF (drag-and-drop is fine).

Choose Medium quality, Medium speed (recommended).

Choose the manuscript category (and study design if it is original research).

Click Start review.

Download your report from Results.

What you get (outputs)

Your results are saved locally to outputs/ and are also available as download buttons in the UI.

Common files

*_review.md — the main structured review

critic_issue_log.md — critic pass notes (issues/questions)

figure_notes.txt — figure/table notes (vision model)

reporting_checklist_gaps.json — reporting checklist gaps (if produced)

Uploads are stored in

private_inputs/

Troubleshooting

“Ollama not reachable”

Open Ollama and make sure it is running.

“Missing model(s)”

Run setup_models.bat and choose the recommended option.

Then re-run run_ui.bat.

The UI loads but the review does not start

First run can be slow while models warm up.

Wait 30–60 seconds and try again.

I double-click run_ui.bat and nothing happens

Right-click run_ui.bat → Run as administrator (rare).

Or open Command Prompt in the repo folder and run:

run_ui.bat

Model quality presets (plain English)

In the UI you can choose:

High quality, Low speed — best review quality, slowest

Medium quality, Medium speed — recommended balance

Low quality, High speed — fastest quick pass

Models used (local):

Critic: DeepSeek-R1

Writer: Llama 3.3

Vision (figures/tables): Qwen2.5-VL

Advanced (optional)

Where settings live

Review rubric / prompts / templates are in config/

Running from the command line (optional)

If you prefer not to use the UI:

See reviewer/cli.py

License

MIT License
