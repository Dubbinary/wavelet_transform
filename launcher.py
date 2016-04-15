#import core
import os

print("___ Wavelet transformation program ___")

working_dir = os.getcwd()

for files in os.listdir(working_dir+"/res"):
    print(files)