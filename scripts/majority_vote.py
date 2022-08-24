# This code uses the generated mask NIFTI files in each dimension to output a final mask NIFTI file, based on majority voting from the previously generated masks.

# Usage: python3 majority_vote.py mask_axial.nii.gz mask_coronal.nii.gz mask_sagittal.nii.gz out_dir
# Example: python3 majority_vote.py patient1_mask_axial.nii.gz patient1_mask_coronal.nii.gz patient1_mask_sagittal.nii.gz ./patient1_info

# 6/3/22 - created

import sys
import numpy as np
import nibabel as nib
import os
from skimage.measure import label

POSTOP_FILE = sys.argv[1]
AXIAL_MASK_FILE = sys.argv[2]
CORONAL_MASK_FILE = sys.argv[3]
SAGITTAL_MASK_FILE = sys.argv[4]
OUTPUT_DIR = sys.argv[5]

try:
    postop = nib.load(POSTOP_FILE)
except:
   postop = nib.load(POSTOP_FILE.replace('.nii', '.nii.gz'))
axial = nib.load(AXIAL_MASK_FILE).get_fdata()
coronal = nib.load(CORONAL_MASK_FILE).get_fdata()
sagittal = nib.load(SAGITTAL_MASK_FILE).get_fdata()

def remove_objs(mask):
    labels =label(mask, connectivity = 2)
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
        mask[idx] = 0
    return mask

combined = axial + coronal + sagittal

#majority_vote_1 = (combined >= 1).astype(np.uint8)
majority_vote_2 = (combined >= 2).astype(np.uint8)
#majority_vote_3 = (combined >= 3).astype(np.uint8)

#majority_vote_1 = remove_objs(majority_vote_1)
majority_vote_2 = remove_objs(majority_vote_2)
#majority_vote_3 = remove_objs(majority_vote_3)

#majority_vote_1 = nib.Nifti1Image(majority_vote_1, postop.affine)
majority_vote_2 = nib.Nifti1Image(majority_vote_2, postop.affine)
#majority_vote_3 = nib.Nifti1Image(majority_vote_3, postop.affine)

#nib.save(majority_vote_1, os.path.join(OUTPUT_DIR, 'predicted_mask_majority_vote_1.nii.gz'))
nib.save(majority_vote_2, os.path.join(OUTPUT_DIR, 'predicted_mask.nii.gz'))
#nib.save(majority_vote_3, os.path.join(OUTPUT_DIR, 'predicted_mask_majority_vote_3.nii.gz'))