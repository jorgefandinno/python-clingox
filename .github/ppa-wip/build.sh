#!/bin/bash

function usage {
    echo "./$(basename $0) {stable,wip} {jammy,focal,bionic} {create,sync,changes,build,put,clean}*"
}

if [[ $# < 1 ]]; then
    usage
    exit 1
fi

ref="${1}"
shift

case "${ref}" in
    stable|wip)
        ;;
    *)
        usage
        exit 1
esac

rep="${1}"
shift

case "${rep}" in
    jammy|focal|bionic)
        ;;
    *)
        usage
        exit 1
esac

for act in "${@}"; do
    echo "${act}"
    case "${act}" in
        _ppa)
            apt-get install -y software-properties-common
            add-apt-repository -y ppa:potassco/${ref}
            apt-get update
            apt-get install -y tree debhelper python3-clingo
            ;;
        create)
            sudo pbuilder create --basetgz /var/cache/pbuilder/${ref}-${rep}.tgz --distribution ${rep} --debootstrapopts --variant=buildd
            sudo pbuilder execute --basetgz /var/cache/pbuilder/${ref}-${rep}.tgz --save-after-exec -- build.sh ${ref} ${rep} _ppa
            ;;
        sync)
            rsync -aq \
                --exclude __pycache__ \
                --exclude .mypy_cache \
                --exclude '*,cover' \
                --exclude '*.egg-info' \
                --exclude dist \
                --exclude build \
                ../../clingox \
                ../../setup.py \
                ../../README.md \
                ../../LICENSE \
                $rep/
            ;;
        changes)
            VERSION="$(sed -n "/version[ ]*=/s/.*['\"]\([0-9]\+\.[0-9]\+\.[0-9]\+.*\)['\"].*/\1/p" ../../setup.py)"
            BUILD=$(curl -sL http://ppa.launchpad.net/potassco/${ref}/ubuntu/pool/main/p/python3-clingox/ | sed -n "/${VERSION//./\\.}-${rep}[0-9]\+\.dsc/s/.*${rep}\([0-9]\+\).*/\1/p" | sort -rn | head -1)
            cat > ${rep}/debian/changelog <<EOF
python3-clingox (${VERSION}-${rep}$[BUILD+1]) ${rep}; urgency=medium

  * build for git revision $(git rev-parse HEAD)

 -- Roland Kaminski <kaminski@cs.uni-potsdam.de>  $(date -R)
EOF
            ;;
        build)
            VERSION="$(head -n 1 ${rep}/debian/changelog | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+\(-[a-z0-9]\+\)\?')"
            (
                cd "${rep}"
                pdebuild --buildresult .. --auto-debsign --debsign-k 744d959e10f5ad73f9cf17cc1d150536980033d5 -- --basetgz /var/cache/pbuilder/${ref}-${rep}.tgz --source-only-changes
                sed -i '/\.buildinfo$/d' ../python3-clingox_${VERSION}_source.changes
                debsign --no-re-sign -k744d959e10f5ad73f9cf17cc1d150536980033d5 ../python3-clingox_${VERSION}_source.changes
            )
            ;;
        put)
            VERSION="$(head -n 1 ${rep}/debian/changelog | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+\(-[a-z0-9]\+\)\?')"
            dput ppa:potassco/${ref} python3-clingox_${VERSION}_source.changes
            ;;
        clean)
            rm -rf \
                "${rep}"/clingox \
                "${rep}"/setup.py \
                "${rep}"/README.md \
                "${rep}"/LICENSE \
                "${rep}"/debian/files \
                "${rep}"/debian/.debhelper \
                "${rep}"/debian/python3-clingox.debhelper.log \
                "${rep}"/debian/python3-clingox.substvars \
                "${rep}"/debian/python3-clingox \
                "${rep}"/debian/debhelper-build-stamp \
                "${rep}"/debian/tmp \
                "${rep}"/obj-x86_64-linux-gnu \
                *.build \
                *.deb \
                *.dsc \
                *.buildinfo \
                *.changes \
                *.ddeb \
                *.tar.xz \
                *.upload
            git checkout "${rep}/debian/changelog" "${rep}/debian/rules"
            ;;
        *)
            usage
            exit 1
    esac
done
