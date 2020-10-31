#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
scene="$1"
years="$2"
model="${3:-base}"
if [[ -d /out ]]; then
    model_dir=/out/models//2020-06-02/${model}
else
    model_dir=${HOME}/src/eec/predicts/models/brazil/2020-10-27/${model}
fi

echo ${scene}
${DIR}/restore.py project -m ${model_dir} ab ${scene} ${years}
${DIR}/restore.py project -m ${model_dir} cs-ab ${scene} ${years}
${DIR}/restore.py combine bii ${scene} ${years}
