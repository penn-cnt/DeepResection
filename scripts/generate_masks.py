# This code uses the trained deep learning model to generate mask NIFTI files in each dimension given the NIFTI file for the post-operative MRI

# Usage: python3 generate_masks.py postop.nii out_dir
# Example: python3 generate_masks.py patient1_postop.nii ./patient1_info patient1_mask.nii

# 6/3/22 - created

import sys
from this import d
import numpy as np
import nibabel as nib
import imageio
import os
import tensorflow as tf
import cv2
from keras.models import Model
from keras.layers import Input, Conv2D
from keras.utils.generic_utils import get_custom_objects
import warnings
from skimage.measure import label
import segmentation_models as sm
warnings.filterwarnings("ignore")

def generate_postop(postop, dim):
    if dim == 1:
        total_slices = postop.shape[2]
    elif dim == 2:
        total_slices = postop.shape[1]
    else:
        total_slices = postop.shape[0]
    input_arr = np.zeros((total_slices, 256, 256, 1))
    MAX_IMG = np.max(postop)

    # loop through all slices
    for slice in range(0, total_slices):
        if slice < 10:
            output_file_name = 'temp_img00' + str(slice) + '_postop.png'
        elif slice < 100:
            output_file_name = 'temp_img0' + str(slice) + '_postop.png'
        else:
            output_file_name = 'temp_img' + str(slice) + '_postop.png'
        
        # normalize the pixel values of the slice
        if dim == 1:
            img = postop[:,:,slice]/MAX_IMG
        elif dim == 2:
            img = postop[:,slice,:]/MAX_IMG
        else:
            img = postop[slice,:,:]/MAX_IMG

        # save as a png file
        img = (img*255).astype(np.uint8)
        img = cv2.resize(img, (256, 256))
        imageio.imwrite(output_file_name, img)

        # reload the image
        img_arr = np.asarray(imageio.imread(output_file_name))

        # update the input array
        input_arr[slice,:,:,0] = img_arr

        # remove the png file for memory purposes
        os.remove(output_file_name)

    # rescale pixel values
    input_arr = input_arr / 255.0
    return input_arr

def generate_mask(input_arr, postop, dim, dim_name):
    BACKBONE = 'efficientnetb1'

    base_model = sm.Unet(BACKBONE, encoder_weights=None, classes=1, activation='sigmoid')
    inp = Input(shape=(256, 256, 1))
    l1 = Conv2D(3, (1, 1)) (inp)
    out = base_model(l1)


    model = Model(inp, out, name = base_model.name)
    model.load_weights(f'model/model_{dim_name}.h5')
    #model.load_weights(f'models/model_{fold}_{dim_name}.h5')

    # predict the resected tissue for each slice in the 3D input array
    preds = model.predict(input_arr, verbose = 1)
    preds = (preds > 0.5).astype(np.uint8)

    output = np.zeros(postop.shape)
    total_slices = input_arr.shape[0]

    # adjust the output array dimensions so that they are the same as the original 3D image array
    if dim == 1:
        realX = postop.shape[0]
        realY = postop.shape[1]
        for slice in range(0, total_slices):
            output[:,:,slice] = cv2.resize(preds[slice,:,:,0], (realY, realX))
    elif dim == 2:
        realX = postop.shape[0]
        realY = postop.shape[2]
        for slice in range(0, total_slices):
            output[:,slice,:] = cv2.resize(preds[slice,:,:,0], (realY, realX))
    else:
        realX = postop.shape[1]
        realY = postop.shape[2]
        for slice in range(0, total_slices):
            output[slice,:,:] = cv2.resize(preds[slice,:,:,0], (realY, realX))
    

    # get each continuous object in the mask
    mask_data_int = output.astype(np.uint8)
    labels =label(mask_data_int, connectivity = 2)
    object_labels = list(np.unique(labels))
    object_labels.remove(0)

    # get the continuous object that has the largest volume
    MAX_OBJ = 0
    MAX_OBJ_VOL = 0
    for obj_lab in object_labels:
        vol = np.sum(labels == obj_lab)
        if vol > MAX_OBJ_VOL:
            MAX_OBJ_VOL = vol
            MAX_OBJ = obj_lab

    # remove every other object from the mask
    if MAX_OBJ != 0:
        object_labels.remove(MAX_OBJ)
    for obj_lab in object_labels:
        idx = (labels == obj_lab)
        output[idx] = 0
    return output

# load the post-operative file and convert to a numpy array
POSTOP_FILE = sys.argv[1]
postop = nib.load(POSTOP_FILE)

postop_3D = postop.get_fdata()
patient_name = POSTOP_FILE.split('/')[1]

axial = generate_postop(postop_3D, 1)
coronal = generate_postop(postop_3D, 2)
sagittal = generate_postop(postop_3D, 3)

# define loss measure for the model so that it will compile
def dice_coeff(y_true, y_pred):
    epsilon = 10 ** -7
    intersection = tf.reduce_sum(y_true * y_pred)
    union = tf.reduce_sum(y_true + y_pred)
    dice_score = (2.0 * intersection + epsilon) / (union + epsilon)
    return dice_score

def dice_loss(y_true, y_pred):
    loss = 1 - dice_coeff(y_true, y_pred)
    return loss

get_custom_objects().update({"dice": dice_loss})

# determine the fold of the patient
patient_name = POSTOP_FILE.split('/')[1]

axial_mask = generate_mask(axial, postop_3D, 1, 'axial')
coronal_mask = generate_mask(coronal, postop_3D, 2, 'coronal')
sagittal_mask = generate_mask(sagittal, postop_3D, 3, 'sagittal')

# convert the output array into a NIFTI file
ni_mask_axial = nib.Nifti1Image(axial_mask, postop.affine)
ni_mask_coronal = nib.Nifti1Image(coronal_mask, postop.affine)
ni_mask_sagittal = nib.Nifti1Image(sagittal_mask, postop.affine)
OUTPUT_DIR = sys.argv[2]
nib.save(ni_mask_axial, os.path.join(OUTPUT_DIR, 'predicted_mask_axial.nii.gz'))
nib.save(ni_mask_coronal, os.path.join(OUTPUT_DIR, 'predicted_mask_coronal.nii.gz'))
nib.save(ni_mask_sagittal, os.path.join(OUTPUT_DIR, 'predicted_mask_sagittal.nii.gz'))