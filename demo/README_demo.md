## Demo (synthetic content — safe to share)

This folder contains a completely fictional manuscript and figures so users can run the pipeline immediately after cloning.

Run:
```bash
python -m reviewer.cli --input demo/synthetic_manuscript.pdf \
  --rubric config/rubrics/core_rubric.json \
  --out outputs/demo_review.md \
  --manuscript_type original_research \
  --study_design diagnostic_accuracy \
  --has_ai \
  --figure_images demo/figures/fig1.png demo/figures/fig2.png
```

Expected outputs:
- outputs/demo_review.md
- outputs/critic_issue_log.md
- outputs/figure_notes.txt
