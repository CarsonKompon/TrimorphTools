import bpy
import bmesh
import mathutils
import math
import json
import datetime
import struct
import os
import io
from .data_stream import *

# If this is not an empty string then it will output the object data to a json file at the given path
DEBUG_JSON = ""

def read_dma_skin(context, filepath):
    print("running read_dma_skin...")

    buffered_input_stream = io.BufferedReader(io.FileIO(filepath, mode="rb"))

    skin_type = read_short(buffered_input_stream)

    data = {}

    if(skin_type == 0):
        print("Static skin file found, loading...")
        data = read_static_skin(buffered_input_stream)
    elif(skin_type == 1):
        print("Shape skin file found, loading...")
        data = read_shape_skin(buffered_input_stream)
    elif(skin_type == 2):
        print("Bone skin file found, loading...")
        data = read_bone_skin(buffered_input_stream)
    else:
        print("Unknown skin file version found, aborting...")
        return {'CANCELLED'}

    if(DEBUG_JSON != ""):
        with open(DEBUG_JSON, "w") as f:
            json.dump(data, f, indent=4)

    if(data.get("vertex_coords") is None):
        print("No vertex coordinates found, aborting...")
        return {'CANCELLED'}

    create_mesh_from_skin(data, filepath)

    return {'FINISHED'}

def create_mesh_from_skin(data, filepath):

    texture_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(filepath)), os.path.pardir), os.path.pardir) + "\\texture\\"
    has_textures = os.path.exists(texture_path)
    if(has_textures):
        print("Found textures folder!")
    else:
        print("Textures folder not found!")

    material_count = len(data["materials"])
    material_verts = []
    material_faces = []
    material_texcoords = []
    anim_frame = 0
    for i in range(material_count):
        current_verts = []
        current_faces = []
        current_texcoords = []
        current_frame = data["vertex_coords"][0]
        for j in range(0, len(current_frame), 3):
            current_verts.append([-current_frame[j], current_frame[j+2], current_frame[j+1]])
        for j in range(len(data["face_indices"][i])):
            current_faces.append(data["face_indices"][i][j])
        for j in range(0, len(data["face_texcoords"][i]), 3):
            current_texcoords.append(data["face_texcoords"][i][j])
            current_texcoords.append(data["face_texcoords"][i][j+2])
            current_texcoords.append(data["face_texcoords"][i][j+1])
        material_verts.append(current_verts)
        material_faces.append(current_faces)
        material_texcoords.append(current_texcoords)
    for i in range(material_count):
        material = data["materials"][i]
        vertices = material_verts[i]
        faces = material_faces[i]
        texcoords = material_texcoords[i]
        mat_name = material["name"]
        mesh = bpy.data.meshes.new(mat_name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        object = bpy.data.objects.new(mat_name, mesh)
        if(has_textures and material["textured"]):
            tex_name = material["texture"].split('\\')[-1].split('.')[0]
            mat = bpy.data.materials.new(name=tex_name)
            mat.diffuse_color = (1, 1, 1, 1)
            mat.use_nodes = True
            mat_principled_bsdf = mat.node_tree.nodes.get("Principled BSDF")
            tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(texture_path + material["texture"])
            mat.node_tree.links.new(tex_node.outputs[0], mat_principled_bsdf.inputs[0])
            object.data.materials.append(mat)
        bpy.context.collection.objects.link(object)
        object.select_set(True)

        uv_layer = mesh.uv_layers.new(name="UVMap")
        mesh.uv_layers.active = uv_layer
        for face in mesh.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_layer.data[loop_idx].uv = texcoords[loop_idx]
        
        if(data.get("skeleton") is not None):
            bpy.context.view_layer.objects.active = object
            bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=object.matrix_world.translation, scale=(1, 1, 1))
            armature = bpy.data.armatures[-1]
            create_bone_hierarchy(data["skeleton"]["bones"], None, armature)
            print(armature)
            #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            ...

def create_bone_hierarchy(bones, parent, armature):
    for i in range(len(bones)):
        bone = bones[i]
        edit_bone = armature.edit_bones.new(bone["name"])
        bonePos = [bone["translation"][2], bone["translation"][1], -bone["translation"][0]]
        if(parent is not None):
            edit_bone.parent = parent
            edit_bone.head = parent.head + mathutils.Vector(bonePos)
        else:
            edit_bone.head = mathutils.Vector([0, 0, 0])
        edit_bone.tail = edit_bone.head + mathutils.Vector([0, 1, 0])
        if(len(bone["children"]) > 0):
            create_bone_hierarchy(bone["children"], edit_bone, armature)

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportDMA(Operator, ImportHelper):
    """Can import a Trimorph Engine Skin file"""
    bl_idname = "import_trimorph.skin_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Trimorph Engine Skin"

    # ImportHelper mixin class uses this
    filename_ext = ".dma"

    # filter_glob: StringProperty(
    #     default="*.txt",
    #     options={'HIDDEN'},
    #     maxlen=255,  # Max internal buffer length, longer would be clamped.
    # )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    # use_setting: BoolProperty(
    #     name="Example Boolean",
    #     description="Example Tooltip",
    #     default=True,
    # )

    # type: EnumProperty(
    #     name="Example Enum",
    #     description="Choose between two items",
    #     items=(
    #         ('OPT_A', "First Option", "Description one"),
    #         ('OPT_B', "Second Option", "Description two"),
    #     ),
    #     default='OPT_A',
    # )

    def execute(self, context):
        return read_dma_skin(context, self.filepath)





def read_skin_core(stream):
    data = {}
    data["skin_version"] = read_short(stream)
    if(data["skin_version"] != 266 and data["skin_version"] < 263):
        print("Unsupported SkinCore version " + str(data["skin_version"]) + ", aborting...")
        return {}
    else:
        data["timestamp"] = datetime.datetime.fromtimestamp(read_long(stream) / 1000).strftime('%Y-%m-%d %H:%M:%S')
        data["id"] = read_string(stream)
        print("Reading skin core for " + data["id"] + "...")
        data["cylinder_radius"] = read_short(stream)
        if(data["cylinder_radius"] == 0):
            data["cylinder_radius"] = 30
        data["cylinder_height"] = read_short(stream)
        data["box_width"] = read_short(stream)
        data["box_height"] = read_short(stream)
        data["box_depth"] = read_short(stream)
        data["sphere_radius"] = read_short(stream)
        if(read_bool(stream)):
            data["core_scale"] = [read_float(stream), read_float(stream), read_float(stream)]
        else:
            data["core_scale"] = "null"
        if(read_bool(stream)):
            data["core_rotation"] = [read_float(stream), read_float(stream), read_float(stream)]
        else:
            data["core_rotation"] = "null"
        if(read_bool(stream)):
            data["core_translation"] = [read_float(stream), read_float(stream), read_float(stream)]
        else:
            data["core_translation"] = "null"
        data["use_alpha_test"] = read_bool(stream)
        if(data["skin_version"] > 263):
            data["use_mirroring"] = read_bool(stream)
        if(data["skin_version"] < 265):
            thing = read_bool(stream)
            data["interpolation_type"] = 1 if thing else 2
        else:
            data["interpolation_type"] = read_int(stream)
        mat_count = read_short(stream)
        data["materials"] = []
        data["face_indices"] = []
        data["face_texcoords"] = []
        data["face_vertex_colors"] = []
        for i in range(mat_count):
            data["materials"].append(read_material(stream))
        for i in range(mat_count):
            new_count = read_short(stream)
            face_inds = []
            for j in range(0, new_count, 3):
                pos = [read_char(stream), read_char(stream), read_char(stream)]
                face_inds.append([pos[0], pos[2], pos[1]])
            data["face_indices"].append(face_inds)
        for i in range(mat_count):
            new_count = read_short(stream)
            face_texcoords = []
            for j in range(0, new_count, 2):
                face_texcoords.append([read_float(stream), read_float(stream)])
            data["face_texcoords"].append(face_texcoords)
        if(data["skin_version"] >= 266):
            for i in range(mat_count):
                new_count = read_short(stream)
                face_vertex_colors = []
                for j in range(0, new_count, 3):
                    pos = [read_float(stream), read_float(stream), read_float(stream)]
                    face_vertex_colors.append([pos[0], pos[1], pos[2]])
                data["face_vertex_colors"].append(face_vertex_colors)
        else:
            for i in range(mat_count):
                new_count = read_short(stream)
                face_vertex_colors = []
                for j in range(new_count):
                    face_vertex_colors.append(1.0)
        contact_point_count = read_short(stream)
        data["contact_points"] = []
        if(contact_point_count > 0):
            data["contact_points"].append(read_contact_point(stream))
        if(read_bool(stream)):
            data["lod"] = read_lod(stream)


    return data

def read_static_skin(stream):
    data = read_skin_core(stream)
    data["skin_type"] = 0
    data["static_version"] = read_short(stream)
    if(data["static_version"] != 258):
        print("Unsupported Static Skin version " + str(data["static_version"]) + ", aborting...")
        return {}
    else:
        print("Reading Static Skin version " + str(data["static_version"]) + "...")
        vertex_coord_count = read_short(stream)
        data["vertex_coords"] = [[]]
        for i in range(vertex_coord_count):
            data["vertex_coords"][0].append(read_float(stream))
    return data

def read_shape_skin(stream):
    data = read_skin_core(stream)
    data["skin_type"] = 1
    data["shape_version"] = read_short(stream)
    if(data["shape_version"] != 258):
        print("Unsupported Shape Skin version " + str(data["shape_version"]) + ", aborting...")
        return data
    else:
        print("Reading Shape Skin version " + str(data["shape_version"]) + "...")
        vertex_coord_count = read_short(stream)
        data["vertex_coords"] = []
        for i in range(vertex_coord_count):
            c = read_short(stream)
            coords = []
            if(c > 0):
                for j in range(c):
                    coords.append(read_float(stream))
                data["vertex_coords"].append(coords)
        data["default_fps"] = read_short(stream)
        animation_count = read_short(stream)
        if(animation_count > 0):
            data["animations"] = []
            for i in range(animation_count):
                data["animations"].append(read_animation(stream))
    return data

def read_bone_skin(stream):
    data = read_skin_core(stream)
    data["skin_type"] = 2
    data["bone_version"] = read_short(stream)
    if(data["bone_version"] != 1):
        print("Unsupported Bone Skin version " + str(data["bone_version"]) + ", aborting...")
        return data
    else:
        print("Reading Bone Skin version " + str(data["bone_version"]) + "...")
        vertex_coord_count = read_int(stream)
        data["vertex_coords"] = [[]]
        for i in range(vertex_coord_count):
            data["vertex_coords"][0].append(read_float(stream))
        data["skeleton"] = read_skeleton(stream)
        data["default_fps"] = read_short(stream)
        anim_sequence_count = read_short(stream)
        data["anim_sequences"] = []
        if(anim_sequence_count > 0):
            for i in range(anim_sequence_count):
                data["anim_sequences"].append(read_animation(stream))
    return data

def read_material(stream):
    material = {}
    material["material_version"] = read_short(stream)
    if(material["material_version"] != 257):
        print("Unsupported Material version " + str(material["material_version"]) + ", aborting...")
        return material
    else:
        material["name"] = read_string(stream)
        print("Reading Material " + material["name"] + "...")
        material["transparent"] = read_bool(stream)
        material["textured"] = read_bool(stream)
        if(material["textured"]):
            material["texture"] = read_string(stream)
    return material

def read_contact_point(stream):
    point = {}
    point["point_version"] = read_short(stream)
    if(point["point_version"] == 257):
        point["name"] = read_string(stream)
        print("Reading Contact Point " + point["name"] + "...")
        point["vertices"] = [read_short(stream), read_short(stream), read_short(stream)]
        if(read_bool(stream)):
            point["core_translation"] = [read_float(stream), read_float(stream), read_float(stream)]
        else:
            point["core_translation"] = "null"
        if(read_bool(stream)):
            point["core_rotation"] = [read_float(stream), read_float(stream), read_float(stream)]
        else:
            point["core_rotation"] = "null"
        point["sphere_radius"] = read_float(stream)
        anim_count = read_short(stream)
        point["has_animation"] = []
        point["animations"] = []
        point["rotations"] = []
        for i in range(anim_count):
            has_anim = read_bool(stream)
            point["has_animation"].append(has_anim)
            if(has_anim):
                point["animations"].append([read_float(stream), read_float(stream), read_float(stream)])
                point["rotations"].append([read_float(stream), read_float(stream), read_float(stream)])
    return point

def read_lod(stream):
    lod = {}
    lod["lod_version"] = read_short(stream)
    if(lod["lod_version"] != 258 and lod["lod_version"] != 257):
        print("Unsupported LOD version " + str(lod["lod_version"]) + ", aborting...")
        return {}
    else:
        print("Reading LOD with version " + str(lod["lod_version"]) + "...")
        lod["start_distance"] = read_float(stream)
        lod["end_distance"] = read_float(stream)
        lod["end_level"] = read_short(stream)
        lod["start_level"] = read_short(stream)
        if(lod["lod_version"] > 257):
            lod["frame_used"] = read_short(stream)
        texcoord_count = read_short(stream)
        for i in range(texcoord_count):
            lod["face_texcoords"].append(read_float(stream))
        face_vert_count = read_char(stream)
        for i in range(face_vert_count):
            inner_count = read_char(stream)
            thing = []
            for j in range(inner_count):
                thing.append(read_char(stream))
            lod["face_indices"].append(thing)
        face_ind_count = read_short(stream)
        for i in range(face_ind_count):
            inner_count = read_short(stream)
            thing = []
            for j in range(inner_count):
                thing.append(read_short(stream))
            lod["face_indices"].append(thing)
        lod_level_count = read_short(stream)
        for i in range(lod_level_count):
            lod["lod_levels"].append(read_lod_level(stream, i))
    return lod

def read_lod_level(stream, num):
    level = {}
    level["lod_level_version"] = read_short(stream)
    if(level["lod_level_version"] != 257):
        print("Unsupported LODLevel version " + str(level["lod_level_version"]) + ", aborting...")
        return {}
    else:
        print("Reading LODLevel with version " + str(level["lod_level_version"]) + "...")
        level["level"] = num
        count = read_short(stream)
        if(count != 0):
            level["levels"] = []
            for i in range(count):
                lvl = {}
                lvl["a"] = read_byte(stream)
                lvl["b"] = read_short(stream)
                lvl["c"] = read_short(stream)
                if(lvl["a"] & 1 != 0):
                    lvl["aa"] = read_short(stream)
                    lvl["bb"] = [read_float(stream), read_float(stream)]
                if(lvl["a"] & 2 != 0):
                    lvl["aa"] = read_short(stream)
                    lvl["cc"] = read_char(stream)
                level["levels"].append(lvl)
    return level

def read_animation(stream):
    anim = {}
    anim["animation_version"] = read_short(stream)
    if(anim["animation_version"] != 258):
        print("Unsupported AnimationSequence version " + str(anim["animation_version"]) + ", aborting...")
        return {}
    else:
        anim["name"] = read_string(stream)
        anim["description"] = read_string(stream)
        print("Reading AnimationSequence " + anim["name"] + " (" + anim["description"] + ")...")
        anim["from_frame"] = read_short(stream)
        anim["to_frame"] = read_short(stream)
        anim["front_speed"] = read_float(stream)
        anim["side_speed"] = read_float(stream)
        anim["eye_level"] = read_short(stream)
        anim["camera_level"] = read_short(stream)
        anim["framerate"] = read_short(stream)
    return anim

def read_skeleton(stream):
    skeleton = {}
    bone_count = read_short(stream)
    print("Reading skeleton with " + str(bone_count) + " bones...")
    skeleton["bones"] = []
    for i in range(bone_count):
        skeleton["bones"].append(read_bone(stream))
    return skeleton

def read_bone(stream):
    bone = {}
    bone["id"] = read_int(stream)
    print("Reading bone " + str(bone["id"]) + "...")
    bone["name"] = read_string(stream)
    bone_weight_count = read_short(stream)
    bone["weights"] = []
    for i in range(bone_weight_count):
        bone["weights"].append(read_float(stream))
    vert_count = read_short(stream)
    bone["vertices"] = []
    for i in range(vert_count):
        bone["vertices"].append(read_int(stream))
    bone["scale"] = [read_float(stream), read_float(stream), read_float(stream)]
    bone["rotation"] = [read_float(stream), read_float(stream), read_float(stream), read_float(stream)]
    bone["translation"] = [read_float(stream), read_float(stream), read_float(stream)]
    child_count = read_short(stream)
    bone["children"] = []
    for i in range(child_count):
        bone["children"].append(read_bone(stream))
    bone["animation"] = read_bone_animation(stream)
    return bone

def read_bone_animation(stream):
    bone_anim = {}
    print("Reading bone animation...")
    scale_count = read_short(stream)
    bone_anim["scales"] = []
    for i in range(scale_count):
        bone_anim["scales"].append([read_float(stream), read_float(stream), read_float(stream)])
    rotation_count = read_short(stream)
    bone_anim["rotations"] = []
    for i in range(rotation_count):
        bone_anim["rotations"].append([read_float(stream), read_float(stream), read_float(stream), read_float(stream)])
    translation_count = read_short(stream)
    bone_anim["translations"] = []
    for i in range(translation_count):
        bone_anim["translations"].append([read_float(stream), read_float(stream), read_float(stream)])
    return bone_anim