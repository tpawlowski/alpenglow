import sys
sys.path.append('..')
import skimage.external.tifffile as tiff
import skimage as skimage
import numpy as np

# example use case
# from skimage import data
# generate(data.camera(), 4)


def generate(image, stripes, destination='.', overlap=0.25, blur_levels=10, margins=(0, 38, 19)):
    inverted_image = skimage.util.invert(image)
    height = inverted_image.shape[1]
    stripe_height = int(height / (stripes - (stripes - 1) * overlap))
    overlap_height = int(stripe_height * overlap)

    for blur_id, number in enumerate(np.linspace(0.0, 3.0, num=blur_levels)):
        blurred_image = (skimage.filters.gaussian(image, number)*255).astype('uint8')
        blurred_inverted_image = (skimage.filters.gaussian(inverted_image, number)*255).astype('uint8')

        for stripe_id in range(stripes):
            margin_left = margins[stripe_id % len(margins)]
            margin_right = max(margins) - margin_left
            rows_from = (stripe_height - overlap_height) * stripe_id
            rows_to = rows_from + stripe_height

            stripe = blurred_image[rows_from:rows_to]
            stripe_invert = blurred_inverted_image[rows_from:rows_to]

            padded_stripe = np.pad(stripe, ((0, 0), (margin_left, margin_right)), 'constant', constant_values=(0))
            padded_stripe_invert = np.pad(stripe_invert, ((0, 0), (margin_left, margin_right)), 'constant', constant_values=(0))
            output_image = np.vstack((padded_stripe, padded_stripe_invert))

            tiff.imsave("%s/%02d_%02d.tif" % (destination, stripe_id, blur_id), output_image)
