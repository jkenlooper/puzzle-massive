# Prompt for each DigitalOcean access key and export as TF_VAR_* variables.
# See the encrypt_tfvars.sh and decrypt_tfvars.sh if wanting to persist these to
# disk securely.
# Usage: Source the script.
# source secure_tfvars.sh

read -s -p "DigitalOcean API Access Token:
" TF_VAR_do_token
export TF_VAR_do_token

read -s -p "DigitalOcean Spaces access key ID:
" TF_VAR_do_spaces_access_key_id
export TF_VAR_do_spaces_access_key_id

read -s -p "DigitalOcean Spaces secret access key:
" TF_VAR_do_spaces_secret_access_key
export TF_VAR_do_spaces_secret_access_key

echo "
If not deploying new droplets then these can be blank."
read -s -p "DigitalOcean Spaces access key ID for the droplet to use (can be blank):
" TF_VAR_do_app_spaces_access_key_id
export TF_VAR_do_app_spaces_access_key_id

read -s -p "DigitalOcean Spaces secret access key for the droplet to use (can be blank):
" TF_VAR_do_app_spaces_secret_access_key
export TF_VAR_do_app_spaces_secret_access_key
