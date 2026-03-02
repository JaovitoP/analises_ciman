<p align="center">
  | <a href ="#objetivo"> Objetivo do Projeto </a>
  | <a href ="#tecnologias"> Tecnologias </a>
  | <a href ="#comofunciona"> Como Funciona? </a>
  | <a href ="#comorodar"> Como Rodar </a>  |
</p>

<span id="objetivo">

## 📌Objetivo do Projeto

> [!IMPORTANT]
> Este projeto Streamlit tem como objetivo analisar e comparar dados de focos de incêndio no Brasil em diferentes anos e em diferentes biomas, estados e regiões.


<span id="tecnologias"> 
 
## 🔌**Tecnologias**
> [!NOTE]
> Tecnologias utilizadas no desenvolvimento:

<h4 align="left">
    <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt='TypeScript'></a>
    <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/Streamlit-%23FE4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white" alt='TypeScript'></a>
    <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white" alt='TypeScript'></a>
    <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black" alt='TypeScript'></a>
    <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white" alt='TypeScript'></a>

</h4>
<br>

<span id="comofunciona">
  
## ❓**Como Funciona?**
<img width="1915" height="352" alt="Screenshot from 2026-03-02 09-32-11" src="https://github.com/user-attachments/assets/9f88a70d-54d5-49fe-bf30-1da10f05c958" />

A aplicação conta com uma interface simples e intuitiva na qual é possível filtrar os dados por um também filtrar por um ano específico, ou por intervalo de tempo: ano de início e ano de fim. No caso da imagem a seguir, ao clicar no botão 'Gerar Relatório' são gerados gráficos de barras para cada bioma, no intervalo de tempo selecionado. O mesmo fluxo é utilizado nas páginas Brasil, Estados e Regiões.

<img width="1915" height="988" alt="Screenshot from 2026-03-02 09-36-18" src="https://github.com/user-attachments/assets/86cf0bac-cb97-4c51-a0e6-a0eeb829a5b2" />

<img width="1915" height="295" alt="Screenshot from 2026-03-02 09-37-28" src="https://github.com/user-attachments/assets/62721174-a7b0-4d05-b8eb-d68c2779e0ac" />

A aplicação também é responsiva,de modo que é possível acessar por diferentes dispositivos.

<img width="397" height="865" alt="Screenshot from 2026-03-02 09-41-20" src="https://github.com/user-attachments/assets/98f7fec1-d077-4b0a-89c8-03c1f01a05f6" />

<img width="397" height="865" alt="Screenshot from 2026-03-02 09-43-05" src="https://github.com/user-attachments/assets/f977c5ff-41ab-4cdd-9ae6-0e05295a4dc6" />



<span id="comorodar">

## 🚀 **Executando o projeto**

#### **1. Clone o repositório**

```bash
git clone https://github.com/JaovitoP/analises_ciman.git 
cd app
```

#### **2. Setup**

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente no linux
source .venv/bin/activate

# Ativar ambiente no Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

streamlit run streamlit_app.py # A aplicação abrirá no endereço http://localhost:8501
```
