---
name: xpression-3d-import
description: Bring 3D models and animation into Ross XPression from Blender, Maya, 3ds Max, Houdini, SketchUp, CAD or Cinema 4D. Use when choosing an export format, preparing a model so it imports cleanly (materials, scale, axes, pivots), or converting 3D animation into something XPression can play.
---

# 3D assets into XPression

## What XPression imports

| Format | Use for | Notes |
|---|---|---|
| **FBX** | Static models with materials from any 3D app | Ross supports importing FBX models with their baked-in materials. |
| **OBJ** (+MTL) | The most compatible static mesh route | Simple materials. Textures sit next to the file. |
| **OBJ sequence** | Mesh / vertex animation | One OBJ per frame. XPression treats the sequence as an animated object. |
| **3DS** | Legacy static models | Old format with limits on texture names and polygon counts. Prefer FBX or OBJ. |
| **C4D** | Cinema 4D scenes | 64-bit XPression imports models, materials, lights and cameras. |

Transform animation (position, rotation, scale) is usually best **rebuilt inside XPression** with its own keyframes, so producers can change it. Bake to an OBJ sequence only for deformation that XPression can't do itself.

## By source application

- **Blender**: run `tools/blender_export_xpression.py` (FBX, OBJ or OBJ sequence; Y-up, −Z forward, modifiers applied, triangulated, textures copied):
  ```bash
  blender scene.blend --background --python tools/blender_export_xpression.py -- --out D:/XPN/Assets/Trophy --mode fbx
  blender scene.blend --background --python tools/blender_export_xpression.py -- --out D:/XPN/Assets/Ribbon --mode objseq --start 1 --end 120
  ```
- **Maya / 3ds Max / MotionBuilder**: File → Export → FBX. Turn on Embed Media, Triangulate and Smoothing Groups. Turn off leaf bones and animation (for static models), and set Up Axis to Y. In 3ds Max, use groups to organise parts. Each group becomes something you can animate in XPression.
- **Houdini**: ROP FBX Output (static), or ROP Geometry with `$F4` in the file name for an OBJ sequence.
- **SketchUp / CAD (STEP, IGES, Revit …)**: convert to a mesh first (Blender, or a converter such as Pixyz or Asset Transformer), then decimate and export FBX or OBJ. CAD exports are often millions of polygons, so decimate hard for real-time playout.
- **glTF / GLB / USD / Collada (DAE)**: import into Blender, then export FBX or OBJ with the script above.
- **Cinema 4D**: import `.c4d` directly in 64-bit XPression, or export FBX if you're targeting older or 32-bit systems.

## Make it import cleanly

1. **Apply transforms** (scale = 1, rotation = 0), and put the pivot where XPression should rotate the object.
2. **Units**: XPression scenes work in pixels, so expect to scale imports up. Export at real-world size and adjust scale in XPression, or pass `--scale` in the Blender script.
3. **Materials**: give each part its own named material, and bake procedural or node shaders to image textures. Keep textures as PNG or JPG with **short, plain file names** in the same folder.
4. **Geometry**: triangulate, remove hidden or internal faces, and keep counts sensible. Many objects in a scene all render every frame.
5. **Naming**: name parts clearly (`Trophy_Base`, `Trophy_Cup`). Those names become the XPression objects you animate and publish.
6. **Normals**: recalculate them outside and use auto-smooth or face smoothing so edges stay crisp.

## In XPression after import

- Re-assign or upgrade materials: reflections (`ReflectionMap2D` with an HDRI), refraction, brand colours. Sharing a material across objects makes later recolouring a one-line edit (see `xpression-project-edit`).
- Add lights. Imported scenes often arrive dark.
- Animate in XPression and publish the parts the producer needs to control.

## Check the result

- Open the imported object in XPression's Object Manager and confirm part names, material count and polygon load (watch the Perf meter).
- Check the error/status list for missing textures. That's nearly always a path or file-name problem.
