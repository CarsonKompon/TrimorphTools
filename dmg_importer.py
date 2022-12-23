import bpy
import bmesh
import datetime
import gzip
import struct
import os
from io import BufferedReader

def read_dmg_locale(context, filepath):
    print("running read_dmg_locale...")

    file_input_stream = open(filepath, "rb")
    gzip_input_stream = gzip.GzipFile(fileobj=file_input_stream, mode='rb')
    buffered_input_stream = BufferedReader(gzip_input_stream)

    data_version = read_short(buffered_input_stream)

    data = {}

    if(data_version >= 1297):
        print("Cell file found, loading...")
        data = get_map_data_from_cell(buffered_input_stream, data_version)
    else:
        print("Map file found, loading...")
        data = get_map_data(buffered_input_stream, data_version, filepath)

    create_mesh_from_map(data, filepath)

    return {'FINISHED'}

def create_mesh_from_map(data, filepath):
    
    cells = data["cells"]

    for cell in cells:

        vertices = cell["vertex"]
        texcoord = cell["texcoord"]

        # Get the faces
        faces = []
        face_verts = []
        face_texcoords = []
        current_face = 0
        for j in range(len(cell["texture_list"])):
            faces.append([])
            face_verts.append([])
            face_texcoords.append([])
        j = 0
        count = 0
        for k in range(0, len(vertices), 3):
            if(current_face < len(cell["texture_list"])-1 and j == cell["face_start"][current_face + 1]):
                current_face += 1
                count = 0
            faces[current_face].append([count+0, count+1, count+2])
            face_verts[current_face].append(vertices[k+0])
            face_verts[current_face].append(vertices[k+1])
            face_verts[current_face].append(vertices[k+2])
            for l in [0, 2, 1]:
                if(k+l < len(texcoord)):
                    face_texcoords[current_face].append(texcoord[k+l])
                else:
                    face_texcoords[current_face].append([0, 0])
            count += 3
            j += 1

        # Get the textures
        texture_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(filepath)), os.path.pardir), os.path.pardir) + "\\texture\\"
        has_textures = os.path.exists(texture_path)
        if(has_textures):
            print("Found textures folder!")
        else:
            print("Textures folder not found!")

        for i in range(0, len(cell["texture_list"])):
            tex_name = cell["texture_list"][i].split('\\')[-1].split('.')[0]
            mesh = bpy.data.meshes.new(tex_name)
            mesh.from_pydata(face_verts[i], [], faces[i])
            mesh.update()
            object = bpy.data.objects.new(tex_name, mesh)
            if(has_textures):
                material = bpy.data.materials.new(name=tex_name)
                material.diffuse_color = (1, 1, 1, 1)
                material.use_nodes = True
                mat_principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
                tex_node = material.node_tree.nodes.new("ShaderNodeTexImage")
                tex_node.image = bpy.data.images.load(texture_path + cell["texture_list"][i])
                material.node_tree.links.new(tex_node.outputs[0], mat_principled_bsdf.inputs[0])
                object.data.materials.append(material)
            bpy.context.collection.objects.link(object)
            object.select_set(True)
            object.scale = (0.01, 0.01, 0.01)
            uv_layer = mesh.uv_layers.new(name="UVMap")
            mesh.uv_layers.active = uv_layer
            for face in mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_layer.data[loop_idx].uv = face_texcoords[i][loop_idx]
        

        alpha_vertices = cell["alpha_vertex"]
        alpha_texcoord = cell["alpha_texcoord"]

        # Get the faces
        alpha_faces = []
        alpha_face_verts = []
        alpha_face_texcoords = []
        alpha_current_face = 0
        for j in range(len(cell["alpha_texture_list"])):
            alpha_faces.append([])
            alpha_face_verts.append([])
            alpha_face_texcoords.append([])
        j = 0
        count = 0
        nextStart = 0
        if(len(cell["alpha_texture_list"]) >= 1):
            nextStart = cell["alpha_face_count"][0]
        for k in range(0, len(alpha_vertices), 3):
            if(j == nextStart):
                alpha_current_face += 1
                if(alpha_current_face >= len(cell["alpha_texture_list"])-1):
                    nextStart += 9999999
                else:
                    nextStart += cell["alpha_face_count"][alpha_current_face + 1]
                count = 0
            alpha_faces[alpha_current_face].append([count, count+1, count+2])
            alpha_face_verts[alpha_current_face].append(alpha_vertices[k])
            alpha_face_verts[alpha_current_face].append(alpha_vertices[k+1])
            alpha_face_verts[alpha_current_face].append(alpha_vertices[k+2])
            for l in range(0, 3):
                if(k+l < len(alpha_texcoord)):
                    alpha_face_texcoords[alpha_current_face].append(alpha_texcoord[k+l])
                else:
                    alpha_face_texcoords[alpha_current_face].append([0, 0])
            count += 3
            j += 1

        for i in range(0, len(cell["alpha_texture_list"])):
            tex_name = cell["alpha_texture_list"][i].split('\\')[-1].split('.')[0]
            mesh = bpy.data.meshes.new(tex_name)
            mesh.from_pydata(alpha_face_verts[i], [], alpha_faces[i])
            mesh.update()
            object = bpy.data.objects.new(tex_name, mesh)
            if(has_textures):
                material = bpy.data.materials.new(name=tex_name)
                material.diffuse_color = (1, 1, 1, 1)
                material.blend_method = 'CLIP'
                material.shadow_method = 'CLIP'
                material.use_nodes = True
                mat_principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
                tex_node = material.node_tree.nodes.new("ShaderNodeTexImage")
                tex_node.image = bpy.data.images.load(texture_path + cell["alpha_texture_list"][i])
                material.node_tree.links.new(tex_node.outputs[0], mat_principled_bsdf.inputs[0])
                material.node_tree.links.new(tex_node.outputs["Alpha"], mat_principled_bsdf.inputs["Alpha"])
                object.data.materials.append(material)
            bpy.context.collection.objects.link(object)
            object.select_set(True)
            
            uv_layer = mesh.uv_layers.new(name="UVMap")
            mesh.uv_layers.active = uv_layer
            for face in mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_layer.data[loop_idx].uv = alpha_face_texcoords[i][loop_idx]

    

def get_map_data(stream, version, filepath):
    data = {}
    data["locale_data_version"] = version
    data["locale_id"] = read_int(stream)
    data["world_name"] = read_string(stream)
    data["game_name"] = ""
    if(version >= 800):
        data["game_name"] = read_string(stream)
    data["creation_date"] = datetime.datetime.fromtimestamp(read_long(stream) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    data["cell_list_size"] = read_int(stream)
    data["center_point"] = [read_int(stream), read_int(stream), read_int(stream)]
    data["width"] = read_int(stream)
    data["height"] = read_int(stream)
    data["depth"] = read_int(stream)
    if(read_bool(stream)):
        data["background_music"] = read_string(stream)
    if(read_bool(stream)):
        data["channel_name"] = read_string(stream)
    if(read_bool(stream)):
        data["ban_mask"] = read_string(stream)
    if(read_bool(stream)):
        data["channel_topic"] = read_string(stream)
    data["max_irc_users"] = read_int(stream)
    data["is_private_channel"] = read_bool(stream)
    data["is_secret_channel"] = read_bool(stream)
    data["is_invite_only_channel"] = read_bool(stream)
    data["is_quiet_channel"] = read_bool(stream)
    world_entries_size = read_int(stream)
    data["world_entries"] = []
    for i in range(world_entries_size):
        entry = {}
        entry["name"] = read_string(stream)
        entry_pos = [read_float(stream), read_float(stream), read_float(stream)]
        entry["position"] = [entry_pos[0], entry_pos[2], entry_pos[1]]
        entry_rot = [read_float(stream), read_float(stream), read_float(stream)]
        entry["rotation"] = [entry_rot[0], entry_rot[2], entry_rot[1]]
        entry["cell"] = read_string(stream)
        entry["type"] = read_int(stream)
        data["world_entries"].append(entry)
    data["ambient_light"] = [read_float(stream), read_float(stream), read_float(stream), read_float(stream)]
    light_count = read_short(stream)
    data["lights"] = []
    if(light_count > 0):
        data["has_lights"] = read_bool(stream)
        if(version >= 802):
            data["has_lightmaps"] = read_bool(stream)
        else:
            data["has_lightmaps"] = data["has_lights"]
        for i in range(light_count):
            light = {}
            light["type"] = read_byte(stream)
            light["position"] = [read_int(stream), read_int(stream), read_int(stream)]
            light["intensity"] = read_float(stream)
            light["color"] = [read_short(stream), read_short(stream), read_short(stream)]
            light["near"] = read_short(stream)
            light["far"] = read_short(stream)
            light["shadows"] = read_byte(stream)
            light["name"] = read_string(stream)
            excluded_cell_count = read_byte(stream)
            if(excluded_cell_count > 0):
                light["excluded_cells"] = []
                for j in range(excluded_cell_count):
                    light["excluded_cells"].append(read_string(stream))
            data["lights"].append(light)
    waypoint_count = read_int(stream)
    if(waypoint_count > 0):
        data["waypoints"] = []
        for i in range(waypoint_count):
            waypoint = {}
            waypoint["list_index"] = i
            waypoint["position"] = [read_float(stream), read_float(stream), read_float(stream)]
            waypoint["cell_id"] = read_int(stream)
            if(version > 793):
                waypoint["sequence"] = read_int(stream)
            if(version > 800):
                linked_indices_count = read_int(stream)
                if(linked_indices_count > 0):
                    waypoint["linked_indices"] = []
                    for j in range(linked_indices_count):
                        waypoint["linked_indices"].append(read_int(stream))
            if(version > 802):
                waypoint["group_id"] = read_int(stream)
            if(version > 804):
                waypoint["leading_id"] = read_int(stream)
                waypoint["trailing_id"] = read_int(stream)
                waypoint["racing_offset"] = read_float(stream)
                waypoint["overtaking_offset"] = read_float(stream)
            waypoint["type_flags"] = read_long(stream)
            type_flag_string = ""
            addedFlag = False
            if(waypoint["type_flags"] & 1):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "NEVER_LINK"
                addedFlag = True
            if(waypoint["type_flags"] & 2):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "OBSTACLE"
                addedFlag = True
            if(waypoint["type_flags"] & 4):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "GOAL"
                addedFlag = True
            if(waypoint["type_flags"] & 8):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "FINISH"
                addedFlag = True
            if(waypoint["type_flags"] & 16):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "DEPART"
                addedFlag = True
            if(waypoint["type_flags"] & 32):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "DESTINATION"
                addedFlag = True
            if(waypoint["type_flags"] & 64):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "DETOUR"
                addedFlag = True
            if(waypoint["type_flags"] & 128):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "NEVER_COMPILE"
                addedFlag = True
            if(waypoint["type_flags"] & 256):
                if(addedFlag):
                    type_flag_string += "| "
                type_flag_string += "SECTOR_NODE"
                addedFlag = True
            if(addedFlag == False):
                type_flag_string = "<none>"
            waypoint["type_flag_string"] = type_flag_string
            data["waypoints"].append(waypoint)
    data["cells"] = []
    for i in range(data["cell_list_size"]):
        cellpath = os.path.join(os.path.dirname(os.path.abspath(filepath)), "c" + str(i) + ".dmg")
        if(os.path.exists(cellpath) == False):
            print("Cell " + str(i) + " not found!")
            continue
        print("Cell " + str(i) + " found! Loading...")
        file_input_stream = open(cellpath, "rb")
        gzip_input_stream = gzip.GzipFile(fileobj=file_input_stream, mode='rb')
        buffered_input_stream = BufferedReader(gzip_input_stream)
        cell_version = read_short(buffered_input_stream)
        data["cells"].append(get_cell_data(buffered_input_stream, cell_version))
    return data

def get_cell_data(stream, version):
    cell = {}
    cell["map_cell_version"] = version
    cell_pos = [read_int(stream), read_int(stream), read_int(stream)]
    cell["position"] = [-cell_pos[0], cell_pos[2], cell_pos[1]]
    cell["width"] = read_int(stream)
    cell["height"] = read_int(stream)
    cell["depth"] = read_int(stream)
    cell["xl"] = read_int(stream)
    cell["xr"] = read_int(stream)
    cell["yt"] = read_int(stream)
    cell["yb"] = read_int(stream)
    cell["zb"] = read_int(stream)
    cell["zf"] = read_int(stream)
    cell["id"] = read_int(stream)
    cell["name"] = read_string(stream)
    cell["total_face_count"] = read_int(stream)
    cell["total_reg_faces"] = read_int(stream)
    cell["total_alpha_faces"] = read_int(stream)
    cell["texture_count"] = read_short(stream)
    cell["texture_alpha_count"] = read_short(stream)
    cell["portal_count"] = read_int(stream)
    if(version >= 1296):
        cell["gravity"] = read_float(stream)
        cell["enable_combat"] = read_bool(stream)
        cell["irc_channel"] = read_string(stream)
    else:
        cell["gravity"] = 9.81
        cell["enable_combat"] = True
        cell["irc_channel"] = ""
    cell["face_start"] = []
    cell["face_count"] = []
    cell["texture_list"] = []
    for i in range(cell["texture_count"]):
        cell["texture_list"].append(read_string(stream))
        cell["face_start"].append(read_int(stream))
        cell["face_count"].append(read_int(stream))
    cell["alpha_texture_list"] = []
    cell["alpha_face_count"] = []
    if(cell["texture_alpha_count"] > 0):
        for i in range(cell["texture_alpha_count"]):
            cell["alpha_texture_list"].append(read_string(stream))
            cell["alpha_face_count"].append(read_int(stream))
    vertex_count = (cell["total_reg_faces"] + cell["portal_count"] * 2) * 9
    cell["vertex"] = []
    for i in range(0, vertex_count, 3):
        pos = [read_float(stream), read_float(stream), read_float(stream)]
        cell["vertex"].append([-pos[0], pos[2], pos[1]])
    texcoord_count = cell["total_reg_faces"] * 6
    cell["texcoord"] = []
    for i in range(0, texcoord_count, 2):
        cell["texcoord"].append([read_float(stream), read_float(stream)])
    vertex_color_count = cell["total_reg_faces"] * 9
    cell["vertex_color"] = []
    for i in range(0, vertex_color_count, 3):
        pos = [read_float(stream), read_float(stream), read_float(stream)]
        cell["vertex_color"].append([-pos[0], pos[2], pos[1]])
    alpha_vertex_count = cell["total_alpha_faces"] * 9
    cell["alpha_vertex"] = []
    for i in range(0, alpha_vertex_count, 3):
        pos = [read_float(stream), read_float(stream), read_float(stream)]
        cell["alpha_vertex"].append([-pos[0], pos[2], pos[1]])
    alpha_texcoord_count = cell["total_alpha_faces"] * 6
    cell["alpha_texcoord"] = []
    for i in range(0, alpha_texcoord_count, 2):
        cell["alpha_texcoord"].append([read_float(stream), read_float(stream)])
    alpha_vertex_color_count = cell["total_alpha_faces"] * 9
    cell["alpha_vertex_color"] = []
    for i in range(0, alpha_vertex_color_count, 3):
        pos = [read_float(stream), read_float(stream), read_float(stream)]
        cell["alpha_vertex_color"].append([-pos[0], pos[2], pos[1]])
    if(read_bool(stream)):
        cell["bsp_node"] = read_bsp(stream)
    if(read_bool(stream)):
        cell["alpha_bsp_node"] = read_bsp(stream)
    cell["portal_plane"] = []
    cell["portal_center"] = []
    cell["portal_radius"] = []
    cell["portal_link"] = []
    cell["portal_name"] = []
    cell["portal_vis_node_list"] = []
    for i in range(cell["portal_count"]):
        cell["portal_plane"].append([read_float(stream), read_float(stream), read_float(stream), read_float(stream)])
        cell["portal_center"].append([read_float(stream), read_float(stream), read_float(stream)])
        cell["portal_radius"].append(read_float(stream))
        cell["portal_link"].append(read_int(stream))
        cell["portal_name"].append(read_string(stream))
        cell["portal_vis_node_list"].append(read_portal_vis_node(stream))
    if(read_bool(stream)):
        cell["light_tree"] = read_light_tree(stream)
    lightmap_count = read_int(stream)
    cell["lightmap"] = []
    for i in range(lightmap_count):
        lightmap_n = read_int(stream)
        current = []
        for j in range(65536):
            current.append(read_short(stream))
        cell["lightmap"].append(current)
    if(len(cell["lightmap"]) > 0):
        l = cell["reg_face_count"] * 6
        cell["lightmap_texcoord"] = []
        for i in range(0, l, 3):
            cell["lightmap_texcoord"].append([read_float(stream), read_float(stream), read_float(stream)])
        cell["lightmap_tex_index"] = []
        for i in range(cell["texture_count"]):
            cell["lightmap_tex_index"].append(read_short(stream))
        l = cell["alpha_face_count"] * 6
        cell["alpha_lightmap_texcoord"] = []
        for i in range(0, l, 3):
            cell["alpha_lightmap_texcoord"].append([read_float(stream), read_float(stream), read_float(stream)])
        cell["alpha_lightmap_tex_index"] = read_short()
    else:
        cell["lightmap_texcoord"] = cell["texcoord"]
        cell["alpha_lightmap_texcoord"] = cell["alpha_texcoord"]
    return cell

def get_map_data_from_cell(stream, version):
    data = {}
    cell_data = get_cell_data(stream, version)
    data["locale_data_version"] = version
    data["locale_id"] = 0
    data["world_name"] = "unknown"
    data["game_name"] = ""
    data["creation_date"] = "Unknown"
    data["cell_list_size"] = 1
    data["center_point"] = [0, 0, 0]
    data["width"] = 0
    data["height"] = 0
    data["depth"] = 0
    data["max_irc_users"] = 8
    data["is_private_channel"] = False
    data["is_secret_channel"] = False
    data["is_invite_only_channel"] = False
    data["is_quiet_channel"] = False
    data["world_entries"] = []
    data["ambient_light"] = [1.0, 1.0, 1.0, 1.0]
    data["has_lights"] = False
    data["has_lightmaps"] = False
    data["lights"] = []
    data["waypoints"] = []
    data["cells"] = []
    data["cells"].append(cell_data)
    return data

# Define a ton of functions for reading the locale file
def read_string(stream):
    length = stream.read(2)
    length = int.from_bytes(length, byteorder='big')
    string = stream.read(length)
    return string.decode("utf-8")

def read_int(stream):
    return int.from_bytes(stream.read(4), byteorder='big')

def read_short(stream):
    return int.from_bytes(stream.read(2), byteorder='big')

def read_long(stream):
    return int.from_bytes(stream.read(8), byteorder='big')

def read_bool(stream):
    return stream.read(1) == b'\x01'

def read_float(stream):
    return struct.unpack('>f', stream.read(4))[0]

def read_byte(stream):
    return int.from_bytes(stream.read(1), byteorder='big')

# Recursive function for reading the BSP tree
def read_bsp(stream):
    bsp_node = {}
    bsp_node["version"] = read_byte(stream) # In Versusville, if this is < 4 then it will refuse to load
    bsp_node["node_count"] = read_int(stream)
    bsp_node["ppe"] = []
    bsp_node["n_polys"] = []
    bsp_node["vertex_index"] = []
    bsp_node["front"] = []
    bsp_node["back"] = []
    bsp_node["tex_index"] = []
    bsp_node["i1"] = []
    bsp_node["i2"] = []
    for j in range(bsp_node["node_count"]):
        bsp_node["ppe"].append([read_float(stream), read_float(stream), read_float(stream), read_float(stream)])
        bsp_node["n_polys"].append(read_short(stream))
        vertex_index = []
        tex_index = []
        for k in range(bsp_node["n_polys"][j]):
            vertex_index.append(read_int(stream))
            tex_index.append(read_short(stream))
        bsp_node["vertex_index"].append(vertex_index)
        bsp_node["tex_index"].append(tex_index)
        bsp_node["front"].append(read_int(stream))
        bsp_node["back"].append(read_int(stream))
        bsp_node["i1"].append(read_byte(stream))
        bsp_node["i2"].append(read_byte(stream))
    print("Loaded BSP with " + str(bsp_node["node_count"]) + " nodes")
    return bsp_node

# Recursive function for reading the portal tree
def read_portal_vis_node(stream):
    portal_vis_node = {}
    if(read_int(stream) > 0):
        portal_vis_node["name"] = read_string(stream)
    portal_vis_node["a"] = read_int(stream)
    portal_var_size = read_int(stream)
    portal_vis_node["b"] = []
    portal_vis_node["c"] = []
    for k in range(portal_var_size):
        portal_vis_node["b"].append(read_int(stream))
        portal_vis_node["c"].append(read_portal_vis_node(stream))
    print("Loaded portal vis node with " + str(portal_var_size) + " children")
    return portal_vis_node

# Recursive function for reading the light tree
def read_light_tree(stream):
    light_tree = {}
    light_tree["light_count"] = read_short(stream)
    light_tree["light_list"] = []
    for j in range(light_tree["light_count"]):
        light_tree["light_list"].append(read_short(stream))
    light_tree["x_mid"] = read_int(stream)
    light_tree["y_mid"] = read_int(stream)
    light_tree["z_mid"] = read_int(stream)
    light_tree["light_quads"] = []
    for j in range(8):
        if(read_bool(stream)):
            light_tree["light_quads"].append(read_light_tree(stream))
    print("Loaded light tree with " + str(light_tree["light_count"]) + " lights")
    return light_tree


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportDMG(Operator, ImportHelper):
    """Can import an entire Trimorph Engine locale, or individual cells."""
    bl_idname = "import_trimorph.locale_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Trimorph Engine Locale"

    # ImportHelper mixin class uses this
    filename_ext = ".dmg"

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
        return read_dmg_locale(context, self.filepath)
