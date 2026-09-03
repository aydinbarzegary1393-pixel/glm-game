#!/usr/bin/env python3
"""Comprehensive FPS game update - all requested features."""

with open('/home/z/my-project/download/fps-game.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove external image URLs - CSS gradients for offline
c = c.replace(
    "background:url('https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/c021ed7594c0.png') center/cover no-repeat",
    "background:linear-gradient(135deg,#0a0e1a 0%,#1a1a2e 30%,#16213e 60%,#0f3460 100%)"
)

# 2. Add victory screen + medkit CSS
extra_css = """
/* Victory Screen */
#victory-screen{position:fixed;inset:0;z-index:300;display:flex;align-items:center;justify-content:center;flex-direction:column;background:rgba(0,40,0,0.88)}
#victory-screen.hidden{display:none}
#victory-screen h2{font-size:58px;color:#2ecc71;margin-bottom:10px;letter-spacing:8px;text-shadow:0 0 40px rgba(46,204,113,0.6),0 0 80px rgba(46,204,113,0.3)}
#victory-screen .victory-sub{color:rgba(150,255,150,0.6);font-size:14px;margin-bottom:35px;letter-spacing:2px}
#victory-screen .pause-btn{width:280px}
/* Medkit Notify */
#medkit-notify{position:fixed;top:55px;left:50%;transform:translateX(-50%);z-index:55;pointer-events:none;color:#2ecc71;font-size:20px;font-weight:700;letter-spacing:2px;text-shadow:0 0 10px rgba(46,204,113,0.6);opacity:0;transition:opacity 0.3s}
#medkit-notify.show{opacity:1}
"""
c = c.replace('</style>', extra_css + '</style>')

# 3. Add victory screen HTML
victory_html = """
<!-- VICTORY SCREEN -->
<div id="victory-screen" class="hidden">
<div style="position:relative;z-index:1;text-align:center">
<h2 data-en="YOU WON!" data-fa="&#x062A;&#x0648; &#x0628;&#x0631;&#x062F;&#x06CC;!">YOU WON!</h2>
<p class="victory-sub" data-en="ALL ENEMIES ELIMINATED" data-fa="&#x0647;&#x0645;&#x0647; &#x062F;&#x0634;&#x0645;&#x0646;&#x0627;&#x0646; &#x0646;&#x0627;&#x0628;&#x0648;&#x062F; &#x0634;&#x062F;&#x0646;&#x062F;">ALL ENEMIES ELIMINATED</p>
<button class="pause-btn" onclick="restartGame()" data-en="PLAY AGAIN" data-fa="&#x0628;&#x0627;&#x0632;&#x06CC; &#x062F;&#x0648;&#x0628;&#x0627;&#x0631;&#x0647;">PLAY AGAIN</button>
<button class="pause-btn exit-btn" onclick="backToMenuFromVictory()" data-en="MAIN MENU" data-fa="&#x0645;&#x0646;&#x0648;&#x06CC; &#x0627;&#x0635;&#x0644;&#x06CC;">MAIN MENU</button>
</div>
</div>

<!-- MEDKIT NOTIFICATION -->
<div id="medkit-notify" data-en="+10 HEALTH" data-fa="+10 &#x0633;&#x0644;&#x0627;&#x0645;&#x062A;&#x06CC;">+10 HEALTH</div>
"""
c = c.replace('<!-- GAME HUD -->', victory_html + '\n<!-- GAME HUD -->')

# 4. Add kill counter + medkit variables
c = c.replace(
    'const enemies = [];',
    'const enemies = [];\nlet killCount = 0;\nconst medkits = [];\nconst MEDKIT_HEAL = 10;'
)

# 5. Replace enemy system with spawn zones + improved collision
old_check = '''// ===== ENEMY SYSTEM =====
function checkEnemyWall(px, pz) {
  var r = 0.5;
  for (var i = 0; i < colliders.length; i++) {
    var c = colliders[i];
    if (c.maxY - c.minY < 0.5) continue;
    if (c.maxY < 0.3 || c.minY > 2.2) continue;
    if (px + r > c.minX && px - r < c.maxX &&
        pz + r > c.minZ && pz - r < c.maxZ) return true;
  }
  return false;
}'''

new_check = '''// ===== ENEMY SYSTEM =====
const mapSpawnZones = [
  [{x1:-18,z1:-18,x2:18,z2:18}],
  [{x1:-5,z1:-35,x2:5,z2:-25},{x1:-13,z1:-12,x2:13,z2:0},{x1:-1,z1:1,x2:3,z2:7},{x1:-4,z1:8,x2:7,z2:16},{x1:-10,z1:22,x2:10,z2:34}],
  [{x1:-14,z1:-3,x2:3,z2:8},{x1:-9,z1:8,x2:0,z2:28},{x1:5,z1:1,x2:12,z2:16},{x1:10,z1:16,x2:26,z2:28},{x1:1,z1:-2,x2:14,z2:6}],
  [{x1:-15,z1:-20,x2:15,z2:20}]
];

function checkEnemyWall(px, pz) {
  var r = 0.5;
  for (var i = 0; i < colliders.length; i++) {
    var c = colliders[i];
    if (c.maxY - c.minY < 0.5) continue;
    if (c.maxY < 0.1 || c.minY > 2.5) continue;
    if (px + r > c.minX && px - r < c.maxX &&
        pz + r > c.minZ && pz - r < c.maxZ) return true;
  }
  return false;
}

function isInsideMapZone(x, z) {
  var zones = mapSpawnZones[currentMap] || mapSpawnZones[0];
  for (var i = 0; i < zones.length; i++) {
    var zn = zones[i];
    if (x >= zn.x1 && x <= zn.x2 && z >= zn.z1 && z <= zn.z2) return true;
  }
  return false;
}'''

c = c.replace(old_check, new_check)

# 6. Replace spawnEnemies with zone-aware version + medkit functions
old_spawn = '''function spawnEnemies() {
  clearEnemies();
  var count = DIFFICULTY_COUNTS[difficulty];
  var px = player.position.x, pz = player.position.z;
  for (var i = 0; i < count; i++) {
    var angle, dist, ex, ez, attempts = 0;
    do {
      angle = (i / count) * Math.PI * 2 + Math.random() * 0.5;
      dist = 8 + Math.random() * 10;
      ex = px + Math.cos(angle) * dist;
      ez = pz + Math.sin(angle) * dist;
      ex = Math.max(-15, Math.min(15, ex));
      ez = Math.max(-15, Math.min(15, ez));
      attempts++;
    } while (checkEnemyWall(ex, ez) && attempts < 10);
    createEnemy(ex, ez);
  }
}'''

new_spawn = '''function spawnEnemies() {
  clearEnemies();
  clearMedkits();
  killCount = 0;
  var count = DIFFICULTY_COUNTS[difficulty];
  var zones = mapSpawnZones[currentMap] || mapSpawnZones[0];
  var px = player.position.x, pz = player.position.z;
  for (var i = 0; i < count; i++) {
    var ex, ez, attempts = 0, valid = false;
    do {
      var zone = zones[Math.floor(Math.random() * zones.length)];
      ex = zone.x1 + Math.random() * (zone.x2 - zone.x1);
      ez = zone.z1 + Math.random() * (zone.z2 - zone.z1);
      if (!checkEnemyWall(ex, ez)) {
        var dx = ex - px, dz = ez - pz;
        if (Math.sqrt(dx*dx + dz*dz) >= 6) valid = true;
      }
      attempts++;
    } while (!valid && attempts < 50);
    if (valid) createEnemy(ex, ez);
  }
}

function clearMedkits() {
  for (var i = medkits.length - 1; i >= 0; i--) {
    scene.remove(medkits[i].group);
    medkits[i].group.traverse(function(ch) {
      if (ch.geometry) ch.geometry.dispose();
      if (ch.material) ch.material.dispose();
    });
  }
  medkits.length = 0;
}

function dropMedkit(x, z) {
  var mkGroup = new THREE.Group();
  var boxMat = new THREE.MeshStandardMaterial({color:0x2ecc71, roughness:0.4, metalness:0.1});
  var boxMesh = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.35, 0.5), boxMat);
  boxMesh.position.y = 0.175; mkGroup.add(boxMesh);
  var crossMat = new THREE.MeshBasicMaterial({color:0xffffff});
  var crossH = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.02, 0.08), crossMat);
  crossH.position.y = 0.36; mkGroup.add(crossH);
  var crossV = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.02, 0.3), crossMat);
  crossV.position.y = 0.36; mkGroup.add(crossV);
  var edgeMat = new THREE.MeshStandardMaterial({color:0xe74c3c, roughness:0.5});
  var edge1 = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.02, 0.52), edgeMat);
  edge1.position.y = 0.35; mkGroup.add(edge1);
  mkGroup.position.set(x, 0, z);
  scene.add(mkGroup);
  medkits.push({group: mkGroup});
}

function updateMedkits() {
  var px = player.position.x, pz = player.position.z;
  for (var i = medkits.length - 1; i >= 0; i--) {
    var mk = medkits[i];
    mk.group.position.y = 0.1 + Math.sin(Date.now() * 0.003) * 0.05;
    mk.group.rotation.y += 0.02;
    var dx = px - mk.group.position.x;
    var dz = pz - mk.group.position.z;
    if (Math.sqrt(dx*dx + dz*dz) < 1.2) {
      if (playerHealth < MAX_HEALTH) {
        playerHealth = Math.min(MAX_HEALTH, playerHealth + MEDKIT_HEAL);
        updateHealthBar();
        var notify = document.getElementById('medkit-notify');
        notify.classList.add('show');
        setTimeout(function() { notify.classList.remove('show'); }, 1200);
      }
      scene.remove(mk.group);
      mk.group.traverse(function(ch) {
        if (ch.geometry) ch.geometry.dispose();
        if (ch.material) ch.material.dispose();
      });
      medkits.splice(i, 1);
    }
  }
}'''

c = c.replace(old_spawn, new_spawn)

# 7. Improve zombie textures (256x256)
old_ztex = """// Zombie skin texture
var _zCanvas = document.createElement('canvas'); _zCanvas.width=128; _zCanvas.height=128;
var _zCtx = _zCanvas.getContext('2d');
_zCtx.fillStyle='#6b8a5e'; _zCtx.fillRect(0,0,128,128);
for(var _i=0;_i<800;_i++){var _v=0.6+Math.random()*0.5;_zCtx.fillStyle='rgba('+Math.floor(80*_v)+','+Math.floor(100*_v)+','+Math.floor(60*_v)+',0.4)';_zCtx.fillRect(Math.random()*128,Math.random()*128,2+Math.random()*6,2+Math.random()*6)}
for(var _i=0;_i<400;_i++){var _v=0.9+Math.random()*0.3;_zCtx.fillStyle='rgba('+Math.floor(140*_v)+','+Math.floor(160*_v)+','+Math.floor(120*_v)+',0.3)';_zCtx.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*4,1+Math.random()*4)}
_zCtx.strokeStyle='rgba(50,70,40,0.2)';_zCtx.lineWidth=1;
for(var _i=0;_i<15;_i++){_zCtx.beginPath();var _sx=Math.random()*128,_sy=Math.random()*128;_zCtx.moveTo(_sx,_sy);for(var _j=0;_j<3;_j++){_sx+=(Math.random()-0.5)*30;_sy+=Math.random()*20;_zCtx.lineTo(_sx,_sy)}_zCtx.stroke()}
tex.zombieSkin=(function(){var t=new THREE.CanvasTexture(_zCanvas);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t})();

// Zombie dark skin (limbs)
var _zdCanvas=document.createElement('canvas');_zdCanvas.width=64;_zdCanvas.height=64;
var _zdCtx=_zdCanvas.getContext('2d');
_zdCtx.fillStyle='#4a6a3a';_zdCtx.fillRect(0,0,64,64);
for(var _i=0;_i<600;_i++){var _v=0.5+Math.random()*0.5;_zdCtx.fillStyle='rgba('+Math.floor(60*_v)+','+Math.floor(85*_v)+','+Math.floor(45*_v)+',0.4)';_zdCtx.fillRect(Math.random()*64,Math.random()*64,2+Math.random()*5,2+Math.random()*5)}
tex.zombieDark=(function(){var t=new THREE.CanvasTexture(_zdCanvas);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t})();"""

new_ztex = """// Zombie skin texture (HQ 256x256)
tex.zombieSkin=(function(){
  var cv=document.createElement('canvas');cv.width=256;cv.height=256;
  var ctx=cv.getContext('2d');
  ctx.fillStyle='#5a7a4a';ctx.fillRect(0,0,256,256);
  for(var i=0;i<3000;i++){var v=0.5+Math.random()*0.6;ctx.fillStyle='rgba('+Math.floor(75*v)+','+Math.floor(105*v)+','+Math.floor(55*v)+',0.35)';ctx.fillRect(Math.random()*256,Math.random()*256,3+Math.random()*12,3+Math.random()*12);}
  for(var i=0;i<1500;i++){var v=0.8+Math.random()*0.4;ctx.fillStyle='rgba('+Math.floor(120*v)+','+Math.floor(150*v)+','+Math.floor(95*v)+',0.25)';ctx.fillRect(Math.random()*256,Math.random()*256,2+Math.random()*8,2+Math.random()*8);}
  ctx.strokeStyle='rgba(35,55,25,0.3)';ctx.lineWidth=1.5;
  for(var i=0;i<30;i++){ctx.beginPath();var sx=Math.random()*256,sy=Math.random()*256;ctx.moveTo(sx,sy);for(var j=0;j<5;j++){sx+=(Math.random()-0.5)*40;sy+=Math.random()*25;ctx.lineTo(sx,sy);}ctx.stroke();}
  for(var i=0;i<20;i++){ctx.fillStyle='rgba(80,30,20,0.3)';ctx.beginPath();ctx.ellipse(Math.random()*256,Math.random()*256,4+Math.random()*8,3+Math.random()*6,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}
  for(var i=0;i<5000;i++){var v=0.6+Math.random()*0.4;ctx.fillStyle='rgba('+Math.floor(50*v)+','+Math.floor(70*v)+','+Math.floor(35*v)+',0.15)';ctx.fillRect(Math.random()*256,Math.random()*256,1,1);}
  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;
})();
// Zombie dark skin (HQ 256x256)
tex.zombieDark=(function(){
  var cv=document.createElement('canvas');cv.width=256;cv.height=256;
  var ctx=cv.getContext('2d');
  ctx.fillStyle='#3a5a2a';ctx.fillRect(0,0,256,256);
  for(var i=0;i<2500;i++){var v=0.4+Math.random()*0.6;ctx.fillStyle='rgba('+Math.floor(55*v)+','+Math.floor(80*v)+','+Math.floor(38*v)+',0.35)';ctx.fillRect(Math.random()*256,Math.random()*256,3+Math.random()*10,3+Math.random()*10);}
  for(var i=0;i<1000;i++){var v=0.3+Math.random()*0.4;ctx.fillStyle='rgba('+Math.floor(30*v)+','+Math.floor(50*v)+','+Math.floor(20*v)+',0.3)';ctx.fillRect(Math.random()*256,Math.random()*256,2+Math.random()*8,2+Math.random()*8);}
  ctx.strokeStyle='rgba(25,40,15,0.35)';ctx.lineWidth=1;
  for(var i=0;i<20;i++){ctx.beginPath();var sx=Math.random()*256,sy=Math.random()*256;ctx.moveTo(sx,sy);for(var j=0;j<4;j++){sx+=(Math.random()-0.5)*35;sy+=Math.random()*20;ctx.lineTo(sx,sy);}ctx.stroke();}
  for(var i=0;i<15;i++){ctx.fillStyle='rgba(60,20,15,0.4)';ctx.beginPath();ctx.ellipse(Math.random()*256,Math.random()*256,3+Math.random()*7,2+Math.random()*5,Math.random()*Math.PI,0,Math.PI*2);ctx.fill();}
  var t=new THREE.CanvasTexture(cv);t.wrapS=THREE.RepeatWrapping;t.wrapT=THREE.RepeatWrapping;return t;
})();"""

c = c.replace(old_ztex, new_ztex)

# 8. Improve gun textures
old_gun = """// Main body
const gunBody = new THREE.Mesh(
  new THREE.BoxGeometry(0.08, 0.12, 0.5),
  new THREE.MeshStandardMaterial({color:0x2c2c2c, roughness:0.3, metalness:0.8})
);
gunGroup.add(gunBody);

// Barrel
const barrel = new THREE.Mesh(
  new THREE.BoxGeometry(0.04, 0.04, 0.35),
  new THREE.MeshStandardMaterial({color:0x1a1a1a, roughness:0.2, metalness:0.9})
);
barrel.position.set(0, 0.02, -0.35);
gunGroup.add(barrel);

// Handle/grip
const grip = new THREE.Mesh(
  new THREE.BoxGeometry(0.07, 0.18, 0.08),
  new THREE.MeshStandardMaterial({color:0x3d2b1f, roughness:0.8, metalness:0.1})
);
grip.position.set(0, -0.13, 0.1);
grip.rotation.x = 0.2;
gunGroup.add(grip);

// Magazine
const mag = new THREE.Mesh(
  new THREE.BoxGeometry(0.06, 0.15, 0.06),
  new THREE.MeshStandardMaterial({color:0x333333, roughness:0.4, metalness:0.7})
);
mag.position.set(0, -0.12, -0.02);
gunGroup.add(mag);

// Sight
const sight = new THREE.Mesh(
  new THREE.BoxGeometry(0.03, 0.04, 0.03),
  new THREE.MeshStandardMaterial({color:0x1a1a1a, roughness:0.3, metalness:0.9})
);
sight.position.set(0, 0.09, -0.15);
gunGroup.add(sight);"""

new_gun = """// Gun procedural textures
var _gBCv=document.createElement('canvas');_gBCv.width=256;_gBCv.height=256;
var _gb=_gBCv.getContext('2d');_gb.fillStyle='#2c2c2c';_gb.fillRect(0,0,256,256);
for(var _i=0;_i<3000;_i++){var _g=Math.floor(30+Math.random()*30);_gb.fillStyle='rgba('+_g+','+_g+','+_g+',0.2)';_gb.fillRect(Math.random()*256,Math.random()*256,1+Math.random()*3,1+Math.random()*2);}
_gb.strokeStyle='rgba(60,60,60,0.15)';_gb.lineWidth=1;
for(var _i=0;_i<256;_i+=32){_gb.beginPath();_gb.moveTo(_i,0);_gb.lineTo(_i,256);_gb.stroke();}
for(var _i=0;_i<256;_i+=32){_gb.beginPath();_gb.moveTo(0,_i);_gb.lineTo(256,_i);_gb.stroke();}
_gb.strokeStyle='rgba(80,80,80,0.3)';_gb.lineWidth=0.5;
for(var _i=0;_i<20;_i++){_gb.beginPath();_gb.moveTo(Math.random()*256,Math.random()*256);_gb.lineTo(Math.random()*256,Math.random()*256);_gb.stroke();}
var _gBT=new THREE.CanvasTexture(_gBCv);
var _gBrCv=document.createElement('canvas');_gBrCv.width=128;_gBrCv.height=128;
var _br=_gBrCv.getContext('2d');_br.fillStyle='#1a1a1a';_br.fillRect(0,0,128,128);
for(var _i=0;_i<2000;_i++){var _g=Math.floor(15+Math.random()*25);_br.fillStyle='rgba('+_g+','+_g+','+_g+',0.15)';_br.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*2,1+Math.random()*4);}
_br.strokeStyle='rgba(40,40,40,0.2)';_br.lineWidth=0.5;
for(var _i=0;_i<128;_i+=16){_br.beginPath();_br.moveTo(_i,0);_br.lineTo(_i,128);_br.stroke();}
var _gBrT=new THREE.CanvasTexture(_gBrCv);
var _gGCv=document.createElement('canvas');_gGCv.width=128;_gGCv.height=128;
var _gr=_gGC!Cv.getContext('2d');_gr.fillStyle='#3d2b1f';_gr.fillRect(0,0,128,128);
for(var _i=0;_i<2000;_i++){var _v=0.7+Math.random()*0.5;_gr.fillStyle='rgba('+Math.floor(61*_v)+','+Math.floor(43*_v)+','+Math.floor(31*_v)+',0.3)';_gr.fillRect(Math.random()*128,Math.random()*128,1+Math.random()*3,Math.random()*6);}
_gr.strokeStyle='rgba(25,18,12,0.4)';_gr.lineWidth=1.5;
for(var _i=0;_i<128;_i+=6){_gr.beginPath();_gr.moveTo(0,_i+Math.random()*2);_gr.lineTo(128,_i+Math.random()*2);_gr.stroke();}
var _gGT=new THREE.CanvasTexture(_gGCv);
var _gMCv=document.createElement('canvas');_gMCv.width=64;_gMCv.height=64;
var _mg=_gMCv.getContext('2d');_mg.fillStyle='#333333';_mg.fillRect(0,0,64,64);
for(var _i=0;_i<1000;_i++){var _g=Math.floor(35+Math.random()*30);_mg.fillStyle='rgba('+_g+','+_g+','+_g+',0.2)';_mg.fillRect(Math.random()*64,Math.random()*64,1+Math.random()*2,1+Math.random()*2);}
var _gMT=new THREE.CanvasTexture(_gMCv);

// Main body
const gunBody = new THREE.Mesh(
  new THREE.BoxGeometry(0.08, 0.12, 0.5),
  new THREE.MeshStandardMaterial({map:_gBT, roughness:0.3, metalness:0.8})
);
gunGroup.add(gunBody);

// Barrel
const barrel = new THREE.Mesh(
  new THREE.BoxGeometry(0.04, 0.04, 0.35),
  new THREE.MeshStandardMaterial({map:_gBrT, roughness:0.2, metalness:0.9})
);
barrel.position.set(0, 0.02, -0.35);
gunGroup.add(barrel);

// Handle/grip
const grip = new THREE.Mesh(
  new THREE.BoxGeometry(0.07, 0.18, 0.08),
  new THREE.MeshStandardMaterial({map:_gGT, roughness:0.8, metalness:0.1})
);
grip.position.set(0, -0.13, 0.1);
grip.rotation.x = 0.2;
gunGroup.add(grip);

// Magazine
const mag = new THREE.Mesh(
  new THREE.BoxGeometry(0.06, 0.15, 0.06),
  new THREE.MeshStandardMaterial({map:_gMT, roughness:0.4, metalness:0.7})
);
mag.position.set(0, -0.12, -0.02);
gunGroup.add(mag);

// Sight
const sight = new THREE.Mesh(
  new THREE.BoxGeometry(0.03, 0.04, 0.03),
  new THREE.MeshStandardMaterial({color:0x1a1a1a, roughness:0.3, metalness:0.9})
);
sight.position.set(0, 0.09, -0.15);
gunGroup.add(sight);"""

# Fix typo
new_gun = new_gun.replace('_gGC!Cv', '_gGCv')

c = c.replace(old_gun, new_gun)

# 9. Add kill tracking + medkit drop + victory in shoot()
old_death = """      if (enemy.health <= 0) {
        scene.remove(enemy.group);
        enemy.group.traverse(function(ch) {
          if (ch.geometry) ch.geometry.dispose();
          if (ch.material) ch.material.dispose();
        });
        var idx = enemies.indexOf(enemy);
        if (idx > -1) enemies.splice(idx, 1);
      }"""

new_death = """      if (enemy.health <= 0) {
        var dropX = enemy.group.position.x, dropZ = enemy.group.position.z;
        scene.remove(enemy.group);
        enemy.group.traverse(function(ch) {
          if (ch.geometry) ch.geometry.dispose();
          if (ch.material) ch.material.dispose();
        });
        var idx = enemies.indexOf(enemy);
        if (idx > -1) enemies.splice(idx, 1);
        killCount++;
        if (killCount % 2 === 0) dropMedkit(dropX, dropZ);
        if (enemies.length === 0) playerWin();
      }"""

c = c.replace(old_death, new_death)

# 10. Add playerWin + backToMenuFromVictory after playerDie
old_die = """function playerDie() {
  gameStarted = false;
  document.getElementById('death-screen').classList.remove('hidden');
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('debug').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'none';
  document.getElementById('reload-hud').style.display = 'none';
  if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
  if (document.pointerLockElement) document.exitPointerLock();
}"""

new_die = """function playerDie() {
  gameStarted = false;
  document.getElementById('death-screen').classList.remove('hidden');
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('debug').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'none';
  document.getElementById('reload-hud').style.display = 'none';
  if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
  if (document.pointerLockElement) document.exitPointerLock();
}

function playerWin() {
  gameStarted = false;
  document.getElementById('victory-screen').classList.remove('hidden');
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('debug').style.display = 'none';
  document.getElementById('reload-hud').style.display = 'none';
  if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
  if (document.pointerLockElement) document.exitPointerLock();
}

function backToMenuFromVictory() {
  document.getElementById('victory-screen').classList.add('hidden');
  clearEnemies(); clearMedkits(); exitToMenu();
}"""

c = c.replace(old_die, new_die)

# 11. Fix startGame
old_start = """function startGame() {
  clearMap();
  mapLoaders[currentMap]();
  document.querySelectorAll('.menu-overlay').forEach(m => m.classList.add('hidden'));
  pauseOvl.classList.add('hidden');
  document.getElementById('crosshair').style.display = 'block';
  document.getElementById('debug').style.display = 'block';
  gameStarted = true;
  ammo = maxAmmo;
  isReloading = false;
  reloadAnimTime = 0;
  gunGroup.rotation.z = 0;
  playerHealth = MAX_HEALTH;
  updateHealthBar();
  document.getElementById('reload-hud').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'flex';
  document.getElementById('death-screen').classList.add('hidden');
  yaw = 0; pitch = 0;
  player.position.set(0, PLAYER_HEIGHT, 0);
  player.rotation.y = 0;
  pitchObj.rotation.x = 0;
  if (isMobileDevice) {
    document.getElementById('mobile-controls').style.display = 'block';
    if (!joyStick) initJoystick();
  } else {
    renderer.domElement.requestPointerLock();
  }
  spawnEnemies();
}"""

new_start = """function startGame() {
  clearMap(); clearMedkits();
  mapLoaders[currentMap]();
  document.querySelectorAll('.menu-overlay').forEach(m => m.classList.add('hidden'));
  pauseOvl.classList.add('hidden');
  document.getElementById('crosshair').style.display = 'block';
  document.getElementById('debug').style.display = 'block';
  gameStarted = true;
  ammo = maxAmmo; isReloading = false; canShoot = true;
  reloadAnimTime = 0; gunGroup.rotation.z = 0;
  playerHealth = MAX_HEALTH; killCount = 0;
  updateHealthBar();
  document.getElementById('reload-hud').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'flex';
  document.getElementById('death-screen').classList.add('hidden');
  document.getElementById('victory-screen').classList.add('hidden');
  yaw = 0; pitch = 0;
  player.rotation.y = 0; pitchObj.rotation.x = 0;
  if (isMobileDevice) {
    document.getElementById('mobile-controls').style.display = 'block';
    if (!joyStick) initJoystick();
  } else {
    renderer.domElement.requestPointerLock();
  }
  spawnEnemies();
}"""

c = c.replace(old_start, new_start)

# 12. Fix exitToMenu
old_exit = """function exitToMenu() {
  gameStarted = false;
  pauseOvl.classList.add('hidden');
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('debug').style.display = 'none';
  document.getElementById('reload-hud').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'none';
  if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
  yaw = 0; pitch = 0;
  player.position.set(0, PLAYER_HEIGHT, 0);
  player.rotation.y = 0;
  pitchObj.rotation.x = 0;
  clearBulletHoles();
  clearEnemies();
  showMenu('main-menu');
}"""

new_exit = """function exitToMenu() {
  gameStarted = false;
  pauseOvl.classList.add('hidden');
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('debug').style.display = 'none';
  document.getElementById('reload-hud').style.display = 'none';
  document.getElementById('health-bar-container').style.display = 'none';
  document.getElementById('death-screen').classList.add('hidden');
  document.getElementById('victory-screen').classList.add('hidden');
  if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
  yaw = 0; pitch = 0;
  player.position.set(0, PLAYER_HEIGHT, 0);
  player.rotation.y = 0; pitchObj.rotation.x = 0;
  ammo = maxAmmo; isReloading = false; canShoot = true;
  reloadAnimTime = 0; gunGroup.rotation.z = 0;
  playerHealth = MAX_HEALTH; killCount = 0;
  updateHealthBar();
  clearBulletHoles(); clearEnemies(); clearMedkits();
  showMenu('main-menu');
}"""

c = c.replace(old_exit, new_exit)

# 13. Fix ESC handler
old_esc = """  if (e.code === 'Escape' && !isLocked && gameStarted) {
    gameStarted = false;
    pauseOvl.classList.add('hidden');
    document.getElementById('crosshair').style.display = 'none';
    document.getElementById('debug').style.display = 'none';
    document.getElementById('health-bar-container').style.display = 'none';
    if (isMobileDevice) document.getElementById('mobile-controls').style.display = 'none';
    yaw = 0; pitch = 0;
    player.position.set(0, PLAYER_HEIGHT, 0);
    player.rotation.y = 0;
    pitchObj.rotation.x = 0;
    clearBulletHoles();
    clearEnemies();
    showMenu('main-menu');
  }"""

new_esc = """  if (e.code === 'Escape' && !isLocked && gameStarted) {
    exitToMenu();
  }"""

c = c.replace(old_esc, new_esc)

# 14. Add updateMedkits in game loop
c = c.replace(
    '    // Update enemies\n    updateEnemies(dt);',
    '    // Update enemies\n    updateEnemies(dt);\n    // Update medkits\n    updateMedkits();'
)

# 15. Fix mousedown to check victory screen too
c = c.replace(
    "!e.target.closest('#death-screen')",
    "!e.target.closest('#death-screen')&&!e.target.closest('#victory-screen')"
)

# 16. Fix restartGame
c = c.replace(
    """function restartGame() {
  document.getElementById('death-screen').classList.add('hidden');
  startGame();
}""",
    """function restartGame() {
  document.getElementById('death-screen').classList.add('hidden');
  document.getElementById('victory-screen').classList.add('hidden');
  startGame();
}"""
)

# 17. Fix backToMenuFromDeath
c = c.replace(
    """function backToMenuFromDeath() {
  document.getElementById('death-screen').classList.add('hidden');
  clearEnemies();
  exitToMenu();
}""",
    """function backToMenuFromDeath() {
  document.getElementById('death-screen').classList.add('hidden');
  clearEnemies(); clearMedkits(); exitToMenu();
}"""
)

# 18. Open Vertigo passage wider
c = c.replace(
    "addWall(-5, 2.5, 1, 8, 5, 0.5, CONCRETE);\n  addWall(8, 2.5, 1, 10, 5, 0.5, CONCRETE);",
    "addWall(-7, 2.5, 1, 5, 5, 0.5, CONCRETE);\n  addWall(5, 2.5, 1, 12, 5, 0.5, CONCRETE);"
)

# Write output
with open('/home/z/my-project/download/fps-game.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("OK - All changes applied!")
print(f"File size: {len(c)} bytes, {c.count(chr(10))+1} lines")
