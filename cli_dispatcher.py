import os
import sys, getopt
import core

working_dir = os.getcwd()
img_path = None


def cdisp(argv):
    try:
        opts, args = getopt.getopt(argv, "e:d:s:", ["file=", "outfile="])
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
            mode = args[0] if len(args) > 0 else "D2"
            threshold = float(args[1]) if len(args) > 1 else 0.05
            print("Mode: "+ mode)
            print("Treshhold: "+ str(threshold))
            img = core.encode(img_path, mode, threshold)
        elif opt in ("-d", "--file"):   #decode
            print(arg)
        elif opt in ("-s", "--file"):
            core.save(img, arg)


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