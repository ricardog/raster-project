#!/bin/bash -ev

MODEL_DIR=$HOME/src/eec/predicts/models/dasgupta/2020-05-05
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
YEARS=2020:2051:5
YEARS=2020:2025:5
${DIR}/dasgupta.py project -m ${MODEL_DIR} -f ab ${YEARS}
#${DIR}/dasgupta.py project -m ${MODEL_DIR} ab ${YEARS}

${DIR}/dasgupta.py project -m ${MODEL_DIR} -f cs-ab ${YEARS}
#${DIR}/dasgupta.py project -m ${MODEL_DIR} cs-ab ${YEARS}

${DIR}/dasgupta.py combine ab ${YEARS}
${DIR}/dasgupta.py combine cs-ab ${YEARS}
${DIR}/dasgupta.py combine bii ${YEARS}
