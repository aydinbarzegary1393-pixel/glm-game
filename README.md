# FPS Game - Three.js Single-File Shooter

A first-person shooter game built entirely in a single HTML file using Three.js r128.

## Features
- 4 Maps: Test, Vertigo, Dust 2, Shoot House
- Zombie enemies with AI pathfinding and wall collision
- Procedural high-quality textures (no external images needed)
- Gun with reload animation and recoil
- Health system with damage flash
- Medkit drops (every 2 kills)
- Victory screen when all enemies eliminated
- Mobile touch controls support
- Persian/English language support
- Difficulty levels: Easy, Medium, Hard, Impossible

## Offline Play
This game works fully offline! All textures are generated procedurally in JavaScript. The only external file needed is `fps-game-assets/three.min.js` (Three.js r128).

## How to Play
1. Open `fps-game.html` in a modern web browser
2. Make sure `fps-game-assets/` folder is next to the HTML file
3. Choose your device (PC/Mobile)
4. Select a map and start playing!

### Controls (PC)
- **WASD** - Move
- **Mouse** - Look around
- **Left Click** - Shoot
- **R** - Reload
- **Space** - Jump
- **ESC** - Pause/Menu

## File Structure
```
fps-game.html              - Main game file (single HTML)
fps-game-assets/
  three.min.js             - Three.js r128 library
  tex_*.png                - Texture reference files (optional)
```
