
import pandas as pd
import plotly.graph_objects as go

def calculate(benchmark_series, tickers_df, window=15):
    """
    Calculate Relative Rotation Graph (RRG) metrics:
      - RS ratio: ticker / benchmark
      - Normalized around ~100
      - 5-day % change => momentum ~101
    """
    rs = tickers_df.div(benchmark_series, axis=0)
    rs_mean = rs.rolling(window).mean()
    rs_std = rs.rolling(window).std(ddof=0)
    rs_normalized = 100 + ((rs - rs_mean) / rs_std)

    roc = rs_normalized.pct_change(periods=5) * 100
    rs_momentum = 101 + ((roc - roc.rolling(window).mean()) / roc.rolling(window).std(ddof=0))
    return rs_normalized, rs_momentum

def build_frames(rs_data, rsm_data, tail_points, total_frames):
    """
    Generates frames for animation with:
      - Tail points shown as circles
      - The last point as an arrow indicating movement direction
    """
    frames = []
    slider_steps = []
    tickers_list = rs_data.columns

    if len(rs_data) < 2:
        key = "SingleFrame"
        single_frame = {"data": [], "name": key}
        for t in tickers_list:
            x, y = rs_data[t], rsm_data[t]
            txt = [None] * (len(x) - 1) + [t]
            single_frame["data"].append(
                go.Scatter(
                    x=x, y=y,
                    mode="lines+markers+text",
                    name=t,
                    text=txt,
                    textposition="middle right",
                    cliponaxis=False,
                    marker={"symbol": ["triangle-up"], "size": [14], "opacity": 1}
                )
            )
        frames.append(single_frame)
        slider_steps.append({"args": [[key]], "label": key, "method": "animate"})
        return frames, slider_steps

    n = tail_points
    for i in range(total_frames, -1, -1):
        start = len(rs_data) - n - i
        end = start + n
        if start < 0:
            start = 0
        if end > len(rs_data):
            end = len(rs_data)
        if (end - start) < 1:
            continue  # Skip frames with no data

        start_date = rs_data.index[start].strftime("%Y-%m-%d")
        end_date = rs_data.index[end - 1].strftime("%Y-%m-%d")
        key = f"{start_date} - {end_date}"

        frame_data = {"data": [], "name": key}
        for t in tickers_list:
            x = rs_data[t][start:end]
            y = rsm_data[t][start:end]
            txt = [None] * (len(x) - 1) + [t]  # Label only last point

            if len(x) > 1:
                dx = x.iloc[-1] - x.iloc[-2]  # Change in x
                dy = y.iloc[-1] - y.iloc[-2]  # Change in y

                if abs(dx) > abs(dy):  # If movement is mostly horizontal
                    arrow_symbol = "triangle-right" if dx > 0 else "triangle-left"
                else:  # If movement is mostly vertical
                    arrow_symbol = "triangle-up" if dy > 0 else "triangle-down"
            else:
                arrow_symbol = "triangle-up"  # Default to up if only one point

            frame_data["data"].append(
                go.Scatter(
                    x=x, y=y,
                    mode="lines+markers+text",
                    name=t,
                    text=txt,
                    textposition="middle right",
                    cliponaxis=False,
                    marker={
                        "symbol": ["circle"] * (len(x) - 1) + [arrow_symbol],
                        "size": [8] * (len(x) - 1) + [14],
                        "opacity": 1
                    }
                )
            )
        frames.append(frame_data)
        slider_steps.append({
            "args": [[key], {
                "frame": {"duration": 0, "redraw": True},
                "mode": "immediate",
                "transition": {"duration": 0}
            }],
            "label": key,
            "method": "animate"
        })

    return frames, slider_steps


def plot(rs_input, rsm_input, tail=3, frame=10):
    """
    RRG with:
      - Frequency dropdown (Daily, Weekly, Monthly) updates time slider dynamically
      - Time slider remains static in position but updates time range
      - Tail slider remains fixed
      - Play/Pause functionality
      - Ticker labels now move with Monthly and Daily (like Weekly)
    """
    if isinstance(rs_input, dict) and isinstance(rsm_input, dict):
        freq_rs = rs_input
        freq_rsm = rsm_input
    else:
        raise ValueError("Please pass freq_rs/freq_rsm as dictionaries.")

    freq_frames = {}
    time_sliders = {}
    for freq_key in freq_rs:
        rs_data = freq_rs[freq_key]
        rsm_data = freq_rsm[freq_key]
        fdata, fsteps = build_frames(rs_data, rsm_data, tail, frame)

        freq_frames[freq_key] = (fdata, fsteps)
        # Time slider now dynamically updates based on selected frequency
        time_sliders[freq_key] = {
            "active": len(fsteps) - 1 if fsteps else 0,
            "steps": fsteps,
            "currentvalue": {"prefix": "Time: "},
            "x": 0.1, "y": 1.2, "len": 0.9,
            "xanchor": "left", "yanchor": "bottom"
        }


    default_freq = "Daily"
    default_frames, default_steps = freq_frames[default_freq]
    initial_data = default_frames[-1]["data"] if default_frames else []
    initial_frames = default_frames

    # Tail Slider (Remains Static)
    tail_slider = {
        "active": (tail - 1) if 1 <= tail <= 10 else 2,
        "currentvalue": {"prefix": "Tail: "},
        "x": 0.1, "y": 0.01, "len": 0.9,
        "xanchor": "left", "yanchor": "top",
        "steps": [
            {"method": "update", "label": str(tval), "args": [{"frames": freq_frames[default_freq][0], "data": freq_frames[default_freq][0][-1]["data"]}]} for tval in range(1, 11)
        ]
    }

    # Quadrant Shapes (Restored)
    shapes = [
        dict(type="rect", x0=94, y0=100, x1=100, y1=106, fillcolor="rgba(0,0,255,0.2)", line_width=0),
        dict(type="rect", x0=100, y0=100, x1=106, y1=106, fillcolor="rgba(0,255,0,0.2)", line_width=0),
        dict(type="rect", x0=94, y0=94, x1=100, y1=100, fillcolor="rgba(255,0,0,0.2)", line_width=0),
        dict(type="rect", x0=100, y0=94, x1=106, y1=100, fillcolor="rgba(255,255,0,0.2)", line_width=0),
        dict(type="line", x0=100, y0=94, x1=100, y1=106, line=dict(color="black", width=1, dash="dash")),
        dict(type="line", x0=94, y0=100, x1=106, y1=100, line=dict(color="black", width=1, dash="dash"))
    ]

    # Annotations (Restored)
    annotations = [
        dict(x=97, y=105, text="Improving", showarrow=True, arrowhead=2, ax=0, ay=-10, font=dict(size=14, color="blue")),
        dict(x=103, y=105, text="Leading", showarrow=True, arrowhead=2, ax=0, ay=-10, font=dict(size=14, color="green")),
        dict(x=97, y=95, text="Lagging", showarrow=True, arrowhead=2, ax=0, ay=10, font=dict(size=14, color="red")),
        dict(x=103, y=95, text="Weakening", showarrow=True, arrowhead=2, ax=0, ay=10, font=dict(size=14, color="orange"))
    ]

    # Construct Figure Dictionary (Ensure Shapes & Annotations are Included)
    fig_dict = {
        "data": initial_data,
        "layout": {
            "title": "RRG",
            "autosize": True,
            "margin": {"l": 40, "r": 40, "t": 100, "b": 150},
            "xaxis": {"range": [94, 106], "title": "JdK RS Ratio"},
            "yaxis": {"range": [94, 106], "title": "JdK RS Momentum"},
            "shapes": shapes,  # Ensure Shapes Persist
            "annotations": annotations,  # Ensure Annotations Persist
            "sliders": [tail_slider, time_sliders[default_freq]],
            "updatemenus": [
                {
                    "buttons": [{"label": freq_key, "method": "update", "args": [
                        {"frames": freq_frames[freq_key][0], "data": freq_frames[freq_key][0][-1]["data"]},
                        {"sliders": [tail_slider, time_sliders[freq_key]]}
                    ]} for freq_key in freq_rs.keys()],
                    "direction": "down",
                    "showactive": True,
                    "x": 0.8, "xanchor": "right",
                    "y": 1.6, "yanchor": "top"
                },
                                {
                    "buttons": [
                        {
                            "label": "Play",
                            "method": "animate",
                            "args": [
                                None,
                                {
                                    "frame": {"duration": 500, "redraw": True},
                                    "mode": "next",
                                    "fromcurrent": True,
                                    "transition": {"duration": 500}
                                }
                            ]
                        },
                        {
                            "label": "Pause",
                            "method": "animate",
                            "args": [
                                [None],
                                {
                                    "mode": "immediate",
                                    "frame": {"duration": 0, "redraw": False},
                                    "transition": {"duration": 0}
                                }
                            ]
                        }
                    ],
                    "direction": "left",
                    "showactive": True,
                    "x": 0.1,
                    "xanchor": "center",
                    "y": 1.6,
                    "yanchor": "top"
                }

            ]
        },
        "frames": initial_frames
    }

    # Build and show the figure
    fig = go.Figure(fig_dict)
    fig.show(config={"responsive": True})
    