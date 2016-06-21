import os
import sys, getopt
import core
import warnings
warnings.filterwarnings("ignore")

working_dir = os.getcwd()
img_path = None
help_msg = '\n#For help:\n' \
           '> wvlt.py -h\n' \
           '\n#Encode picture:\n' \
           '> wvlt.py -e <inputfile> [color_mode, mode, threshold]\n' \
           '\n#Decode picture:\n' \
           '> wvlt.py -d <inputfile> [color_mode, mode]\n' \
           '\n#Compess picture:\n' \
           '> wvlt.py -c <inputfile> [color_mode, mode, threshold]\n' \
           '\n#Merge two pictures with different compression rate:\n' \
           '> wvlt.py -m <inputfile1> [<inputfile2>, color_mode, mode, threshold_1, threshold_2]\n' \
           '\n#Save result to file:\n' \
           '> wvlt.py -[edcm] <inputfile1> -s <outputfile> [<inputfile2>, color_mode, mode, threshold_1, threshold_2]  \n' \
           '\n#Use verbose mod:\n' \
           'wvlt.py -[vedcm]\n'


def cdisp(argv):
    try:
        opts, args = getopt.getopt(argv, "e:d:c:m:g:s:v", ["encode=", "decode=", "compress=", "merge=", "save="])
        print(opts)
        print(args)
        if len(opts) == 0:
            print(help_msg)
    except getopt.GetoptError:
        print(help_msg)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_msg)
            sys.exit()
        elif opt in ("-e", "--encode"):   #encode
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"
            threshold = float(args[2]) if len(args) > 2 else 0.05
            img = core.encode(img_path, color_mode, mode, threshold)
        elif opt in ("-d", "--decode"):   #decode not works\\\\\\\\\\\\\\\\\\
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"

            img = core.decode(img_path, color_mode, mode)
        elif opt in ("-c", "--compress"):
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"
            threshold = float(args[2]) if len(args) > 2 else 0.05
            encoded_img = core.encode(img_path, color_mode, mode, threshold)
            img = core.decode(encoded_img,color_mode,mode)
        elif opt in ("-m", "--merge"):   #merge
            img_path_1 = arg
            img_path_2 = args[0]
            color_mode = args[1] if len(args) > 1 else "F"
            mode = args[2] if len(args) > 2 else "D2"
            threshold_1 = float(args[3]) if len(args) > 3 else 0.01
            threshold_2 = float(args[4]) if len(args) > 3 else 0.01
            encoded_img_1 = core.encode(img_path_1, color_mode, mode, threshold_1)
            encoded_img_2 = core.encode(img_path_2, color_mode, mode, threshold_2)
            img = core.compression_merge(encoded_img_1, encoded_img_2, mode)
        elif opt in ("-g", "--file"):
            if arg == '':
                img_path = choose_image()
            else:
                img_path = arg
            color_mode = args[0] if len(args) > 0 else "RGB"
            mode = args[1] if len(args) > 1 else "D2"
            threshold = float(args[2]) if len(args) > 2 else 0.05
            encoded_img = core.exp(img_path, color_mode, mode, threshold)
            # img = core.decode(encoded_img, color_mode, mode)
        elif opt in ("-s", "--save"):   #save as image
            core.save(img, arg)
        elif opt == "-v":   #verbose
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