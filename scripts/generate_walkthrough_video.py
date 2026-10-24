"""
WindLens UK - Automated Walkthrough Video Generator
Renders a 1920x1080 MP4 video timed for voiceover demonstration (4m 45s).
Adds glowing focal boxes, timecodes, focus targets, and teleprompter scripts.
"""

import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "docs", "windlens-demo-walkthrough.mp4")

# Resolution & Encoding
WIDTH = 1920
HEIGHT = 1080
FPS = 2  # 2 frames per second gives smooth second-by-second timer and rapid rendering

# Font configuration
FONT_PATH = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/segoeuib.ttf"
FONT_MONO_PATH = "C:/Windows/Fonts/consola.ttf"

font_title = ImageFont.truetype(FONT_BOLD_PATH, 28)
font_focus = ImageFont.truetype(FONT_BOLD_PATH, 22)
font_script = ImageFont.truetype(FONT_PATH, 24)
font_timer = ImageFont.truetype(FONT_MONO_PATH, 26)
font_badge = ImageFont.truetype(FONT_BOLD_PATH, 16)
font_pill = ImageFont.truetype(FONT_BOLD_PATH, 18)

# Walkthrough timeline sections
SECTIONS = [
    {
        "id": 1,
        "title": "SECTION 1: INTRODUCTION & UK POWER TRADING PROBLEM",
        "image": "01_executive_overview.png",
        "duration": 30,
        "focus_label": "WindLens UK Platform & National Grid Imbalance Risk",
        "focus_box": (30, 15, 450, 70),  # Logo & branding
        "script": "Hello. Welcome to WindLens UK, an energy analytics platform engineered for UK day-ahead power trading desks and renewable portfolio managers. In Great Britain, trading desks must commit generation schedules before the Day-Ahead Auction gate closure at 11:00 AM on the day prior to delivery. With over 28 gigawatts of wind, forecast uncertainty directly drives imbalance exposure and cashout risk."
    },
    {
        "id": 2,
        "title": "SECTION 2: GATE CUTOFF & ELEXON BMRS PROVENANCE",
        "image": "01_executive_overview.png",
        "duration": 45,
        "focus_label": "Decision Cutoff (11:00 D-1) & Multi-Run WINDFOR Ingestion",
        "focus_box": (1320, 15, 1890, 65),  # Cutoff badge and date picker
        "script": "Our reporting scope evaluates all 31 days of January 2026—1,488 half-hour settlement periods. At the top of the interface, notice the decision cutoff filter set to 11:00 D-1 Europe/London. All calculations strictly respect UK Local Time (GMT/BST). WindLens UK integrates two core Elexon BMRS streams: FUELHH for actual metered wind outturn, and WINDFOR for multi-run forecast publications."
    },
    {
        "id": 3,
        "title": "SECTION 3: FORECAST EXPLORER — POINT-IN-TIME INTEGRITY",
        "image": "02_forecast_explorer.png",
        "duration": 60,
        "focus_label": "Settlement Period 24 Evolution & Green Star Gate-Selected Forecast",
        "focus_box": (45, 130, 1875, 750),  # Revision chart & gate marker
        "script": "In the Forecast Explorer for Settlement Period 24 (Midday 11:30–12:00): Elexon publishes multiple WINDFOR forecast runs leading up to delivery. Other dashboards mistakenly evaluate performance against the latest forecast published immediately before delivery. That is hindsight analysis. Here, at 11:00 D-1, the latest eligible forecast was 8,458 MW—marked with our green star. Later runs updated this, but were unavailable at gate closure. WindLens isolates post-cutoff runs, guaranteeing zero lookahead bias."
    },
    {
        "id": 4,
        "title": "SECTION 4: ACCURACY METRICS & ERROR DISTRIBUTION",
        "image": "03_accuracy_analysis.png",
        "duration": 60,
        "focus_label": "Statistical Verification: MAE 837 MW, RMSE 1,079 MW, Bias +204 MW, MAPE 6.6%",
        "focus_box": (45, 130, 1875, 520),  # KPI cards & accuracy trend
        "script": "In Accuracy Analysis, we track error volatility across all 31 days of January. Our Core Analytics module computes four transparent metrics: MAE (837 MW), RMSE (1,079 MW), and Signed Bias (+204 MW). Following UK market standard convention—Forecast minus Actual—positive bias indicates over-forecasting. Crucially, periods where actual wind was 0 MW are strictly isolated from MAPE, eliminating mathematical division-by-zero distortion."
    },
    {
        "id": 5,
        "title": "SECTION 5: 48-PERIOD SETTLEMENT LEDGER & CSV EXPORT",
        "image": "04_settlement_ledger.png",
        "duration": 30,
        "focus_label": "Half-Hourly Audit Ledger & One-Click CSV Export (1,488 Records)",
        "focus_box": (45, 130, 1875, 850),  # Ledger table and export button
        "script": "In the Settlement Ledger, operations and trading desks have a complete 48-period audit trail with verified UK local timestamps, settlement period IDs, outturn, and gate-selected forecasts. With one click, traders can download the full CSV export containing all 1,488 rows for downstream trade reconciliation and settlement risk analysis."
    },
    {
        "id": 6,
        "title": "SECTION 6: RESIDUAL DEMAND PROCUREMENT SIMULATOR",
        "image": "05_scenario_simulator.png",
        "duration": 40,
        "focus_label": "Dispatchable Thermal Need (20,802 MW) vs Outturn (21,069 MW)",
        "focus_box": (45, 130, 1875, 820),  # Sliders & balancing cards
        "script": "Finally, in the Scenario Simulator, we translate wind uncertainty into commercial procurement requirements. With 38,000 MW national demand and 8,000 MW non-wind baseload, WindLens calculates the Planned Thermal Need (20,802 MW) versus Actual Outturn (21,069 MW). This reveals the exact dispatchable flexibility that gas CCGTs, peakers, and battery storage had to provide in the balancing mechanism."
    },
    {
        "id": 7,
        "title": "SECTION 7: ARCHITECTURE & DEPLOYMENT HANDOVER",
        "image": "01_executive_overview.png",
        "duration": 20,
        "focus_label": "Production Summary: Docker Containerized, 45 Tests Passing, Elexon Ready",
        "focus_box": (45, 880, 1875, 1020),  # Bottom architecture / disclaimer
        "script": "To summarize: WindLens UK delivers complete point-in-time integrity with zero lookahead bias, transparent error metrics, and commercial dispatch modeling. The application is Docker containerized, verified with 45 automated pytest suites, and ready for deployment into your trading desk infrastructure. Thank you."
    }
]

TOTAL_DURATION = sum(s["duration"] for s in SECTIONS)  # 285 seconds (04:45)

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def render_frame(sec_elapsed, section, section_sec_elapsed):
    # Load base image
    img_path = os.path.join(SCREENSHOTS_DIR, section["image"])
    frame = Image.open(img_path).convert("RGBA")
    
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 1. Top Global Progress Bar (Y: 0 to 6)
    progress_pct = sec_elapsed / TOTAL_DURATION
    draw.rectangle([0, 0, WIDTH, 6], fill=(30, 41, 59, 255))
    draw.rectangle([0, 0, int(WIDTH * progress_pct), 6], fill=(20, 184, 166, 255))
    
    # 2. Glowing Focus Box around key UI area (if defined)
    box = section["focus_box"]
    if box:
        x1, y1, x2, y2 = box
        # Pulsing effect based on second
        pulse = (sec_elapsed % 2 == 0)
        border_col = (45, 212, 191, 230) if pulse else (20, 184, 166, 170)
        bg_col = (13, 148, 136, 35) if pulse else (13, 148, 136, 15)
        
        # Subtle highlight background
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=bg_col, outline=border_col, width=3)
        
        # Focus pill label
        pill_text = "FOCUS HERE"
        pill_w = 120
        pill_h = 28
        pill_x = min(x1 + 10, WIDTH - pill_w - 20)
        pill_y = max(y1 - 32, 12)
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=6, fill=(13, 148, 136, 240), outline=(45, 212, 191, 255), width=1)
        draw.text((pill_x + 12, pill_y + 4), pill_text, fill=(2, 6, 23, 255), font=font_badge)

    # 3. Lower-Third Teleprompter HUD Card
    hud_h = 210
    hud_y = HEIGHT - hud_h - 15
    hud_x1 = 20
    hud_x2 = WIDTH - 20
    
    # HUD glassmorphism card
    draw.rounded_rectangle([hud_x1, hud_y, hud_x2, hud_y + hud_h], radius=12, fill=(2, 6, 23, 242), outline=(30, 41, 59, 255), width=2)
    # Teal accent top strip
    draw.rounded_rectangle([hud_x1, hud_y, hud_x2, hud_y + 4], radius=2, fill=(20, 184, 166, 255))
    
    # Header: Timer Badge + Title + Focus Target
    time_badge = f"{format_time(sec_elapsed)} / {format_time(TOTAL_DURATION)}"
    time_box_w = 265
    draw.rounded_rectangle([hud_x1 + 16, hud_y + 14, hud_x1 + 16 + time_box_w, hud_y + 48], radius=6, fill=(15, 23, 42, 255), outline=(45, 212, 191, 200), width=1)
    draw.text((hud_x1 + 28, hud_y + 18), f"REC {time_badge}", fill=(45, 212, 191, 255), font=font_timer)
    
    # Section Title (offset to right of timer badge)
    draw.text((hud_x1 + 295, hud_y + 18), section["title"], fill=(248, 250, 252, 255), font=font_title)
    
    # Focus description badge
    focus_text = f"LOOK AT: {section['focus_label']}"
    draw.text((hud_x1 + 20, hud_y + 56), focus_text, fill=(251, 191, 36, 255), font=font_focus)
    
    # Script Box / Teleprompter
    wrapped_lines = textwrap.wrap(section["script"], width=130)
    script_y = hud_y + 92
    
    # Label pill
    pill_label_w = 210
    draw.rounded_rectangle([hud_x1 + 20, script_y, hud_x1 + 20 + pill_label_w, script_y + 24], radius=4, fill=(13, 148, 136, 220))
    draw.text((hud_x1 + 28, script_y + 3), "SPEAK SCRIPT ALOUD:", fill=(2, 6, 23, 255), font=font_badge)
    
    # Show first 3 lines of script with quotes
    line_y = script_y + 32
    for line in wrapped_lines[:3]:
        draw.text((hud_x1 + 20, line_y), line, fill=(241, 245, 249, 255), font=font_script)
        line_y += 30

    # Composite overlay
    frame = Image.alpha_composite(frame, overlay).convert("RGB")
    return frame

def main():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"FFmpeg binary: {ffmpeg_exe}")
    print(f"Generating video to: {OUTPUT_VIDEO}")
    print(f"Total video duration: {TOTAL_DURATION}s ({format_time(TOTAL_DURATION)})")
    
    # Setup FFmpeg pipe
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",  # Video from stdin pipe
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",  # Clean silent audio track
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    total_frames = int(TOTAL_DURATION * FPS)
    frame_idx = 0
    current_sec = 0
    
    for section in SECTIONS:
        sec_duration = section["duration"]
        frames_in_section = int(sec_duration * FPS)
        
        print(f"Rendering {section['title']} ({sec_duration}s = {frames_in_section} frames)...")
        
        for sf in range(frames_in_section):
            sec_elapsed = frame_idx / FPS
            sec_in_section = sf / FPS
            
            frame_img = render_frame(sec_elapsed, section, sec_in_section)
            proc.stdin.write(frame_img.tobytes())
            frame_idx += 1
            
    proc.stdin.close()
    proc.wait()
    
    if proc.returncode == 0:
        file_size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
        print(f"SUCCESS: Generated {OUTPUT_VIDEO} ({file_size_mb:.2f} MB)")
    else:
        print(f"ERROR: FFmpeg failed with return code {proc.returncode}")

if __name__ == "__main__":
    main()
