"""Export the selected Blender objects for Ross XPression.

Run inside Blender (Scripting tab, or headless):
    blender scene.blend --background --python blender_export_xpression.py -- --out D:/XPN/Assets/MyModel --mode fbx
    blender scene.blend --background --python blender_export_xpression.py -- --out D:/XPN/Assets/MyAnim  --mode objseq --start 1 --end 120

Modes
  fbx     single FBX with textures copied/embedded (static models with materials)
  obj     single OBJ + MTL + copied textures (most compatible static route)
  objseq  one OBJ per frame (XPression imports OBJ sequences for mesh animation)

Defaults favour XPression: Y-up, -Z forward, modifiers applied, triangulated, no leaf bones.
Check scale and orientation after import and adjust --scale if needed. Written from Blender
4.x APIs and not yet verified against every XPression build.
"""
import argparse, os, sys
import bpy


def args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True, help='output path without extension (folder is created)')
    p.add_argument('--mode', choices=['fbx', 'obj', 'objseq'], default='fbx')
    p.add_argument('--start', type=int, default=None)
    p.add_argument('--end', type=int, default=None)
    p.add_argument('--scale', type=float, default=1.0)
    return p.parse_args(argv)


def main():
    a = args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    if not bpy.context.selected_objects:
        for ob in bpy.context.view_layer.objects:
            if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}:
                ob.select_set(True)
    scene = bpy.context.scene

    if a.mode == 'fbx':
        bpy.ops.export_scene.fbx(
            filepath=a.out + '.fbx', use_selection=True, global_scale=a.scale,
            apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
            use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True,
            add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True)
    else:
        start = a.start if a.start is not None else scene.frame_start
        end = a.end if a.end is not None else scene.frame_end
        bpy.ops.wm.obj_export(
            filepath=a.out + '.obj', export_selected_objects=True, global_scale=a.scale,
            forward_axis='NEGATIVE_Z', up_axis='Y', apply_modifiers=True,
            export_triangulated_mesh=True, export_normals=True, export_uv=True,
            export_materials=True, path_mode='COPY',
            export_animation=(a.mode == 'objseq'), start_frame=start, end_frame=end)
    print('exported', a.mode, '->', a.out)


if __name__ == '__main__':
    main()
