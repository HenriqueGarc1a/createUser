# Super Prompt — Ubuntu User Manager

Crie uma aplicação desktop para **Ubuntu** chamada **Ubuntu User Manager**, voltada para criação e administração simples de usuários locais em máquinas de laboratório.

A aplicação deve ter interface gráfica nativa, simples, limpa e integrada ao GNOME/Ubuntu.

O foco é permitir que uma pessoa sem conhecimento técnico consiga:

- visualizar usuários;
- buscar usuários;
- criar usuários;
- resetar senhas;
- excluir usuários;
- realizar ações administrativas mediante autenticação com senha de administrador.

A aplicação deve ser distribuída como um pacote `.deb`, pronto para instalação em máquinas Ubuntu, sem exigir que o usuário final instale Python, pip, ambiente virtual ou ferramentas de desenvolvimento.

---

# 1. Stack

Utilize:

- Python 3
- GTK4
- Libadwaita
- PyGObject
- Polkit / `pkexec`
- Bash ou Python para o helper privilegiado
- `.desktop`
- PyInstaller ou solução equivalente para empacotamento
- Docker apenas como ambiente de build
- pacote Debian `.deb`

A aplicação **não deve rodar inteira como root**.

Somente operações realmente administrativas devem receber privilégios elevados.

A interface gráfica deve sempre rodar como usuário normal.

---

# 2. Arquitetura

Estruture a aplicação assim:

```text
GUI GTK4 / Libadwaita
        ↓
Application Services
        ↓
Polkit / pkexec
        ↓
Privileged Helper
        ↓
Linux
```

Comandos administrativos possíveis:

```text
useradd
userdel
usermod
chpasswd
chage
```

O frontend nunca deve executar comandos administrativos diretamente sem passar pelo mecanismo de autorização.

---

# 3. Estrutura de projeto

Utilize uma estrutura semelhante a:

```text
ubuntu-user-manager/
├── src/
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── create_user_dialog.py
│   │   ├── reset_password_dialog.py
│   │   ├── delete_user_dialog.py
│   │   └── user_row.py
│   ├── services/
│   │   ├── user_service.py
│   │   └── privileged_service.py
│   └── utils/
│       ├── username.py
│       └── validators.py
├── helper/
│   └── user_manager_helper.py
├── polkit/
│   └── com.local.usermanager.policy
├── desktop/
│   └── ubuntu-user-manager.desktop
├── packaging/
│   ├── debian/
│   │   ├── control
│   │   ├── postinst
│   │   ├── prerm
│   │   └── postrm
│   └── build-deb.sh
├── docker/
│   └── build.sh
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── install.sh
├── uninstall.sh
├── requirements.txt
├── README.md
└── dist/
```

Separe claramente responsabilidades entre:

```text
UI
↓
Services
↓
Privileged interface
↓
Helper
↓
Sistema operacional
```

---

# 4. Tela principal

A tela inicial deve possuir aparência semelhante às configurações nativas do Ubuntu.

Exemplo:

```text
Ubuntu User Manager

[ Buscar usuário...                              ]

Henrique Garcia Manfio
henrique_24112345
Matrícula: 24112345

                        [ Resetar senha ] [ ⋮ ]


João da Silva
joao_24154321
Matrícula: 24154321

                        [ Resetar senha ] [ ⋮ ]


Maria Souza
maria_24199876
Matrícula: 24199876

                        [ Resetar senha ] [ ⋮ ]


                               [ + Criar usuário ]
```

Utilize componentes do Libadwaita sempre que possível.

A aplicação deve parecer parte do GNOME/Ubuntu.

---

# 5. Listagem de usuários

A tela deve listar usuários humanos relevantes.

Para cada usuário exibir:

- nome completo;
- username;
- matrícula;
- botão de reset de senha;
- menu secundário com opção de exclusão.

Deve existir busca por:

- nome;
- username;
- matrícula.

Não mostrar contas internas do Linux, como:

```text
root
daemon
bin
sys
sync
games
man
lp
mail
news
uucp
proxy
www-data
backup
list
irc
gnats
nobody
systemd-*
```

Utilize critérios adequados para identificar usuários humanos, incluindo UID quando necessário.

---

# 6. Criação de usuário

Ao clicar:

```text
+ Criar usuário
```

abrir uma janela/modal.

Campos:

```text
Nome completo
[                                      ]

Matrícula
[                                      ]

Username
henrique_24112345

Senha temporária
A matrícula será utilizada como senha inicial.

[ Cancelar ]                 [ Criar usuário ]
```

O administrador não informa manualmente a senha.

A senha inicial será automaticamente igual à matrícula.

---

# 7. Regra do username

O username deve ser gerado automaticamente no formato:

```text
primeiro_nome_matricula
```

Exemplo:

```text
Nome:
Henrique Garcia Manfio de Almeida

Matrícula:
24112345

Resultado:
henrique_24112345
```

Outros exemplos:

```text
João da Silva + 23123456
→ joao_23123456

María Eduarda Souza + 22111222
→ maria_22111222
```

Antes de gerar o username:

- converter para lowercase;
- remover acentos;
- remover caracteres inválidos;
- garantir compatibilidade com usernames Linux.

O nome completo original deve continuar armazenado corretamente, incluindo acentos.

---

# 8. Nome completo e diretório home

O nome completo deve ser armazenado no sistema Linux.

Equivalente:

```bash
useradd \
    -m \
    -c "Henrique Garcia Manfio de Almeida" \
    henrique_24112345
```

Home esperado:

```text
/home/henrique_24112345
```

Utilize o shell padrão adequado do Ubuntu.

---

# 9. Matrícula

A matrícula deve:

- ser obrigatória;
- conter apenas números;
- inicialmente possuir exatamente 8 dígitos;
- ter sua regra centralizada para facilitar alterações futuras.

Exemplo válido:

```text
24112345
```

Inválidos:

```text
123
2411A345
24-112345
2411 2345
```

---

# 10. Senha temporária

A senha temporária deve ser sempre igual à matrícula.

Exemplo:

```text
Username:
henrique_24112345

Matrícula:
24112345

Senha temporária:
24112345
```

Depois da criação, obrigatoriamente marque a senha como expirada:

```bash
chage -d 0 henrique_24112345
```

Fluxo:

```text
Administrador cria usuário
        ↓
Senha inicial = matrícula
        ↓
Conta criada
        ↓
Senha marcada como expirada
        ↓
Usuário faz primeiro login
        ↓
Ubuntu exige alteração da senha
        ↓
Usuário define uma nova senha
```

A matrícula nunca deve permanecer como senha permanente.

---

# 11. Perfil de permissões do usuário criado

Todo usuário criado pela aplicação deve conseguir **usar o computador normalmente para estudo e desenvolvimento**, mas não deve receber privilégios administrativos tradicionais.

O objetivo é que o usuário possa:

- entrar na sessão gráfica normalmente;
- acessar sua pasta pessoal;
- criar, editar e excluir seus próprios arquivos;
- utilizar navegador;
- utilizar IDEs e editores;
- acessar a internet;
- conectar e trocar redes Wi-Fi/Ethernet normalmente através do NetworkManager;
- utilizar áudio;
- utilizar vídeo/GPU quando aplicável;
- utilizar USB e periféricos comuns;
- utilizar Docker;
- executar ferramentas de desenvolvimento já instaladas;
- utilizar Git, Java, Maven, Node, npm, compiladores e outras ferramentas já disponíveis;
- executar aplicações normais instaladas na máquina.

Mas ele **não deve**:

- possuir `sudo`;
- pertencer ao grupo `sudo`;
- possuir acesso administrativo geral;
- instalar pacotes globalmente via `apt`/`apt-get`;
- executar `dpkg -i` no sistema sem autorização;
- alterar usuários;
- alterar grupos;
- alterar configurações críticas do sistema;
- executar `systemctl` para modificar serviços do sistema sem autorização;
- editar arquivos protegidos em `/etc`, `/usr`, `/boot` etc.;
- modificar o helper do Ubuntu User Manager;
- modificar policies do Polkit;
- criar novos administradores.

O script de criação deve configurar automaticamente esse perfil.

---

# 12. Docker para os usuários criados

**Requisito explícito do projeto:** todo usuário criado pela aplicação deve ser incluído no grupo `docker`, caso o grupo exista.

Exemplo:

```bash
usermod -aG docker henrique_24112345
```

Caso o grupo `docker` não exista, o helper deve:

- não falhar silenciosamente;
- registrar um aviso técnico;
- informar de forma amigável que o Docker não está instalado/configurado;
- continuar criando o usuário normalmente, se o restante da operação for válido.

O helper nunca deve remover grupos existentes acidentalmente. Ao adicionar grupos utilize sempre comportamento equivalente a:

```bash
usermod -aG grupo usuario
```

e nunca um comando que substitua toda a lista de grupos suplementares.

## Risco conhecido e aceito — grupo `docker`

O grupo `docker` tradicional do Docker Engine concede, na prática, capacidades equivalentes a privilégios de `root`, pois um usuário com acesso ao daemon Docker pode iniciar containers com acesso privilegiado, montar partes do filesystem do host e contornar diversas restrições locais.

Mesmo assim, **neste projeto o uso do grupo `docker` é uma decisão operacional deliberada e um risco conhecido e aceito**.

A política adotada é:

```text
Usuário sem sudo
+
Usuário fora do grupo sudo
+
Usuário no grupo docker
+
Uso identificado por matrícula
+
Ambiente controlado
+
Rastreabilidade operacional
```

A justificativa é que os usuários pertencem a um ambiente controlado, são identificados individualmente por matrícula e existe registro de utilização da máquina. A prioridade do projeto é permitir uma experiência simples de desenvolvimento, inclusive uso de Docker sem `sudo`, evitando complexidade adicional para o usuário final.

O helper deve, portanto, adicionar o usuário ao grupo `docker` quando este grupo existir:

```bash
usermod -aG docker henrique_24112345
```

Não implementar Docker Rootless como requisito da MVP.

O README deve registrar explicitamente esta decisão arquitetural:

> O acesso ao grupo `docker` pode fornecer capacidades equivalentes a root. Este risco é conhecido e aceito neste ambiente devido ao modelo de uso controlado, identificação individual dos usuários e rastreabilidade operacional.

### Limitação da rastreabilidade

Não trate logs locais como garantia forense absoluta.

Como um usuário com controle do Docker daemon pode potencialmente obter capacidades equivalentes a root, ele também pode, em determinados cenários, alterar arquivos ou registros locais da máquina.

Portanto:

- logs locais servem para rastreabilidade operacional;
- identificação por matrícula ajuda na responsabilização;
- registros importantes, quando necessário, devem preferencialmente ser enviados ou armazenados fora da máquina local;
- não afirmar que logs locais são impossíveis de adulterar.

Essa limitação deve ser documentada, mas **não bloqueia o uso do grupo `docker` nesta MVP**.

---

# 13. Rede sem sudo

O usuário deve conseguir utilizar a rede normalmente sem precisar de `sudo`.

Priorize o comportamento padrão do Ubuntu Desktop com:

```text
NetworkManager
+
Polkit
+
sessão local ativa
```

Não crie regras excessivamente permissivas de sudo para comandos de rede.

O usuário deve conseguir, quando permitido pela política padrão do Ubuntu:

- conectar em Wi-Fi;
- trocar de rede;
- utilizar Ethernet;
- desconectar/conectar;
- visualizar redes disponíveis.

Não conceda acesso root apenas para permitir gerenciamento cotidiano da rede.

Caso uma versão específica do Ubuntu ou o ambiente de laboratório exija associação adicional, deixe essa configuração centralizada e documentada.

Não adicione grupos obsoletos ou desnecessários sem verificar a necessidade.

---

# 14. Grupos básicos do usuário

Não adicione usuários cegamente a uma grande lista de grupos.

Determine grupos adicionais com base no Ubuntu alvo e no hardware disponível.

Quando necessário, podem existir grupos como:

```text
audio
video
render
plugdev
```

mas prefira os mecanismos modernos de ACL/logind do Ubuntu sempre que eles já concederem acesso adequado à sessão local.

A aplicação deve possuir uma lista configurável de grupos extras.

Exemplo conceitual:

```python
DEFAULT_EXTRA_GROUPS = [
    "docker",
]
```

E grupos opcionais podem ser adicionados somente quando existirem e forem necessários.

Nunca adicionar automaticamente o usuário aos grupos:

```text
sudo
adm
root
shadow
disk
lxd
```

Nem a outros grupos que forneçam privilégios administrativos equivalentes, salvo requisito explícito futuro.

---

# 15. Instalação de programas e alterações do sistema

O usuário criado deve ser um usuário padrão, não administrador.

Sem `sudo`, operações como:

```bash
apt install pacote
apt remove pacote
dpkg -i pacote.deb
```

não devem funcionar diretamente.

O objetivo é impedir **instalações e alterações globais no sistema operacional**.

Não crie regras de sudo como:

```text
NOPASSWD: ALL
```

nem regras equivalentes.

Também não conceda permissões de escrita para usuários comuns em:

```text
/etc
/usr
/opt
/boot
/var/lib
```

sem necessidade específica.

## Importante sobre “baixar coisas”

Não tente impedir downloads normais de arquivos via navegador ou internet.

O escopo desta aplicação é impedir **alterações administrativas e instalações globais no sistema**, não implementar controle parental, proxy, firewall de conteúdo ou bloqueio de downloads.

Também documente que mecanismos como:

- AppImage;
- binários executados diretamente da home;
- instalações locais em `~/.local`;
- `npm install` local;
- ambientes virtuais;
- ferramentas que não exigem root;

podem continuar disponíveis para um usuário comum.

Bloquear completamente execução/instalação de software no espaço do próprio usuário exigiria uma política de segurança muito mais ampla e está fora da MVP.

---

# 16. Reset de senha

Cada usuário deve possuir:

```text
Resetar senha
```

Ao clicar:

```text
Resetar senha de Henrique Garcia?

A senha será redefinida para:

24112345

O usuário será obrigado a definir
uma nova senha no próximo login.

[ Cancelar ]               [ Resetar senha ]
```

Depois da confirmação, solicitar autenticação administrativa através do Polkit.

O reset deve realizar o equivalente a:

```bash
echo 'henrique_24112345:24112345' | chpasswd
chage -d 0 henrique_24112345
```

A senha não deve ser passada como argumento de processo.

---

# 17. Autenticação administrativa

Operações somente de leitura não devem pedir autenticação:

```text
Listar usuários      → sem autenticação
Buscar usuário       → sem autenticação
Ver informações      → sem autenticação
```

Operações administrativas devem solicitar autenticação:

```text
Criar usuário        → Polkit
Resetar senha        → Polkit
Excluir usuário      → Polkit
```

A autenticação deve usar o popup gráfico padrão do Ubuntu.

Não implementar uma caixa própria solicitando a senha sudo.

Não armazenar a senha administrativa.

Não capturar manualmente a senha do administrador.

Use o mecanismo oficial Polkit.

---

# 18. Polkit

Defina ações separadas:

```text
com.local.usermanager.create
com.local.usermanager.reset-password
com.local.usermanager.delete
```

Crie:

```text
/usr/share/polkit-1/actions/com.local.usermanager.policy
```

O frontend deve chamar somente o helper autorizado.

A aplicação não deve executar `sudo` diretamente.

---

# 19. Helper privilegiado

Crie um helper separado:

```text
/usr/lib/ubuntu-user-manager/user-manager-helper
```

Operações permitidas:

```text
create-user
reset-password
delete-user
```

Não permitir execução de comandos arbitrários.

O helper deve possuir uma lista fechada de operações permitidas.

---

# 20. Fluxo completo do create-user

A operação `create-user` deve realizar, de forma transacional tanto quanto possível:

```text
Validar nome
↓
Validar matrícula
↓
Gerar username
↓
Verificar duplicidade
↓
Criar usuário
↓
Criar home
↓
Definir nome completo
↓
Definir senha temporária = matrícula
↓
Marcar senha como expirada
↓
Adicionar grupos extras permitidos
↓
Adicionar ao grupo docker se disponível
↓
Garantir que NÃO pertence a sudo/adm/etc.
↓
Retornar sucesso
```

Exemplo conceitual:

```bash
useradd -m -c "Henrique Garcia Manfio de Almeida" henrique_24112345
```

Definir senha via `chpasswd` usando `stdin`.

Depois:

```bash
chage -d 0 henrique_24112345
```

Depois:

```bash
usermod -aG docker henrique_24112345
```

Somente se o grupo `docker` existir.

Antes de finalizar, valide que o usuário não recebeu acidentalmente grupos administrativos proibidos.

---

# 21. Validação no helper

Mesmo que a interface já tenha validado os dados, valide tudo novamente no helper.

Validar:

- nome;
- matrícula;
- username;
- tamanho da matrícula;
- caracteres permitidos;
- existência do usuário;
- duplicidade;
- operação solicitada;
- grupos permitidos;
- grupos proibidos.

Não confie no frontend.

---

# 22. Segurança contra command injection

Nunca faça:

```python
os.system("useradd " + username)
```

Use:

```python
subprocess.run([
    "useradd",
    "-m",
    "-c",
    full_name,
    username
], check=True)
```

Não concatenar comandos shell.

---

# 23. Senhas e processos

Não passe senha através de argumento da linha de comando.

Não fazer:

```text
user-manager-helper reset henrique_24112345 24112345
```

Quando uma senha precisar ser passada para outro processo, utilize:

- stdin;
- pipe;
- IPC seguro.

---

# 24. Associação da matrícula

A matrícula será inicialmente recuperada através do username.

Formato:

```text
henrique_24112345
```

Crie:

```python
extract_registration("henrique_24112345")
```

Resultado:

```text
24112345
```

Também:

```python
generate_username(
    "Henrique Garcia",
    "24112345"
)
```

Resultado:

```text
henrique_24112345
```

---

# 25. Usuários duplicados

Antes de criar:

1. verificar username;
2. verificar matrícula.

Nunca sobrescrever uma conta existente.

---

# 26. Exclusão

Adicionar opção:

```text
Excluir usuário
```

Antes:

```text
Excluir Henrique Garcia?

Username:
henrique_24112345

Digite a matrícula para confirmar:

[                         ]

[ Cancelar ]              [ Excluir ]
```

O botão só deve ser habilitado se a matrícula estiver correta.

A exclusão deve passar pelo Polkit.

---

# 27. Home durante exclusão

Por padrão, **não remover automaticamente o diretório home**.

Utilize comportamento equivalente a:

```bash
userdel username
```

e preserve:

```text
/home/username
```

Nunca apagar arquivos silenciosamente.

---

# 28. Feedback visual

Criação concluída:

```text
✓ Usuário criado com sucesso

Nome:
Henrique Garcia Manfio

Username:
henrique_24112345

Senha inicial:
sua matrícula

A senha deverá ser alterada
no primeiro login.
```

Reset:

```text
✓ Senha resetada

A senha temporária voltou a ser
a matrícula.

O usuário deverá alterá-la
no próximo login.
```

Exclusão:

```text
✓ Usuário removido

O diretório pessoal foi preservado.
```

Nunca mostrar traceback Python ao usuário final.

---

# 29. Logs

Pode registrar:

```text
create_user username=henrique_24112345 success=true
reset_password username=henrique_24112345 success=true
```

Nunca registrar:

- senha;
- conteúdo enviado ao `chpasswd`;
- senha administrativa.

---

# 30. Integração com Ubuntu

Criar:

```text
ubuntu-user-manager.desktop
```

Instalar em:

```text
/usr/share/applications/ubuntu-user-manager.desktop
```

Nome:

```text
Ubuntu User Manager
```

Categorias:

```text
Settings;
System;
```

O launcher deve executar diretamente o aplicativo empacotado.

---

# 31. Aplicação standalone

A máquina final não deve precisar ter Python instalado manualmente.

Empacote usando PyInstaller ou solução equivalente compatível com:

- PyGObject;
- GTK4;
- Libadwaita.

O usuário final não deve executar:

```bash
python3 main.py
pip install ...
```

---

# 32. Dependências nativas

Dependências apropriadas do sistema podem continuar sendo instaladas através do APT.

Exemplos:

```text
GTK4
Libadwaita
Polkit
```

Declare corretamente no `.deb`.

---

# 33. Docker apenas para build

Docker deve ser utilizado **somente para construir o aplicativo**.

Não execute a aplicação dentro de Docker em produção.

Não use:

```text
docker run --privileged
```

para administrar o host.

Arquitetura:

```text
DESENVOLVIMENTO

Código fonte
     ↓
Docker Build
     ↓
Executável
     ↓
Pacote Debian


MÁQUINA FINAL

ubuntu-user-manager.deb
     ↓
Aplicação Ubuntu
     ↓
Polkit
     ↓
Helper
     ↓
Linux
```

---

# 34. Dockerfile

O Dockerfile deve:

1. utilizar Ubuntu como base;
2. instalar ferramentas de desenvolvimento;
3. instalar Python;
4. instalar PyGObject;
5. instalar GTK4;
6. instalar Libadwaita;
7. instalar PyInstaller ou alternativa;
8. copiar o código;
9. gerar o executável;
10. construir a estrutura Debian;
11. gerar o `.deb`;
12. colocar o resultado em `/dist`.

---

# 35. Build

Quero conseguir executar:

```bash
docker build -t ubuntu-user-manager-builder .
```

Depois:

```bash
docker run --rm \
    -v "$(pwd)/dist:/dist" \
    ubuntu-user-manager-builder
```

Resultado:

```text
dist/
└── ubuntu-user-manager_1.0.0_amd64.deb
```

---

# 36. Makefile

Criar:

```bash
make build
make package
make clean
make release
```

`make release` deve executar o fluxo completo.

---

# 37. Pacote Debian

O pacote deve instalar aproximadamente:

```text
/opt/ubuntu-user-manager/
    ubuntu-user-manager
    runtime/

/usr/lib/ubuntu-user-manager/
    user-manager-helper

/usr/share/polkit-1/actions/
    com.local.usermanager.policy

/usr/share/applications/
    ubuntu-user-manager.desktop
```

---

# 38. Permissões dos arquivos da aplicação

O helper deve pertencer a:

```text
root:root
```

Usuários comuns não devem conseguir modificá-lo.

Arquivos Polkit também devem possuir permissões adequadas.

---

# 39. Instalação

Em qualquer Ubuntu compatível:

```bash
sudo apt install ./ubuntu-user-manager_1.0.0_amd64.deb
```

Depois o aplicativo deve aparecer no launcher.

---

# 40. Versionamento

Utilize:

```text
1.0.0
1.1.0
1.2.0
2.0.0
```

Instalar uma versão nova deve atualizar a aplicação sem modificar contas existentes.

---

# 41. Desinstalação

Deve funcionar:

```bash
sudo apt remove ubuntu-user-manager
sudo apt purge ubuntu-user-manager
```

Nunca:

- excluir usuários;
- excluir homes;
- alterar senhas;
- bloquear contas.

---

# 42. install.sh e uninstall.sh

Crie scripts auxiliares para desenvolvimento.

O método oficial de distribuição continua sendo o `.deb`.

O `uninstall.sh` nunca deve remover usuários.

---

# 43. README

Criar README completo contendo:

1. objetivo;
2. arquitetura;
3. stack;
4. estrutura de diretórios;
5. funcionamento do Polkit;
6. criação de usuário;
7. perfil de permissões dos usuários;
8. funcionamento da rede;
9. funcionamento do Docker;
10. **risco conhecido e aceito do grupo docker**;
11. justificativa operacional para o uso do grupo `docker`;
12. limitação da rastreabilidade local;
13. reset de senha;
14. exclusão;
15. segurança;
16. build Docker;
17. geração do `.deb`;
18. instalação;
19. desinstalação;
20. troubleshooting;
21. limitações;
22. ideias para V2.

---

# 44. Tela de login / lock screen

A primeira versão deve funcionar como aplicação desktop normal.

Não tente modificar o GDM inicialmente.

Organize o código para futura integração com a tela de login:

```text
Tela de Login
        ↓
Administrar usuários
        ↓
Autenticação administrativa
        ↓
Ubuntu User Manager
```

Mantenha GUI separada do helper privilegiado.

---

# 45. UX

Priorizar:

- simplicidade;
- aparência nativa Ubuntu;
- poucos botões;
- nenhuma necessidade de terminal;
- mensagens compreensíveis;
- confirmação em ações perigosas.

Não mostrar termos como:

```text
useradd
chpasswd
chage
UID
pkexec
Polkit
```

na interface final.

---

# 46. Código

Gerar código:

- organizado;
- modular;
- legível;
- com type hints;
- sem abstrações desnecessárias;
- pronto para execução;
- com tratamento de erros.

Tratar:

```text
subprocess errors
permission denied
authentication cancelled
user already exists
user not found
invalid registration
invalid username
failed password reset
failed user deletion
missing docker group
```

---

# 47. Evitar overengineering

Não criar:

- banco de dados;
- API web;
- servidor HTTP;
- Kubernetes;
- Redis;
- RabbitMQ;
- microserviços;
- autenticação própria.

Arquitetura:

```text
GTK
↓
Python
↓
Polkit
↓
Helper
↓
Linux
```

---

# 48. Resultado esperado — criação

```text
Abrir Ubuntu User Manager
        ↓
Criar usuário
        ↓
Nome + Matrícula
        ↓
Username = primeiro_nome_matricula
        ↓
Polkit
        ↓
Conta criada
        ↓
Senha = matrícula
        ↓
Senha expirada
        ↓
Usuário incluído no grupo docker, se disponível
        ↓
Usuário NÃO recebe sudo
        ↓
Usuário pode utilizar a máquina normalmente
        ↓
Primeiro login exige nova senha
```

---

# 49. Resultado esperado — perfil final

Exemplo:

```text
Nome:
Henrique Garcia Manfio de Almeida

Username:
henrique_24112345

Home:
/home/henrique_24112345

Senha temporária:
24112345

Primeiro login:
troca obrigatória de senha

Rede:
uso normal sem sudo

Docker:
permitido através do grupo docker

sudo:
NÃO

Instalações globais com APT:
NÃO

Arquivos pessoais:
permitidos

Ferramentas de desenvolvimento:
permitidas

Alterações administrativas do sistema:
bloqueadas pelo modelo normal de permissões do Ubuntu
```

Lembre-se de documentar que **o acesso tradicional ao grupo `docker` reduz fortemente a garantia prática da última linha**, pois esse grupo permite contornar diversas restrições de privilégio.

---

# 50. Resultado esperado — distribuição

Na máquina de desenvolvimento:

```bash
make release
```

Resultado:

```text
dist/
└── ubuntu-user-manager_1.0.0_amd64.deb
```

Na máquina final:

```bash
sudo apt install ./ubuntu-user-manager_1.0.0_amd64.deb
```

Não deve ser necessário baixar:

```text
Python
pip
PyInstaller
dependências de desenvolvimento
código fonte
```

---

# 51. Ordem de implementação

## Etapa 1 — Helper

- listar usuários;
- criar;
- resetar;
- excluir;
- validar dados;
- configurar grupos;
- validar grupos proibidos;
- incluir em `docker`.

## Etapa 2 — Polkit

- create;
- reset;
- delete.

## Etapa 3 — GTK4/Libadwaita

- tela principal;
- listagem;
- busca;
- criação;
- reset;
- exclusão.

## Etapa 4 — Empacotamento standalone

## Etapa 5 — Pacote Debian

## Etapa 6 — Docker para build

## Etapa 7 — Makefile

## Etapa 8 — README

---

# 52. Entrega

Não apenas descreva como fazer.

**Gere efetivamente o projeto completo.**

Entregue:

- todos os arquivos;
- código Python;
- helper;
- policy Polkit;
- `.desktop`;
- Dockerfile;
- Makefile;
- scripts de build;
- estrutura Debian;
- scripts install/uninstall;
- requirements;
- README.

Depois explique:

1. o que foi criado;
2. como a arquitetura funciona;
3. como executar em desenvolvimento;
4. como testar criação;
5. como verificar os grupos do usuário;
6. como testar acesso à rede;
7. como testar Docker sem sudo;
8. como confirmar que o usuário não possui sudo;
9. como testar primeiro login;
10. como testar reset;
11. como testar exclusão;
12. como testar autenticação Polkit;
13. como gerar o `.deb`;
14. como instalar em outra máquina;
15. quais dependências continuam sendo fornecidas pelo Ubuntu;
16. como gerar uma nova versão;
17. como desinstalar;
18. quais melhorias seriam apropriadas para uma V2;
19. quais riscos permanecem pelo uso do grupo `docker` e como eles são tratados operacionalmente.

Priorize uma **MVP completamente funcional, simples, segura e instalável**, sem adicionar funcionalidades desnecessárias.
