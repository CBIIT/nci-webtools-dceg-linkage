#!/bin/bash
#
# Description:  This script will replace tokens in the config.ini file with their corresponding actual values
# Usage: ./configure.sh --key1 value1 --key2 value2

# create hash for parameters
declare -A parameters=( [username]= [password]= [port]= )
valid=true
filename=SNP_Query_loginInfo.ini

# assign arguments to parameters
while true; do
        # if parameter matches --*, then assign its value to the corresponding key
        [[ $1 == --* ]] && parameters[${1:2}]=$2 && shift 2 || break
done

# display any error messages
for key in "${!parameters[@]}"; do
        [ -z "${parameters[$key]}" ] && echo -e "\e[91m[error]\e[39m missing parameter:\e[93m $key \e[39m" && valid=false
done

# replace tokens in config.ini file
if [ $valid = true ]; then

        for key in "${!parameters[@]}"; do
                sed -i "s|\@${key}@|${parameters[$key]}|g" $filename
        done

        echo -e "\e[92mLDlink configured successfully\e[39m"

# display usage if incorrect
else
        echo

        echo -e "\e[32mUsage:"
        echo -e "\e[95m sh\e[39m configure.sh \e[92m[options]"

        echo -e "\e[32mOptions:"
        echo -e "\e[39m --username\e[92m user.name"
        echo -e "\e[39m --password\e[92m user.password"
        echo -e "\e[39m --port\e[92m 0-65535"
fi

