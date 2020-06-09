#!/bin/bash -e

#MODEL_DIR=$HOME/src/eec/predicts/models/dasgupta/2020-05-22
#MODEL_DIR=$HOME/src/eec/predicts/models/dasgupta/2020-05-22/nohpd
#MODEL_DIR=$HOME/src/eec/predicts/models/dasgupta/2020-05-22/nohpd-ageclass
MODEL_DIR=$HOME/src/eec/predicts/models/dasgupta/2020-05-22/ageclass
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
YEARS=2020:2061:5
#for scene in early late base; do
for scene in base early late_23 late_26 late_29 ; do
    ${DIR}/dasgupta.py project -m ${MODEL_DIR} -f ab ${scene} ${YEARS}
    ${DIR}/dasgupta.py project -m ${MODEL_DIR} ab ${scene} ${YEARS}

    ${DIR}/dasgupta.py project -m ${MODEL_DIR} -f cs-ab ${scene} ${YEARS}
    ${DIR}/dasgupta.py project -m ${MODEL_DIR} cs-ab ${scene} ${YEARS}

    ${DIR}/dasgupta.py combine ab ${scene} ${YEARS}
    ${DIR}/dasgupta.py combine cs-ab ${scene} ${YEARS}
    ${DIR}/dasgupta.py combine bii ${scene} ${YEARS}

    #${DIR}/dasgupta.py mask -m ${MODEL_DIR} -f ab ${scene} ${YEARS}
    #${DIR}/dasgupta.py mask -m ${MODEL_DIR} ab ${scene} ${YEARS}

    #${DIR}/dasgupta.py mask -m ${MODEL_DIR} -f cs-ab ${scene} ${YEARS}
    #${DIR}/dasgupta.py mask -m ${MODEL_DIR} cs-ab ${scene} ${YEARS}
done
