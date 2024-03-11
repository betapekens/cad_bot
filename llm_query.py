
import cadquery as cq

import cadquery as cq

# Create a 2D rectangle with dimensions 50x30
obj = cq.Workplane("XY").rect(50, 30)

# Extrude the rectangle to create a 3D faceplate
obj = obj.extrude(5)

cq.exporters.export(obj, "stl_files/obj.stl")