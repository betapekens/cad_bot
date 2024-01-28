import cadquery as cq

# Set the dimensions of the box
length = 10.0
width = 5.0
height = 3.0
radius = 0.5

# Create an empty box with rounded edges
obj = (
    cq.Workplane("XY")
    .box(length, width, height, combine=False)
    .edges("|Z")
    .chamfer(radius)
)


cq.exporters.export(obj, 'stl_files/obj.stl')