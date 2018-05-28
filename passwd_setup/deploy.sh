# /bin/bash
#get hash password
password=$1
sbxfile=$2

hash=$(python -c "from passlib.hash import sha512_crypt; print(sha512_crypt.encrypt('$1'))")
echo "password_hash=$hash"
ansible-playbook ./passwd.yml --extra-vars "password_hash=$hash" -i $2
