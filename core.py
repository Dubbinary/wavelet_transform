from PIL import Image
import numpy as np
import sys
from math import sqrt

verbose = False
sizes = [2 ** i for i in range(1, 12)]

CL_D2 = [1/sqrt(2), 1/sqrt(2)]              # D2 coefficients of low frequency filter
CL_D4 = [(1 + sqrt(3)) / (4 * sqrt(2)),     # D4 coefficients of low frequency filter
        (3 + sqrt(3)) / (4 * sqrt(2)),
        (3 - sqrt(3)) / (4 * sqrt(2)),
        (1 - sqrt(3)) / (4 * sqrt(2))]
CL_D6 = [   0.47046721 / sqrt(2),  # D6 coefficients of low frequency filter
            1.14111692 / sqrt(2),
            0.650365 / sqrt(2),
            -0.19093442 / sqrt(2),
            -0.12083221 / sqrt(2),
            0.0498175 / sqrt(2),]


def get_hpf_coeffs(CL):            # Coefficients of high frequency filter
    N = len(CL)                    # The number of coefficients
    CH = [(-1)**k * CL[N - k - 1]  # The coefficients in reverse order with alternating sign
        for k in range(N)]
    return CH

def pconv(data, CL, CH, delta = 0):
    assert(len(CL) == len(CH))          # Dimensions lists factors should be equal
    N = len(CL)
    M = len(data)
    out = []                            # List a result, until empty
    for k in range(0, M, 2):            # Loop through the numbers 0, 2, 4 ...
        sL = 0                          # Low-frequency coefficient
        sH = 0                          # High-frequency coefficient
        for i in range(N):              # We find ourselves weighted sums
            sL += data[(k + i - delta) % M] * CL[i]
            sH += data[(k + i - delta) % M] * CH[i]
        out.append(sL)
        out.append(sH)
    return out


def get_icoeffs(CL, CH):
    assert(len(CL) == len(CH))          # Dimensions lists factors should be equal
    iCL = []                            # The coefficients of the first line
    iCH = []                            # The coefficients of the second line
    # for k in range(0, len(CL), 3):
    for k in range(0, len(CL), 2):
        iCL.extend([CL[k-2], CH[k-2]])
        iCH.extend([CL[k-1], CH[k-1]])
    return (iCL, iCH)


def dwt2(image, CL):
    CH = get_hpf_coeffs(CL)     # Calculate the missing coefficients
    w, h = image.shape
    imageT = image.copy()       # Copy the original image to convert
    for i in range(h):          # Process the lines
        imageT[i, :] = pconv(imageT[i, :], CL, CH)
    # print(imageT)
    for i in range(w):          # Process the columns
        imageT[:, i] = pconv(imageT[:, i], CL, CH)
    # print(imageT)
    data = imageT.copy()
    data[0:h / 2, 0:w / 2] = imageT[0:h:2, 0:w:2]   # top-left
    data[h / 2:h, 0:w / 2] = imageT[1:h:2, 0:w:2]   # bottom-left
    data[0:h / 2, w / 2:w] = imageT[0:h:2, 1:w:2]   # top-right
    data[h / 2:h, w / 2:w] = imageT[1:h:2, 1:w:2]   # bottom-right
    return data

def idwt2(data, CL):
    w, h = data.shape

    # Rearrange the columns and rows back
    imageT = data.copy()
    imageT[0:h:2, 0:w:2] = data[0:h/2, 0:w/2]
    imageT[1:h:2, 0:w:2] = data[h/2:h, 0:w/2]
    imageT[0:h:2, 1:w:2] = data[0:h/2, w/2:w]
    imageT[1:h:2, 1:w:2] = data[h/2:h, w/2:w]

    CH = get_hpf_coeffs(CL)
    iCL, iCH = get_icoeffs(CL, CH)
    image = imageT.copy()               # Copy the original image to convert
    for i in range(w):                  # Process the columns
        image[:, i] = pconv(image[:, i], iCL, iCH, delta=len(iCL)-2)
    # print(image)
    for i in range(h):                  # Process the lines
        image[i, :] = pconv(image[i, :], iCL, iCH, delta=len(iCL)-2)
    # print(image)

    return image


def open_image(path, mode, color_mode):
    image = Image.open(path, mode).convert(color_mode)
    im_width = image.width
    im_heigh = image.height
    if im_heigh != im_width or im_width not in sizes:
        image = adapt_img_size(image)
    image_array = np.array(image)
    print(image)
    image.close
    return image_array


def adapt_img_size(img):
    print("Resizing image...")
    im_width = img.width
    im_heigh = img.height
    if im_heigh < im_width:
        side = im_heigh
    else:
        side = im_width

    for i in sizes:
        if side < i:
            side = sizes[sizes.index(i)-1]
            break

    img = img.resize((side, side))
    return img


def encode(path, color_mode="F", mode="D2", threshold=0.05):
    print("--- Encoding block ---")
    print("Color mode: " + color_mode)
    print("Mode: " + mode)
    print("Treshhold: " + str(threshold))

    image_arr = open_image(path, "r", color_mode)
    if verbose: Image._show(Image.fromarray(image_arr, color_mode))
    CL = check_mode(mode)

    data = image_arr.copy()/255
    print(CL)

    w, h = data.shape
    while w >= len(CL) and h >= len(CL):
        data[0:w, 0:h] = dwt2(data[0:w, 0:h], CL)
        w /= 2
        h /= 2

    # data = dwt2(data, CL)
    if verbose: Image._show(Image.fromarray(data * 255, color_mode))
    encoded_img = data
    print("Quantization with parameter "+str(threshold)+" ...")
    encoded_img[abs(data) < threshold] = 0
    # print(encoded_img*255)
    encoded_img = Image.fromarray(encoded_img * 255, color_mode)
    if verbose: Image._show(encoded_img)
    print("--- Encoding DONE ---")
    return encoded_img

def decode(path, color_mode="F", mode="D2"):
    print("--- Decoding block ---")
    print("Color mode: " + color_mode)
    print("Mode: " + mode)

    if isinstance(path, str):
        image_arr = open_image(path, "r", color_mode)
    else:
        image_arr = np.array(path)
        color_mode = path.mode
    # print(image_arr)
    CL = check_mode(mode)
    if verbose: Image._show(Image.fromarray(image_arr, color_mode))
    data = image_arr.copy() / 255
    print(CL)
    # print(data)

    im_width, im_heigh = data.shape
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        data[0:w, 0:h] = idwt2(data[0:w, 0:h], CL)
        w *= 2
        h *= 2
    # data = idwt2(data, CL)
    # print(data*255)
    decoded_img = Image.fromarray(data * 255, color_mode)
    if verbose: Image._show(decoded_img)
    print("--- Decoding DONE ---")
    return decoded_img

def merge(img1, img2, mode):
    color_mode = img1.mode
    image1_arr = np.array(img1)
    image2_arr = np.array(img2)
    img=Image.fromarray(image1_arr+image2_arr, color_mode)
    merged = decode(img, color_mode, mode)
    Image._show(merged)
    return merged

def exp(path, color_mode="F", mode="D2", threshold=0.05):
    print("--- Encoding block ---")
    print("Color mode: " + color_mode)
    print("Mode: " + mode)
    print("Treshhold: " + str(threshold))
    img= Image.open(path, "r")
    Image._show(img)
    img_arr = np.array(img)
    ch = get_channels(img)
    Image._show(Image.fromarray(np.array(img_arr), color_mode))
    # print(ch)
    # print(image_arr)
    # Image._show(Image.fromarray(np.array(ch), color_mode))
    # data = image_arr.copy() / 255
    # print(data)
    # Image._show(Image.fromarray(data, color_mode))
    print()
    # Image._show(Image.fromarray(data*255, color_mode))
    # image_arr = open_image(path, "r", color_mode)
    # if verbose: Image._show(Image.fromarray(image_arr, color_mode))
    # CL = check_mode(mode)
    #
    # data = image_arr.copy() / 255
    # print(CL)
    #
    # w, h = data.shape
    # while w >= len(CL) and h >= len(CL):
    #     data[0:w, 0:h] = dwt2(data[0:w, 0:h], CL)
    #     w /= 2
    #     h /= 2
    #
    # # data = dwt2(data, CL)
    # if verbose: Image._show(Image.fromarray(data * 255, color_mode))
    # encoded_img = data
    # print("Quantization with parameter " + str(threshold) + " ...")
    # encoded_img[abs(data) < threshold] = 0
    # # print(encoded_img*255)
    # encoded_img = Image.fromarray(encoded_img * 255, color_mode)
    # if verbose: Image._show(encoded_img)
    print("--- Encoding DONE ---")

def get_channels(img):
    w = img.width
    h = img.height
    print("Width: "+str(w)+" \nHeight: "+str(h))
    red_ch = [[0 for i in range(w)] for i in range(h)]
    green_ch = [[0 for i in range(w)] for i in range(h)]
    blue_ch = [[0 for i in range(w)] for i in range(h)]
    for i in range(0, w):
        for j in range(i, h):
            r,g,b = img.getpixel((i, j))
            red_ch[i][j] = r
            green_ch[i][j] = g
            blue_ch[i][j] = g
    # print(np.array(red_ch))
    # Image._show(Image.fromarray(np.array(red_ch) , "L"))
    # Image._show(Image.fromarray(np.array(green_ch), "L"))
    # Image._show(Image.fromarray(np.array(blue_ch), "L"))
    return (red_ch, green_ch, blue_ch)

def check_mode(mode):
    if mode == "D2":
        CL = CL_D2
    elif mode == "D4":
        CL = CL_D4
    elif mode == "D6":
        CL = CL_D6
    else:
        print("*** Unknown encode mod: " + mode + " ***")
        sys.exit(1)
    return CL




def save(img, path):
    print("Saving to "+str(path)+" ...")
    img = img.convert("L")
    img.save(path)
