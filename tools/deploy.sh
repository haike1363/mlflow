#!/bin/bash
SHELL_DIR=$(
  cd "$(dirname "$0")" || exit
  pwd
)
cd "${SHELL_DIR}" || exit

set -eu

cd ..

scp mlflow/store/model_registry/tclake_store.py root@114.132.177.125:/usr/lib/python3.9/lib/python3.9/site-packages/mlflow/store/model_registry/
scp mlflow/store/model_registry/gravitino_store.py root@114.132.177.125:/usr/lib/python3.9/lib/python3.9/site-packages/mlflow/store/model_registry/
scp mlflow/tracking/_model_registry/utils.py root@114.132.177.125:/usr/lib/python3.9/lib/python3.9/site-packages/mlflow/tracking/_model_registry/
scp tools/* root@114.132.177.125:/root/mlflow/tools/
#ssh root@114.132.177.125 'bash /root/mlflow/tools/test_gravitino_store.sh'
ssh root@114.132.177.125 'bash /root/mlflow/tools/test_tclake_store.sh'

