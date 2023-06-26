import os
import json
import shutil

from segment import parse_obj, subclip
from volume import read_tif, write_nrrd

if __name__ == "__main__":
    SEGMENT_ID = '20230505164332'
    filename   = f'./output/segment/{SEGMENT_ID}.obj'

    NRRD_OUTPUT = './output/volume'
    NRRD_INFO   = './output/volume/meta.json'

    # config & path
    with open('config.json') as f:
        config = json.load(f)

    # TIF_INPUT    = config['TIF_INPUT']
    # RAW_SAMPLING = config['RAW_SAMPLING']
    # TIF_SAMPLING = config['TIF_SAMPLING']
    TIF_INPUT    = '../full-scrolls/Scroll1.volpkg/volumes/20230205180739'
    RAW_SAMPLING = 1
    TIF_SAMPLING = 1

    shutil.rmtree(NRRD_OUTPUT, ignore_errors=True)
    os.makedirs(NRRD_OUTPUT)

    data = parse_obj(filename)
    subclip_list = subclip(data)
    # subclip_list = subclip(data, 150 * RAW_SAMPLING * TIF_SAMPLING)

    # save relevant info and copy to client
    meta = {}
    meta['nrrd'] = subclip_list

    for NRRD_CHUNK in subclip_list:
        NRRD_ID = NRRD_CHUNK['id']
        NRRD_SUBCLIP = NRRD_CHUNK['clip']

        # extract image stack from .tif files
        image_stack = read_tif(TIF_INPUT, NRRD_SUBCLIP, RAW_SAMPLING, TIF_SAMPLING)

        NRRD_CHUNK['shape'] = {}
        NRRD_CHUNK['shape']['w'] = image_stack.shape[0]
        NRRD_CHUNK['shape']['h'] = image_stack.shape[1]
        NRRD_CHUNK['shape']['d'] = image_stack.shape[2]

        # generate .nrrd file from image stack
        write_nrrd(f'{NRRD_OUTPUT}/{NRRD_ID}.nrrd', image_stack)

    with open(NRRD_INFO, "w") as outfile:
        json.dump(meta, outfile, indent=4)

    shutil.rmtree('client/public/volume', ignore_errors=True)
    shutil.copytree(NRRD_OUTPUT, 'client/public/volume', dirs_exist_ok=True)

