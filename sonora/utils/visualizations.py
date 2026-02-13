
import plotly.graph_objects as go
import numpy as np

def create_multi_track_timeline(segments, emotion_tokens=None):
    """
    Creates a DAW-style multi-track timeline using Plotly.
    """
    if not segments:
        return go.Figure()

    fig = go.Figure()
    
    # Tracks: 0: Source, 1: BGM, 2: Dub
    track_names = ["SOURCE VOCALS (JP)", "BGM/SFX STEM", "NEW DUB (EN)"]
    colors = ["#95a5a6", "#16a085", "#2980b9"]
    
    for track_idx, name in enumerate(track_names):
        # Add a placeholder bar for the whole duration
        total_duration = segments[-1][-1]['end']
        
        # Add actual segments for the Dub track
        if track_idx == 2:
            for idx, seg in enumerate(segments):
                start = seg[0]['start']
                end = seg[-1]['end']
                token = emotion_tokens[idx] if emotion_tokens else "neutral"
                
                # Color based on emotion
                emotion_colors = {
                    "happy": "#f1c40f", "sad": "#3498db", 
                    "angry": "#e74c3c", "excited": "#e67e22"
                }
                color = emotion_colors.get(token, colors[track_idx])
                
                fig.add_trace(go.Bar(
                    x=[end - start],
                    y=[name],
                    base=start,
                    orientation='h',
                    marker=dict(color=color, line=dict(color='white', width=1)),
                    hoverinfo='text',
                    text=f"Seg {idx+1}: {token.upper()}",
                    showlegend=False
                ))
        else:
            # Just show a solid bar for background tracks for now
            fig.add_trace(go.Bar(
                x=[total_duration],
                y=[name],
                base=0,
                orientation='h',
                marker=dict(color=colors[track_idx], opacity=0.6),
                showlegend=False
            ))

    fig.update_layout(
        barmode='stack',
        height=300,
        margin=dict(l=10, r=10, t=30, b=30),
        xaxis=dict(title="Time (seconds)", gridcolor="#34495e"),
        yaxis=dict(gridcolor="#34495e"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        yaxis_autorange='reversed'
    )
    
    return fig

def create_emotion_heatmap(intensities, times):
    """
    Creates a heatmap visualization for emotion intensity/prosody.
    """
    fig = go.Figure(data=go.Heatmap(
        z=[intensities],
        x=times,
        colorscale='Viridis',
        showscale=False
    ))
    
    fig.update_layout(
        height=100,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
