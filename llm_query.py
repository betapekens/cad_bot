
import cadquery as cq

# Define the dimensions of the faceplate
diameter = 100.0
thickness = 10.0

# Create a circular faceplate with increased thickness
faceplate = cq.Workplane("XY").circle(diameter/2).extrude(thickness)

# Store the final object in the variable 'obj'
obj = faceplate

cq.exporters.export(obj, "stl_files/obj.stl")