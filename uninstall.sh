#!/bin/sh
# Development convenience uninstaller. This script MUST NEVER remove
# user accounts, homes, or passwords — see spec section 41 and
# packaging/debian/{prerm,postrm}, which enforce the same invariant at
# the package-manager level.
set -eu

echo "==> Removendo pacote ubuntu-user-manager (contas de usuário não são afetadas)"
sudo apt remove ubuntu-user-manager
