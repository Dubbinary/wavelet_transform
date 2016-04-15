from PIL import Image

file = Image.open("res/1.jpg", "r").convert("L")
file.show()
file.close()