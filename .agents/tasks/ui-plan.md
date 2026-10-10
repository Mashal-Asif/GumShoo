# Implementation Plan: GumShoo Streamlit Front-End

## Overview

This plan implements the complete Streamlit front-end for GumShoo (spec tasks 5-6). The backend is fully implemented and all tests pass. The front-end consists of theme/styling assets and three application pages that integrate with the existing backend architecture.

## Status Analysis

**✅ Already Implemented (Backend):**
- Core services: registry, schema, readers, settings, navigation
- All 4 stub detection tools with proper self-registration
- Comprehensive test suite (104 tests passing)
- Project structure and configuration

**❌ Missing (Front-End):**
- CSS stylesheet and Streamlit theme configuration
- Home page (entry point)
- Input page (with tabbed input methods)
- Results page (with export functionality)

## Implementation Plan

### Task 5: Theme and Styling Assets

- [ ] 1. Create CSS stylesheet with professional GumShoo theme.
      Implement color palette (ink, muted, line, plum, lavender), Google Fonts (Source Serif 4, Inter), typography styles, topbar navigation, module eyebrows, button styles, file uploader styling, and WCAG AA contrast compliance.
      Files: `d:\GumShoo\assets\style.css`
      Verify: Load Home page and confirm styles are applied correctly.

- [ ] 2. Create Streamlit theme configuration file.
      Configure primaryColor=#6B21A8 (plum), backgroundColor=#FFFFFF, secondaryBackgroundColor=#EDE9FE (lavender), textColor=#1A1A2E (ink), font=sans serif, server.headless=true.
      Files: `d:\GumShoo\assets\.streamlit\config.toml`
      Verify: Run `python -m streamlit run app/Home.py` and confirm theme colors are applied.

### Task 6: Application Pages

- [ ] 3. Implement Home page (main entry point).
      Set page config using settings.page_title and settings.page_layout, load custom CSS, initialize session state (selected_tool=None, analysis_complete=False, result=None), import all tool modules for self-registration, display topbar navigation, show 4 tool cards in 2x2 grid from registry.list_all_tools(), include module number eyebrows (01-04), show tool status without emoji, implement tool selection buttons calling navigate_to_input(), add footer disclaimer about estimates vs verdicts.
      Files: `d:\GumShoo\app\Home.py`
      Verify: Run application, confirm all 4 tools display with correct status, test tool selection navigation.

- [ ] 4. Implement Input page (tabbed input collection).
      Set page config, load CSS, redirect to Home if no selected_tool, display tool info from registry, implement 3 input tabs (Upload File, Paste Text, Enter URL), validate file extensions per tool.accepted_input_types (image: png/jpg/jpeg/webp; text: txt/docx; csv: csv), dispatch files correctly (.png/.jpg/.jpeg/.webp → read_image, .txt → read_text_file, .docx → read_docx with text/image routing, .csv → read_csv with column detection), implement text paste with processing modes (whole document vs line-separated posts), implement URL fetching with InputReader.fetch_url, validate file sizes vs settings, show loading states during URL fetch and analysis, display clear error messages for InputValidationError and SSRFProtectionError, call tool.analyze_fn(input_data) and navigate_to_results(result), provide Back to Home button.
      Files: `d:\GumShoo\app\pages\1_Input.py`
      Verify: Test all input methods with each tool type, confirm validation and error handling work correctly.

- [ ] 5. Implement Results page (display and export).
      Set page config, load CSS, redirect to Home if no result, display topbar, show prominent "estimate not verdict" disclaimer, display demo mode warning when is_demo=True, render single results with 3 metrics (Classification, Confidence %, Model), display result.details as key/value pairs, show result.warnings with st.warning, render batch results as DataFrame with label/score%/model_name/is_demo columns, implement CSV download button converting results to DataFrame, implement JSON download button with result.to_dict(), provide "Analyze Another" button calling navigate_to_input(selected_tool), provide "Back to Home" button calling navigate_to_home().
      Files: `d:\GumShoo\app\pages\2_Results.py`
      Verify: Test single and batch result display, confirm export buttons work, verify navigation buttons function.

### Integration Verification

- [ ] 6. Final integration testing and polishing.
      Test complete end-to-end workflow: Home → Tool Selection → Input (all 3 methods) → Results → Navigation back. Verify CSS loads in all pages (relative path from Streamlit's cwd), confirm all tool imports trigger self-registration, test error handling paths, verify no emoji appear anywhere, confirm WCAG AA contrast in all text elements, test Windows PowerShell compatibility with `python -m streamlit run app/Home.py`.
      Files: All pages updated as needed for polish
      Verify: Complete manual testing of all workflows and error scenarios.

## Key Implementation Decisions

### CSS Loading Strategy
Load CSS in each page using `with open("assets/style.css")` and `st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)`. This works from any page because Streamlit's cwd is the project root when running `python -m streamlit run app/Home.py`.

### Tool Registration Side Effects
Import all four tool packages (`tools.deepfake`, `tools.sentiment`, `tools.fraud`, `tools.propaganda`) in Home.py so their `__init__.py` files execute and register with the global registry instance. This ensures tools are available before the UI tries to display them.

### File Extension Routing
Based on file extension and tool.accepted_input_types:
- Images (.png, .jpg, .jpeg, .webp) → InputReader.read_image()
- Text files (.txt) → InputReader.read_text_file()
- DOCX files (.docx) → InputReader.read_docx() then route text to text tools or first image to image tools
- CSV files (.csv) → InputReader.read_csv() and show detected column name

### Batch Processing Support
Sentiment analysis tool accepts `List[str]` and returns `List[AnalysisResult]`. Results page handles both single results and lists. CSV input and line-separated text input create batch processing scenarios.

### Error Handling Patterns
Display user-friendly error messages for:
- InputValidationError: File size limits, invalid formats, empty content
- SSRFProtectionError: Blocked IP ranges, invalid schemes
- Analysis errors: Model failures, invalid input data

### Navigation State Management
Use session state for:
- `selected_tool`: Current tool name (None when on Home page)
- `result`: Analysis result(s) for Results page (None when no results)
- `analysis_complete`: Boolean flag for workflow state

### Demo Mode Indicators
Always show prominent indicators when `is_demo=True`:
- Info banner on Results page: "DEMO MODE: These results are generated from stub implementations"
- Warning text in result.warnings from stub tools
- Tool status display shows "Demo Mode" (no emoji)

## Integration Pitfalls to Avoid

1. **CSS Path Resolution**: Use `assets/style.css` relative path, not absolute. Streamlit's working directory is the project root when launched with `python -m streamlit run app/Home.py`.

2. **Tool Import Order**: Import tool packages in Home.py before accessing registry.list_all_tools(). The import side effects must happen before UI rendering.

3. **Session State Initialization**: Call `init_session_state()` in every page to ensure consistent state, but only set defaults for missing keys to preserve navigation state.

4. **Result Type Handling**: Check if result is a list before rendering. Single results and batch results need different display logic.

5. **File Size Validation**: Check file size before calling InputReader methods to provide better error messages.

6. **URL Security**: Never bypass InputReader.fetch_url() validation. All URL input must go through SSRF protection.

7. **Error Message Clarity**: Catch InputValidationError and SSRFProtectionError separately to show appropriate user-facing messages.

8. **Demo Mode Consistency**: Always check `result.is_demo` and display warnings. Users must understand these are not real analysis results.

9. **Windows Path Handling**: Use forward slashes in CSS paths and avoid Windows-specific path operations in Streamlit components.

10. **Streamlit Theme Integration**: The config.toml must be in `assets/.streamlit/` and colors must match CSS custom properties for consistency.