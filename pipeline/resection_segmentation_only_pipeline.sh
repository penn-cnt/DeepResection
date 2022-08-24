# This code uses the given pre-operative and post-operative images and outputs 
# a resection segmentation.

# Usage: resection_pipeline.sh patient_name postop.nii output_dir
# Example: ./pipeline/resection_pipeline.sh 25_f 25_f_postop.nii.gz analysis/25_f

# 6/11/20 - created

# name input variables and mask output filename
patient_id=${1}
postop_file=${2}
output_dir=${3}

# generate predicted mask files in each dimension for the post-operative image
python3 ./scripts/generate_masks.py ${postop_file} ${output_dir}

axial_mask="${output_dir}/predicted_mask_axial.nii.gz"
coronal_mask="${output_dir}/predicted_mask_coronal.nii.gz"
sagittal_mask="${output_dir}/predicted_mask_sagittal.nii.gz"

# generate final predicted mask files for the post-operative image based on 2 majority votes
python3 ./scripts/majority_vote.py ${postop_file} ${axial_mask} ${coronal_mask} ${sagittal_mask} ${output_dir}
