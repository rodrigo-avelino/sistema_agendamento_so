================================================================================
   SISTEMA DE AGENDAMENTO MÉDICO - PROJETO DE SISTEMAS OPERACIONAIS
================================================================================

DESCRIÇÃO
---------
Este software é uma simulação de um sistema de agendamento médico distribuído,
desenvolvido para demonstrar conceitos fundamentais de Sistemas Operacionais,
incluindo:
1. Gerenciamento de Processos e Threads (Concorrência).
2. Sistema de Arquivos (Persistência e Estrutura de Diretórios).
3. Sincronização e Exclusão Mútua (Locks e Semáforos).
4. Operações de Entrada/Saída (Logs e Relatórios PDF).

O sistema opera como um servidor local único ("Single Artifact") que serve tanto
a API quanto as interfaces de Administração e Cliente.

--------------------------------------------------------------------------------
INSTRUÇÕES DE INSTALAÇÃO E EXECUÇÃO
--------------------------------------------------------------------------------

IMPORTANTE: O sistema é "portátil". Não requer instalação de Python ou bibliotecas
na máquina do usuário, pois todas as dependências estão embutidas no executável.

### AMBIENTE WINDOWS
1. Localize o arquivo `SistemaMedico_Win.exe`.
2. Dê um clique duplo para executar.
   - Uma janela de terminal (console) se abrirá. NÃO a feche. Ela é o processo
     do servidor rodando em background.
   - Na primeira execução, o sistema criará automaticamente a pasta `data/`
     no mesmo diretório do executável.
3. Abra seu navegador (Chrome, Edge, Firefox) e acesse:
   - Painel Admin: http://localhost:8000/admin
   - Painel Cliente: http://localhost:8000/client

### AMBIENTE LINUX (Ubuntu/Mint/Debian)
1. Abra o terminal na pasta onde está o arquivo `SistemaMedico_Linux`.
2. Conceda permissão de execução (necessário apenas na primeira vez):
   $ chmod +x SistemaMedico_Linux
3. Execute o sistema:
   $ ./SistemaMedico_Linux
4. O servidor iniciará mostrando logs de [BOOT].
5. Abra seu navegador e acesse os links acima.

--------------------------------------------------------------------------------
GUIA DE USO (CENÁRIOS DE TESTE)
--------------------------------------------------------------------------------

1. CONFIGURAÇÃO INICIAL (ADMIN)
   - Acesse http://localhost:8000/admin
   - Cadastre um novo médico (ex: "Dr. House" - Cardiologia).
   - Clique no ícone de engrenagem (⚙) para definir a agenda.
   - Marque os dias da semana e horários disponíveis e salve.
   - TESTE DE I/O: Clique em "Gerar Novo Relatório". O sistema irá gerar um PDF
     na pasta `data/relatorios` e disponibilizará o download na lista.

2. SIMULAÇÃO DE CONCORRÊNCIA (CLIENTES)
   - Abra duas abas (ou navegadores diferentes) em http://localhost:8000/client
   - Selecione a data correspondente à agenda criada.
   - No Cliente A: Clique em um horário (ex: 09:00).
     > O botão ficará AZUL (Seu Lock).
   - No Cliente B: Observe o mesmo horário imediatamente.
     > O botão ficará AMARELO (Bloqueado por outro processo).
     > Tente clicar: O sistema impedirá a ação (Exclusão Mútua).
   - No Cliente A: Clique em "Confirmar".
     > O horário ficará VERMELHO (Ocupado/Persistido) para ambos.

3. TESTE DE INTEGRIDADE E LOGS
   - Todas as ações geram registros de auditoria.
   - No Admin, observe a janela "Logs do Sistema" rolando em tempo real.
   - Os dados físicos podem ser verificados na pasta `data/` criada ao lado do executável.

--------------------------------------------------------------------------------
ESTRUTURA DE ARQUIVOS (GERADA AUTOMATICAMENTE)
--------------------------------------------------------------------------------
Ao rodar o executável, a seguinte estrutura será criada para persistência:

(Pasta Atual)/
 ├── SistemaMedico_Linux (ou .exe)
 └── data/                  <-- [SO] Manipulação de Sistema de Arquivos
     ├── consultas/
     │   ├── medicos.json   (Banco de dados de médicos)
     │   └── consultas.json (Banco de dados de agendamentos)
     ├── logs/
     │   └── system_logs.json (Registro de eventos I/O)
     └── relatorios/
         └── relatorio_*.pdf (Arquivos binários gerados)

--------------------------------------------------------------------------------
SOLUÇÃO DE PROBLEMAS
--------------------------------------------------------------------------------
* Erro: "Address already in use" ou porta ocupada.
  - Certifique-se de que não há outra instância do programa rodando.
  - Feche o terminal/console anterior antes de abrir novamente.

* Erro: Relatório PDF não abre.
  - Verifique se você tem um leitor de PDF instalado.
  - Verifique se a pasta `data/relatorios` tem permissão de escrita.

================================================================================