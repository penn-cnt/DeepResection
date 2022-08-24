# This code uses the given pre-operative and post-operative images and outputs the resection percentages by brain region as a json file
# and prints percent volume resected for each ROI in the brain

# Usage: resection_pipeline.sh patient_name preop.nii postop.nii output_dir
# Example: ./pipeline/resection_pipeline.sh 25_f 25_f_preop.nii.gz 25_f_postop.nii.gz analysis/25_f

# 6/11/20 - created

# define inputs and prompt user for the is_continuous input
patient_id=${1}
preop_file=${2}
postop_file=${3}
output_dir=${4}
preop_onlyfile="$(basename $preop_file)"

# create output directory
mkdir ${output_dir}

# apply an atlas to pre-operative image, register atlas to post-operative image
python3 ./scripts/pre2post.py ${patient_id} ${preop_file} ${postop_file} ${output_dir}

# register DKL atlas to preoperative image
python3 ./scripts/register_atlas_to_preop.py ${patient_id} ${output_dir}/pre2post_${preop_onlyfile} ${output_dir}

# generate predicted mask files in each dimension for the post-operative image
python3 ./scripts/generate_masks.py ${postop_file} ${output_dir}

axial_mask="${output_dir}/predicted_mask_axial.nii.gz"
coronal_mask="${output_dir}/predicted_mask_coronal.nii.gz"
sagittal_mask="${output_dir}/predicted_mask_sagittal.nii.gz"

# generate final predicted mask files for the post-operative image based on 2 majority votes
python3 ./scripts/majority_vote.py ${postop_file} ${axial_mask} ${coronal_mask} ${sagittal_mask} ${output_dir}

# generate a txt file that calculates the resection volume and percent remaining by brain region
mask_file="${output_dir}/predicted_mask.nii.gz"
atlas_file="${output_dir}/${patient_id}_DKT_DL.nii.gz"
atlas_mappings="atlas/dkt_atlas_mappings.txt"

python3 ./scripts/calculate_resected_volumes.py ${postop_file} ${mask_file} ${atlas_file} ${atlas_mappings} ${output_dir}
