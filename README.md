## 🛡️ Configuração de Segurança (Variáveis de Ambiente)

Por motivos de segurança, chaves de API e bancos de dados não são versionados neste repositório.

1. Na raiz do projeto, duplique o arquivo de exemplo:
   `cp .env.example .env`
2. Adicione suas chaves reais (ex: `GEMINI_API_KEY`) no arquivo `.env` gerado.
3. Repita o processo na pasta do frontend:
   `cp nexus-ui/.env.example nexus-ui/.env`
   
Seus dados locais (arquivos `.db` e diretórios de notas) já estão protegidos pelo `.gitignore`.