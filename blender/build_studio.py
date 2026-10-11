import bpy, bmesh, math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.resolution_x = 2048
scene.render.resolution_y = 2048
scene.render.film_transparent = True

def new_mat(name, base_color, metallic=0.0, roughness=0.5, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    def si(node, key, val):
        if key in node.inputs:
            node.inputs[key].default_value = val
    si(bsdf, 'Base Color', base_color)
    si(bsdf, 'Metallic', metallic)
    si(bsdf, 'Roughness', roughness)
    if emission_color is not None and 'Emission Color' in bsdf.inputs:
        si(bsdf, 'Emission Color', emission_color)
    if 'Emission Strength' in bsdf.inputs:
        si(bsdf, 'Emission Strength', emission_strength)
    if emission_color is not None and 'Emission' in bsdf.inputs and 'Emission Color' not in bsdf.inputs:
        si(bsdf, 'Emission', emission_color)
    try:
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    except Exception:
        pass
    return mat

def bevel(obj, width=0.08, segments=2):
    m = obj.modifiers.new(name="Bevel", type='BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(30)

mat_wall = new_mat("Wall_Cream", (0.94, 0.90, 0.82, 1), metallic=0.02, roughness=0.72)
mat_wall_gold = new_mat("Wall_Gold", (0.92, 0.82, 0.58, 1), metallic=0.08, roughness=0.62)
mat_fin = new_mat("Fin_Bronze", (0.68, 0.58, 0.42, 1), metallic=0.35, roughness=0.45)
mat_glass = new_mat("Glass_Blue", (0.18, 0.28, 0.62, 1), metallic=0.0, roughness=0.08)
try: mat_glass.blend_method = 'BLEND'
except: pass
mat_podium = new_mat("Podium_Stone", (0.88, 0.84, 0.78, 1), roughness=0.68)
mat_band = new_mat("Band_Light", (1, 1, 1, 1), emission_color=(1, 0.92, 0.55, 1), emission_strength=4.0)
mat_ring_gold = new_mat("Ring_Gold", (1, 0.86, 0.42, 1), metallic=0.55, roughness=0.28, emission_color=(1, 0.62, 0.12, 1), emission_strength=2.2)
mat_ring_blue = new_mat("Ring_Blue", (0.72, 0.84, 1, 1), metallic=0.45, roughness=0.32, emission_color=(0.25, 0.55, 1, 1), emission_strength=2.0)
mat_cabin = new_mat("Cabin_White", (0.96, 0.96, 0.98, 1), roughness=0.35, metallic=0.12)
mat_hub = new_mat("Hub", (1, 1, 1, 1), emission_color=(1, 1, 1, 1), emission_strength=6.0)
mat_ground = new_mat("Ground_Asphalt", (0.08, 0.10, 0.14, 1), roughness=0.82)
mat_road = new_mat("Road", (0.11, 0.13, 0.18, 1), roughness=0.55, metallic=0.15)
mat_line = new_mat("Line", (1, 0.95, 0.62, 1), emission_color=(1, 0.78, 0.15, 1), emission_strength=1.5)

# ground
bpy.ops.mesh.primitive_plane_add(size=420, location=(0, 0, 0))
ground = bpy.context.active_object; ground.name = "Ground"; ground.data.materials.append(mat_ground)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.02))
road = bpy.context.active_object; road.name = "CotaiStrip_Road"; road.scale = (200, 20, 1)
road.data.materials.append(mat_road)

for i in range(-88, 92, 14):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(i, 0, 0.04))
    line = bpy.context.active_object; line.name = f"RoadMark_{i}"; line.scale = (5, 0.45, 1)
    line.data.materials.append(mat_line)

def build_tower(name, cx, cy, height=44):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 2.6))
    podium = bpy.context.active_object; podium.name = f"{name}_Podium"; podium.scale = (20, 20, 5.2)
    podium.data.materials.append(mat_podium); bevel(podium, 0.35, 2)
    col.objects.link(podium); bpy.context.scene.collection.objects.unlink(podium)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 5.35))
    band = bpy.context.active_object; band.name = f"{name}_Band"; band.scale = (20.6, 20.6, 0.55)
    band.data.materials.append(mat_band)
    col.objects.link(band); bpy.context.scene.collection.objects.unlink(band)
    levels = [(10.5, height*0.62), (8.4, height*0.28), (6.2, height*0.18)]
    z_base = 5.35
    for idx, (w, h) in enumerate(levels):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, z_base + h/2))
        blk = bpy.context.active_object; blk.name = f"{name}_Block_{idx}"; blk.scale = (w, w, h)
        blk.data.materials.append(mat_wall if idx==0 else mat_wall_gold)
        bevel(blk, 0.18, 2)
        col.objects.link(blk); bpy.context.scene.collection.objects.unlink(blk)
        if idx==0:
            for f in range(5):
                fx = cx + (f - 2) * 1.65
                bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, cy, z_base + h/2))
                fin = bpy.context.active_object; fin.name = f"{name}_Fin_{f}"; fin.scale = (0.32, w+0.6, h*0.92)
                fin.data.materials.append(mat_fin)
                col.objects.link(fin); bpy.context.scene.collection.objects.unlink(fin)
            for wy in range(9):
                wz = z_base + 2.8 + wy * 2.45
                for side in (-1, 1):
                    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx + side*(w/2+0.02), cy, wz))
                    win = bpy.context.active_object; win.name = f"{name}_Win_{wy}_{side}"; win.scale = (1, 5.2, 1.35)
                    win.rotation_euler = (0, math.radians(90 if side>0 else -90), 0)
                    win.data.materials.append(mat_glass)
                    col.objects.link(win); bpy.context.scene.collection.objects.unlink(win)
        z_base += h
    cz = z_base
    for k in range(3):
        s = 5.6 - k*1.2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz + 0.45))
        cr = bpy.context.active_object; cr.name = f"{name}_Crown_{k}"; cr.scale = (s, s, 0.9)
        cr.data.materials.append(mat_wall_gold); bevel(cr, 0.12, 2)
        col.objects.link(cr); bpy.context.scene.collection.objects.unlink(cr)
        cz += 0.95
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(cx, cy, cz + 0.6))
    pin = bpy.context.active_object; pin.name = f"{name}_Pinnacle"; pin.data.materials.append(mat_hub)
    col.objects.link(pin); bpy.context.scene.collection.objects.unlink(pin)
    return col

towerA = build_tower("Tower_A", -11.2, -4.2, 44)
towerB = build_tower("Tower_B", 11.2, -4.2, 41)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4.2, 23.2))
bridge = bpy.context.active_object; bridge.name = "SkyBridge"; bridge.scale = (24, 3.2, 1.1)
bridge.data.materials.append(mat_fin); bevel(bridge, 0.12, 2)

def create_ring(name, center, radius, tilt_x, tilt_y, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.42, major_segments=96, minor_segments=20, location=center)
    ring = bpy.context.active_object; ring.name = name; ring.rotation_euler = (math.radians(tilt_x), math.radians(tilt_y), 0)
    ring.data.materials.append(mat)
    wf = ring.modifiers.new(name="Wireframe", type='WIREFRAME')
    wf.thickness = 0.06; wf.use_replace = False; wf.material_offset = 1
    if len(ring.data.materials) < 2: ring.data.materials.append(mat)
    return ring

center = (0, -4.2, 26.5)
R = 11.2
ringA = create_ring("Ring_A_Gold", (center[0], center[1], center[2]+7.0), R, 7, 10, mat_ring_gold)
ringB = create_ring("Ring_B_Blue", (center[0], center[1], center[2]-7.0), R, -7, -10, mat_ring_blue)

def cabin_at(name, cx, cy, cz):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.52, location=(cx, cy, cz))
    cap = bpy.context.active_object; cap.name = name; cap.scale = (1, 0.78, 1.25)
    cap.data.materials.append(mat_cabin)
    return cap

n = 14
for i in range(n):
    ang = (i/n)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin_at(f"Cabin_A_{i:02d}", center[0]+x*0.985, center[1]+y*0.12, center[2]+7.0+y)
for i in range(n):
    ang = (i/n)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin_at(f"Cabin_B_{i:02d}", center[0]+x*0.985, center[1]+y*0.12, center[2]-7.0+y)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=center)
hub = bpy.context.active_object; hub.name="Hub"; hub.data.materials.append(mat_hub)
ld = bpy.data.lights.new(name="HubLight", type='POINT'); ld.energy=1800; ld.color=(1,1,1)
lo = bpy.data.objects.new(name="HubLightObj", object_data=ld); lo.location=center; bpy.context.collection.objects.link(lo)

cam_data = bpy.data.cameras.new(name="PreviewCam")
cam_obj = bpy.data.objects.new(name="PreviewCamObj", object_data=cam_data)
cam_obj.location=(38,-36,28)
direction = Vector(center) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

import os
out_dir = "/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports"
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"studio-city.blend"))
glb_out = os.path.join(out_dir,"studio-city.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb_out, export_format='GLB', export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    print(f"GLB exported: {glb_out}")
except Exception as e:
    print(f"GLB export failed: {e}")
    import traceback; traceback.print_exc()
print(f"Objects: {len(bpy.data.objects)}")
for o in bpy.data.objects:
    if o.type=='MESH': print(f"  MESH {o.name} verts={len(o.data.vertices)} polys={len(o.data.polygons)}")
print("DONE")
