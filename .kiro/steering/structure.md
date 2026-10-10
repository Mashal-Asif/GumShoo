# Structure
app/        Streamlit entry point and pages
core/       tool registry, result schema, input readers, settings
tools/      one package per tool (deepfake, sentiment, fraud, propaganda)
models/     model files (gitignored) and model cards
assets/     style.css and theme
tests/      pytest tests
legacy/     old prototype, read-only reference
Rule: each tool implements one interface and registers in one place.
Adding a tool means adding one folder and one registry entry.
