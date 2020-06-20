from svgpathtools import svg2paths2, wsvg, disvg
import math

paths, attributes, svg_attributes = svg2paths2('test1.svg')

print(f'{len(paths)} paths')

lengths = [p.length() for p in paths]
print(f'Min length: {min(lengths)}')
print(f'Max length: {max(lengths)}')

min_length = 2
max_length = 1000

paths_2 = [p for p in paths if min_length < p.length() < max_length]

for a in attributes:
    a['fill'] = 'none'
    a['stroke'] = '#1a1a1a'

wsvg(paths_2, attributes=attributes, svg_attributes=svg_attributes, filename='output1.svg')

bounds = [p.bbox() for p in paths]
x_min = min([b[0] for b in bounds])
x_max = max([b[1] for b in bounds])
y_min = min([b[2] for b in bounds])
y_max = max([b[3] for b in bounds])
x_size = x_max - x_min
y_size = y_max - y_min
print(f'Bounding box: {x_min}, {x_size}, {y_min}, {y_size}')

scale_factor = 0.1
print(f'New size: {x_size * scale_factor}, {y_size * scale_factor}')

gcode = open('output.gcode', 'w')

def scale(point):
    return (round(scale_factor * (point.real - x_min), 2),
            round(scale_factor * (point.imag - y_min), 2))

min_segment_length = 0.1

last_x = -1
last_y = -1
def write_gcode_move(x, y, z, skip_check=False):
    global last_x, last_y
    if skip_check or math.hypot(x - last_x, y - last_y) > min_segment_length:
        gcode.write(f'G0 X{x} Y{y} Z{z} F6000\n')
        last_x = x
        last_y = y

z_high = 1
z_low = 0

for p in paths_2:
    write_gcode_move(*scale(p[0].start), z_high)
    write_gcode_move(*scale(p[0].start), z_low, skip_check=True)
    for s in p:
        write_gcode_move(*scale(s.end), z_low)
    write_gcode_move(*scale(p[-1].end), z_high, skip_check=True)

gcode.close()
