"""
Centralized Plotly Chart Styling Configuration
Light/creamy backgrounds with dark text for readability
"""

def apply_dark_theme(fig):
    """
    Apply light/creamy background with dark text.
    """
    # Update main layout with creamy/white background
    fig.update_layout(
        plot_bgcolor="#FAF9F6",  # Creamy white
        paper_bgcolor="#FAF9F6",  # Creamy white
        font=dict(color="#1F2937", size=12, family="Inter, sans-serif"),
        title_font=dict(color="#111827", size=16, family="Inter, sans-serif"),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_color="#1F2937"
        ),
        legend=dict(
            font=dict(color="#1F2937", size=11),
            bgcolor="rgba(255,255,255,0.9)"
        )
    )
    
    # Force ALL axes to have dark text on light background
    fig.update_xaxes(
        gridcolor="rgba(0,0,0,0.1)",
        zerolinecolor="rgba(0,0,0,0.2)",
        color="#1F2937",
        tickfont=dict(color="#1F2937", size=11),
        title_font=dict(color="#111827", size=12)
    )
    
    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.1)",
        zerolinecolor="rgba(0,0,0,0.2)",
        color="#1F2937",
        tickfont=dict(color="#1F2937", size=11),
        title_font=dict(color="#111827", size=12)
    )
    
    # Force all traces to have dark text if they have text
    for trace in fig.data:
        if hasattr(trace, 'textfont'):
            trace.textfont = dict(color="#1F2937")
    
    return fig
