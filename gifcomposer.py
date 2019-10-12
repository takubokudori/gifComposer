#!/usr/bin/python3
from pathlib import Path
from PIL import Image, ImageSequence
import glob
from argparse import ArgumentParser

verbose = False


def print_v(s):
    global verbose
    if verbose:
        print(s)


def get_images(path_org):
    frames = []
    print_v(f"Glob {path_org}")
    images = glob.glob("{}/*.png".format(path_org))
    for i in images:
        new_frame = Image.open(i)
        rgba_pic = new_frame.convert(mode='RGBA')
        frames.append(rgba_pic)
    return frames


def get_gif_frames(file):
    print_v(f"Get {file} gif frames")
    im = Image.open(file)
    return (frame.copy() for frame in ImageSequence.Iterator(im))


def write_frames(frames, destination):
    print_v(f"Save png to {destination}")
    dir_dest = Path(destination)
    if not dir_dest.is_dir():
        dir_dest.mkdir(0o700)

    for i, f in enumerate(frames):
        # Save the file as png
        name = f'{destination}/{i + 1}.png'
        f.save(name, format='PNG')  # pngとして保存


def transparent_gif_frame(im):
    print_v(f"Transparent gif frame...")
    image = im.copy()
    alpha = image.split()[3]
    image = image.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
    image.paste(255, mask=mask)
    return image


def transparent_png(im):
    print_v(f"Transparent gif frame...")
    trans = Image.new('RGBA', im.size, (0, 0, 0, 0))
    for x in range(im.size[0]):
        for y in range(im.size[1]):
            pixel = im.getpixel((x, y))
            if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
                continue
            trans.putpixel((x, y), pixel)
    return trans


def composite(back_im, front_im):
    print_v(f"Composite files")
    canvas = Image.new('RGBA', front_im.size, (255, 255, 255, 0))
    canvas.paste(front_im, (0, 0), front_im)
    return Image.alpha_composite(back_im, canvas)


usage = f"""./{__file__} [-f <front_file>] [-b <back_file>] [-w <dir>] [-o <output_file>]
    Composite png and gif.
    """


def main():
    global verbose
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('-f', '--front', type=str,
                           required=True,
                           dest='front_file',
                           help='front image (png or gif)')
    argparser.add_argument('-b', '--back', type=str,
                           required=True,
                           dest='back_file',
                           help='concatnate target file name')
    argparser.add_argument('-w', '--workspace', type=str,
                           default='temp',
                           dest='workspace_dir',
                           help='workspace directory')
    argparser.add_argument('-o', '--output', type=str,
                           default='output.gif',
                           dest='output_filename',
                           help='output file.gif')
    argparser.add_argument('-tf', '--transparent-front',
                           action='store_true',
                           help='transparent front file flag')
    argparser.add_argument('-tb', '--transparent-back',
                           action='store_true',
                           help='transparent back file flag')
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='show verbose messages')
    args = argparser.parse_args()

    back_file = args.back_file
    front_file = args.front_file
    workspace_dir = args.workspace_dir
    output_filename = args.output_filename
    verbose = args.verbose

    frames = get_gif_frames(front_file)
    write_frames(frames, workspace_dir)

    pngs = get_images(workspace_dir)

    back_im = Image.open(back_file)
    if back_im.size != pngs[0].size:
        back_im=back_im.resize(pngs[0].size)

    if args.transparent_front:
        back_im = transparent_png(back_im)
    fixed_pics = [composite(back_im, front_im) for front_im in pngs]
    if args.transparent_back:
        fixed_pics = [transparent_gif_frame(x) for x in fixed_pics]

    x = fixed_pics[0].copy()  # swap position
    fixed_pics[0] = fixed_pics[1].copy()
    fixed_pics[1] = x.copy()
    fixed_pics.append(fixed_pics[0].copy())
    im = fixed_pics[1].copy()
    im.save(output_filename, save_all=True, optimize=False, append_images=fixed_pics[2:], duration=50, loop=0,
            transparency=255, disposal=2)
    print(f"Saved {output_filename}")


if __name__ == '__main__':
    main()
