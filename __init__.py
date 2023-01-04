# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Trimorph Tools",
    "author" : "Carson Kompon",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

import bpy

from .dmg_constructor import ImportDMG
from .dma_importer import ImportDMA

def menu_dmg_import(self, context):
    self.layout.operator(ImportDMG.bl_idname, text="Trimorph Locale (.dmg)")

def menu_dma_import(self, context):
    self.layout.operator(ImportDMA.bl_idname, text="Trimorph Skin (.dma)")

def register():
    bpy.utils.register_class(ImportDMG)
    bpy.types.TOPBAR_MT_file_import.append(menu_dmg_import)

    bpy.utils.register_class(ImportDMA)
    bpy.types.TOPBAR_MT_file_import.append(menu_dma_import)

def unregister():
    bpy.utils.unregister_class(ImportDMG)
    bpy.types.TOPBAR_MT_file_import.remove(menu_dmg_import)
    
    bpy.utils.unregister_class(ImportDMA)
    bpy.types.TOPBAR_MT_file_import.remove(menu_dma_import)
