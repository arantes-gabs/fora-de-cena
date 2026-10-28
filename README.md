# Fora de Cena

![Fora de Cena — saídas criativas para suas chamadas](assets/brand/readme-cover.png)

Desapareça da webcam com um gesto e reapareça quando quiser. Teleporte, fumaça, poeira, pixels e portal para suas chamadas.

[Baixar](#baixar) · [Windows](#windows) · [Mac](#mac) · [Linux](#linux) · [Como usar](#como-usar) · [Ajuda](#ajuda)

## Baixar

**Os aplicativos já incluem Python, bibliotecas e modelos. Não precisa baixar o código-fonte nem compilar.**

| Seu computador | Download | Versão |
| --- | --- | --- |
| **Windows 64 bits — instalar** | [Baixar instalador](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Setup.exe) | 0.4.0 |
| **Windows 64 bits — executar sem instalar** | [Baixar executável único](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Portatil.exe) | 0.4.0 |
| **Mac Apple Silicon — M1 em diante** | [Baixar DMG](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/ForaDeCena-0.5.0-beta.1-macos-arm64-experimental.dmg) | 0.5.0-beta.1 |
| **Linux Intel/AMD 64 bits** | [Baixar TAR.GZ x64](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.2/ForaDeCena-0.5.0-beta.2-linux-x86_64-experimental.tar.gz) | 0.5.0-beta.2 |
| **Linux ARM64** | [Baixar TAR.GZ ARM64](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.2/ForaDeCena-0.5.0-beta.2-linux-arm64-experimental.tar.gz) | 0.5.0-beta.2 |
| **Mac Intel** | Ainda sem download | Em desenvolvimento |

Mac e Linux são **betas experimentais** e podem apresentar falhas. As versões são diferentes entre sistemas: escolha pela sua plataforma.

**Use os links acima.** O botão **Code → Download ZIP** baixa o código-fonte, não o aplicativo pronto. Os ZIPs de fontes e licenças nas Releases não precisam ser instalados para usar.

### Preciso instalar mais alguma coisa?

| Quero usar… | Windows | Mac | Linux |
| --- | --- | --- | --- |
| **Só a prévia e os efeitos dentro do app** | Nada adicional de câmera virtual | Nada adicional de câmera virtual | Nada adicional de câmera virtual |
| **O vídeo com efeitos nas chamadas** | OBS Studio | OBS Studio 30+ | Driver `v4l2loopback` |

**No Linux, OBS não é necessário e não substitui o `v4l2loopback`.** Veja os passos do seu sistema abaixo.

---

## Windows

### Abrir o aplicativo

- **Instalador:** execute o `Setup.exe`, conclua a instalação e abra pelo menu Iniciar.
- **Executável único:** abra o `Portatil.exe`. Não precisa instalar; a abertura pode demorar enquanto prepara os componentes temporários.

Os executáveis não têm assinatura digital. Baixe pela Release oficial e mantenha as proteções do Windows ativadas.

### Usar nas chamadas

1. Instale o [OBS Studio pelo site oficial](https://obsproject.com/download).
2. No Fora de Cena, abra **Configurar → Meet → Preparar vídeo para o Meet**.
3. Use sua **webcam física** como entrada e **OBS Virtual Camera** como saída.
4. Inicie a câmera no Fora de Cena.
5. No Meet, Teams, Discord ou outro programa, selecione **OBS Virtual Camera**.

Não precisa manter o OBS aberto. Se estiver aberto, deixe a câmera virtual parada nele enquanto o Fora de Cena a utiliza.

---

## Mac

**Compatível com Apple Silicon — M1 em diante — e macOS 15 ou posterior.** Para conferir seu chip, abra **menu Apple → Sobre Este Mac**.

### Abrir o aplicativo

1. Baixe e abra o **DMG**.
2. Arraste **Fora de Cena.app** para **Aplicativos** e abra por essa pasta.
3. Se a Apple bloquear a abertura, após tentar abrir, vá a **Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim**.
4. Permita o acesso à webcam quando solicitado.

Esta beta não tem notarização Apple. Autorize somente o download oficial; não desative o Gatekeeper. Há confirmação de funcionamento em um M1, sem garantia para todas as combinações de hardware e serviços.

### Usar nas chamadas

1. Instale o [OBS Studio 30 ou posterior](https://obsproject.com/download), compatível com seu macOS.
2. Abra o OBS, **inicie e pare a câmera virtual uma vez** e feche o OBS.
3. Se solicitado, autorize **OBS Virtual Camera** em **Ajustes do Sistema → Geral → Itens de Início e Extensões → Extensões de Câmera**. Reabra o navegador.
4. No Fora de Cena, use a **webcam física** como entrada e **OBS Virtual Camera** como saída. Inicie o vídeo.
5. Na chamada, selecione **OBS Virtual Camera**.

Não deixe a câmera virtual iniciada no OBS ao mesmo tempo.

[Mais informações sobre o Mac →](MAC_APPLE_SILICON.md)

---

## Linux

**Para enviar os efeitos às chamadas, é necessário configurar o `v4l2loopback`.** Sem ele, você pode testar normalmente na prévia do app.

### Abrir o aplicativo

1. Baixe o **TAR.GZ** da sua arquitetura. A maioria dos PCs Intel/AMD usa **x64**.
2. Extraia em uma **pasta nova**, mantendo o executável `ForaDeCena` e a pasta `_internal` juntos.
3. Abra `ForaDeCena`. Se o duplo clique não funcionar, abra um terminal nessa pasta e execute:
```bash
./ForaDeCena
```
**Não execute o aplicativo com `sudo`.** Não misture arquivos de betas diferentes.

Se não souber sua arquitetura, execute `uname -m`: `x86_64` corresponde a x64; `aarch64` ou `arm64`, a ARM64.

A base é Ubuntu 22.04/glibc 2.35, com ambiente gráfico. Outras distribuições podem exigir bibliotecas adicionais. Não há pacote para 32 bits ou Alpine/musl.

### Preparar a câmera virtual — Ubuntu ou Linux Mint

Se já existe uma câmera `v4l2loopback` configurada, use o dispositivo existente. Caso contrário, abra o Terminal e execute **uma linha por vez**:
```bash
sudo apt update
sudo apt install v4l2loopback-dkms linux-headers-$(uname -r)
sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label="Fora de Cena"
```
A senha solicitada é a do computador e não aparece ao digitar. Depois de reiniciar, pode ser necessário repetir a linha `sudo modprobe…`.

Esses comandos são para Ubuntu/Mint. Em outras distribuições, consulte a [documentação do driver](https://github.com/v4l2loopback/v4l2loopback#distributions). Se o Secure Boot exigir assinatura do módulo, siga as instruções da distribuição, mantendo a proteção ativada.

### Usar nas chamadas

1. No Fora de Cena, selecione sua **webcam física** como entrada.
2. Em **Configurar → Meet**, escolha **Câmera virtual Linux** e o dispositivo de saída, ou **Automático**.
3. **Inicie o vídeo no Fora de Cena primeiro.**
4. Depois, na chamada, selecione a câmera virtual. Com a configuração acima, ela se chama **Fora de Cena**.

[Mais informações sobre o Linux →](LINUX.md)

---

## Como usar

Os passos são os mesmos nos três sistemas:

1. Em **Configurar → Câmera**, escolha sua webcam e clique em **Iniciar câmera**.
2. Clique em **Capturar fundo (4 s)** e saia do enquadramento.
3. Confira o cenário vazio e clique em **Confirmar fundo vazio**.
4. Volte, escolha um efeito e use **Ativar efeito** ou faça o gesto ensinado em **Como fazer**.
5. Use **Reaparecer** para voltar ou **Restaurar · F8** para interromper o efeito.

No Mac, alguns teclados exigem **Fn + F8**. O botão **Restaurar** está sempre disponível.

**Mantenha o fundo Estático**, padrão recomendado, e a câmera fixa. Recapture o fundo se mudar a posição ou a iluminação. A opção **Em movimento** é experimental e também exige a captura inicial.

Na chamada, desative o desfoque e os fundos virtuais do serviço. Seu microfone continua sendo o normal da reunião; o Fora de Cena não produz áudio.

### Sair automaticamente do Meet — opcional

A extensão serve apenas para fechar a aba vinculada do Meet após o desaparecimento. **Os efeitos funcionam sem ela.**

A opção começa desligada e exige vínculo explícito com a reunião. [Veja como configurar →](COMO_USAR.md#sair-do-meet-automaticamente-opcional)

---

## Ajuda

| Problema | O que conferir |
| --- | --- |
| A webcam não aparece | Permissões do sistema, outros programas usando a câmera e **Atualizar lista**. |
| Os efeitos aparecem no app, mas não na chamada | Selecione a **câmera virtual**, não a webcam física. |
| A câmera virtual não aparece no Linux | Confira o `v4l2loopback` e inicie o vídeo no Fora de Cena antes de selecionar a câmera na chamada. |
| O gesto não dispara | Veja **Como fazer**, melhore a iluminação e relaxe a mão antes de repetir. A ativação manual também funciona. |
| Está lento | Pare a câmera, tente **640 × 480** e mantenha o fundo **Estático**. |
| Quero recuperar a imagem imediatamente | Clique em **Restaurar**. |

720p a 30 FPS é um objetivo e depende do hardware. A compatibilidade com chamadas depende do aplicativo, navegador e permissões.

[**Relatar um erro ou resultado de teste →**](https://github.com/arantes-gabs/fora-de-cena/issues/new/choose)

Informe seu sistema, versão do app e o que aconteceu. Os relatos são públicos: remova dados pessoais, senhas, tokens e chaves dos logs. Para vulnerabilidades, siga [SECURITY.md](SECURITY.md).

## Privacidade

As imagens são processadas no computador. O aplicativo não grava imagens, não abre o microfone nem envia vídeo a servidores próprios. O fundo fica em memória durante a sessão.

**O MediaPipe declara métricas de uso/desempenho.** Foram observadas tentativas HTTPS em uma amostra sintética; a origem exata segue em investigação. Processamento local não significa ausência garantida de conexões externas.

A chamada transmite pelo serviço escolhido. Os efeitos podem falhar e **não garantem anonimização**.

[Política completa de privacidade →](PRIVACY.md)

## Código-fonte

O repositório inclui aplicativo, efeitos, gestos, auxiliar de vídeo, extensão, testes e receitas de empacotamento.

- [Executar pelos fontes e conhecer a arquitetura](DESENVOLVIMENTO.md)
- [Construir os pacotes](DISTRIBUIR.md)
- [Estado da adaptação Mac/Linux](MULTIPLATAFORMA.md)
- [Contribuir na sua cópia](CONTRIBUTING.md)

Cada Release oferece os fontes correspondentes e os avisos dos componentes distribuídos.

## Licenças e créditos

Aplicativo principal: **MIT**. Auxiliar independente de saída de vídeo: **GPL-2.0-only**. Bibliotecas, modelos e drivers mantêm suas próprias licenças.

Ao redistribuir, preserve o acesso aos pacotes **Fontes-Saida** e **Licencas** disponíveis nas Releases.

[Licença](LICENSE) · [Avisos de terceiros](THIRD_PARTY_NOTICES.md)

[VanishCam](https://github.com/Nicovic17/vanish_webcam) foi a referência técnica inicial. O Fora de Cena usa implementação própria e não inclui código ou recursos desse projeto. As ilustrações e a identidade visual foram fornecidas pelo mantenedor.
