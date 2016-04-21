import os
import sys, getopt
import core
import warnings
warnings.filterwarnings("ignore")

working_dir = os.getcwd()
img_path = None


def cdisp(argv):
    try:
        opts, args = getopt.getopt(argv, "e:d:c:m:s:v", ["file=", "outfile="])
        # print(args)
        # print(opts)
    except getopt.GetoptError:
        print('*** wvlt.py -[ed] <inputfile> -s <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('wvlt.py -[ed] <inputfile> -s <outputfile>')
            sys.exit()
        elif opt in ("-e", "--file"):   #encode
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"
            threshold = float(args[2]) if len(args) > 2 else 0.05
            img = core.encode(img_path, color_mode, mode, threshold)
        elif opt in ("-d", "--file"):   #decode not works\\\\\\\\\\\\\\\\\\
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"

            img = core.decode(img_path, color_mode, mode)
        elif opt in ("-c", "--file"):
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"
            threshold = float(args[2]) if len(args) > 2 else 0.05
            encoded_img = core.encode(img_path, color_mode, mode, threshold)
            img = core.decode(encoded_img,color_mode,mode)
        elif opt in ("-m", "--file"):
            img_path_1 = arg
            img_path_2 = args[0]
            color_mode = args[1] if len(args) > 1 else "F"
            mode = args[2] if len(args) > 2 else "D2"
            threshold_1 = float(args[3]) if len(args) > 3 else 0.05
            threshold_2 = float(args[4]) if len(args) > 4 else 0.05
            encoded_img_1 = core.encode(img_path_1, color_mode, mode, threshold_1)
            encoded_img_2 = core.encode(img_path_2, color_mode, mode, threshold_2)
            img = core.merge(encoded_img_1, encoded_img_2, mode)
        elif opt in ("-s", "--file"):
            core.save(img, arg)
        elif opt == "-v":
            core.verbose = True
            print("Verbose: " + str(core.verbose))



def choose_image():
    res_path = working_dir + "/res/"
    print("Available images from standard dir:")
    i = 0
    for files in os.listdir(res_path):
        print(str(i)+") "+files)
        i+=1
    try:
        return res_path+os.listdir(res_path)[int(input("> Choose image: "))]
    except(IndexError):
        print("***  Image not found. ***")
    except(Exception):
        print("***  Image not found. ***")