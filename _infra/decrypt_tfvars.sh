# This script sets the TF_VAR_* variables from the output of decrypting each
# encrypted file that was generated by the encrypt_tfvars.sh script.
# It also sets the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY which allows the
# use of the 'aws s3' command if that is installed.
# Usage: Source the script and pass in the environment directory.
# Example for development:
# source decrypt_tfvars.sh development

if [ -d "$1" ]; then
  if [ \
    -e "$1/.do_token" -a \
    -e "$1/.do_spaces_access_key_id" -a \
    -e "$1/.do_spaces_secret_access_key" -a \
    -e "$1/.do_app_spaces_access_key_id" -a \
    -e "$1/.do_app_spaces_secret_access_key" \
    ]; then
    echo "Decrypting $1/.do_* files and exporting TF_VAR_* variables."

    TF_VAR_do_token=$(gpg --quiet --decrypt $1/.do_token)
    export TF_VAR_do_token

    TF_VAR_do_spaces_access_key_id=$(gpg --quiet --decrypt $1/.do_spaces_access_key_id)
    AWS_ACCESS_KEY_ID=$TF_VAR_do_spaces_access_key_id
    export TF_VAR_do_spaces_access_key_id
    export AWS_ACCESS_KEY_ID

    TF_VAR_do_spaces_secret_access_key=$(gpg --quiet --decrypt $1/.do_spaces_secret_access_key)
    AWS_SECRET_ACCESS_KEY="${TF_VAR_do_spaces_secret_access_key}"
    export TF_VAR_do_spaces_secret_access_key
    export AWS_SECRET_ACCESS_KEY

    TF_VAR_do_app_spaces_access_key_id=$(gpg --quiet --decrypt $1/.do_app_spaces_access_key_id)
    export TF_VAR_do_app_spaces_access_key_id

    TF_VAR_do_app_spaces_secret_access_key=$(gpg --quiet --decrypt $1/.do_app_spaces_secret_access_key)
    export TF_VAR_do_app_spaces_secret_access_key

  else
    echo 'missing files'
  fi
else
  echo 'first arg should be a directory'
fi