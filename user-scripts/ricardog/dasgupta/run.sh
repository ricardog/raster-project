#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
scene="$1"
years="$2"
model="${3:-base}"
if [[ -d /out ]]; then
    model_dir=/out/models/dasgupta/2020-06-02/${model}
else
    model_dir=${HOME}/src/eec/predicts/models/dasgupta/2020-06-02/${model}
fi

echo ${scene}
${DIR}/dasgupta.py project -m ${model_dir} -f ab ${scene} ${years}
${DIR}/dasgupta.py project -m ${model_dir} ab ${scene} ${years}

${DIR}/dasgupta.py project -m ${model_dir} -f cs-ab ${scene} ${years}
${DIR}/dasgupta.py project -m ${model_dir} cs-ab ${scene} ${years}

${DIR}/dasgupta.py combine ab ${scene} ${years}
${DIR}/dasgupta.py combine cs-ab ${scene} ${years}
${DIR}/dasgupta.py combine bii ${scene} ${years}
