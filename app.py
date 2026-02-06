import json


if not ollama_ok():
st.error("Ollama is not reachable. Start Ollama and try again.")
st.stop()


preset = PRESETS[preset_key]
missing = [
tag
for tag in (preset["critic"], preset["writer"], preset["vlm"])
if not ollama_has_model(tag)
]
if missing:
st.error("Missing model(s) for this preset: " + ", ".join(missing))
st.info("Run `setup_models.bat` to install models, then come back and try again.")
st.stop()


if not reviewer_cli_exists():
st.error("Reviewer engine not found at reviewer/cli.py")
st.stop()


pdf_path = saved_path
out_md = OUTPUTS_DIR / f"{pdf_path.stem}_review.md"


st.info("Running… this can take several minutes depending on preset and PDF size.")


rc = run_pipeline(
pdf_path=pdf_path,
out_md=out_md,
preset=preset,
manuscript_type=manuscript_type,
study_design=study_design,
has_ai=has_ai,
fig_dpi=fig_dpi,
fig_max_pages=fig_max_pages,
fig_fallback=fig_fallback,
temperature=temperature,
show_live_log=show_live_log,
)


if rc == 0:
st.success("Review complete.")
else:
st.error(f"Review exited with code {rc}. See terminal output for details.")


# Always show any existing outputs for the last uploaded PDF
if uploaded_pdf:
pdf_path = saved_path
out_md = OUTPUTS_DIR / f"{pdf_path.stem}_review.md"
critic_log = OUTPUTS_DIR / "critic_issue_log.md"
fig_notes = OUTPUTS_DIR / "figure_notes.txt"
checklist = OUTPUTS_DIR / "reporting_checklist_gaps.json"


tabs = st.tabs(["Review", "Critic log", "Figure notes", "Checklist gaps"])


with tabs[0]:
txt = file_text(out_md)
if txt:
st.download_button("Download review.md", txt, file_name=out_md.name, mime="text/markdown")
st.text_area("Preview", txt, height=450)
else:
st.caption("No review output yet.")


with tabs[1]:
txt = file_text(critic_log)
if txt:
st.download_button("Download critic_issue_log.md", txt, file_name=critic_log.name, mime="text/markdown")
st.text_area("Preview", txt, height=450)
else:
st.caption("No critic log yet.")


with tabs[2]:
txt = file_text(fig_notes)
if txt:
st.download_button("Download figure_notes.txt", txt, file_name=fig_notes.name, mime="text/plain")
st.text_area("Preview", txt, height=450)
else:
st.caption("No figure notes yet.")


with tabs[3]:
if checklist.exists():
raw = checklist.read_text(encoding="utf-8", errors="ignore")
st.download_button("Download reporting_checklist_gaps.json", raw, file_name=checklist.name, mime="application/json")
try:
st.json(json.loads(raw))
except Exception:
st.code(raw, language="json")
else:
st.caption("No checklist gaps file yet.")


st.divider()
st.subheader("Your uploaded PDFs (private_inputs)")
ensure_dirs()
pdfs = sorted(PRIVATE_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
if not pdfs:
st.caption("No PDFs saved yet.")
else:
for p in pdfs[:30]:
st.caption(f"- {p.name}")
