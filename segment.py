import os
import json
import shutil
import numpy as np


def parse_obj(filename):
    vertices = []
    normals = []
    uvs = []
    faces = []

    # read line
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('v '):
                vertices.append([float(x) for x in line[2:].split()])
            elif line.startswith('vn '):
                normals.append([float(x) for x in line[3:].split()])
            elif line.startswith('vt '):
                uvs.append([float(x) for x in line[3:].split()])
            elif line.startswith('f '):
                indices = [x.split('/') for x in line.split()[1:]]
                faces.append(indices)

    # calculate bounding box
    vertices = np.array(vertices)
    mean_vertices = np.mean(vertices, axis=0)
    max_x = np.max(np.abs(vertices[:, 0] - mean_vertices[0]))
    max_y = np.max(np.abs(vertices[:, 1] - mean_vertices[1]))
    max_z = np.max(np.abs(vertices[:, 2] - mean_vertices[2]))

    bounding_box = {}
    bounding_box['min'] = mean_vertices - np.array([max_x, max_y, max_z])
    bounding_box['max'] = mean_vertices + np.array([max_x, max_y, max_z])
    bounding_box['min'][bounding_box['min'] < 0] = 0
    bounding_box['max'][bounding_box['max'] < 0] = 0

    # output
    data = {}
    data['vertices']    = np.array(vertices)
    data['normals']     = np.array(normals)
    data['uvs']         = np.array(uvs)
    data['faces']       = np.array(faces)
    data['boundingBox'] = bounding_box

    return data

def save_obj(filename, data):
    vertices = data['vertices']
    normals  = data['normals']
    uvs      = data['uvs']
    faces    = data['faces']

    with open(filename, 'w') as f:

        for i in range(len(vertices)):
            vertex = vertices[i]
            f.write(f"v {' '.join(str(x) for x in vertex)}\n")

        for i in range(len(normals)):
            normal = normals[i]
            f.write(f"vn {' '.join(str(x) for x in normal)}\n")

        for uv in uvs:
            f.write(f"vt {' '.join(str(x) for x in uv)}\n")

        for face in faces:
            indices = ' '.join(['/'.join(map(str, vertex)) for vertex in face])
            f.write(f"f {indices}\n")

def subclip(data):
    vertices     = data['vertices']
    uvs          = data['uvs']
    bounding_box = data['boundingBox']

    min_x, min_y, min_z = bounding_box['min']
    max_x, max_y, max_z = bounding_box['max']
    max_z = 100
    
    w = 150
    h = 150
    d = 100

    subclip_list = []
    for x in range(int(min_x), int(max_x), 150):
        for y in range(int(min_y), int(max_y), 150):
            for z in range(int(min_z), int(max_z), 100):
                if (x < 0): x = 0
                if (y < 0): y = 0
                if (z < 0): z = 0
                if (x + w > max_x): w = max_x - x
                if (y + h > max_y): h = max_y - y
                if (z + d > max_z): d = max_z - z
                # print('hi')

                if np.any((vertices[:, 0] >= x) & (vertices[:, 0] < x + w) &
                          (vertices[:, 1] >= y) & (vertices[:, 1] < y + h) &
                          (vertices[:, 2] >= z) & (vertices[:, 2] < z + d)):
                    item = {}
                    item['id'] = str(len(subclip_list))
                    item['clip'] = { 'x': x, 'y': y, 'z': z, 'w': w, 'h': h, 'd': d }
                    item['shape'] = { 'w': w, 'h': h, 'd': d }
                    subclip_list.append(item)

    return subclip_list

if __name__ == "__main__":
    # config & path
    with open('config.json') as f:
        config = json.load(f)

    OBJ_INPUT     = config['OBJ_INPUT']

    OBJ_OUTPUT    = './output/segment'
    OBJ_INFO      = './output/segment/meta.json'

    # clear .obj output folder
    shutil.rmtree(OBJ_OUTPUT, ignore_errors=True)
    os.makedirs(OBJ_OUTPUT)

    # copy .obj files from .volpkg
    SEGMENT_LIST = []

    if (OBJ_INPUT != ''):
        subfolders = [f.path for f in os.scandir(OBJ_INPUT) if f.is_dir()]

        for subfolder in subfolders:
            folder_name = os.path.basename(subfolder)
            obj_file_path = os.path.join(subfolder, folder_name + '.obj')

            if os.path.isfile(obj_file_path):
                shutil.copy(obj_file_path , OBJ_OUTPUT)
                SEGMENT_LIST.append(folder_name)

    # parse .obj files and get relevant info and copy to client
    meta = {}
    meta['view_segment'] = OBJ_INPUT != ''
    meta['obj'] = []

    for SEGMENT_ID in SEGMENT_LIST:
        filename = f'{OBJ_OUTPUT}/{SEGMENT_ID}.obj'

        data = parse_obj(filename)
        c = data['boundingBox']['min']
        b = data['boundingBox']['max']

        info = {}
        info['id'] = SEGMENT_ID
        info['clip'] = {}
        info['clip']['x'] = int(c[0])
        info['clip']['y'] = int(c[1])
        info['clip']['z'] = int(c[2])
        info['clip']['w'] = int(b[0] - c[0])
        info['clip']['h'] = int(b[1] - c[1])
        info['clip']['d'] = int(b[2] - c[2])

        meta['obj'].append(info)

    with open(OBJ_INFO, "w") as outfile:
        json.dump(meta, outfile, indent=4)

    shutil.rmtree('client/public/segment', ignore_errors=True)
    shutil.copytree(OBJ_OUTPUT, 'client/public/segment', dirs_exist_ok=True)

