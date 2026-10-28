# Testes de ponta a ponta

Testes do sistema de aluguel de imóveis feitos pelo navegador, como um usuário
faria: entrar, buscar, filtrar, assinar e encerrar contratos, trocar de perfil.
São 29 casos, escritos em [`casos.feature`](casos.feature) e automatizados com
Playwright e pytest em [`test_prototipo.py`](test_prototipo.py).

| Arquivo | Para que serve |
|---|---|
| `casos.feature` | Os cenários em Gherkin, em português (CT01 a CT29) |
| `test_prototipo.py` | Um teste para cada cenário, com o mesmo código CT |
| `conftest.py` | Abre um navegador novo por caso, grava vídeo e tira screenshot |
| `apoio.py` | Contas de exemplo, login e a cópia dos bancos |
| `demo_narrada.py` | Grava a demonstração narrada em MP4 |
| `gerar_relatorio.py` | Monta o relatório HTML a partir dos resultados |

Os testes não estragam seus dados: antes de começar, a suíte copia os bancos, e
restaura a cópia antes de cada caso e no fim.

## Passo a passo no Windows

Se você nunca usou o terminal, siga na ordem. Cada comando vai numa linha; digite
(ou cole) e aperte Enter.

### 1. Instale o Python

1. Entre em https://www.python.org/downloads/ e baixe a versão mais recente.
2. Abra o instalador. **Na primeira tela, marque "Add Python to PATH"** antes de
   clicar em "Install Now". Sem isso o terminal não encontra o Python.
3. Quando terminar, feche o instalador.

### 2. Abra o terminal nesta pasta

1. No Explorador de Arquivos, abra a pasta `e2e` do projeto.
2. Clique na barra de endereço (onde aparece o caminho da pasta), apague o que
   estiver escrito, digite `powershell` e aperte Enter.
3. Abre uma janela azul ou preta já nesta pasta. Confira o Python:

```
python --version
```

Deve aparecer algo como `Python 3.14.x`. Se aparecer um erro, volte ao passo 1 e
reinstale marcando "Add Python to PATH".

### 3. Instale as ferramentas

```
pip install playwright pytest edge-tts httpx
```

```
python -m playwright install chromium
```

O segundo comando baixa o navegador que os testes usam (uns 150 MB).

### 4. Deixe o sistema no ar

Os testes conversam com o sistema de verdade, então ele precisa estar rodando,
com os dados de exemplo. Siga o README da raiz do projeto para:

1. subir os serviços: `python subir_servicos.py` (na raiz do projeto);
2. subir a tela: `npm run dev` (na pasta `biblioteca-online`);
3. carregar os dados de exemplo uma vez: `python seed.py`, depois, com os
   serviços parados, `python seed_contratos.py` (na pasta `biblioteca`).

Os casos esperam 18 imóveis e 42 contratos. Se os dados forem outros, a suíte
para logo no começo e diz o que fazer.

### 5. Rode os testes

```
python -m pytest test_prototipo.py -v
```

Leva menos de um minuto. Cada linha mostra um caso com `PASSED` (passou) ou
`FAILED` (falhou). Hoje passam 27 de 29: o CT26 e o CT29 falham por dois
defeitos reais do sistema, descritos no relatório.

Para rodar um caso só, use `-k` com o código dele:

```
python -m pytest test_prototipo.py -v -k CT14
```

Para ver o navegador fazendo os testes na tela:

```
$env:E2E_VISIVEL = "1"; python -m pytest test_prototipo.py -v
```

O resultado fica em `resultados/`: um screenshot e um vídeo por caso, e o
`resultados.json` com o placar.

### 6. Gere o relatório

```
python gerar_relatorio.py
```

Abra `resultados/relatorio/index.html` no navegador.

## Demonstração narrada

O `demo_narrada.py` grava um vídeo de uns 6 minutos passando pelo sistema, com
narração em português gerada pela voz Francisca (edge-tts). Precisa de internet
(a voz é gerada num serviço da Microsoft) e do ffmpeg.

### Instale o ffmpeg

1. Entre em https://www.gyan.dev/ffmpeg/builds/ e baixe o
   `ffmpeg-release-full.7z` (ou o `.zip`, se não tiver o 7-Zip).
2. Extraia numa pasta fixa, por exemplo `C:\ffmpeg`. Dentro dela há uma pasta
   `bin` com o `ffmpeg.exe`.
3. Coloque essa pasta no PATH: aperte a tecla Windows, digite "variáveis de
   ambiente" e abra "Editar as variáveis de ambiente do sistema". Clique em
   "Variáveis de Ambiente", selecione `Path` em "Variáveis do usuário", clique em
   "Editar", depois em "Novo", e cole o caminho da pasta `bin`
   (por exemplo `C:\ffmpeg\bin`). Confirme com OK em todas as janelas.
4. **Feche e abra o terminal de novo** e confira:

```
ffmpeg -version
```

### Grave

Com o navegador aparecendo na tela enquanto grava:

```
python demo_narrada.py --visivel
```

Sem abrir janela (você pode continuar usando o computador):

```
python demo_narrada.py
```

O vídeo sai em `resultados/demo/demonstracao_narrada.mp4`. Para só ver o texto da
narração, sem gravar:

```
python demo_narrada.py --roteiro
```

A gravação usa o Microsoft Edge quando ele está instalado, para que as mensagens
do navegador (como "Preencha este campo.") saiam em português. Sem ele, usa o
Chromium do Playwright, que as mostra em inglês.
