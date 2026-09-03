#!/usr/bin/env python3
"""
Update FPS Game: Fix bugs, improve textures, generate PNG texture files,
and update HTML for offline play.
"""
import os
import math
import random
from PIL import Image, ImageDraw

# Paths
GAME_DIR = "/home/z/my-project/download"
ASSETS_DIR = os.path.join(GAME_DIR, "fps-game-assets")
HTML_SRC = os.path.join(GAME_DIR, "fps-game.html")
HTML_DST = os.path.join(GAME_DIR, "fps-game.html")

os.makedirs(ASSETS_DIR, exist_ok=True)

# Monkey-patch ImageDraw.rectangle to be safe
_orig_rect = ImageDraw.ImageDraw.rectangle
def _safe_rect(self, xy, **kwargs):
    try:
        _orig_rect(self, xy, **kwargs)
    except (ValueError, TypeError):
        pass
ImageDraw.ImageDraw.rectangle = _safe_rect

def rrect(draw, x1, y1, x2, y2, **kw):
    """Safe rectangle draw"""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    if x2 <= x1: x2 = x1 + 1
    if y2 <= y1: y2 = y1 + 1
    draw.rectangle([x1, y1, x2, y2], **kw)

# ============================================================
# PART 1: Generate Texture PNG Files
# ============================================================

def gen_brick(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (122, 92, 58))
    d = ImageDraw.Draw(img)
    bw, bh, gap = 30, 14, 2
    for r in range(h // bh + 1):
        off = (r % 2) * bw // 2
        for c in range(-1, w // bw + 2):
            v = 0.85 + random.random() * 0.3
            rr, gg, bb = int(160*v), int(100*v), int(65*v)
            x1 = c * bw + off + gap; y1 = r * bh + gap
            x2 = x1 + bw - gap*2; y2 = y1 + bh - gap*2
            if x1 < w and y1 < h and x2 > 0 and y2 > 0:
                rrect(d, max(0,x1), max(0,y1), min(w-1,x2), min(h-1,y2), fill=(rr,gg,bb))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_sand(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (196, 168, 104))
    d = ImageDraw.Draw(img)
    for _ in range(3000):
        v = 0.8 + random.random()*0.4; rr,gg,bb = int(196*v),int(168*v),int(104*v)
        x,y = random.randint(0,w-1),random.randint(0,h-1); sz=1+random.randint(0,2)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_sand_ground(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (194, 168, 120))
    d = ImageDraw.Draw(img)
    for _ in range(4000):
        v = 0.85+random.random()*0.3; rr,gg,bb = int(194*v),int(168*v),int(120*v)
        x,y = random.randint(0,w-1),random.randint(0,h-1); sz=random.randint(0,3)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_concrete(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (138, 138, 138))
    d = ImageDraw.Draw(img)
    for _ in range(5000):
        v = 0.7+random.random()*0.6; g=int(138*v)
        x,y = random.randint(0,w-1),random.randint(0,h-1); sz=1+random.randint(0,2)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(g,g,g))
    for _ in range(8):
        d.line([(random.randint(0,w-1),random.randint(0,h-1)),(random.randint(0,w-1),random.randint(0,h-1))],fill=(60,60,60),width=1)
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_metal_floor(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (102, 119, 136))
    d = ImageDraw.Draw(img)
    for i in range(0,w+1,32): d.line([(i,0),(i,h)],fill=(100,120,140),width=1)
    for i in range(0,h+1,32): d.line([(0,i),(w,i)],fill=(100,120,140),width=1)
    for x in range(16,w,32):
        for y in range(16,h,32): d.ellipse([x-2,y-2,x+2,y+2],fill=(150,170,190))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_metal_wall(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (119, 136, 153))
    d = ImageDraw.Draw(img)
    for i in range(0,w+1,64): d.line([(i,0),(i,h)],fill=(90,110,130),width=1)
    for i in range(0,h+1,64): d.line([(0,i),(w,i)],fill=(90,110,130),width=1)
    for _ in range(1200):
        g=100+random.randint(0,60); x,y=random.randint(0,w-1),random.randint(0,h-1)
        rrect(d,x,y,min(w-1,x+random.randint(2,5)),y+1,fill=(g,g+10,g+20))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_crate(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (139, 105, 20))
    d = ImageDraw.Draw(img)
    for i in range(0,w,32): d.line([(i,0),(i,h)],fill=(90,50,10),width=2)
    for _ in range(2000):
        v=0.8+random.random()*0.4; rr,gg,bb=int(139*v),int(105*v),int(20*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1)
        rrect(d,x,y,min(w-1,x+random.randint(0,8)),y+1,fill=(rr,gg,bb))
    d.rectangle([8,8,w-9,h-9],outline=(80,50,10),width=4)
    d.line([(0,0),(w,h)],fill=(80,50,10),width=4)
    d.line([(w,0),(0,h)],fill=(80,50,10),width=4)
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_dark_metal(path, w=128, h=128):
    img = Image.new('RGB', (w, h), (68, 85, 102))
    d = ImageDraw.Draw(img)
    for _ in range(3000):
        g=60+random.randint(0,40); x,y=random.randint(0,w-1),random.randint(0,h-1); sz=1+random.randint(0,3)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(g,g+8,g+16))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_concrete_floor(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (85, 85, 85))
    d = ImageDraw.Draw(img)
    for i in range(0,w+1,64): d.line([(i,0),(i,h)],fill=(70,70,70),width=1)
    for i in range(0,h+1,64): d.line([(0,i),(w,i)],fill=(70,70,70),width=1)
    for _ in range(4000):
        g=70+random.randint(0,30); x,y=random.randint(0,w-1),random.randint(0,h-1); sz=1+random.randint(0,2)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(g,g,g))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_hedge(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (45, 90, 30))
    d = ImageDraw.Draw(img)
    for _ in range(4000):
        v=0.7+random.random()*0.6; rr,gg,bb=int(45*v),int(90*v),int(30*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1); sz=2+random.randint(0,5)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    for _ in range(300):
        v=0.6+random.random()*0.8; rr,gg,bb=int(35*v),int(110*v),int(25*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1)
        rx,ry=2+random.randint(0,3),1+random.randint(0,2)
        d.ellipse([x-rx,y-ry,x+rx,y+ry],fill=(rr,gg,bb))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_zombie_skin(path, w=512, h=512):
    img = Image.new('RGB', (w, h), (90, 122, 74))
    d = ImageDraw.Draw(img)
    for _ in range(5000):
        v=0.5+random.random()*0.6; rr,gg,bb=int(75*v),int(105*v),int(55*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1); sz=3+random.randint(0,15)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    for _ in range(2500):
        v=0.8+random.random()*0.4; rr,gg,bb=int(120*v),int(150*v),int(95*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1); sz=2+random.randint(0,10)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    for _ in range(40):
        sx,sy=random.randint(0,w-1),random.randint(0,h-1); pts=[(sx,sy)]
        for _ in range(8): sx+=(random.random()-0.5)*60; sy+=random.random()*35; pts.append((int(sx),int(sy)))
        for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=(35,55,25),width=2)
    for _ in range(25):
        cx,cy=random.randint(0,w-1),random.randint(0,h-1); rx=5+random.randint(0,12); ry=4+random.randint(0,8)
        d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=(120,30,20))
        d.ellipse([cx-rx//2,cy-ry//2,cx+rx//2,cy+ry//2],fill=(80,15,10))
    for _ in range(8000):
        v=0.6+random.random()*0.4; rr,gg,bb=int(50*v),int(70*v),int(35*v)
        img.putpixel((random.randint(0,w-1),random.randint(0,h-1)),(rr,gg,bb))
    for _ in range(15):
        cx,cy=random.randint(0,w-1),random.randint(0,h-1); s=3+random.randint(0,6)
        d.ellipse([cx-s,cy-s,cx+s,cy+s],fill=(100,25,15))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_zombie_dark(path, w=512, h=512):
    img = Image.new('RGB', (w, h), (58, 90, 42))
    d = ImageDraw.Draw(img)
    for _ in range(4000):
        v=0.4+random.random()*0.6; rr,gg,bb=int(55*v),int(80*v),int(38*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1); sz=3+random.randint(0,12)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    for _ in range(1500):
        v=0.3+random.random()*0.4; rr,gg,bb=int(30*v),int(50*v),int(20*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1); sz=2+random.randint(0,8)
        rrect(d,x,y,min(w-1,x+sz),min(h-1,y+sz),fill=(rr,gg,bb))
    for _ in range(30):
        sx,sy=random.randint(0,w-1),random.randint(0,h-1); pts=[(sx,sy)]
        for _ in range(6): sx+=(random.random()-0.5)*50; sy+=random.random()*30; pts.append((int(sx),int(sy)))
        for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=(25,40,15),width=1)
    for _ in range(18):
        cx,cy=random.randint(0,w-1),random.randint(0,h-1); rx=4+random.randint(0,10); ry=3+random.randint(0,7)
        d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=(90,20,15))
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_gun_body(path, w=512, h=512):
    img = Image.new('RGB', (w, h), (44, 44, 44))
    d = ImageDraw.Draw(img)
    for _ in range(6000):
        g=30+random.randint(0,30); x,y=random.randint(0,w-1),random.randint(0,h-1); sx=1+random.randint(0,4); sy=1+random.randint(0,3)
        rrect(d,x,y,min(w-1,x+sx),min(h-1,y+sy),fill=(g,g,g))
    for i in range(0,w+1,32): d.line([(i,0),(i,h)],fill=(60,60,60),width=1)
    for i in range(0,h+1,32): d.line([(0,i),(w,i)],fill=(60,60,60),width=1)
    for _ in range(40):
        x1,y1=random.randint(0,w-1),random.randint(0,h-1)
        d.line([(x1,y1),(x1+random.randint(-40,40),y1+random.randint(-20,20))],fill=(80,80,80),width=1)
    for _ in range(8):
        cx,cy,cr=random.randint(0,w-1),random.randint(0,h-1),5+random.randint(0,20)
        d.ellipse([cx-cr,cy-cr,cx+cr,cy+cr],outline=(55,55,55),width=2)
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_gun_barrel(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (26, 26, 26))
    d = ImageDraw.Draw(img)
    for _ in range(3000):
        g=15+random.randint(0,25); x,y=random.randint(0,w-1),random.randint(0,h-1)
        rrect(d,x,y,min(w-1,x+random.randint(1,3)),min(h-1,y+random.randint(1,5)),fill=(g,g,g))
    for i in range(0,w+1,16): d.line([(i,0),(i,h)],fill=(40,40,40),width=1)
    for i in range(0,h+1,16): d.line([(0,i),(w,i)],fill=(40,40,40),width=1)
    for _ in range(15):
        d.line([(random.randint(0,w-1),random.randint(0,h-1)),(random.randint(0,w-1),random.randint(0,h-1))],fill=(25,30,40),width=1)
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_gun_grip(path, w=256, h=256):
    img = Image.new('RGB', (w, h), (61, 43, 31))
    d = ImageDraw.Draw(img)
    for _ in range(3000):
        v=0.7+random.random()*0.5; rr,gg,bb=int(61*v),int(43*v),int(31*v)
        x,y=random.randint(0,w-1),random.randint(0,h-1)
        rrect(d,x,y,min(w-1,x+random.randint(1,4)),min(h-1,y+random.randint(1,8)),fill=(rr,gg,bb))
    for i in range(0,h,5):
        offset=random.random()*3
        for x in range(w):
            y=int(i+math.sin(x*0.05)*2+offset)
            if 0<=y<h:
                old=img.getpixel((x,y)); img.putpixel((x,y),(max(0,old[0]-15),max(0,old[1]-10),max(0,old[2]-8)))
    for cy in range(10,h-10,8):
        for cx in range(10,w-10,8):
            d.line([(cx,cy),(cx+4,cy+4)],fill=(45,30,20),width=1)
            d.line([(cx+4,cy),(cx,cy+4)],fill=(45,30,20),width=1)
    img.save(path); print(f"  {os.path.basename(path)}")

def gen_gun_mag(path, w=128, h=128):
    img = Image.new('RGB', (w, h), (51, 51, 51))
    d = ImageDraw.Draw(img)
    for _ in range(2000):
        g=35+random.randint(0,30); x,y=random.randint(0,w-1),random.randint(0,h-1)
        rrect(d,x,y,min(w-1,x+random.randint(1,3)),min(h-1,y+random.randint(1,3)),fill=(g,g,g))
    for i in range(0,w+1,24): d.line([(i,0),(i,h)],fill=(65,65,65),width=1)
    img.save(path); print(f"  {os.path.basename(path)}")

# Generate all textures
print("=== Generating texture PNG files ===")
gen_brick(os.path.join(ASSETS_DIR, "tex_brick.png"))
gen_sand(os.path.join(ASSETS_DIR, "tex_sand.png"))
gen_sand_ground(os.path.join(ASSETS_DIR, "tex_sand_ground.png"))
gen_concrete(os.path.join(ASSETS_DIR, "tex_concrete.png"))
gen_metal_floor(os.path.join(ASSETS_DIR, "tex_metal_floor.png"))
gen_metal_wall(os.path.join(ASSETS_DIR, "tex_metal_wall.png"))
gen_crate(os.path.join(ASSETS_DIR, "tex_crate.png"))
gen_dark_metal(os.path.join(ASSETS_DIR, "tex_dark_metal.png"))
gen_concrete_floor(os.path.join(ASSETS_DIR, "tex_concrete_floor.png"))
gen_hedge(os.path.join(ASSETS_DIR, "tex_hedge.png"))
gen_zombie_skin(os.path.join(ASSETS_DIR, "tex_zombie_skin.png"))
gen_zombie_dark(os.path.join(ASSETS_DIR, "tex_zombie_dark.png"))
gen_gun_body(os.path.join(ASSETS_DIR, "tex_gun_body.png"))
gen_gun_barrel(os.path.join(ASSETS_DIR, "tex_gun_barrel.png"))
gen_gun_grip(os.path.join(ASSETS_DIR, "tex_gun_grip.png"))
gen_gun_mag(os.path.join(ASSETS_DIR, "tex_gun_mag.png"))
print("\n=== All texture PNG files generated ===")

# ============================================================
# PART 2: Update HTML File
# ============================================================

print("\n=== Updating HTML file ===")

with open(HTML_SRC, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# --- Fix 1: Change Three.js CDN to local file ---
old = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
new = '<script src="fps-game-assets/three.min.js"></script>'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [1] Three.js CDN -> local file")

# --- Fix 2: STEP_UP for Vertigo stairs ---
old = 'const STEP_UP = 0.4;'
new = 'const STEP_UP = 0.55;'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [2] STEP_UP 0.4 -> 0.55 (Vertigo stairs)")

# --- Fix 3: Improve checkEnemyWall ---
old = """function checkEnemyWall(px, pz) {
  var r = 0.5;
  for (var i = 0; i < colliders.length; i++) {
    var c = colliders[i];
    if (c.maxY - c.minY < 0.5) continue;
    if (c.maxY < 0.1 || c.minY > 2.5) continue;
    if (px + r > c.minX && px - r < c.maxX &&
        pz + r > c.minZ && pz - r < c.maxZ) return true;
  }
  return false;
}"""
new = """function checkEnemyWall(px, pz) {
  var r = 0.5;
  for (var i = 0; i < colliders.length; i++) {
    var c = colliders[i];
    if (c.maxY - c.minY < 0.35) continue;
    if (c.maxY < -0.5 || c.minY > 2.5) continue;
    if (px + r > c.minX && px - r < c.maxX &&
        pz + r > c.minZ && pz - r < c.maxZ) return true;
  }
  return false;
}"""
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [3] checkEnemyWall Y-range fixed for multi-level maps")

# --- Fix 4: Zombie skin 512x512 ---
old = 'var cv=document.createElement(\'canvas\');cv.width=256;cv.height=256;\n  var ctx=cv.getContext(\'2d\');\n  ctx.fillStyle=\'#5a7a4a\';ctx.fillRect(0,0,256,256);\n  for(var i=0;i<3000;i++){var v=0.5+Math.random()*0.6;ctx.fillStyle=\'rgba(\'+Math.floor(75*v)+\',\'+Math.floor(105*v)+\',\'+Math.floor(55*v)+\',0.35)\';ctx.fillRect(Math.random()*256,Math.random()*256,3+Math.random()*12,3+Math.random()*12);}\n  for(var i=0;i<1500;i++){var v=0.8+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(120*v)+\',\'+Math.floor(150*v)+\',\'+Math.floor(95*v)+\',0.25)\';ctx.fillRect(Math.random()*256,Math.random()*256,2+Math.random()*8,2+Math.random()*8);}\n  ctx.strokeStyle=\'rgba(35,55,25,0.3)\';ctx.lineWidth=1.5;\n  for(var i=0;i<30;i++){ctx.beginPath();var sx=Math.random()*256,sy=Math.random()*256;ctx.moveTo(sx,sy);for(var j=0;j<5;j++){sx+=(Math.random()-0.5)*40;sy+=Math.random()*25;ctx.lineTo(sx,sy);}ctx.stroke();}\n  for(var i=0;i<20;i++){ctx.fillStyle=\'rgba(80,30,20,0.3)\';ctx.beginPath();ctx.ellipse(Math.random()*256,Math.random()*256,4+Math.random()*8,3+Math.random()*6,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  for(var i=0;i<5000;i++){var v=0.6+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(50*v)+\',\'+Math.floor(70*v)+\',\'+Math.floor(35*v)+\',0.15)\';ctx.fillRect(Math.random()*256,Math.random()*256,1,1);}\n  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;'
new = 'var cv=document.createElement(\'canvas\');cv.width=512;cv.height=512;\n  var ctx=cv.getContext(\'2d\');\n  ctx.fillStyle=\'#5a7a4a\';ctx.fillRect(0,0,512,512);\n  for(var i=0;i<5000;i++){var v=0.5+Math.random()*0.6;ctx.fillStyle=\'rgba(\'+Math.floor(75*v)+\',\'+Math.floor(105*v)+\',\'+Math.floor(55*v)+\',0.35)\';ctx.fillRect(Math.random()*512,Math.random()*512,3+Math.random()*16,3+Math.random()*16);}\n  for(var i=0;i<2500;i++){var v=0.8+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(120*v)+\',\'+Math.floor(150*v)+\',\'+Math.floor(95*v)+\',0.25)\';ctx.fillRect(Math.random()*512,Math.random()*512,2+Math.random()*12,2+Math.random()*12);}\n  ctx.strokeStyle=\'rgba(35,55,25,0.35)\';ctx.lineWidth=2;\n  for(var i=0;i<40;i++){ctx.beginPath();var sx=Math.random()*512,sy=Math.random()*512;ctx.moveTo(sx,sy);for(var j=0;j<8;j++){sx+=(Math.random()-0.5)*60;sy+=Math.random()*35;ctx.lineTo(sx,sy);}ctx.stroke();}\n  for(var i=0;i<30;i++){ctx.fillStyle=\'rgba(80,30,20,0.4)\';ctx.beginPath();ctx.ellipse(Math.random()*512,Math.random()*512,5+Math.random()*12,4+Math.random()*8,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  for(var i=0;i<15;i++){ctx.fillStyle=\'rgba(100,20,15,0.5)\';ctx.beginPath();ctx.ellipse(Math.random()*512,Math.random()*512,3+Math.random()*6,2+Math.random()*4,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  for(var i=0;i<8000;i++){var v=0.6+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(50*v)+\',\'+Math.floor(70*v)+\',\'+Math.floor(35*v)+\',0.15)\';ctx.fillRect(Math.random()*512,Math.random()*512,1,1);}\n  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [4] Zombie skin texture upgraded to 512x512")

# --- Fix 5: Zombie dark 512x512 ---
old = 'var cv=document.createElement(\'canvas\');cv.width=256;cv.height=256;\n  var ctx=cv.getContext(\'2d\');\n  ctx.fillStyle=\'#3a5a2a\';ctx.fillRect(0,0,256,256);\n  for(var i=0;i<2500;i++){var v=0.4+Math.random()*0.6;ctx.fillStyle=\'rgba(\'+Math.floor(55*v)+\',\'+Math.floor(80*v)+\',\'+Math.floor(38*v)+\',0.35)\';ctx.fillRect(Math.random()*256,Math.random()*256,3+Math.random()*10,3+Math.random()*10);}\n  for(var i=0;i<1000;i++){var v=0.3+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(30*v)+\',\'+Math.floor(50*v)+\',\'+Math.floor(20*v)+\',0.3)\';ctx.fillRect(Math.random()*256,Math.random()*256,2+Math.random()*8,2+Math.random()*8);}\n  ctx.strokeStyle=\'rgba(25,40,15,0.35)\';ctx.lineWidth=1;\n  for(var i=0;i<20;i++){ctx.beginPath();var sx=Math.random()*256,sy=Math.random()*256;ctx.moveTo(sx,sy);for(var j=0;j<4;j++){sx+=(Math.random()-0.5)*35;sy+=Math.random()*20;ctx.lineTo(sx,sy);}ctx.stroke();}\n  for(var i=0;i<15;i++){ctx.fillStyle=\'rgba(60,20,15,0.4)\';ctx.beginPath();ctx.ellipse(Math.random()*256,Math.random()*256,3+Math.random()*7,2+Math.random()*5,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;'
new = 'var cv=document.createElement(\'canvas\');cv.width=512;cv.height=512;\n  var ctx=cv.getContext(\'2d\');\n  ctx.fillStyle=\'#3a5a2a\';ctx.fillRect(0,0,512,512);\n  for(var i=0;i<4000;i++){var v=0.4+Math.random()*0.6;ctx.fillStyle=\'rgba(\'+Math.floor(55*v)+\',\'+Math.floor(80*v)+\',\'+Math.floor(38*v)+\',0.35)\';ctx.fillRect(Math.random()*512,Math.random()*512,3+Math.random()*14,3+Math.random()*14);}\n  for(var i=0;i<1500;i++){var v=0.3+Math.random()*0.4;ctx.fillStyle=\'rgba(\'+Math.floor(30*v)+\',\'+Math.floor(50*v)+\',\'+Math.floor(20*v)+\',0.3)\';ctx.fillRect(Math.random()*512,Math.random()*512,2+Math.random()*10,2+Math.random()*10);}\n  ctx.strokeStyle=\'rgba(25,40,15,0.4)\';ctx.lineWidth=1.5;\n  for(var i=0;i<30;i++){ctx.beginPath();var sx=Math.random()*512,sy=Math.random()*512;ctx.moveTo(sx,sy);for(var j=0;j<6;j++){sx+=(Math.random()-0.5)*50;sy+=Math.random()*30;ctx.lineTo(sx,sy);}ctx.stroke();}\n  for(var i=0;i<20;i++){ctx.fillStyle=\'rgba(60,20,15,0.5)\';ctx.beginPath();ctx.ellipse(Math.random()*512,Math.random()*512,4+Math.random()*10,3+Math.random()*7,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  for(var i=0;i<10;i++){ctx.fillStyle=\'rgba(90,15,10,0.4)\';ctx.beginPath();ctx.ellipse(Math.random()*512,Math.random()*512,2+Math.random()*5,2+Math.random()*4,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}\n  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [5] Zombie dark texture upgraded to 512x512")

# --- Fix 6: Gun body 512x512 ---
old = 'var _gBCv=document.createElement(\'canvas\');_gBCv.width=256;_gBCv.height=256;\nvar _gb=_gBCv.getContext(\'2d\');_gb.fillStyle=\'#2c2c2c\';_gb.fillRect(0,0,256,256);\nfor(var _i=0;_i<3000;_i++){var _g=Math.floor(30+Math.random()*30);_gb.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.2)\';_gb.fillRect(Math.random()*256,Math.random()*256,1+Math.random()*3,1+Math.random()*2);}\n_gb.strokeStyle=\'rgba(60,60,60,0.15)\';_gb.lineWidth=1;\nfor(var _i=0;_i<256;_i+=32){_gb.beginPath();_gb.moveTo(_i,0);_gb.lineTo(_i,256);_gb.stroke();}\nfor(var _i=0;_i<256;_i+=32){_gb.beginPath();_gb.moveTo(0,_i);_gb.lineTo(256,_i);_gb.stroke();}\n_gb.strokeStyle=\'rgba(80,80,80,0.3)\';_gb.lineWidth=0.5;\nfor(var _i=0;_i<20;_i++){_gb.beginPath();_gb.moveTo(Math.random()*256,Math.random()*256);_gb.lineTo(Math.random()*256,Math.random()*256);_gb.stroke();}\nvar _gBT=new THREE.CanvasTexture(_gBCv);'
new = 'var _gBCv=document.createElement(\'canvas\');_gBCv.width=512;_gBCv.height=512;\nvar _gb=_gBCv.getContext(\'2d\');_gb.fillStyle=\'#2c2c2c\';_gb.fillRect(0,0,512,512);\nfor(var _i=0;_i<6000;_i++){var _g=Math.floor(30+Math.random()*30);_gb.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.2)\';_gb.fillRect(Math.random()*512,Math.random()*512,1+Math.random()*4,1+Math.random()*3);}\n_gb.strokeStyle=\'rgba(60,60,60,0.15)\';_gb.lineWidth=1;\nfor(var _i=0;_i<512;_i+=32){_gb.beginPath();_gb.moveTo(_i,0);_gb.lineTo(_i,512);_gb.stroke();}\nfor(var _i=0;_i<512;_i+=32){_gb.beginPath();_gb.moveTo(0,_i);_gb.lineTo(512,_i);_gb.stroke();}\n_gb.strokeStyle=\'rgba(80,80,80,0.3)\';_gb.lineWidth=0.5;\nfor(var _i=0;_i<40;_i++){_gb.beginPath();_gb.moveTo(Math.random()*512,Math.random()*512);_gb.lineTo(Math.random()*512,Math.random()*512);_gb.stroke();}\n_gb.strokeStyle=\'rgba(55,55,55,0.25)\';_gb.lineWidth=2;\nfor(var _i=0;_i<8;_i++){var _wx=Math.random()*512,_wy=Math.random()*512,_wr=5+Math.random()*20;_gb.beginPath();_gb.arc(_wx,_wy,_wr,0,Math.PI*2);_gb.stroke();}\nvar _gBT=new THREE.CanvasTexture(_gBCv);'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [6] Gun body texture upgraded to 512x512 with wear marks")

# --- Fix 7: Gun barrel 256x256 ---
old = 'var _gBrCv=document.createElement(\'canvas\');_gBrCv.width=128;_gBrCv.height=128;\nvar _br=_gBrCv.getContext(\'2d\');_br.fillStyle=\'#1a1a1a\';_br.fillRect(0,0,128,128);\nfor(var _i=0;_i<2000;_i++){var _g=Math.floor(15+Math.random()*25);_br.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.15)\';_br.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*2,1+Math.random()*4);}\n_br.strokeStyle=\'rgba(40,40,40,0.2)\';_br.lineWidth=0.5;\nfor(var _i=0;_i<128;_i+=16){_br.beginPath();_br.moveTo(_i,0);_br.lineTo(_i,128);_br.stroke();}\nvar _gBrT=new THREE.CanvasTexture(_gBrCv);'
new = 'var _gBrCv=document.createElement(\'canvas\');_gBrCv.width=256;_gBrCv.height=256;\nvar _br=_gBrCv.getContext(\'2d\');_br.fillStyle=\'#1a1a1a\';_br.fillRect(0,0,256,256);\nfor(var _i=0;_i<3000;_i++){var _g=Math.floor(15+Math.random()*25);_br.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.15)\';_br.fillRect(Math.random()*256,Math.random()*256,1+Math.random()*3,1+Math.random()*5);}\n_br.strokeStyle=\'rgba(40,40,40,0.2)\';_br.lineWidth=0.5;\nfor(var _i=0;_i<256;_i+=16){_br.beginPath();_br.moveTo(_i,0);_br.lineTo(_i,256);_br.stroke();}\nfor(var _i=0;_i<256;_i+=16){_br.beginPath();_br.moveTo(0,_i);_br.lineTo(256,_i);_br.stroke();}\n_br.strokeStyle=\'rgba(25,30,40,0.15)\';_br.lineWidth=1;\nfor(var _i=0;_i<15;_i++){_br.beginPath();_br.moveTo(Math.random()*256,Math.random()*256);_br.lineTo(Math.random()*256,Math.random()*256);_br.stroke();}\nvar _gBrT=new THREE.CanvasTexture(_gBrCv);'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [7] Gun barrel texture upgraded to 256x256 with rifling")

# --- Fix 8: Gun grip 256x256 with checkering ---
old = 'var _gGCv=document.createElement(\'canvas\');_gGCv.width=128;_gGCv.height=128;\nvar _gr=_gGCv.getContext(\'2d\');_gr.fillStyle=\'#3d2b1f\';_gr.fillRect(0,0,128,128);\nfor(var _i=0;_i<2000;_i++){var _v=0.7+Math.random()*0.5;_gr.fillStyle=\'rgba(\'+Math.floor(61*_v)+\',\'+Math.floor(43*_v)+\',\'+Math.floor(31*_v)+\',0.3)\';_gr.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*3,Math.random()*6);}\n_gr.strokeStyle=\'rgba(25,18,12,0.4)\';_gr.lineWidth=1.5;\nfor(var _i=0;_i<128;_i+=6){_gr.beginPath();_gr.moveTo(0,_i+Math.random()*2);_gr.lineTo(128,_i+Math.random()*2);_gr.stroke();}\nvar _gGT=new THREE.CanvasTexture(_gGCv);'
new = 'var _gGCv=document.createElement(\'canvas\');_gGCv.width=256;_gGCv.height=256;\nvar _gr=_gGCv.getContext(\'2d\');_gr.fillStyle=\'#3d2b1f\';_gr.fillRect(0,0,256,256);\nfor(var _i=0;_i<3000;_i++){var _v=0.7+Math.random()*0.5;_gr.fillStyle=\'rgba(\'+Math.floor(61*_v)+\',\'+Math.floor(43*_v)+\',\'+Math.floor(31*_v)+\',0.3)\';_gr.fillRect(Math.random()*256,Math.random()*256,1+Math.random()*4,Math.random()*8);}\n_gr.strokeStyle=\'rgba(25,18,12,0.4)\';_gr.lineWidth=1.5;\nfor(var _i=0;_i<256;_i+=5){_gr.beginPath();_gr.moveTo(0,_i+Math.random()*3);_gr.lineTo(256,_i+Math.random()*3);_gr.stroke();}\n_gr.strokeStyle=\'rgba(40,28,18,0.3)\';_gr.lineWidth=1;\nfor(var _cx=8;_cx<256;_cx+=8){for(var _cy=8;_cy<256;_cy+=8){_gr.beginPath();_gr.moveTo(_cx,_cy);_gr.lineTo(_cx+4,_cy+4);_gr.stroke();_gr.beginPath();_gr.moveTo(_cx+4,_cy);_gr.lineTo(_cx,_cy+4);_gr.stroke();}}\nvar _gGT=new THREE.CanvasTexture(_gGCv);'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [8] Gun grip texture upgraded to 256x256 with checkering")

# --- Fix 9: Gun mag 128x128 ---
old = 'var _gMCv=document.createElement(\'canvas\');_gMCv.width=64;_gMCv.height=64;\nvar _mg=_gMCv.getContext(\'2d\');_mg.fillStyle=\'#333333\';_mg.fillRect(0,0,64,64);\nfor(var _i=0;_i<1000;_i++){var _g=Math.floor(35+Math.random()*30);_mg.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.2)\';_mg.fillRect(Math.random()*64,Math.random()*64,1+Math.random()*2,1+Math.random()*2);}\nvar _gMT=new THREE.CanvasTexture(_gMCv);'
new = 'var _gMCv=document.createElement(\'canvas\');_gMCv.width=128;_gMCv.height=128;\nvar _mg=_gMCv.getContext(\'2d\');_mg.fillStyle=\'#333333\';_mg.fillRect(0,0,128,128);\nfor(var _i=0;_i<2000;_i++){var _g=Math.floor(35+Math.random()*30);_mg.fillStyle=\'rgba(\'+_g+\',\'+_g+\',\'+_g+\',0.2)\';_mg.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*3,1+Math.random()*3);}\n_mg.strokeStyle=\'rgba(65,65,65,0.25)\';_mg.lineWidth=1;\nfor(var _i=0;_i<128;_i+=24){_mg.beginPath();_mg.moveTo(_i,0);_mg.lineTo(_i,128);_mg.stroke();}\nvar _gMT=new THREE.CanvasTexture(_gMCv);'
if old in html:
    html = html.replace(old, new)
    changes += 1
    print("  [9] Gun mag texture upgraded to 128x128 with ridges")

print(f"\n  Total HTML changes applied: {changes}")

# --- Save the updated HTML ---
with open(HTML_DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n=== Updated HTML saved to {HTML_DST} ===")

# Verify
with open(HTML_DST, 'r') as f:
    content = f.read()
    checks = {
        'Local Three.js': 'fps-game-assets/three.min.js' in content,
        'STEP_UP=0.55': 'STEP_UP = 0.55' in content,
        'checkEnemyWall fixed': 'c.maxY < -0.5' in content,
        'Zombie skin 512': 'cv.width=512;cv.height=512' in content,
    }
    print("\n=== Verification ===")
    for name, ok in checks.items():
        print(f"  {'✓' if ok else '✗'} {name}")

print(f"\n=== Files in {ASSETS_DIR} ===")
for f in sorted(os.listdir(ASSETS_DIR)):
    size = os.path.getsize(os.path.join(ASSETS_DIR, f))
    print(f"  {f} ({size:,} bytes)")
