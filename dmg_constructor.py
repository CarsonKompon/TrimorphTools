import bpy
import bmesh
import datetime
import gzip
import os
from io import BufferedReader
from .data_stream import *
from .importers.kvs.dmg_importer_versusville import ImporterVersusvilleDMG
from .importers.alias.dmg_importer_alias import ImporterAliasDMG

def read_dmg_locale(context, filepath):
    print("running read_dmg_locale...")

    file_input_stream = open(filepath, "rb")
    gzip_input_stream = gzip.GzipFile(fileobj=file_input_stream, mode='rb')
    buffered_input_stream = BufferedReader(gzip_input_stream)

    data_version = read_short(buffered_input_stream)

    data = {}

    if(data_version >= 1000):
        # Cell File
        print("Cell file version " + str(data_version) + " found...")
        if(data_version <= 1296):
            # Alias Cell File
            print("Using Alias Cell File Importer...")
            data = ImporterAliasDMG.get_map_data_from_cell(buffered_input_stream, data_version)
        else:
            # Versusville/Minigolf Cell File
            print("Using Versusville Cell File Importer...")
            data = ImporterVersusvilleDMG.get_map_data_from_cell(buffered_input_stream, data_version)
    else:
        # Map File
        print("Map file version " + str(data_version) + " found...")
        if(data_version <= 791):
            # Alias Map File
            print("Using Alias Map File Importer...")
            data = ImporterAliasDMG.get_map_data(buffered_input_stream, data_version, filepath)
        else:
            # Versusville/Minigolf Map File
            print("Using Versusville Map File Importer...")
            data = ImporterVersusvilleDMG.get_map_data(buffered_input_stream, data_version, filepath)

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
            object.scale = (0.01, 0.01, 0.01)
            uv_layer = mesh.uv_layers.new(name="UVMap")
            mesh.uv_layers.active = uv_layer
            for face in mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_layer.data[loop_idx].uv = alpha_face_texcoords[i][loop_idx]

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
