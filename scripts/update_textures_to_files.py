#!/usr/bin/env python3
"""
1. Generate background image for game menu
2. Update HTML to load all textures from PNG files instead of procedural generation
3. Copy files to git repo and prepare for push
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter

GAME_DIR = "/home/z/my-project/download"
ASSETS_DIR = os.path.join(GAME_DIR, "fps-game-assets")
HTML_SRC = os.path.join(GAME_DIR, "fps-game.html")

# ============================================================
# PART 1: Create Background Image
# ============================================================
print("=== Creating background image ===")

w, h = 1920, 1080
img = Image.new('RGB', (w, h), (10, 14, 26))
d = ImageDraw.Draw(img)

# Dark gradient base
for y in range(h):
    t = y / h
    r = int(10 + t * 15)
    g = int(14 + t * 20)
    b = int(26 + t * 40)
    d.line([(0, y), (w, y)], fill=(r, g, b))

# Grid lines (like a sci-fi HUD)
for x in range(0, w, 80):
    alpha = 15 + int(10 * math.sin(x * 0.01))
    d.line([(x, 0), (x, h)], fill=(20 + alpha, 30 + alpha, 50 + alpha), width=1)
for y in range(0, h, 80):
    alpha = 15 + int(10 * math.sin(y * 0.01))
    d.line([(0, y), (w, y)], fill=(20 + alpha, 30 + alpha, 50 + alpha), width=1)

# Glowing crosshair in center
cx, cy = w // 2, h // 2
for i in range(200, 0, -1):
    alpha = int(30 * (1 - i / 200))
    color = (alpha, alpha + 10, alpha + 30)
    d.ellipse([cx - i, cy - i, cx + i, cy + i], outline=color)

# Cross lines
d.line([(cx - 300, cy), (cx - 50, cy)], fill=(40, 80, 120), width=2)
d.line([(cx + 50, cy), (cx + 300, cy)], fill=(40, 80, 120), width=2)
d.line([(cx, cy - 300), (cx, cy - 50)], fill=(40, 80, 120), width=2)
d.line([(cx, cy + 50), (cx, cy + 300)], fill=(40, 80, 120), width=2)

# Random particles/stars
for _ in range(200):
    x = random.randint(0, w - 1)
    y = random.randint(0, h - 1)
    brightness = random.randint(30, 80)
    sz = random.choice([1, 1, 1, 2])
    d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=(brightness, brightness + 10, brightness + 30))

# Title text area glow
for i in range(100, 0, -1):
    alpha = int(8 * (1 - i / 100))
    d.rectangle([w//2 - 300, 100 - i, w//2 + 300, 100 + 80 + i], fill=(alpha, alpha + 2, alpha + 8))

# Apply slight blur for smooth look
img = img.filter(ImageFilter.GaussianBlur(radius=1))
img.save(os.path.join(ASSETS_DIR, "bg_menu.png"))
print("  bg_menu.png created (1920x1080)")

# Also create a smaller version for faster loading
img_small = img.resize((960, 540), Image.LANCZOS)
img_small.save(os.path.join(ASSETS_DIR, "bg_menu_small.jpg"), quality=85)
print("  bg_menu_small.jpg created (960x540)")

# ============================================================
# PART 2: Update HTML to use PNG texture files
# ============================================================
print("\n=== Updating HTML to load textures from PNG files ===")

with open(HTML_SRC, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# --- Change 1: Add TextureLoader and _loadTex helper after 'const tex = {};' ---
old = 'const tex = {};'
new = '''const tex = {};
// Texture loader for PNG files (offline-ready)
var _texLoader = new THREE.TextureLoader();
function _loadTex(name, rx, ry) {
  var t = _texLoader.load('fps-game-assets/' + name);
  t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping;
  if (rx) t.repeat.set(rx, ry || rx);
  return t;
}'''
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [1] Added _loadTex helper function")

# --- Change 2: Replace brick procedural texture with PNG load ---
old = """// Brick texture
tex.brick = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#7a5c3a'; ctx.fillRect(0,0,w,h);
    var bw=30, bh=14, gap=2;
    for (var r=0; r < Math.ceil(h/bh); r++) {
      var off = (r%2) * bw/2;
      for (var c=-1; c < Math.ceil(w/bw)+1; c++) {
        var v = 0.85 + Math.random()*0.3;
        var rr = Math.floor(160*v), gg = Math.floor(100*v), bb = Math.floor(65*v);
        ctx.fillStyle = 'rgb('+rr+','+gg+','+bb+')';
        ctx.fillRect(c*bw+off+gap, r*bh+gap, bw-gap*2, bh-gap*2);
      }
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.9, metalness:0.05});
})();"""
new = """// Brick texture (loaded from PNG)
tex.brick = new THREE.MeshStandardMaterial({map:_loadTex('tex_brick.png'), roughness:0.9, metalness:0.05});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [2] Brick texture -> PNG")

# --- Change 3: Sand texture ---
old = """// Sand/Plaster texture
tex.sand = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#c4a868'; ctx.fillRect(0,0,w,h);
    for (var i=0; i < 2000; i++) {
      var v = 0.8 + Math.random()*0.4;
      var rr = Math.floor(196*v), gg = Math.floor(168*v), bb = Math.floor(104*v);
      ctx.fillStyle = 'rgba('+rr+','+gg+','+bb+',0.5)';
      ctx.fillRect(Math.random()*w, Math.random()*h, 1+Math.random()*2, 1+Math.random()*2);
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.95, metalness:0.02});
})();"""
new = """// Sand/Plaster texture (loaded from PNG)
tex.sand = new THREE.MeshStandardMaterial({map:_loadTex('tex_sand.png'), roughness:0.95, metalness:0.02});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [3] Sand texture -> PNG")

# --- Change 4: Sand ground texture (with repeat) ---
old = """// Sand ground texture
tex.sandGround = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#c2a878'; ctx.fillRect(0,0,w,h);
    for (var i=0; i < 3000; i++) {
      var v = 0.85 + Math.random()*0.3;
      var rr = Math.floor(194*v), gg = Math.floor(168*v), bb = Math.floor(120*v);
      ctx.fillStyle = 'rgba('+rr+','+gg+','+bb+',0.4)';
      ctx.fillRect(Math.random()*w, Math.random()*h, Math.random()*3, Math.random()*3);
    }
  }, 128, 128);
  t.repeat.set(20,20);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.95, metalness:0.02});
})();"""
new = """// Sand ground texture (loaded from PNG, with repeat)
tex.sandGround = new THREE.MeshStandardMaterial({map:_loadTex('tex_sand_ground.png',20,20), roughness:0.95, metalness:0.02});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [4] Sand ground texture -> PNG (repeat 20x20)")

# --- Change 5: Concrete texture ---
old = """// Concrete texture
tex.concrete = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#8a8a8a'; ctx.fillRect(0,0,w,h);
    for (var i=0; i < 4000; i++) {
      var v = 0.7 + Math.random()*0.6;
      var g = Math.floor(138*v);
      ctx.fillStyle = 'rgba('+g+','+g+','+g+',0.3)';
      ctx.fillRect(Math.random()*w, Math.random()*h, 1+Math.random()*2, 1+Math.random()*2);
    }
    // Cracks
    ctx.strokeStyle = 'rgba(60,60,60,0.15)'; ctx.lineWidth = 1;
    for (var i=0; i < 5; i++) {
      ctx.beginPath(); ctx.moveTo(Math.random()*w, Math.random()*h);
      ctx.lineTo(Math.random()*w, Math.random()*h); ctx.stroke();
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.85, metalness:0.1});
})();"""
new = """// Concrete texture (loaded from PNG)
tex.concrete = new THREE.MeshStandardMaterial({map:_loadTex('tex_concrete.png'), roughness:0.85, metalness:0.1});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [5] Concrete texture -> PNG")

# --- Change 6: Metal floor texture ---
old = """// Metal floor texture
tex.metalFloor = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#667788'; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle = 'rgba(100,120,140,0.4)'; ctx.lineWidth = 1;
    for (var i=0; i <= w; i += 32) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,h); ctx.stroke(); }
    for (var i=0; i <= h; i += 32) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(w,i); ctx.stroke(); }
    // Rivets
    ctx.fillStyle = 'rgba(150,170,190,0.5)';
    for (var x=16; x < w; x+=32) for (var y=16; y < h; y+=32) {
      ctx.beginPath(); ctx.arc(x,y,2,0,Math.PI*2); ctx.fill();
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.4, metalness:0.6});
})();"""
new = """// Metal floor texture (loaded from PNG)
tex.metalFloor = new THREE.MeshStandardMaterial({map:_loadTex('tex_metal_floor.png'), roughness:0.4, metalness:0.6});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [6] Metal floor texture -> PNG")

# --- Change 7: Metal wall texture ---
old = """// Metal wall texture
tex.metalWall = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#778899'; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle = 'rgba(90,110,130,0.3)'; ctx.lineWidth = 1;
    for (var i=0; i <= w; i += 64) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,h); ctx.stroke(); }
    for (var i=0; i <= h; i += 64) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(w,i); ctx.stroke(); }
    for (var i=0; i < 800; i++) {
      var g = Math.floor(100 + Math.random()*60);
      ctx.fillStyle = 'rgba('+g+','+(g+10)+','+(g+20)+',0.15)';
      ctx.fillRect(Math.random()*w, Math.random()*h, 2+Math.random()*4, 1);
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.35, metalness:0.7});
})();"""
new = """// Metal wall texture (loaded from PNG)
tex.metalWall = new THREE.MeshStandardMaterial({map:_loadTex('tex_metal_wall.png'), roughness:0.35, metalness:0.7});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [7] Metal wall texture -> PNG")

# --- Change 8: Crate texture ---
old = """// Crate/Wood texture
tex.crate = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#8b6914'; ctx.fillRect(0,0,w,h);
    // Wood planks
    ctx.strokeStyle = 'rgba(90,50,10,0.4)'; ctx.lineWidth = 2;
    for (var i=0; i < w; i += 32) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,h); ctx.stroke(); }
    // Wood grain
    for (var i=0; i < 1500; i++) {
      var v = 0.8 + Math.random()*0.4;
      var rr = Math.floor(139*v), gg = Math.floor(105*v), bb = Math.floor(20*v);
      ctx.fillStyle = 'rgba('+rr+','+gg+','+bb+',0.3)';
      ctx.fillRect(Math.random()*w, Math.random()*h, Math.random()*8, 1);
    }
    // Cross braces
    ctx.strokeStyle = 'rgba(80,50,10,0.5)'; ctx.lineWidth = 4;
    ctx.strokeRect(8,8,w-16,h-16);
    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(w,h); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(w,0); ctx.lineTo(0,h); ctx.stroke();
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.8, metalness:0.05});
})();"""
new = """// Crate/Wood texture (loaded from PNG)
tex.crate = new THREE.MeshStandardMaterial({map:_loadTex('tex_crate.png'), roughness:0.8, metalness:0.05});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [8] Crate texture -> PNG")

# --- Change 9: Dark metal texture ---
old = """// Dark metal texture
tex.darkMetal = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#445566'; ctx.fillRect(0,0,w,h);
    for (var i=0; i < 2000; i++) {
      var g = Math.floor(60 + Math.random()*40);
      ctx.fillStyle = 'rgba('+g+','+(g+8)+','+(g+16)+',0.2)';
      ctx.fillRect(Math.random()*w, Math.random()*h, 1+Math.random()*3, 1+Math.random()*3);
    }
  }, 64, 64);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.3, metalness:0.8});
})();"""
new = """// Dark metal texture (loaded from PNG)
tex.darkMetal = new THREE.MeshStandardMaterial({map:_loadTex('tex_dark_metal.png'), roughness:0.3, metalness:0.8});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [9] Dark metal texture -> PNG")

# --- Change 10: Concrete floor texture (with repeat) ---
old = """// Concrete floor (indoor)
tex.concreteFloor = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#555555'; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle = 'rgba(70,70,70,0.3)'; ctx.lineWidth = 1;
    for (var i=0; i <= w; i += 64) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,h); ctx.stroke(); }
    for (var i=0; i <= h; i += 64) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(w,i); ctx.stroke(); }
    for (var i=0; i < 3000; i++) {
      var g = Math.floor(70 + Math.random()*30);
      ctx.fillStyle = 'rgba('+g+','+g+','+g+',0.2)';
      ctx.fillRect(Math.random()*w, Math.random()*h, 1+Math.random()*2, 1+Math.random()*2);
    }
  }, 128, 128);
  t.repeat.set(10,10);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.85, metalness:0.1});
})();"""
new = """// Concrete floor (loaded from PNG, with repeat)
tex.concreteFloor = new THREE.MeshStandardMaterial({map:_loadTex('tex_concrete_floor.png',10,10), roughness:0.85, metalness:0.1});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [10] Concrete floor texture -> PNG (repeat 10x10)")

# --- Change 11: Hedge texture ---
old = """// Hedge texture (for Test Map boundary)
tex.hedge = (function() {
  const t = makeCanvasTex(function(ctx, w, h) {
    ctx.fillStyle = '#2d5a1e'; ctx.fillRect(0,0,w,h);
    for (var i=0; i < 3000; i++) {
      var v = 0.7 + Math.random()*0.6;
      var rr = Math.floor(45*v), gg = Math.floor(90*v), bb = Math.floor(30*v);
      ctx.fillStyle = 'rgba('+rr+','+gg+','+bb+',0.5)';
      var s = 2+Math.random()*5;
      ctx.fillRect(Math.random()*w, Math.random()*h, s, s);
    }
    // Leaf shapes
    for (var i=0; i < 200; i++) {
      var v = 0.6 + Math.random()*0.8;
      var rr = Math.floor(35*v), gg = Math.floor(110*v), bb = Math.floor(25*v);
      ctx.fillStyle = 'rgba('+rr+','+gg+','+bb+',0.6)';
      var x = Math.random()*w, y = Math.random()*h;
      ctx.beginPath(); ctx.ellipse(x,y,2+Math.random()*3,1+Math.random()*2,Math.random()*Math.PI,0,Math.PI*2); ctx.fill();
    }
  }, 128, 128);
  return new THREE.MeshStandardMaterial({map:t, roughness:0.95, metalness:0.0});
})();"""
new = """// Hedge texture (loaded from PNG)
tex.hedge = new THREE.MeshStandardMaterial({map:_loadTex('tex_hedge.png'), roughness:0.95, metalness:0.0});"""
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [11] Hedge texture -> PNG")

# --- Change 12: Zombie skin texture -> PNG ---
# Find and replace the entire zombie skin block
old_zombie_skin_start = '// Zombie skin texture (HQ 512x512)\ntex.zombieSkin=(function(){'
old_zombie_skin_end = '})();'
if old_zombie_skin_start in html:
    # Find the start and end of this block
    start_idx = html.index(old_zombie_skin_start)
    # Find the matching })();  - it's the first one after start
    end_search = html.index('\n\n// Zombie dark skin', start_idx)
    old_block = html[start_idx:end_search]
    new_block = "// Zombie skin texture (loaded from PNG 512x512)\ntex.zombieSkin = _loadTex('tex_zombie_skin.png');\n\n"
    html = html[:start_idx] + new_block + html[end_search:]
    changes += 1
    print("  [12] Zombie skin texture -> PNG")

# --- Change 13: Zombie dark texture -> PNG ---
old_zombie_dark_start = '// Zombie dark skin (HQ 512x512)\ntex.zombieDark=(function(){'
if old_zombie_dark_start in html:
    start_idx = html.index(old_zombie_dark_start)
    # Find where this block ends (next section starts with // =====)
    end_search = html.index('\n// ===== COLLISION', start_idx)
    old_block = html[start_idx:end_search]
    new_block = "// Zombie dark skin (loaded from PNG 512x512)\ntex.zombieDark = _loadTex('tex_zombie_dark.png');\n"
    html = html[:start_idx] + new_block + html[end_search:]
    changes += 1
    print("  [13] Zombie dark texture -> PNG")

# --- Change 14: Gun body texture -> PNG ---
old = 'var _gBCv=document.createElement(\'canvas\');_gBCv.width=512;_gBCv.height=512;'
if old in html:
    # Replace the entire gun body texture generation block
    start_marker = '// Gun procedural textures\n'
    if start_marker in html:
        start_idx = html.index(start_marker)
        # Find end of all gun texture generation (before "// Main body")
        end_marker = '\n// Main body\n'
        if end_marker in html:
            end_idx = html.index(end_marker, start_idx)
            old_block = html[start_idx:end_idx]
            new_block = """// Gun textures (loaded from PNG files)
var _gBT = _loadTex('tex_gun_body.png');
var _gBrT = _loadTex('tex_gun_barrel.png');
var _gGT = _loadTex('tex_gun_grip.png');
var _gMT = _loadTex('tex_gun_mag.png');
"""
            html = html[:start_idx] + new_block + html[end_idx:]
            changes += 1
            print("  [14] All gun textures -> PNG (body, barrel, grip, mag)")

# --- Change 15: Add background image to menu ---
old = '.menu-overlay{position:fixed;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0a0e1a 0%,#1a1a2e 30%,#16213e 60%,#0f3460 100%)}'
new = '.menu-overlay{position:fixed;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;background:url("fps-game-assets/bg_menu.png") center/cover no-repeat}'
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [15] Menu background -> PNG image")

# --- Change 16: Also update death and victory screens with subtle bg ---
old = '#death-screen{position:fixed;inset:0;z-index:300;display:flex;align-items:center;justify-content:center;flex-direction:column;background:rgba(60,0,0,0.88)}'
new = '#death-screen{position:fixed;inset:0;z-index:300;display:flex;align-items:center;justify-content:center;flex-direction:column;background:rgba(60,0,0,0.92)}'
if old in html:
    html = html.replace(old, new, 1)
    changes += 1
    print("  [16] Death screen bg improved")

# Save
with open(HTML_SRC, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n  Total changes: {changes}")

# Verify
with open(HTML_SRC, 'r') as f:
    content = f.read()
    checks = {
        '_loadTex helper': '_loadTex' in content,
        'brick PNG': "tex_brick.png" in content,
        'zombie skin PNG': "tex_zombie_skin.png" in content,
        'gun body PNG': "tex_gun_body.png" in content,
        'menu bg PNG': "bg_menu.png" in content,
        'no more makeCanvasTex for brick': 'makeCanvasTex(function(ctx, w, h) {\n    ctx.fillStyle = \'#7a5c3a\'' not in content,
    }
    print("\n=== Verification ===")
    for name, ok in checks.items():
        print(f"  {'✓' if ok else '✗'} {name}")

print("\n=== Done ===")
