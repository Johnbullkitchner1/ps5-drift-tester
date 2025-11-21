# drift_gui_pygame.py
import math
import sys
import os
import pygame
from pygame import gfxdraw

# Try optional pydualsense (may not work on macOS/Bluetooth)
try:
    from pydualsense import pydualsense
    DUALSENSE_AVAILABLE = True
except Exception:
    DUALSENSE_AVAILABLE = False

# --- Config ---
IMG_FILENAME = "controller_top.png"   
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 480
DEADZONE = 0.06   # default deadzone for drift detection
STICK_RADIUS = 12

# Approximate positions for overlay highlights relative to image size (fractions: (x_frac, y_frac))
# You may tweak these if your controller image differs
DEFAULT_POS = {
    "left_stick": (0.30, 0.58),
    "right_stick": (0.70, 0.58),
    "dpad": (0.10, 0.58),
    "button_cross": (0.85, 0.50),   # X
    "button_circle": (0.92, 0.41),  # O
    "button_square": (0.78, 0.41),  # []
    "button_triangle": (0.85, 0.33),# △
    "touchpad": (0.50, 0.35),
    "l1": (0.18, 0.12),
    "r1": (0.82, 0.12),
    "l2_bar": (0.14, 0.20),
    "r2_bar": (0.86, 0.20),
    "ps_button": (0.50, 0.40),
}

# --- Helper functions ---
def draw_text(surface, text, x, y, size=18, color=(255,255,255)):
    font = pygame.font.SysFont("Arial", size)
    surf = font.render(text, True, color)
    surface.blit(surf, (x,y))

def scaled_pos(img_rect, frac):
    return (img_rect.left + int(img_rect.width * frac[0]),
            img_rect.top  + int(img_rect.height * frac[1]))

# --- Pygame Init ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("PS5 Drift & Diagnostic (Pygame)")
clock = pygame.time.Clock()

# Load controller image
if not os.path.exists(IMG_FILENAME):
    print(f"ERROR: put a controller image named '{IMG_FILENAME}' in the folder.")
    pygame.quit()
    sys.exit(1)

img = pygame.image.load(IMG_FILENAME).convert_alpha()
# Scale image to fit half the window height with margin
scale_factor = (WINDOW_HEIGHT - 40) / img.get_height()
img_w = int(img.get_width() * scale_factor)
img_h = int(img.get_height() * scale_factor)
img = pygame.transform.smoothscale(img, (img_w, img_h))
img_rect = img.get_rect()
img_rect.left = 20
img_rect.centery = WINDOW_HEIGHT // 2

# Right area for info
info_x = img_rect.right + 20

# Joystick init
pygame.joystick.init()
joystick = None
def find_joystick():
    global joystick
    if pygame.joystick.get_count() == 0:
        joystick = None
        return False
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return True

found = find_joystick()
if not found:
    print("No joystick found. Make sure DualSense is connected (Bluetooth or USB).")
else:
    print("Joystick found:", joystick.get_name())

# Print mapping info to terminal
def print_mapping_info():
    if not joystick:
        return
    print("----- Controller mapping info -----")
    print("Axes (count):", joystick.get_numaxes())
    for i in range(joystick.get_numaxes()):
        print(" axis", i)
    print("Buttons (count):", joystick.get_numbuttons())
    for i in range(joystick.get_numbuttons()):
        print(" button", i)
    print("Hats (d-pad) count:", joystick.get_numhats())
    for i in range(joystick.get_numhats()):
        print(" hat", i)
    print("-----------------------------------")

if joystick:
    print_mapping_info()

# Optional DualSense control (vibration/adaptive triggers)
ds = None
if DUALSENSE_AVAILABLE:
    try:
        ds = pydualsense.DualSense()  # may need USB and permissions
        print("pydualsense initialized")
    except Exception as e:
        ds = None
        print("pydualsense import OK but failed to initialize:", e)

# Main loop variables
deadzone = DEADZONE
show_debug = True

# Basic mapping guesses (these are common but may vary)
# We'll read axes/buttons and show them; use console info if mapping is off.
# Common mapping on many systems:
AXIS_LX = 0
AXIS_LY = 1
AXIS_RX = 2
AXIS_RY = 3
AXIS_L2 = 4  # sometimes triggers are axes 4,5 or buttons
AXIS_R2 = 5

# Button estimates (these indexes may vary):
BTN_X = 0
BTN_CIRCLE = 1
BTN_SQUARE = 2
BTN_TRIANGLE = 3
BTN_L1 = 4
BTN_R1 = 5
BTN_L2 = 6
BTN_R2 = 7
BTN_SHARE = 8
BTN_OPTIONS = 9
BTN_L_STICK = 10
BTN_R_STICK = 11
BTN_PS = 12
BTN_TOUCH = 13

# Utility to draw translucent circle
def draw_glow(surface, pos, r, color=(255,0,0,120)):
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.gfxdraw.filled_circle(s, r, r, r, color)
    surface.blit(s, (pos[0]-r, pos[1]-r))

# Main loop
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        if ev.type == pygame.JOYDEVICEADDED or ev.type == pygame.JOYDEVICEREMOVED:
            find_joystick()
            if joystick:
                print_mapping_info()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_d:
                show_debug = not show_debug
            if ev.key == pygame.K_UP:
                deadzone = max(0.0, deadzone - 0.01)
            if ev.key == pygame.K_DOWN:
                deadzone = min(0.5, deadzone + 0.01)
            # Try vibration test (if pydualsense available)
            if ev.key == pygame.K_v and ds:
                try:
                    ds.set_rumble(0.8, 0.8)  # left, right motors (if supported)
                    pygame.time.delay(300)
                    ds.set_rumble(0.0, 0.0)
                except Exception as e:
                    print("Vibration test failed:", e)

    screen.fill((28,28,28))
    # Draw controller image
    screen.blit(img, img_rect)

    # Default indicator positions (scaled to img_rect)
    pos = {k: scaled_pos(img_rect, v) for k,v in DEFAULT_POS.items()}

    # If no joystick, tell the user
    if not joystick:
        draw_text(screen, "No controller detected. Connect via Bluetooth or USB.", info_x, 20, size=20, color=(255,200,50))
    else:
        # Poll joystick values
        pygame.event.pump()
        # axes
        axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())] if joystick else []
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())] if joystick else []
        hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())] if joystick else []

        # Read left and right sticks (fallbacks)
        lx = axes[AXIS_LX] if len(axes) > AXIS_LX else 0.0
        ly = axes[AXIS_LY] if len(axes) > AXIS_LY else 0.0
        rx = axes[AXIS_RX] if len(axes) > AXIS_RX else 0.0
        ry = axes[AXIS_RY] if len(axes) > AXIS_RY else 0.0

        # Some controllers invert Y; you might flip sign if it feels reversed.
        # Compute stick screen positions
        l_center = pos["left_stick"]
        r_center = pos["right_stick"]
        # scale stick travel to 40 px radius
        travel = int(min(img_rect.width, img_rect.height) * 0.06)
        l_dot = (int(l_center[0] + lx * travel), int(l_center[1] + ly * travel))
        r_dot = (int(r_center[0] + rx * travel), int(r_center[1] + ry * travel))

        # Draw stick bases
        pygame.gfxdraw.filled_circle(screen, l_center[0], l_center[1], STICK_RADIUS+8, (40,40,40))
        pygame.gfxdraw.filled_circle(screen, r_center[0], r_center[1], STICK_RADIUS+8, (40,40,40))
        # Draw live dots
        pygame.gfxdraw.filled_circle(screen, l_dot[0], l_dot[1], STICK_RADIUS, (0,200,0))
        pygame.gfxdraw.filled_circle(screen, r_dot[0], r_dot[1], STICK_RADIUS, (0,200,0))

        # Drift detection
        drifting_left = abs(lx) > deadzone or abs(ly) > deadzone
        drifting_right = abs(rx) > deadzone or abs(ry) > deadzone
        if drifting_left:
            draw_glow(screen, l_center, 36, (255, 80, 80, 100))
        if drifting_right:
            draw_glow(screen, r_center, 36, (255, 80, 80, 100))

        # Buttons highlighting
        def highlight_if_button(index, name):
            if len(buttons) > index and buttons[index]:
                draw_glow(screen, pos[name], 24, (80,200,255,120))

        # Use safe index checking; these indexes may need adjustment for your mapping:
        highlight_if_button(BTN_X, "button_cross")
        highlight_if_button(BTN_CIRCLE, "button_circle")
        highlight_if_button(BTN_SQUARE, "button_square")
        highlight_if_button(BTN_TRIANGLE, "button_triangle")
        highlight_if_button(BTN_TOUCH, "touchpad")
        # PS button (if mapped)
        if len(buttons) > BTN_PS and buttons[BTN_PS]:
            draw_glow(screen, pos["ps_button"], 20, (255,200,120,140))

        # D-pad from hats
        if len(hats) > 0:
            hatx, haty = hats[0]
            if hatx != 0 or haty != 0:
                draw_glow(screen, pos["dpad"], 20, (180,255,120,120))

        # Triggers: try reading axis values if available
        l2_val = axes[AXIS_L2] if len(axes) > AXIS_L2 else (buttons[BTN_L2] if len(buttons)>BTN_L2 else 0.0)
        r2_val = axes[AXIS_R2] if len(axes) > AXIS_R2 else (buttons[BTN_R2] if len(buttons)>BTN_R2 else 0.0)

        # Normalize trigger values to 0..1 depending on how they are reported (some report -1..1)
        def norm_trigger(v):
            if v >= -1.0 and v <= 1.0:
                if v < -0.2:  # treat -1..1 range
                    return (v + 1.0) / 2.0
                else:
                    return v  # already 0..1
            return 0.0

        l2n = norm_trigger(l2_val)
        r2n = norm_trigger(r2_val)

        # draw trigger bars
        bar_w = 140
        bar_h = 18
        lxbar = (info_x + 10, 60)
        rxbar = (info_x + 10, 100)
        pygame.draw.rect(screen, (50,50,50), (lxbar[0], lxbar[1], bar_w, bar_h))
        pygame.draw.rect(screen, (50,50,50), (rxbar[0], rxbar[1], bar_w, bar_h))
        pygame.draw.rect(screen, (80,180,250), (lxbar[0], lxbar[1], int(bar_w * l2n), bar_h))
        pygame.draw.rect(screen, (80,180,250), (rxbar[0], rxbar[1], int(bar_w * r2n), bar_h))
        draw_text(screen, f"L2: {l2n:.2f}", lxbar[0] + bar_w + 8, lxbar[1]-2, size=16)
        draw_text(screen, f"R2: {r2n:.2f}", rxbar[0] + bar_w + 8, rxbar[1]-2, size=16)

        # Button states text
        y = 150
        draw_text(screen, f"Left stick X/Y: {lx:.3f}, {ly:.3f}", info_x, y); y += 24
        draw_text(screen, f"Right stick X/Y: {rx:.3f}, {ry:.3f}", info_x, y); y += 24
        draw_text(screen, f"Deadzone: {deadzone:.2f} (UP/DOWN to adjust)", info_x, y); y += 24
        draw_text(screen, f"Press V to try vibration (if supported)", info_x, y); y += 24
        draw_text(screen, "Toggle debug mapping: D", info_x, y); y += 20

        if show_debug:
            draw_text(screen, f"Axes: {len(axes)} Buttons: {len(buttons)} Hats: {len(hats)}", info_x, y); y += 22
            # Show some raw indices for quick mapping checks
            for i, a in enumerate(axes):
                draw_text(screen, f"axis[{i}] = {a:.3f}", info_x, y); y += 18
            for i, b in enumerate(buttons[:16]):
                draw_text(screen, f"btn[{i}] = {b}", info_x, y); y += 18
            for i, h in enumerate(hats):
                draw_text(screen, f"hat[{i}] = {h}", info_x, y); y += 18

    # Draw small legend
    draw_text(screen, "Legend: red glow = drift detected, blue glow = pressed", 20, WINDOW_HEIGHT - 28, size=14, color=(200,200,200))

    pygame.display.flip()
    clock.tick(60)

# Cleanup
if ds:
    try:
        ds.set_rumble(0,0)
        ds.cleanup()
    except Exception:
        pass
pygame.quit()
