from PIL import Image
import numpy as np
import sys
from math import sqrt

verbose = False
sizes = [2 ** i for i in range(1, 12)]  # Image sizes given by power of 2

CL_D2 = [1/sqrt(2), 1/sqrt(2)]              # D2 coefficients of low frequency filter
CL_D4 = [(1 + sqrt(3)) / (4 * sqrt(2)),     # D4 coefficients of low frequency filter
        (3 + sqrt(3)) / (4 * sqrt(2)),
        (3 - sqrt(3)) / (4 * sqrt(2)),
        (1 - sqrt(3)) / (4 * sqrt(2))]

def get_hpf_coeffs(CL):            # Coefficients of high frequency filter
    """ Return list with coefficients of high frequency filter """
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
    # imageT = image.copy()       # Copy the original image to convert ######################
    imageT = image
    for i in range(h):          # Process the lines
        imageT[i, :] = pconv(imageT[i, :], CL, CH)
    # print(imageT)
    for i in range(w):          # Process the columns
        imageT[:, i] = pconv(imageT[:, i], CL, CH)
    # print(imageT)

    # data = imageT
    data = imageT.copy()  ##########################BAD
    data[0:h / 2, 0:w / 2] = imageT[0:h:2, 0:w:2]   # top-left
    data[h / 2:h, 0:w / 2] = imageT[1:h:2, 0:w:2]   # bottom-left
    data[0:h / 2, w / 2:w] = imageT[0:h:2, 1:w:2]   # top-right
    data[h / 2:h, w / 2:w] = imageT[1:h:2, 1:w:2]   # bottom-right

    return data

def idwt2(data, CL):
    w, h = data.shape

    # Rearrange the columns and rows back
    # imageT = data
    imageT = data.copy()  #####################
    imageT[0:h:2, 0:w:2] = data[0:h/2, 0:w/2]
    imageT[1:h:2, 0:w:2] = data[h/2:h, 0:w/2]
    imageT[0:h:2, 1:w:2] = data[0:h/2, w/2:w]
    imageT[1:h:2, 1:w:2] = data[h/2:h, w/2:w]

    CH = get_hpf_coeffs(CL)
    iCL, iCH = get_icoeffs(CL, CH)
    image = imageT.copy()               # Copy the original image to convert
    for i in range(w):                  # Process the columns
        image[:, i] = pconv(image[:, i], iCL, iCH, delta=len(iCL)-2)

    for i in range(h):                  # Process the lines
        image[i, :] = pconv(image[i, :], iCL, iCH, delta=len(iCL)-2)

    return image


def open_image_as_array(path, open_mode, color_mode):
    image = adapt_img_size(Image.open(path, open_mode).convert(color_mode))
    if is_rgb_color_mode(color_mode):
        image_ch = np.array(get_channels(image))
    else:
        image_ch = np.array(image)
    image.close
    return image_ch


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

    image_ch = open_image_as_array(path, "r", color_mode)

    CL = check_mode(mode)
    if is_rgb_color_mode(color_mode):
        encoded_img = encoding_rgb(image_ch, CL, threshold)
    else:
        encoded_img = encoding_grayscale(image_ch, CL, threshold, color_mode)

    print("--- Encoding DONE ---")
    return encoded_img

def encoding_grayscale(image_ch, CL, threshold, color_mode):
    data = image_ch / 255
    w, h = data.shape
    while w >= len(CL) and h >= len(CL):
        data[0:w, 0:h] = dwt2(data[0:w, 0:h], CL)
        w /= 2
        h /= 2
    show_image_from_nmlz_data(data, color_mode)
    print("Quantization with parameter "+str(threshold)+" ...")
    data[abs(data) < threshold] = 0
    show_image_from_nmlz_data(data, color_mode)
    encoded_img = Image.fromarray(data * 255, color_mode)
    return encoded_img

def encoding_rgb(image_ch, CL, threshold):
    image_ch = [image_ch[0] / 255, image_ch[1] / 255, image_ch[2] / 255]
    w = len(image_ch[0][0])
    h = len(image_ch[0])
    while w >= len(CL) and h >= len(CL):
        image_ch[0][0:w, 0:h] = dwt2(image_ch[0][0:w, 0:h], CL)
        image_ch[1][0:w, 0:h] = dwt2(image_ch[1][0:w, 0:h], CL)
        image_ch[2][0:w, 0:h] = dwt2(image_ch[2][0:w, 0:h], CL)
        w /= 2
        h /= 2
    show_image_from_nmlz_data(image_ch, color_mode="RGB")
    print("Quantization with parameter " + str(threshold) + " ...")
    image_ch[0][abs(image_ch[0]) < threshold] = 0
    image_ch[1][abs(image_ch[1]) < threshold] = 0
    image_ch[2][abs(image_ch[2]) < threshold] = 0
    show_image_from_nmlz_data(image_ch, color_mode="RGB")
    ch = [image_ch[0] * 255, image_ch[1] * 255, image_ch[2] * 255]
    encoded_img = image_from_rgb_channels(ch[0], ch[1], ch[2])
    return encoded_img

def decode(path, color_mode="F", mode="D2"):
    print("--- Decoding block ---")
    print("Color mode: " + color_mode)
    print("Mode: " + mode)

    if isinstance(path, str):
        image_ch = open_image_as_array(path, "r", color_mode)
    else:
        if is_rgb_color_mode(color_mode):
            image_ch = np.array(get_channels(path))
        else:
            image_ch = np.array(path)
        color_mode = path.mode
    show_image_from_nmlz_data(image_ch, color_mode)
    CL = check_mode(mode)

    if is_rgb_color_mode(color_mode):
        decoded_img = decode_rgb(image_ch, CL)
    else:
        decoded_img = decode_grayscale(image_ch, CL, color_mode)
    Image._show(decoded_img)
    print("--- Decoding DONE ---")
    return decoded_img

def decode_grayscale(image_ch, CL, color_mode):
    data = image_ch / 255
    im_width, im_heigh = data.shape
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        data[0:w, 0:h] = idwt2(data[0:w, 0:h], CL)
        w *= 2
        h *= 2

    decoded_img = Image.fromarray(data * 255, color_mode)
    # if verbose: Image._show(decoded_img)
    return decoded_img

def decode_rgb(image_ch, CL):
    image_ch = [image_ch[0] / 255, image_ch[1] / 255, image_ch[2] / 255]
    im_width, im_heigh = len(image_ch[0][0]), len(image_ch[0])
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        image_ch[0][0:w, 0:h] = idwt2(image_ch[0][0:w, 0:h], CL)
        image_ch[1][0:w, 0:h] = idwt2(image_ch[1][0:w, 0:h], CL)
        image_ch[2][0:w, 0:h] = idwt2(image_ch[2][0:w, 0:h], CL)
        w *= 2
        h *= 2
    show_image_from_nmlz_data(image_ch, color_mode="RGB")
    image_ch = [image_ch[0] * 255, image_ch[1] * 255, image_ch[2] * 255]
    decoded_img = image_from_rgb_channels(image_ch[0], image_ch[1], image_ch[2])
    return decoded_img

def compression_merge(img1, img2, mode):
    color_mode = img1.mode
    print('IMG1: '+str(img1.width))
    print('IMG2: ' + str(img2.width))
    if img1.width < img2.width:
        img2 = img2.resize((img1.width, img1.width))
    else:
        img1 = img1.resize((img2.width, img2.width))
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

    img = adapt_img_size(Image.open(path, "r").convert("RGB"))
    ch = np.array(get_channels(img))

    #############ENCODE

    CL = check_mode(mode)
    ch = [ch[0]/255,ch[1]/255,ch[2]/255 ]

    w = len(ch[0][0])
    h = len(ch[0])
    while w >= len(CL) and h >= len(CL):
        ch[0][0:w, 0:h] = dwt2(ch[0][0:w, 0:h], CL)
        ch[1][0:w, 0:h] = dwt2(ch[1][0:w, 0:h], CL)
        ch[2][0:w, 0:h] = dwt2(ch[2][0:w, 0:h], CL)
        w /= 2
        h /= 2
    show_image_from_nmlz_data(ch, color_mode)
    print("Quantization with parameter " + str(threshold) + " ...")
    ch[0][abs(ch[0]) < threshold] = 0
    ch[1][abs(ch[1]) < threshold] = 0
    ch[2][abs(ch[2]) < threshold] = 0
    show_image_from_nmlz_data(ch, color_mode)
    print("--- Encoding DONE ---")

    ##############################DECODE
    im_width, im_heigh = len(ch[0][0]),len(ch[0])
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        ch[0][0:w, 0:h] = idwt2(ch[0][0:w, 0:h], CL)
        ch[1][0:w, 0:h] = idwt2(ch[1][0:w, 0:h], CL)
        ch[2][0:w, 0:h] = idwt2(ch[2][0:w, 0:h], CL)
        w *= 2
        h *= 2

    ch = [ch[0] * 255, ch[1] * 255, ch[2] * 255]
    Image._show(image_from_rgb_channels(ch[0], ch[1], ch[2]))

def get_channels(image):
    """ Return list of RGB channels from image """
    w = image.width
    h = image.height
    red_ch = [[0 for i in range(w)] for i in range(h)]
    green_ch = [[0 for i in range(w)] for i in range(h)]
    blue_ch = [[0 for i in range(w)] for i in range(h)]
    for i in range(0, w):
        for j in range(0, h):
            r,g,b = image.getpixel((i, j))
            red_ch[i][j] = r
            green_ch[i][j] = g
            blue_ch[i][j] = b
    return [red_ch, green_ch, blue_ch]

def image_from_rgb_channels(red_ch, green_ch, blue_ch):
    """ Return object of Image from RGB channels """
    w = len(red_ch[0])
    h = len(red_ch)
    img = Image.new("RGB", (w,h))
    for i in range(0, w):
        for j in range(0, h):
            img.putpixel((i,j),(int(red_ch[i][j]), int(green_ch[i][j]), int(blue_ch[i][j])))
    return img

def check_mode(mode):
    """ Return list with matched coefficients of low frequency filter """
    if mode == "D2":
        CL = CL_D2
    elif mode == "D4":
        CL = CL_D4
    else:
        print("*** Unknown encode mod: " + mode + " ***")
        sys.exit(1)
    return CL

def is_rgb_color_mode(color_mode):
    if color_mode == "RGB":
        return True
    else:
        return False

def show_image_from_nmlz_data(data, color_mode):
    if not verbose: return
    if is_rgb_color_mode(color_mode):
        ch = [data[0] * 255, data[1] * 255, data[2] * 255]
        Image._show(image_from_rgb_channels(ch[0], ch[1], ch[2]))
    else:
        Image._show(Image.fromarray(data * 255, color_mode))


def save(img, path):
    """ Save image on disk by path """
    print("Saving to "+str(path)+" ...")
    img = img.convert("L")
    img.save(path)
