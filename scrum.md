# Scrum - Aluguel de Imóveis

Planejamento ágil do projeto da ECOM021. As sprints abaixo são as que de fato
aconteceram: cada uma corresponde a uma fase do [`PLANO_DE_EXECUCAO.md`](PLANO_DE_EXECUCAO.md),
e o registro do que foi entregue e verificado está em [`VALIDACAO.md`](VALIDACAO.md).

## Atores

- **Inquilino** - procura imóvel, assina e encerra contrato, recebe avisos
- **Proprietário / corretor** - cadastra e administra o portfólio
- **Sistema** - tarefas automáticas: marcar contratos vencidos, varrer e notificar
- **Agente** - assistente que busca imóveis em linguagem natural e redige avisos

---

## Product Backlog

| ID | Como... | Quero... | Para... | Prioridade | Pts |
|----|---------|----------|---------|------------|-----|
| US01 | corretor | cadastrar imóveis no portfólio | manter a oferta atualizada | Alta | 3 |
| US02 | inquilino | filtrar imóveis por cidade, tipo, quartos e faixa de aluguel | achar o que cabe no meu bolso | Alta | 5 |
| US03 | sistema | tratar disponibilidade como sim/não | impedir dois contratos no mesmo imóvel | Alta | 3 |
| US04 | inquilino | me cadastrar | ter acesso ao sistema | Alta | 2 |
| US05 | inquilino | autenticar com e-mail e senha | usar o sistema com segurança | Alta | 3 |
| US06 | corretor | listar os usuários e seus contratos em vigor | administrar a base | Média | 3 |
| US07 | inquilino | assinar um contrato de aluguel | alugar o imóvel | Alta | 5 |
| US08 | inquilino | encerrar o contrato | devolver o imóvel | Alta | 3 |
| US09 | sistema | cobrar multa proporcional ao aluguel por dia de atraso | aplicar a política da imobiliária | Alta | 5 |
| US10 | sistema | recusar segundo contrato em imóvel ocupado | manter a realidade consistente | Alta | 5 |
| US11 | sistema | marcar contratos vencidos como atrasados | manter o status correto | Média | 2 |
| US12 | inquilino | receber alertas de vencimento e atraso | não perder o prazo | Média | 3 |
| US13 | sistema | varrer os contratos e gerar alertas sozinho | notificar sem ação manual | Média | 3 |
| US14 | inquilino | receber recomendações de imóveis pelo meu histórico | descobrir opções parecidas | Baixa | 5 |
| US15 | sistema | rotear tudo por um API Gateway | ter ponto de entrada único | Alta | 5 |
| US16 | sistema | validar o token no gateway | proteger as rotas | Alta | 3 |
| US17 | desenvolvedor | estruturar em microsserviços independentes | facilitar manutenção e evolução | Alta | 8 |
| US18 | inquilino | usar o sistema por uma interface web | fazer tudo de forma visual | Alta | 5 |
| US19 | corretor | ver a saúde real dos microsserviços | saber o que está no ar | Baixa | 3 |
| US20 | desenvolvedor | reusar um framework com Template Method e hotspots | criar aplicações novas rápido | Média | 8 |
| US21 | inquilino | buscar imóvel em linguagem natural | pedir do meu jeito, sem preencher filtro | Baixa | 8 |
| US22 | sistema | deixar o agente redigir o aviso de vencimento | mandar um texto melhor que o padrão | Baixa | 5 |
| US23 | desenvolvedor | ter testes automatizados da regra de negócio | mexer no código sem medo | Média | 8 |

**Total:** 23 histórias · 103 story points.

US20 é a herança direta do trabalho de Reúso de Software. US21 e US22 são o item
opcional do enunciado (Agentic AI).

---

## Sprints

| Sprint | Meta | Histórias | Pts | Status |
|--------|------|-----------|-----|--------|
| 1 | Sanear o esqueleto herdado e torná-lo portável | US17, US19 | 11 | ✅ |
| 2 | Domínio: portfólio de imóveis | US01, US02, US03 | 11 | ✅ |
| 3 | Domínio: contratos, multa e a regra do imóvel único | US07, US08, US09, US10, US11 | 20 | ✅ |
| 4 | Interface web honesta | US06, US12, US14, US18, US19 | 19 | ✅ |
| 5 | Agente | US21, US22 | 13 | ⚠️ construído, não exercitado |
| 6 | Qualidade e documentação | US23 | 8 | ✅ |
| 7 | Revisão de código e testes de ponta a ponta | US05, US16, US23 (refinadas) | - | ✅ |

US04, US05, US15 e US16 (usuários e gateway) vieram prontas do projeto anterior e
atravessaram a migração sem mudança - é o reúso aparecendo no planejamento.

---

## Sprint 1 - Sanear o esqueleto

**Meta:** o projeto herdado tem de rodar sem ajuste manual, com a configuração vinda de
variável de ambiente.

- Corrigir o hotspot obrigatório do framework, que não era obrigatório de fato
- Externalizar 17 URLs e 5 caminhos de banco em variável de ambiente
- Trocar `@app.on_event` depreciado por `lifespan`
- Filtrar headers hop-by-hop no proxy do gateway
- Script que sobe todos os serviços num comando

**Revisão:** o `PUBLIC_ROUTES` que parecia bug não era - o gateway consome o primeiro
segmento como seletor de serviço. Descartado após verificação.

## Sprint 2 - Portfólio de imóveis

**Meta:** o catálogo de livros vira portfólio de imóveis.

- `Livro` → `Imovel`: tipo, endereço, cidade, quartos, banheiros, área, aluguel
- `atualizar_disponibilidade(delta)` → `definir_disponibilidade(bool)`
- Filtros de cidade, tipo, quartos mínimos e faixa de valor, aplicados no serviço
- Seeds com 18 imóveis reais de Maceió, Recife e João Pessoa

**Revisão:** renomear o serviço arrastou os componentes que o consomem; não dava para
separar em sprints diferentes sem deixar o repositório incoerente.

## Sprint 3 - Contratos

**Meta:** empréstimo de 14 dias vira contrato de 12 meses.

- `Emprestimo` → `Contrato`, com `valor_mensal` gravado na assinatura
- Prazo em meses, com ajuste de mês curto (31/01 + 1 mês = 28/02)
- Multa de 1/30 do aluguel por dia de atraso, no lugar dos R$ 0,50 fixos
- Um contrato aberto por imóvel, imposto no serviço **e** por índice no banco
- Compensação: se o INSERT falha, o imóvel volta a ficar disponível

**Revisão:** renomear entidade é operação atômica. As quatro sprints planejadas para
isso viraram uma só.

## Sprint 4 - Interface web

**Meta:** o sistema volta a ser demonstrável, e nenhuma tela mente.

- Telas de imóveis, contratos, usuários, notificações e recomendação com dados reais
- Status dos serviços no menu lendo o `/health` de verdade
- Estado de erro em toda tela: falha de backend aparece como falha

**Revisão:** três telas (Dashboard, Notificações, Usuários) não estavam em nenhuma
história e mostravam dados inventados. Entraram como US06, US12 e US19 revisadas.

## Sprint 5 - Agente

**Meta:** busca em linguagem natural usando a camada de componentes como ferramentas.

- Serviço de agente em :8006, com três ferramentas de leitura
- `IComponenteAgente`: o agente consome componentes e também é um componente
- `AppAvisoVencimento` orquestra o agente pelo Template Method
- Degrada para texto padrão quando o agente está fora ou sem credencial

**Pendência:** a qualidade da resposta do modelo não foi verificada - falta
`ANTHROPIC_API_KEY` na máquina. O que foi testado está em `VALIDACAO.md`, semana 8.

## Sprint 6 - Qualidade e documentação

**Meta:** mexer no código sem medo, e documentação que descreve o que existe.

- 73 testes de unidade com repositórios fake + 4 de integração pelo gateway
- Suíte integrada ao `validar.py`, que roda em 37 checagens
- Diagramas reescritos em Mermaid, refletindo o código final
- README, guia do framework e este documento atualizados

**Revisão:** a suíte achou um bug de fuso no token (declarava 11 horas de validade em
vez de 8) que nenhuma checagem anterior pegava.

## Sprint 7 - Revisão de código e testes de ponta a ponta

**Meta:** revisar o projeto inteiro e testar os fluxos pelo navegador, como um usuário.
Sprint extra, aberta com a folga do cronograma; não traz histórias novas, refina as já
entregues.

- Revisão de código arquivo por arquivo
- Senha com PBKDF2-SHA256 (600 mil iterações, sal por usuário) e segredo do token fora
  do código
- Gateway repassa a identidade aos serviços; contratos restritos ao dono
- Imóveis restritos a admin e proprietário; cadastro público cria só inquilino
- `/health` em paralelo, encerramento com compensação, e-mail repetido devolvendo 400
- 29 casos de ponta a ponta com Playwright (`e2e/`) e demonstração gravada
- Agente com dois provedores de modelo: Gemini (nível gratuito) ou Claude

**Revisão:** a suíte de ponta a ponta passa em 27 dos 29 casos. As duas falhas são
defeitos reais, registrados e mantidos em aberto: o serviço de recomendação não confere
quem está pedindo, e no celular o menu lateral espreme o conteúdo.

---

## Definição de pronto

Uma história só é dada como pronta quando:

1. o comportamento está implementado e o `validar.py` passa inteiro;
2. a regra de negócio nova tem teste que falha se ela for removida;
3. a tela correspondente mostra dado real, ou mostra o erro - nunca dado inventado;
4. o que ficou de fora está escrito, com o motivo.
