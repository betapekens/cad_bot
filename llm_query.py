
import cadquery as cq

import cadquery as cq

# Create a rectangular faceplate
obj = cq.Workplane("XY").rect(50, 30).extrude(5)

# Fillet the edges
obj = obj.edges("|Z").fillet(2)

# Make a hole in the middle
obj = obj.faces(">Z").workplane().hole(10)


cq.exporters.export(obj, "stl_files/obj.stl")