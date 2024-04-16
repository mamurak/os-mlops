#!/bin/bash

for i in {0..50}
do
   projectName="user$i"

   echo "Deleting project: $projectName"
   oc delete project $projectName --ignore-not-found=true --wait=false
done

echo "Deletion process completed."