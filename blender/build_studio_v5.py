
import bpy, math, os
from mathutils import Vector

# Start from v4 blend to keep arc towers + plaza, but rework wheel/void
prev = "/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports/studio-v4.blend"
bpy.ops.wm.open_mainfile(filepath=prev)
print("Loaded v4, reworking wheel/void for V5")
scene = bpy.context.scene

# --- Remove old wheel, spokes, sunburst, bridge for rebuild ---
to_remove = [o for o in bpy.data.objects if o.name.startswith("Ring") or o.name.startswith("Spoke") or o.name.startswith("Sunburst") or o.name.startswith("Cabin") or o.name=="SkyBridge" or o.name=="Hub"]
print(f"Removing {len(to_remove)} old wheel objects")
for o in to_remove:
    try: bpy.data.objects.remove(o, do_unlink=True)
    except: pass
# Remove associated lights
for o in list(bpy.data.objects):
    if "HubLight" in o.name or o.name.startswith("Cabin"):
        try: bpy.data.objects.remove(o, do_unlink=True)
        except: pass

def new_mat(name, base_color, metallic=0.0, roughness=0.5, emission_color=None, emission_strength=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(400,0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(0,0)
    def si(k,v):
        if k in bsdf.inputs: bsdf.inputs[k].default_value=v
    si('Base Color', base_color); si('Metallic', metallic); si('Roughness', roughness)
    if emission_color is not None and 'Emission Color' in bsdf.inputs:
        si('Emission Color', emission_color)
    if 'Emission Strength' in bsdf.inputs:
        si('Emission Strength', emission_strength)
    if emission_color is not None and 'Emission' in bsdf.inputs and 'Emission Color' not in bsdf.inputs:
        si('Emission', emission_color)
    try: nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    except: pass
    return mat

mat_ring_gold = bpy.data.materials.get("Ring_Gold") or new_mat("Ring_Gold", (1,0.86,0.34,1), 0.58, 0.28, emission_color=(1,0.60,0.10,1), emission_strength=2.8)
mat_ring_blue = bpy.data.materials.get("Ring_Blue") or new_mat("Ring_Blue", (0.68,0.82,1,1), 0.50, 0.30, emission_color=(0.20,0.52,1,1), emission_strength=2.6)
mat_truss = bpy.data.materials.get("Truss") or new_mat("Truss", (0.16,0.16,0.18,1), 0.38, 0.52)
mat_cabin = bpy.data.materials.get("Cabin_Gold") or new_mat("Cabin_Gold", (0.96,0.91,0.66,1), 0.20, 0.36)
mat_cabin_glass = bpy.data.materials.get("Cabin_Glass") or new_mat("Cabin_Glass", (0.18,0.30,0.58,1), 0.0, 0.08)
mat_hub = bpy.data.materials.get("Hub") or new_mat("Hub", (1,1,1,1), emission_color=(1,1,1,1), emission_strength=7.5)
mat_fin = bpy.data.materials.get("Fin_Bronze") or new_mat("Fin_Bronze", (0.72,0.62,0.46,1), 0.42, 0.36)
# Make gold more golden for hero wheel
mat_gold_hero = new_mat("GoldHero", (1,0.88,0.32,1), 0.72, 0.22, emission_color=(1,0.72,0.18,1), emission_strength=3.2)
try: mat_cabin_glass.blend_method='BLEND'
except: pass

# --- New wheel centered in void, bigger, thicker, floating ---
center = Vector((0, 0.8, 29.5))  # slightly higher for 130m hero feel
R = 14.2  # bigger than v4 12.0
tube = 0.72  # thicker

def make_ring(name, ctr, tilt_x, tilt_y, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=tube, major_segments=108, minor_segments=28, location=ctr)
    r=bpy.context.active_object; r.name=name; r.rotation_euler=(math.radians(tilt_x), math.radians(tilt_y), 0)
    r.data.materials.append(mat)
    # outer gold edge highlight: add second thinner torus for rim light
    wf=r.modifiers.new(name="Wire", type='WIREFRAME'); wf.thickness=0.070; wf.use_replace=False; wf.material_offset=1
    if len(r.data.materials)<2: r.data.materials.append(mat_truss)
    else: r.data.materials[1]=mat_truss
    return r

# Two rings interlocked figure-8, vertical offset larger for clarity
rA=make_ring("RingA_Gold", (center.x, center.y, center.z+8.6), 3, 6, mat_gold_hero)
rB=make_ring("RingB_Blue", (center.x, center.y, center.z-8.6), -3, -6, mat_ring_gold)  # both gold for hero look
# Make both gold-dominant (hero is gold), second ring slightly warm gold too

# Thicker rim tubes for hero pop: add outer emissive torus
for ctr in [(center.x, center.y, center.z+8.6), (center.x, center.y, center.z-8.6)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=R+0.22, minor_radius=0.18, major_segments=96, minor_segments=16, location=ctr)
    rim=bpy.context.active_object; rim.name=f"RimGlow_{ctr[2]:.0f}"
    rim.rotation_euler=(math.radians(3 if ctr[2]>center.z else -3), math.radians(6 if ctr[2]>center.z else -6), 0)
    rim.data.materials.append(new_mat(f"RimGlowMat_{ctr[2]:.0f}", (1,0.92,0.55,1), emission_color=(1,0.82,0.22,1), emission_strength=4.0))

# Sunburst - denser and longer for hero
for i in range(28):
    ang=(i/28)*math.pi*2
    x=math.cos(ang)*R*0.75; y=math.sin(ang)*R*0.75
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center.x+x*0.5, center.y+y*0.08, center.z+y*0.44))
    ray=bpy.context.active_object; ray.name=f"SunburstH_{i}"; ray.scale=(0.10,0.10,R*0.68)
    ray.rotation_euler=(math.radians(90),0,ang)
    ray.data.materials.append(mat_fin)

for ring_ctr, tilt, prefix in [((center.x,center.y,center.z+8.6),(3,6),"SpokeA"), ((center.x,center.y,center.z-8.6),(-3,-6),"SpokeB")]:
    for i in range(20):
        ang=(i/20)*math.pi*2
        x=math.cos(ang)*R; y=math.sin(ang)*R
        sx=ring_ctr[0]+x*0.5; sy=ring_ctr[1]+y*0.08; sz=ring_ctr[2]+y*0.44
        bpy.ops.mesh.primitive_cylinder_add(radius=0.068, depth=R, location=(sx, sy, sz))
        sp=bpy.context.active_object; sp.name=f"{prefix}_{i:02d}"
        sp.rotation_euler=(math.radians(90),0,ang)
        sp.data.materials.append(mat_truss)

# 17 cabins - larger, with transparent glass bottom
def cabin(name, x,y,z):
    # main capsule larger
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.78, location=(x,y,z))
    c=bpy.context.active_object; c.name=name; c.scale=(1,0.68,1.55)
    c.data.materials.append(mat_cabin)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+0.24, z+0.20))
    win=bpy.context.active_object; win.name=name+"_Win"; win.scale=(1.10,0.14,0.72)
    win.data.materials.append(mat_cabin_glass)
    # glass floor hint
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z-0.42))
    floor=bpy.context.active_object; floor.name=name+"_Floor"; floor.scale=(0.92,0.72,1)
    floor.rotation_euler=(0,0,0)
    floor.data.materials.append(mat_cabin_glass)
    return c

for i in range(9):
    ang=(i/9)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinA_{i:02d}", center.x+x*0.985, center.y+y*0.08, center.z+8.6+y)
for i in range(8):
    ang=(i/8)*math.pi*2 + math.pi/8; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinB_{i:02d}", center.x+x*0.985, center.y+y*0.08, center.z-8.6+y)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.05, location=center)
hub=bpy.context.active_object; hub.name="Hub"; hub.data.materials.append(mat_hub)
# floating bridge: thinner, not blocking wheel - set behind wheel
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.8, 25.2))
br=bpy.context.active_object; br.name="SkyBridge"; br.scale=(32,2.8,0.85); br.data.materials.append(mat_fin)

ld=bpy.data.lights.new(name="HubLightV5", type='POINT'); ld.energy=3200; ld.color=(1,1,1)
lo=bpy.data.objects.new(name="HubLightObjV5", object_data=ld); lo.location=center; bpy.context.collection.objects.link(lo)
# rim lights
for ctr in [(center.x, center.y, center.z+8.6), (center.x, center.y, center.z-8.6)]:
    ld2=bpy.data.lights.new(name=f"RimLight_{ctr[2]:.0f}", type='POINT'); ld2.energy=1800; ld2.color=(1,0.88,0.45)
    lo2=bpy.data.objects.new(name=f"RimLightObj_{ctr[2]:.0f}", object_data=ld2); lo2.location=ctr; bpy.context.collection.objects.link(lo2)

# Update camera to frame wheel as hero
cam = bpy.data.objects.get("PreviewCamObj")
if cam:
    cam.location=(48, -48, 32)
    direction=center - cam.location; cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera=cam

out_dir="/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports"
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"studio-v5.blend"))
glb=os.path.join(out_dir,"studio-v5.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    print(f"GLB v5 exported: {glb} size={os.path.getsize(glb)}")
except Exception as e:
    import traceback; traceback.print_exc()
print(f"Objects v5: {len(bpy.data.objects)}")
print("DONE V5")
