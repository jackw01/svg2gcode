from svgpathtools import svg2paths2, wsvg, disvg
import math

svg_file = 'condensed-irvine.svg'
condense = False
min_length = 1
max_length = 1000
output_size_x = 130
min_segment_length = 0.15
join_distance = 0.3
z_high = 1
z_low = 0
accel_xy_mm_s2 = 4000
accel_z_mm_s2 = 2000
feedrate_xy_mm_min = 6000
feedrate_z_mm_s = 6.67

paths, attributes, svg_attributes = svg2paths2(svg_file)

print(f'{len(paths)} paths')

bounds = [p.bbox() for p in paths]
x_min = min([b[0] for b in bounds])
x_max = max([b[1] for b in bounds])
y_min = min([b[2] for b in bounds])
y_max = max([b[3] for b in bounds])
x_size = x_max - x_min
y_size = y_max - y_min
scale_factor = output_size_x / x_size
print(f'Bounding box: {x_min}, {x_size}, {y_min}, {y_size}')
print(f'New size: {x_size * scale_factor}, {y_size * scale_factor}')

lengths = [p.length() * scale_factor for p in paths]
print(f'Min length: {min(lengths)}')
print(f'Max length: {max(lengths)}')


# Condense
if condense:
    paths.sort(key=lambda p: p.length())

    i = 0
    while i < len(paths):
        print(f'Condensing path {i} (total: {len(paths)})')
        while True:
            next_path = None
            for p in paths:
                if p != paths[i] \
                and abs(p[0].start - paths[i][-1].end) * scale_factor < join_distance:
                    next_path = p
                    break

            if next_path:
                paths[i].extend(next_path)
                paths.remove(next_path)
            else:
                break
        i += 1

print(f'{len(paths)} paths (condensed)')

paths_2 = [p for p in paths if min_length < p.length() * scale_factor < max_length]
paths_2.sort(key=lambda p: p.length(), reverse=True)
print(f'{len(paths_2)} paths (filtered)')


# Export
for a in attributes:
    a['fill'] = 'none'
    a['stroke'] = '#1a1a1a'

wsvg(paths_2,
     attributes=attributes,
     svg_attributes=svg_attributes,
     filename=f'condensed-{svg_file}')


# Write gcode
gcode = open(f'{svg_file}.gcode', 'w')

gcode.write(f'M201 X{accel_xy_mm_s2} Y{accel_xy_mm_s2} Z{accel_z_mm_s2} E1000\n')
gcode.write(f'M203 X100 Y100 Z{feedrate_z_mm_s} E150\n')
gcode.write(f'M204 P{accel_xy_mm_s2} R1000 T{accel_xy_mm_s2}\n')

def scale(point):
    return (round(scale_factor * (point.real - x_min), 2),
            round(scale_factor * (y_max - (point.imag - y_min)), 2))

last_x = -1
last_y = -1
def write_gcode_move(x, y, z, skip_check=False):
    global last_x, last_y
    if skip_check or math.hypot(x - last_x, y - last_y) > min_segment_length:
        gcode.write(f'G0 X{x} Y{y} Z{z} F{feedrate_xy_mm_min}\n')
        last_x = x
        last_y = y

for p in paths_2:
    write_gcode_move(*scale(p[0].start), z_high)
    write_gcode_move(*scale(p[0].start), z_low, skip_check=True)
    for s in p:
        write_gcode_move(*scale(s.end), z_low)
    write_gcode_move(*scale(p[-1].end), z_high, skip_check=True)

gcode.write(f'G0 X0 Y0 Z{z_high} F{feedrate_xy_mm_min}\n')
gcode.close()
