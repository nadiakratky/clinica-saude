# Clínica Saúde+ 🩺

Sistema web Full Stack para agendamento de consultas, desenvolvido como solução para um desafio técnico de estágio Full Stack.

O projeto permite que pacientes consultem horários disponíveis e realizem agendamentos online, enquanto funcionários possuem uma área restrita para visualizar, reagendar e cancelar consultas.

---

## Sobre o projeto

Uma clínica recebe diariamente diversos contatos perguntando sobre datas e horários disponíveis para consulta.

Quando esse processo é realizado manualmente, por exemplo pelo WhatsApp, o paciente precisa aguardar uma resposta e o funcionário precisa conferir a agenda antes de confirmar cada atendimento.

A proposta da **Clínica Saúde+** é simplificar esse processo através de um sistema de agendamento online.

O paciente pode:

- selecionar uma data;
- consultar horários disponíveis;
- realizar um agendamento;
- receber a confirmação imediatamente.

O sistema também possui uma área restrita para funcionários, onde é possível:

- visualizar as consultas cadastradas;
- reagendar uma consulta;
- cancelar um agendamento.

---

## Funcionalidades

### Paciente

- Consulta de horários disponíveis por data
- Agendamento de consulta
- Validação automática de finais de semana
- Validação de feriados nacionais
- Bloqueio de horários já ocupados
- Confirmação do agendamento
- Exibição de orientação para cancelamento ou reagendamento

### Funcionário

- Área protegida por autenticação
- Visualização dos agendamentos
- Reagendamento de consultas
- Cancelamento de consultas
- Atualização automática dos horários disponíveis
- Proteção dos dados dos pacientes na área interna

---

## Tecnologias utilizadas

### Backend

- Python
- Flask
- SQLite
- Requests
- ZoneInfo

### Frontend

- HTML5
- CSS3
- JavaScript

### API externa

O sistema utiliza a API pública **Nager.Date** para consultar os feriados nacionais brasileiros de 2026.

Endpoint utilizado:

```text
https://date.nager.at/api/v3/PublicHolidays/2026/BR
```

---

## Regras de negócio

O sistema segue as seguintes regras:

- Horário de funcionamento: **08:00 às 18:00**
- Cada consulta possui duração de **1 hora**
- O último horário disponível para início de consulta é **17:00**
- Não são permitidos agendamentos aos sábados e domingos
- Não são permitidos agendamentos em feriados nacionais
- Um mesmo horário não pode possuir duas consultas
- Os horários já ocupados deixam de aparecer para novos pacientes
- A listagem de pacientes é acessível somente pela área do funcionário
- Reagendamentos também passam pelas mesmas validações de data e horário

---

## Fluxo do sistema

```text
Paciente escolhe uma data
        ↓
Frontend envia a data para o backend
        ↓
Backend consulta a API de feriados
        ↓
Backend verifica final de semana e feriado
        ↓
Backend consulta horários ocupados no SQLite
        ↓
Retorna somente horários disponíveis
        ↓
Paciente escolhe um horário
        ↓
Informa nome e telefone
        ↓
Backend salva o agendamento
        ↓
Confirmação é exibida ao paciente
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/available?date=2026-10-13` | Consulta horários disponíveis |
| POST | `/appointments` | Cria um novo agendamento |
| GET | `/appointments` | Lista os agendamentos para funcionários autenticados |
| PUT | `/appointments/<id>` | Reagenda uma consulta |
| DELETE | `/appointments/<id>` | Cancela uma consulta |
| POST | `/employee/login` | Autentica o funcionário |
| POST | `/employee/logout` | Encerra a sessão do funcionário |
| GET | `/employee/status` | Verifica se existe uma sessão autenticada |

Durante um reagendamento, também é possível utilizar:

```text
GET /available?date=2026-10-14&exclude_id=1
```

O parâmetro `exclude_id` permite que o horário atual da própria consulta não seja considerado ocupado durante a alteração.

---

## Exemplo de criação de agendamento

### Requisição

```http
POST /appointments
Content-Type: application/json
```

```json
{
    "patient_name": "Maria Silva",
    "phone": "(19) 99999-9999",
    "date": "2026-10-13",
    "time": "09:00"
}
```

### Resposta

```json
{
    "message": "Agendamento realizado com sucesso.",
    "appointment": {
        "id": 1,
        "patient_name": "Maria Silva",
        "phone": "(19) 99999-9999",
        "date": "2026-10-13",
        "time": "09:00",
        "timezone": "America/Sao_Paulo"
    }
}
```

---

## Estrutura do projeto

```text
clinica-agendamento/
│
├── app.py
├── database.db
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```

O banco `database.db` é criado automaticamente pelo sistema caso ainda não exista.

---

## Como executar o projeto

### 1. Clone o repositório

```bash
git clone SEU-LINK-DO-GITHUB
```

Entre na pasta:

```bash
cd clinica-agendamento
```

### 2. Crie um ambiente virtual

Windows:

```bash
python -m venv .venv
```

Ative o ambiente:

```bash
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` deve conter:

```text
Flask
requests
tzdata
```

### 4. Execute o sistema

```bash
python app.py
```

O Flask iniciará o servidor local.

Abra no navegador:

```text
http://127.0.0.1:5000
```

---

## Área do funcionário

Para fins de demonstração do projeto, existe uma senha padrão para acesso à área interna:

```text
clinica2026
```

A senha é validada no backend e não fica armazenada no JavaScript.

O sistema também permite utilizar uma variável de ambiente:

```text
EMPLOYEE_PASSWORD
```

Em uma aplicação real, a autenticação seria substituída por um sistema completo de usuários, senhas criptografadas e níveis de acesso.

---

## Segurança e privacidade

Os dados dos pacientes não são exibidos na área pública.

O endpoint responsável por listar, alterar e cancelar consultas verifica se existe uma sessão de funcionário autenticada antes de liberar as informações.

Além disso, o banco utiliza uma restrição de unicidade para impedir dois agendamentos na mesma data e horário.

```sql
UNIQUE(date, time)
```

Essa validação complementa a verificação realizada pela aplicação.

---

## Tratamento da API de feriados

A consulta de feriados é realizada no backend.

Caso a API de feriados esteja indisponível, o sistema não libera silenciosamente a data para agendamento. A operação é interrompida até que seja possível realizar a validação novamente.

Isso evita que uma consulta seja cadastrada em um feriado sem a verificação necessária.

---

## Fuso horário

As datas de criação dos agendamentos utilizam:

```text
America/Sao_Paulo
```

Dessa forma, o sistema trabalha explicitamente com o horário de Brasília.

---

## Possíveis melhorias futuras

Em uma evolução do projeto poderiam ser implementados:

- cadastro individual de funcionários;
- autenticação com senha criptografada;
- recuperação de senha;
- confirmação de consulta por e-mail ou WhatsApp;
- cadastro de médicos e especialidades;
- diferentes durações de consulta;
- painel com filtros por data;
- histórico de cancelamentos e reagendamentos;
- implantação do sistema em um servidor online.

---

## Desenvolvido por

**Nadia Kratky**

Projeto desenvolvido para demonstrar conhecimentos em desenvolvimento Full Stack, integração com API REST, regras de negócio, banco de dados e desenvolvimento de interfaces web.