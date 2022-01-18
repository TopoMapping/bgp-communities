#!/bin/bash

for i in `ls -1 $1`
do 
	sort -u -o $1/$i $1/$i
done
