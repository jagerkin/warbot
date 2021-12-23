# Copyright 2021 Michael Olson
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
USER="warbot"
APPDIR="/usr/src/app"

if [ -z "%{FLAGS}" ]; then
    FLAGS="--no-dry_run"
fi

if [ -z "${CONFIG}" ]; then
    CONFIG="cfg/warbot.conf"
fi

if [ -z "${DB}" ]; then
    DB="db/warbot.db"
fi

if [ -z "${UID}" ]; then
    UID=$(id -u ${USER})
fi

if [ -z "${GID}" ]; then
    GID=$(id -g ${USER})
fi

if [ ${GID} -ne $(id -g ${USER}) ]; then
    sed -i -e "s/^\(${USER}:[^:]*\):[0-9]*:/\1:${GID}:/" /etc/group
fi

if [ ${UID} -ne $(id -u ${USER}) -o ${GID} -ne $(id -g ${USER}) ]; then
    sed -i -e "s/^\(${USER}:[^:]*\):[0-9]*:[0-9]*:/\1:${UID}:${GID}:/" /etc/passwd
    chown ${USER}.${USER} "${APPDIR}"
    find "${APPDIR}" -type f -xdev -exec chown ${USER}.${USER} \{\} \;
fi

if [ -n "${TZ}" ]; then
    ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone
fi

exec su -c "cd \"${APPDIR}\" && /usr/local/bin/python3.10 main.py ${FLAGS} --config=\"${CONFIG}\" --db=\"${DB}\"" - ${USER}
