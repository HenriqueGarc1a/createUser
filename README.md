# Ubuntu User Manager

Aplicação desktop para **Ubuntu 24.04 LTS** que permite criar e administrar usuários locais em máquinas de laboratório, sem exigir conhecimento técnico do operador e sem exigir Python/pip/venv instalados na máquina final.

## 1. Objetivo

Permitir que uma pessoa sem conhecimento técnico consiga, através de uma interface gráfica simples e nativa ao GNOME/Ubuntu: visualizar, buscar, criar e excluir usuários locais, e resetar suas senhas — sempre mediante autenticação administrativa via Polkit para as operações que alteram o sistema.

## 2. Arquitetura

```
GUI GTK4 / Libadwaita   (usuário normal, nunca root)
        ↓
Application Services     (src/services)
        ↓
Polkit / pkexec           (autenticação gráfica padrão do Ubuntu)
        ↓
Privileged Helper          (root:root, conjunto fechado de operações)
        ↓
Linux (useradd/userdel/usermod/chpasswd/chage)
```

A interface gráfica nunca executa comandos administrativos diretamente. Operações somente-leitura (listar/buscar) não passam por Polkit; apenas criar, resetar senha e excluir exigem autenticação.

**Detalhe de implementação do Polkit:** `pkexec` decide qual ação verificar com base no **caminho do executável** que está sendo chamado, não no argumento passado a ele. Por isso o helper privilegiado é exposto através de três scripts finos e distintos (`/usr/lib/ubuntu-user-manager/helpers/{create-user,reset-password,delete-user}`), cada um mapeado a uma ação Polkit própria e cada um apenas repassando (`exec`) para o binário real do helper com uma operação fixa. A lógica continua centralizada em um único lugar (`helper/operations.py`).

## 3. Stack

- Python 3, GTK4, Libadwaita, PyGObject
- Polkit / `pkexec`
- Empacotamento standalone via PyInstaller
- Distribuição como pacote `.deb`
- Docker apenas como ambiente de build (nunca em produção)

## 4. Estrutura de diretórios

```
src/
├── main.py                       # entrypoint da GUI (Adw.Application)
├── ui/                            # janelas e diálogos (GTK4/Libadwaita)
├── services/                      # user_service (listagem + fachada) e
│                                    privileged_service (ponte com pkexec)
└── utils/                         # validators.py e username.py — fonte
                                     única das regras de matrícula/username
helper/
├── user_manager_helper.py        # entrypoint privilegiado (lê JSON via stdin)
├── operations.py                 # create/reset/delete — revalida tudo
├── linux_users.py                # wrappers subprocess.run em lista de args
├── groups_policy.py              # grupos permitidos/proibidos
└── entrypoints/                  # 3 wrappers finos, um por ação Polkit
polkit/com.local.usermanager.policy
desktop/ubuntu-user-manager.desktop
packaging/
├── debian/{control,postinst,prerm,postrm}
├── build-deb.sh
└── pyinstaller/{app.spec,helper.spec,hooks/,build.sh}
docker/build.sh
Dockerfile, docker-compose.yml, Makefile, install.sh, uninstall.sh,
requirements.txt, VERSION, dist/
```

## 5. Funcionamento do Polkit

Três ações distintas são definidas em `polkit/com.local.usermanager.policy`:

- `com.local.usermanager.create`
- `com.local.usermanager.reset-password`
- `com.local.usermanager.delete`

Cada ação usa `allow_active=auth_admin_keep` e a anotação `org.freedesktop.policykit.exec.allow_gui=true`, o que faz o `pkexec` usar o popup gráfico padrão do Ubuntu para autenticação — a aplicação nunca implementa uma caixa própria de senha nem armazena/captura a senha administrativa.

## 6. Criação de usuário

Fluxo (`helper/operations.py:create_user`):

1. valida nome completo e matrícula;
2. gera o username (`primeiro_nome_matricula`);
3. verifica duplicidade de username **e** de matrícula;
4. `useradd -m -c "<nome completo>" <username>`;
5. restringe a pasta pessoal a `chmod 700` (acesso só pelo próprio dono);
6. define a senha inicial = matrícula, via stdin do `chpasswd` (nunca em argv);
7. marca a senha como expirada (`chage -d 0`);
8. adiciona os grupos extras permitidos (aditivamente, nunca substituindo a lista);
9. valida que o usuário **não** recebeu nenhum grupo proibido;
10. em caso de falha após a criação, tenta desfazer (`userdel`) — melhor esforço, não é uma transação real de banco de dados.

O administrador nunca digita a senha manualmente.

## 7. Perfil de permissões dos usuários criados

O usuário criado:

- **não** recebe `sudo`, nem pertence a `sudo/adm/root/shadow/disk/lxd`;
- **não** consegue instalar pacotes globalmente via `apt`/`dpkg -i`;
- consegue usar normalmente sessão gráfica, home, navegador, IDEs, Git, Docker, rede, áudio, vídeo, USB e demais ferramentas de desenvolvimento já instaladas na máquina.

`helper/groups_policy.py` centraliza `FORBIDDEN_GROUPS` e `DEFAULT_EXTRA_GROUPS`, e revalida a associação de grupos **depois** da criação — isso é uma defesa deliberada contra o `/etc/adduser.conf` (`EXTRA_GROUPS`) injetar grupos indesejados independentemente do que o helper pediu explicitamente.

## 8. Funcionamento da rede

O usuário criado utiliza rede (Wi-Fi/Ethernet, conectar/desconectar/trocar de rede) através do NetworkManager + Polkit + sessão local ativa padrão do Ubuntu Desktop — sem `sudo`. Nenhuma regra de sudo para comandos de rede é criada.

## 9. Funcionamento do Docker

Todo usuário criado é incluído no grupo `docker`, caso esse grupo exista na máquina (`usermod -aG docker <username>`). Se o grupo não existir, o helper não falha silenciosamente: registra um aviso técnico no log e continua a criação normalmente (o restante da operação permanece válido).

## 10. Risco conhecido e aceito — grupo `docker`

> O acesso ao grupo `docker` pode fornecer capacidades equivalentes a root. Este risco é conhecido e aceito neste ambiente devido ao modelo de uso controlado, identificação individual dos usuários e rastreabilidade operacional.

## 11. Justificativa operacional

Os usuários pertencem a um ambiente controlado (laboratório), são identificados individualmente por matrícula, e existe registro de utilização da máquina. A prioridade do projeto é oferecer uma experiência simples de desenvolvimento — inclusive Docker sem `sudo` — evitando a complexidade adicional de Docker Rootless, que não é implementado nesta MVP.

## 12. Limitação da rastreabilidade local

Como um usuário com controle do daemon Docker pode, em determinados cenários, obter capacidades equivalentes a root, ele também pode potencialmente alterar arquivos ou registros locais da máquina. Logs locais (`/var/log/ubuntu-user-manager/helper.log`) servem para rastreabilidade **operacional**, não para garantia forense absoluta. Identificação por matrícula ajuda na responsabilização, mas registros críticos, quando necessário, devem preferencialmente ser armazenados fora da máquina local.

## 13. Reset de senha

A senha é redefinida para a matrícula do próprio usuário e imediatamente marcada como expirada (`chage -d 0`), forçando troca no próximo login. A senha nunca é passada como argumento de processo.

## 14. Exclusão

Exige digitar a matrícula do usuário para confirmar (o botão só habilita quando o valor confere). Por padrão, o diretório home **não** é removido (`userdel` sem `-r`) — nada é apagado silenciosamente.

## 15. Segurança

- Todos os comandos são executados via `subprocess.run`/`Popen` com lista de argumentos — nunca `os.system`/`shell=True`/concatenação de strings.
- Senhas trafegam exclusivamente via stdin (nunca em argv, nunca logadas).
- O helper revalida tudo, mesmo que a GUI já tenha validado (nome, matrícula, username, duplicidade, grupos permitidos/proibidos) — nunca confia no frontend.
- O helper possui um conjunto fechado de operações (`create-user`, `reset-password`, `delete-user`); não executa comandos arbitrários.
- Arquivos do helper e da policy do Polkit pertencem a `root:root`; usuários comuns não conseguem modificá-los.

## 16. Build via Docker

```bash
docker build -t ubuntu-user-manager-builder .
docker run --rm -v "$(pwd)/dist:/dist" ubuntu-user-manager-builder
```

O Docker é usado **apenas** para construir o pacote — a aplicação nunca roda em produção dentro de um container.

## 17. Geração do `.deb`

```bash
make release
```

Resultado: `dist/ubuntu-user-manager_<versão>_amd64.deb`.

## 18. Instalação

```bash
sudo apt install ./dist/ubuntu-user-manager_1.0.0_amd64.deb
```

O aplicativo aparece no launcher do GNOME logo em seguida (categoria Configurações/Sistema).

## 19. Desinstalação

```bash
sudo apt remove ubuntu-user-manager
sudo apt purge ubuntu-user-manager
```

Nunca exclui usuários, homes, senhas ou bloqueia contas — ver `packaging/debian/{prerm,postrm}`.

## 20. Troubleshooting

- **O botão "Criar usuário" nunca habilita:** verifique se o nome não contém números e se a matrícula tem exatamente 8 dígitos.
- **O popup de autenticação não aparece:** confirme que há um agente gráfico do Polkit rodando na sessão (padrão em sessões GNOME normais; ausente em contextos headless/SSH).
- **"O mecanismo de autenticação não está disponível":** o pacote `policykit-1` não está instalado ou o `pkexec` não está no PATH.
- **Usuário criado não aparece no grupo docker:** o grupo `docker` não existe na máquina (Docker Engine não instalado) — a criação do usuário continua válida, apenas sem esse grupo.

## 21. Limitações (MVP)

- Não implementa Docker Rootless (ver seção 10/11).
- Não integra com a tela de login/GDM (aplicação desktop normal por enquanto).
- Não bloqueia instalação/execução de software no espaço do próprio usuário (AppImage, `~/.local`, `npm install` local, venvs continuam disponíveis) — fora do escopo desta aplicação.
- Sem banco de dados, API web ou qualquer infraestrutura além de GTK → Python → Polkit → Helper → Linux, deliberadamente.

## 22. Ideias para V2

- Integração com a tela de login (seção 44 do spec original).
- Ícone próprio da aplicação.
- Suporte a Docker Rootless como alternativa opcional ao grupo `docker`.
- Envio de logs de auditoria para um destino externo (fora da máquina local).
- Suporte multi-versão Ubuntu (22.04 e 24.04 simultaneamente).

---

## Testando

**Ambiente de desenvolvimento (sem empacotar):**
```bash
python3 src/main.py
```

1. **Criação:** clique "+ Criar usuário", preencha nome e matrícula, confirme no popup do Polkit. Verifique com `id <username>`.
2. **Grupos:** `groups <username>` deve conter `docker` (se existir) e nunca `sudo/adm/root/shadow/disk/lxd`.
3. **Ausência de sudo:** como o usuário criado, rode `sudo -l` — deve falhar/negar.
4. **Rede sem sudo:** como o usuário criado, use o applet do NetworkManager para conectar/trocar de rede sem senha administrativa.
5. **Docker sem sudo:** como o usuário criado, rode `docker ps` — deve funcionar sem `sudo` (se o Docker Engine estiver instalado).
6. **Primeiro login:** faça login (ou `su - <username>`) e confirme que o sistema exige definir uma nova senha antes de continuar.
7. **Reset de senha:** clique "Resetar senha", confirme, verifique com `chage -l <username>` que a senha voltou a estar expirada.
8. **Exclusão:** tente excluir com matrícula errada (botão deve permanecer desabilitado); com a matrícula certa, confirme que `/home/<username>` permanece no disco após a exclusão.
9. **Autenticação Polkit:** cancele o popup de autenticação em qualquer operação administrativa e confirme que a aplicação mostra uma mensagem amigável (nunca um traceback Python).
10. **Build do `.deb`:** rode `make release` e confirme que `dist/ubuntu-user-manager_<versão>_amd64.deb` é gerado sem erros.
11. **Instalação em outra máquina:** `sudo apt install ./dist/*.deb` em uma VM/container Ubuntu 24.04 limpo, sem Python/pip pré-instalados manualmente — apenas as dependências resolvidas pelo APT (`policykit-1`, `libgtk-4-1`, `libadwaita-1-0`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `gir1.2-glib-2.0`).
12. **Nova versão:** edite o arquivo `VERSION`, rode `make release` novamente e confirme que contas de usuário existentes não são afetadas pela atualização.
13. **Desinstalação:** `sudo apt purge ubuntu-user-manager` e confirme que nenhuma conta criada anteriormente foi removida ou alterada.
