#!/bin/bash

umount /var/lib/lxc/$1/checkpoint
rm -rf /var/lib/lxc/$1/checkpoint