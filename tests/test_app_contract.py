from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "app.py").read_text(encoding="utf-8")
CONFIG = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")


def test_app_compiles():
    compile(SRC, "app.py", "exec")


def test_all_dashboard_sections_present():
    for name in ["Overview", "Artists", "Collaboration", "Content", "Formats", "Duration", "Health", "Strategy"]:
        assert f'"{name}"' in SRC


def test_navigation_is_segmented_control():
    assert "st.segmented_control(" in SRC
    assert 'key="dashboard_section"' in SRC


def test_artist_comparison_is_local_to_artists():
    assert 'key="artist_comparison_main"' in SRC
    assert "Artist comparison" in SRC


def test_olive_theme_configuration():
    assert 'primaryColor = "#737D52"' in CONFIG
    assert 'backgroundColor = "#EEE9DC"' in CONFIG
    assert 'secondaryBackgroundColor = "#F5F1E7"' in CONFIG


def test_semantic_chart_colors_defined():
    assert "FORMAT_COLORS" in SRC
    assert "COLLAB_COLORS" in SRC
    assert "EXPLICIT_SCATTER_COLORS" in SRC


def test_release_format_chart_uses_semantic_mapping():
    assert 'FORMAT_COLORS.get(str(trace.name).lower()' in SRC


def test_collaboration_donut_uses_semantic_mapping():
    assert "color_discrete_map=COLLAB_COLORS" in SRC


def test_heatmap_has_readable_olive_contrast():
    assert '[0.00, "#F4F0E5"]' in SRC
    assert '[1.00, "#596447"]' in SRC
    assert "colorscale=HEATMAP_SCALE" in SRC


def test_scatter_is_not_overly_faint():
    assert "color_discrete_map=EXPLICIT_SCATTER_COLORS, opacity=0.50" in SRC
    assert "size=5.2" in SRC
    assert '"Clean": "#7C876E"' in SRC
    assert '"Explicit": "#596447"' in SRC


def test_quality_table_is_static():
    assert "render_static_table(" in SRC
    assert "Observed result" in SRC
    assert "Assessment" in SRC


def test_lazy_quality_validation():
    assert "def load_quality_report" in SRC
    assert 'if active_view == "Health"' in SRC


def test_no_old_orange_primary_color_in_app():
    for old in ["#E4572E", "#E85C3F", "#F15A3A", "#B86F59"]:
        assert old not in SRC


def test_no_dash_migration_code_in_final_app():
    assert "Dash(" not in SRC
    assert "dash_app" not in SRC


def test_release_format_order_is_stable():
    assert 'release_order = [c for c in ["album", "single", "compilation"] if c in rfr.columns]' in SRC
    assert '"compilation": "#B9B7A7"' in SRC


def test_collaboration_semantic_order_is_stable():
    assert 'collab_order = ["Solo chart entries", "Collaborative chart entries"]' in SRC
    assert '"Solo chart entries": "#B8B8AA"' in SRC
    assert '"Collaborative chart entries": "#66734C"' in SRC


def test_control_states_are_forced_to_olive():
    assert "FINAL_OLIVE_CONTROL_STATES" in SRC
    assert "background:var(--accent) !important;" in SRC


def test_final_release_format_semantic_colors():
    assert '"album": "#5E6849"' in SRC
    assert '"single": "#9A8F67"' in SRC
    assert '"compilation": "#B9B7A7"' in SRC


def test_final_collaboration_semantic_colors():
    assert '"Solo chart entries": "#B8B8AA"' in SRC
    assert '"Collaborative chart entries": "#66734C"' in SRC


def test_ranked_bar_darkest_color_is_capped():
    assert 'BAR_SCALE = ["#B7B99E", "#A4AA87", "#8D9670", "#747F59", "#566044"]' in SRC


def test_native_control_theme_is_olive():
    assert '--primary-color:#737D52 !important;' in SRC
    assert 'label:has(input:checked) > div:first-child > div' in SRC


def test_metric_transparency_is_preserved_without_formula_heavy_ui():
    assert "Artist concentration (HHI)" in SRC
    assert "Snapshot diversity" in SRC
    assert "Effective artists" in SRC

    # Exact formulas should not clutter the main dashboard UI.
    assert "10,000 × Σ(pᵢ²)" not in SRC
    assert "H = -Σ(pᵢ × ln pᵢ)" not in SRC

    # Formula-level transparency remains in the methodology documentation.
    root = Path(__file__).resolve().parents[1]
    methodology = (
        root / "docs" / "metric_methodology.md"
    ).read_text(encoding="utf-8")

    assert "10,000 × Σ(pᵢ²)" in methodology
    assert "H = -Σ(pᵢ × ln pᵢ)" in methodology
    assert "exp(H)" in methodology


def test_legacy_metrics_are_explicitly_retired_in_dashboard():
    assert "earlier Diversity Score and custom Content Variety Index are retired" in SRC
