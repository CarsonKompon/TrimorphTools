import datetime
import gzip
import os
from io import BufferedReader
from ...data_stream import *

class ImporterAliasDMG():
    def get_map_data(stream, version, filepath):
        data = {}
        data["locale_data_version"] = version
        data["locale_id"] = read_int(stream)
        data["world_name"] = read_string(stream)
        data["game_name"] = "alias"
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
        if(read_bool(stream)):
            print("new stuff")
            aa = read_int(stream)
            print(aa)
            data["aaa"] = []
            for i in range(aa):
                data["aaa"].append([read_int(stream), read_int(stream), read_int(stream), read_int(stream)])
            data["bbb"] = []
            for i in range(aa):
                bb = read_int(stream)
                print(bb)
                if(bb > 0):
                    arr = []
                    for j in range(bb):
                        arr.append(read_int(stream))
                    data["bbb"].append(arr)
                else:
                    data["bbb"].append([])
            cc = read_int(stream)
            print(cc)
            data["ccc"] = []
            for i in range(cc):
                data["ccc"].append(read_int(stream))
            dd = read_int(stream)
            data["ddd"] = []
            for i in range(dd):
                data["ddd"].append(read_float(stream))
            ee = read_int(stream)
            data["eee"] = []
            for i in range(ee):
                data["eee"].append(read_string(stream))
            ff = read_int(stream)
            data["fff"] = []
            for i in range(ff):
                data["fff"].append([read_int(stream), read_int(stream)])
            print("new stuff")
            if(read_bool(stream)):
                gg = read_int(stream)
                print(gg)
                data["ggg"] = []
                for i in range(gg):
                    j = read_int(stream)
                    if(j == -1):
                        data["ggg"].append("null")
                    else:
                        arr = []
                        for k in range(j):
                            str = read_string(stream)
                            if(str.lower() == "rotate"):
                                arrlen = read_int(stream)   
                                for l in range(arrlen):
                                    arr.append(read_int(stream))
                            elif(str.lower() == "flag"):
                                arrlen = read_int(stream)        
                                for l in range(arrlen):
                                    arr.append(read_string(stream))
                        data["ggg"].append({
                            "name": str,
                            "data": arr
                        })

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
            data["cells"].append(ImporterAliasDMG.get_cell_data(buffered_input_stream, cell_version))
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
        for i in range(0, texcoord_count, 6):
            uv1 = [read_float(stream), read_float(stream)]
            uv2 = [read_float(stream), read_float(stream)]
            uv3 = [read_float(stream), read_float(stream)]
            cell["texcoord"].append(uv1)
            cell["texcoord"].append(uv3)
            cell["texcoord"].append(uv2)
        # vertex_color_count = cell["total_reg_faces"] * 9
        # cell["vertex_color"] = []
        # for i in range(0, vertex_color_count, 3):
        #     pos = [read_float(stream), read_float(stream), read_float(stream)]
        #     cell["vertex_color"].append([-pos[0], pos[2], pos[1]])
        alpha_vertex_count = cell["total_alpha_faces"] * 9
        cell["alpha_vertex"] = []
        for i in range(0, alpha_vertex_count, 3):
            pos = [read_float(stream), read_float(stream), read_float(stream)]
            cell["alpha_vertex"].append([-pos[0], pos[2], pos[1]])
        alpha_texcoord_count = cell["total_alpha_faces"] * 6
        cell["alpha_texcoord"] = []
        for i in range(0, alpha_texcoord_count, 2):
            cell["alpha_texcoord"].append([read_float(stream), read_float(stream)])
        # alpha_vertex_color_count = cell["total_alpha_faces"] * 9
        # cell["alpha_vertex_color"] = []
        # for i in range(0, alpha_vertex_color_count, 3):
        #     pos = [read_float(stream), read_float(stream), read_float(stream)]
        #     cell["alpha_vertex_color"].append([-pos[0], pos[2], pos[1]])
        if(read_bool(stream)):
            cell["opaque_qbt"] = ImporterAliasDMG.read_qbtree(stream)
        if(read_bool(stream)):
            cell["alpha_bsp_node"] = ImporterAliasDMG.read_bsp(stream)
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
            cell["portal_vis_node_list"].append(ImporterAliasDMG.read_portal_vis_node(stream))
        if(read_bool(stream)):
            cell["light_tree"] = ImporterAliasDMG.read_light_tree(stream)
        lightmap_count = read_int(stream)
        cell["lightmap"] = []
        for i in range(lightmap_count):
            lightmap_n = read_int(stream)
            current = []
            for j in range(65536):
                current.append(read_short(stream))
            cell["lightmap"].append(current)
        if(len(cell["lightmap"]) > 0):
            cell["lightmap_texcoord"] = []
            for i in range(0, texcoord_count, 3):
                cell["lightmap_texcoord"].append([read_float(stream), read_float(stream), read_float(stream)])
            cell["lightmap_tex_index"] = []
            for i in range(cell["texture_count"]):
                cell["lightmap_tex_index"].append(read_short(stream))
            l = cell["alpha_face_count"] * 6
            cell["alpha_lightmap_texcoord"] = []
            for i in range(0, alpha_texcoord_count, 3):
                cell["alpha_lightmap_texcoord"].append([read_float(stream), read_float(stream), read_float(stream)])
            cell["alpha_lightmap_tex_index"] = read_short(stream)
        else:
            cell["lightmap_texcoord"] = cell["texcoord"]
            cell["alpha_lightmap_texcoord"] = cell["alpha_texcoord"]
        return cell

    def get_map_data_from_cell(stream, version):
        data = {}
        cell_data = ImporterAliasDMG.get_cell_data(stream, version)
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

    def read_qbtree(stream):
        qbtree = {}
        qbtree["version"] = read_short(stream) # In Alias Underground, if this is < 2 then it will refuse to load
        print("Reading QBTree version " + str(qbtree["version"]) + "...")
        qbtree["quad"] = ImporterAliasDMG.read_quad(stream)
        return
    
    def read_quad(stream):
        quad = {}
        quadVersion = read_byte(stream) # In Alias Underground, if this is < 2 then it will refuse to load
        print("Reading Quad version " + str(quadVersion) + "...")
        quad["aa"] = read_byte(stream)
        quad["bb"] = read_int(stream)
        quad["cc"] = [read_int(stream), read_int(stream), read_int(stream)]
        quad["dd"] = read_int(stream)
        quad["ee"] = read_int(stream)
        quad["ff"] = read_int(stream)
        ggLen = read_short(stream)
        quad["gg"] = []
        quad["hh"] = []
        for i in range(ggLen):
            quad["gg"].append(read_int(stream))
            quad["hh"].append(read_short(stream))
        iiLen = read_short(stream)
        quad["ii"] = []
        quad["jj"] = []
        for i in range(iiLen):
            quad["ii"].append(read_int(stream))
            quad["jj"].append(read_short(stream))
        if(read_bool(stream)):
            quad["kk"] = ImporterAliasDMG.read_quad(stream)
        if(read_bool(stream)):
            quad["ll"] = ImporterAliasDMG.read_quad(stream)
        return quad

    # Recursive function for reading the BSP tree
    def read_bsp(stream):
        bsp_node = {}
        bsp_node["version"] = read_short(stream) # In Alias Underground, if this is < 4 then it will refuse to load
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
        portal_vis_node["a"] = read_int(stream)
        portal_var_size = read_int(stream)
        portal_vis_node["b"] = []
        portal_vis_node["c"] = []
        for k in range(portal_var_size):
            portal_vis_node["b"].append(read_int(stream))
            portal_vis_node["c"].append(ImporterAliasDMG.read_portal_vis_node(stream))
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
                light_tree["light_quads"].append(ImporterAliasDMG.read_light_tree(stream))
        print("Loaded light tree with " + str(light_tree["light_count"]) + " lights")
        return light_tree

