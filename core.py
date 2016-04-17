from PIL import Image
import numpy as np

from math import sqrt

encoded_img = None
decoded_img = None
im_width = None
im_heigh = None

CL_D2 = [1/sqrt(2), 1/sqrt(2)]              # D2 coefficients of low frequency filter
CL_D4 = [(1 + sqrt(3)) / (4 * sqrt(2)),     # D4 coefficients of low frequency filter
        (3 + sqrt(3)) / (4 * sqrt(2)),
        (3 - sqrt(3)) / (4 * sqrt(2)),
        (1 - sqrt(3)) / (4 * sqrt(2))]


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


def open_image(path, mode):
    image = Image.open(path, mode).convert("F")
    im_width = image.width
    im_heigh = image.height
    sizes = [2 ** i for i in range(1, 11)]
    if im_heigh != im_width or im_width not in sizes:
        image = adapt_img_size(image)

    image_array = np.array(image)
    print(image)
    image.close
    return image_array


def adapt_img_size(img):
    print("Resizing image...")
    sizes = [2**i for i in range(1, 11)]
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


def encode(path, mode=CL_D2, threshold=0.05):
    image = open_image(path, "r")
    Image._show(Image.fromarray(image, 'F'))
    if mode == "D2":
        CL = CL_D2
    elif mode == "D4":
        CL = CL_D4
    data = image.copy()/255

    im_width, im_heigh = data.shape
    w=im_width
    h=im_heigh
    while w >= len(CL) and h >= len(CL):
        data[0:w, 0:h] = dwt2(data[0:w, 0:h], CL)
        w /= 2
        h /= 2
    # Image._show(Image.fromarray(data * 255, 'F'))
    encoded_img = data
    encoded_img[abs(data) < threshold] = 0
    # Image._show(Image.fromarray(encoded_img * 255, 'F'))

    w = h = len(CL)
    while w <= im_width and h <= im_heigh:
        data[0:w, 0:h] = idwt2(data[0:w, 0:h], CL)
        w *= 2
        h *= 2
    decoded_img = Image.fromarray(data * 255, 'F')
    Image._show(decoded_img)
    return decoded_img

def decode():
    pass





def save(img, path):
    print("Saving to "+str(path)+" ...")
    img = img.convert("L")
    img.save(path)