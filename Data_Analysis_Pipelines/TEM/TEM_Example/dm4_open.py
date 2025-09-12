import dm4
from PIL import Image
import numpy as np

# Open the DM4 file using a context manager
with dm4.DM4File.open("200kV_100kX_OneView_0043.dm4") as dm4data:
    tags = dm4data.read_directory()

    # Navigate through the tags to locate image data and dimensions
    image_data_tag = tags.named_subdirs['ImageList'].unnamed_subdirs[1].named_subdirs['ImageData']
    image_tag = image_data_tag.named_tags['Data']

    # Read dimensions
    XDim = dm4data.read_tag_data(image_data_tag.named_subdirs['Dimensions'].unnamed_tags[0])
    YDim = dm4data.read_tag_data(image_data_tag.named_subdirs['Dimensions'].unnamed_tags[1])

    # Read the image data
    np_array = np.array(dm4data.read_tag_data(image_tag), dtype=np.uint16)
    np_array = np.reshape(np_array, (YDim, XDim))

# Save the image outside the context
output_fullpath = "200kV_100kX_OneView_0043.tif"
image = Image.fromarray(np_array, 'I;16')
image.save(output_fullpath)
print("Image saved successfully:", output_fullpath)
