#!/bin/bash

function confirm {
    local CONFIRM
    echo "${1}? (y/n)"
    read CONFIRM
    case $CONFIRM in
        y|Y|yes|Yes) return 0;;
        *) return -1
    esac
}

if (confirm "Do you want to update")
then
    git pull

    echo Updating submodules
    git submodule foreach git pull origin master
fi
