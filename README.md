# 📘 DOCUMENTAÇÃO COMPLETA --- Treino em Foco

## 📌 Visão Geral

O Treino em Foco é uma aplicação web para gerenciamento de treinos,
desenvolvida com Streamlit + Supabase, com foco em uso rápido no
celular.

## 🎯 Objetivo

-   Criar treinos personalizados
-   Adicionar exercícios
-   Marcar como concluídos
-   Registrar histórico
-   Usar timer de descanso

## 🧱 Tecnologias

-   Python
-   Streamlit
-   Supabase

## 📁 Estrutura do Projeto

treino-em-foco/ ├── app.py ├── requirements.txt └── README.md

## 📄 Arquivos

### app.py

Contém toda lógica, interface e integração com banco.

### requirements.txt

Dependências: streamlit supabase

### README.md

Documentação do projeto.

## 🗄️ Banco de Dados

### workouts

-   id
-   user_id
-   nome

### exercises

-   id
-   workout_id
-   nome
-   done

### workout_history

-   id
-   user_id
-   workout_id
-   nome
-   data

## 🔐 Autenticação

-   Supabase Auth
-   Sessão via session_state

## 🔒 Segurança

Policy: auth.uid() = user_id

## ⚙️ Estado

-   user
-   session
-   treino_selecionado
-   descanso_ate

## 🔄 Fluxo

Login → Treinos → Exercícios → Finalizar → Histórico

## ⚙️ Funcionalidades

-   Login
-   Criar treino
-   Editar treino
-   Timer
-   Histórico

## ⚠️ Problemas resolvidos

-   Login duplicado
-   Checkbox bug
-   Rerun erro

## 📱 Mobile

-   Funciona no navegador
-   Pode virar PWA

## 🚀 Deploy

requirements.txt: streamlit supabase

secrets.toml: SUPABASE_URL = "..." SUPABASE_KEY = "..."

## 🔮 Roadmap

-   Melhor UI
-   Persistir login
-   PWA

## 💡 Filosofia

-   Simples
-   Rápido
-   Mobile first

## 🏁 Status

MVP funcional pronto para evolução
