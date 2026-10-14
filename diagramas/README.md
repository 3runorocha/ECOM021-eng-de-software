# Diagramas

Escritos em Mermaid, dentro dos `.md`. O GitHub renderiza direto na página; para a
apresentação dá para exportar em <https://mermaid.live> colando o bloco.

| | Diagrama | O que mostra |
|---|---|---|
| 1 | [Arquitetura](1_arquitetura.md) | Os 7 processos, banco por serviço, quem chama quem |
| 2 | [Componentes](2_componentes.md) | Contratos `IComponente*`, implementações HTTP, quem consome |
| 3 | [Framework](3_framework.md) | Template Method, frozen spots e hotspots |
| 4 | [Contrato](4_contrato.md) | Assinatura com compensação, encerramento e multa |
| 5 | [Agente](5_agente.md) | O agente consome componentes **e** é um componente |

## Por que texto e não imagem

Os diagramas anteriores eram cinco PNGs do domínio de biblioteca (incluindo modelo de
features e OVM, que eram da Linha de Produto da disciplina antiga e não têm escopo
aqui). Imagem não dá para revisar em diff nem corrigir junto com o código, e as cinco
ficaram erradas assim que o domínio mudou.

Os PNGs continuam recuperáveis no histórico do git:

```bash
git log --oneline --diff-filter=D -- diagramas/
git checkout <commit>^ -- diagramas/3_componentes.png
```
