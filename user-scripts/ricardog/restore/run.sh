#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
scene="$1"
years="$2"
model="${3:-base}"
model_dir=/mnt/predicts/models/brazil/2021-07-01/${model}

echo ${scene}
${DIR}/restore.py project -m ${model_dir} ab ${scene} ${years}
${DIR}/restore.py project -m ${model_dir} cs-ab ${scene} ${years}
${DIR}/restore.py combine bii ${scene} ${years}
