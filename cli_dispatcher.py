import os
import sys, getopt
import core
import warnings
warnings.filterwarnings("ignore")

working_dir = os.getcwd()
img_path = None
help_msg = '\n#For help:\n' \
           '> wvlt.py -h\n' \
           '\n#Compess picture:\n' \
           '> wvlt.py -c <inputfile> [color_mode, mode, [threshold_1,threshold_2,threshold_3]]\n' \
           '\n#Save result to file:\n' \
           '> wvlt.py -c <inputfile1> -s <outputfile> [<inputfile2>, color_mode, mode, [threshold_1, ...]]  \n' \
           '\n#Use verbose mod:\n' \
           '>wvlt.py -vc <inputfile> ...\n' \
           '\nCOLOR_MODE: [F, RGB]' \
           '\nMODE(transformation): [D2, D4]' \
           '\nTHRESHOLD: [0..1]'


def cdisp(argv):
    try:
        opts, args = getopt.getopt(argv, "c:s:v", ["compress="])
        if len(opts) == 0:
            print(help_msg)
    except getopt.GetoptError:
        print(help_msg)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_msg)
            sys.exit()
            img = core.decode(img_path, color_mode, mode)
        elif opt in ("-c", "--compress"):
            img_path = arg
            color_mode = args[0] if len(args) > 0 else "F"
            mode = args[1] if len(args) > 1 else "D2"
            threshold_1 = float(args[2]) if len(args) > 2 else 0.05
            threshold_2 = float(args[3]) if len(args) > 3 else threshold_1
            threshold_3 = float(args[4]) if len(args) > 4 else threshold_1
            encoded_img = core.encode(img_path, color_mode, mode, [threshold_1,threshold_2, threshold_3])
            img = core.decode(encoded_img,color_mode,mode)
        elif opt in ("-s", "--save"):   #save as image
            core.save(img, arg)
        elif opt == "-v":   #verbose
            core.verbose = True
            print("Verbose: " + str(core.verbose))