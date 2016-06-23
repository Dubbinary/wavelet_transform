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
    """
    :param CL: Coefficients of low frequency filter
    :return: Return list with coefficients of high frequency filter
    """
    N = len(CL)                    # The number of coefficients
    CH = [(-1)**k * CL[N - k - 1]  # The coefficients in reverse order with alternating sign
        for k in range(N)]
    return CH

def pconv(data, CL, CH, delta = 0):
    """
    :param data: Data on which performed transformation
    :param CL: Coefficients of low frequency filter
    :param CH: Coefficients of high frequency filter
    :param delta: Parameter which provide shift of coefficients
    :return: Return transformed data
    """
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
    """
    :param CL: Coefficients of low frequency filter
    :param CH: Coefficients of high frequency filter
    :return: Return coefficients that used in backward transformation
    """
    assert(len(CL) == len(CH))          # Dimensions lists factors should be equal
    iCL = []                            # The coefficients of the first line
    iCH = []                            # The coefficients of the second line
    for k in range(0, len(CL), 2):
        iCL.extend([CL[k-2], CH[k-2]])
        iCH.extend([CL[k-1], CH[k-1]])
    return (iCL, iCH)

def dwt2(image, CL):
    """
    :param image: two-dimensional array representation of image
    :param CL: Coefficients of low frequency filter
    :return: Return two-dimensional transformation of image
    """
    CH = get_hpf_coeffs(CL)     # Calculate the missing coefficients
    w, h = image.shape
    imageT = image.copy()       # Copy the original image to convert ######################
    for i in range(h):          # Process the lines
        imageT[i, :] = pconv(imageT[i, :], CL, CH)
    for i in range(w):          # Process the columns
        imageT[:, i] = pconv(imageT[:, i], CL, CH)
    # Rearrange the columns and rows isolating filters
    data = imageT.copy()
    data[0:h / 2, 0:w / 2] = imageT[0:h:2, 0:w:2]   # top-left
    data[h / 2:h, 0:w / 2] = imageT[1:h:2, 0:w:2]   # bottom-left
    data[0:h / 2, w / 2:w] = imageT[0:h:2, 1:w:2]   # top-right
    data[h / 2:h, w / 2:w] = imageT[1:h:2, 1:w:2]   # bottom-right
    return data

def idwt2(data, CL):
    """
    :param data: two-dimensional transformed image
    :param CL: Coefficients of low frequency filter
    :return: Return two-dimensional backward transformation of image
    """
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
    for i in range(h):                  # Process the lines
        image[i, :] = pconv(image[i, :], iCL, iCH, delta=len(iCL)-2)
    return image

def open_image_as_array(path, open_mode, color_mode):
    """
    :param path: Path to image on disc
    :param open_mode: Mode to open image
    :param color_mode: Image color mode
    :return: Return image as numpy array object
    """
    image = adapt_img_size(Image.open(path, open_mode).convert(color_mode))
    if verbose:
        Image._show(image)
    if is_rgb_color_mode(color_mode):
        image_ch = np.array(get_channels(image))
    else:
        image_ch = np.array(image)
    image.close
    return image_ch

def adapt_img_size(img):
    """
    :param img: Image object
    :return: Image object adapted to transformation
    """
    im_width = img.width
    im_heigh = img.height
    if im_heigh == im_width:
        return img
    if verbose:
        print("Resizing image...")
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
    """
    :param path: Path to image on disc
    :param color_mode: Image color mode [F, RGB]
    :param mode: Mode of transformation [D2, D4]
    :param threshold: Parameter of quantization [0..1]
    :return: Encoded numpy image array
    """
    image_ch = open_image_as_array(path, "r", color_mode)
    if verbose:
        print("ENCODING ...\n",
              "\nColor mode: " + color_mode,
              "\nTransformation mode: " + mode,
              "\nTreshhold: " + str(threshold))
    CL = check_mode(mode)
    if is_rgb_color_mode(color_mode):
        encoded_img = encoding_rgb(image_ch, CL, threshold)
    else:
        encoded_img = encoding_grayscale(image_ch, CL, threshold[0])
    return encoded_img

def encoding_grayscale(image_ch, CL, threshold):
    """
    :param image_ch: Numpy array of image channel
    :param CL: Coefficients of low frequency filter
    :param threshold: threshold: Parameter of quantization [0..1]
    :return: Encoded numpy image array
    """
    image_ch = image_ch / 255
    w, h = image_ch.shape
    while w >= len(CL) and h >= len(CL):
        image_ch[0:w, 0:h] = dwt2(image_ch[0:w, 0:h], CL)
        w /= 2
        h /= 2
    show_image_from_nmlz_data(image_ch, color_mode="F")
    if verbose:
        print("Quantization with parameter: ",
              "\nGRAYSCALE_CHANNEL = "+str(threshold))
    image_ch[abs(image_ch) < threshold] = 0
    show_image_from_nmlz_data(image_ch, color_mode="F")
    return image_ch

def encoding_rgb(image_ch, CL, threshold):
    """
    :param image_ch: Numpy array of image channels (red, green, blue)
    :param CL: Coefficients of low frequency filter
    :param threshold: threshold: Parameter of quantization [0..1]
    :return: Encoded numpy image array
    """
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
    if verbose:
        print("Quantization with parameter: ",
              "\nRED_CHANNEL = "+str(threshold[0]),
              "\nGREEN_CHANNEL = " + str(threshold[1]),
              "\nBLUE_CHANNEL = " + str(threshold[2]))
    image_ch[0][abs(image_ch[0]) < threshold[0]] = 0
    image_ch[1][abs(image_ch[1]) < threshold[1]] = 0
    image_ch[2][abs(image_ch[2]) < threshold[2]] = 0
    show_image_from_nmlz_data(image_ch, color_mode="RGB")
    return image_ch

def decode(image_ch, color_mode="F", mode="D2"):
    """
    :param image_ch: Numpy array of encoded image channel(s)
    :param color_mode: Image color mode [F, RGB]
    :param mode: Mode of transformation [D2, D4]
    :return: Decoded image object
    """
    if verbose:
        print("DECODING ...\n",
              "\nColor mode: " + color_mode,
              "\nTransformation mode: " + mode)
    CL = check_mode(mode)
    if is_rgb_color_mode(color_mode):
        decoded_img = decode_rgb(image_ch, CL)
    else:
        decoded_img = decode_grayscale(image_ch, CL)
    if verbose:
        Image._show(decoded_img)
    return decoded_img

def decode_grayscale(image_ch, CL):
    """
    :param image_ch: Numpy array of encoded image channel (grayscale)
    :param CL: Coefficients of low frequency filter
    :return: Decoded image object
    """
    im_width, im_heigh = image_ch.shape
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        image_ch[0:w, 0:h] = idwt2(image_ch[0:w, 0:h], CL)
        w *= 2
        h *= 2
    decoded_img = Image.fromarray(image_ch * 255, "F")
    return decoded_img

def decode_rgb(image_ch, CL):
    """
    :param image_ch: Numpy array of encoded image channels (red, green, blue)
    :param CL: Coefficients of low frequency filter
    :return: Decoded image object
    """
    im_width, im_heigh = len(image_ch[0][0]), len(image_ch[0])
    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        image_ch[0][0:w, 0:h] = idwt2(image_ch[0][0:w, 0:h], CL)
        image_ch[1][0:w, 0:h] = idwt2(image_ch[1][0:w, 0:h], CL)
        image_ch[2][0:w, 0:h] = idwt2(image_ch[2][0:w, 0:h], CL)
        w *= 2
        h *= 2
    image_ch = [image_ch[0] * 255, image_ch[1] * 255, image_ch[2] * 255]
    decoded_img = image_from_rgb_channels(image_ch[0], image_ch[1], image_ch[2])
    return decoded_img

def get_channels(image):
    """
    :param image: Image object
    :return: Return list of RGB channels from image
    """
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
    """
    :param red_ch: Red image channel
    :param green_ch: Green image channel
    :param blue_ch: Blue image channel
    :return: Return object of Image from RGB channels
    """
    w = len(red_ch[0])
    h = len(red_ch)
    img = Image.new("RGB", (w,h))
    for i in range(0, w):
        for j in range(0, h):
            img.putpixel((i,j),(int(red_ch[i][j]), int(green_ch[i][j]), int(blue_ch[i][j])))
    return img

def check_mode(mode):
    """
    :param mode: Name of transformation mode
    :return: Return list with matched coefficients of low frequency filter
    """
    if mode == "D2":
        CL = CL_D2
    elif mode == "D4":
        CL = CL_D4
    else:
        print("*** Unknown encode mod: " + mode + " ***")
        sys.exit(1)
    return CL

def is_rgb_color_mode(color_mode):
    """ Check is color_mode equals RGB mode"""
    if color_mode == "RGB":
        return True
    else:
        return False

def show_image_from_nmlz_data(data, color_mode):
    """
    Shows image in system compatible Image Viewer
    :param data: Image numpy array
    :param color_mode: Image color mode [F, RGB]
    :return:
    """
    if not verbose: return
    if is_rgb_color_mode(color_mode):
        ch = [data[0] * 255, data[1] * 255, data[2] * 255]
        Image._show(image_from_rgb_channels(ch[0], ch[1], ch[2]))
    else:
        Image._show(Image.fromarray(data * 255, color_mode))

def save(img, path):
    """
    Save image on disk by path
    :param img: Image object
    :param path: Path to save image
    :return:
    """
    if verbose:
        print("Saving to "+str(path)+" ...")
    img.save(path)
