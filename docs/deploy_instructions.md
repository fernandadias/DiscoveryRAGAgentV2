# Instruções de Deploy - Discovery RAG Agent V2

Este documento contém instruções detalhadas para deploy do Discovery RAG Agent V2, incluindo tanto o frontend React quanto o backend FastAPI.

## Pré-requisitos

- Conta no [Vercel](https://vercel.com/) para o frontend
- Conta no [Render](https://render.com/) para o backend
- Chave de API da OpenAI
- Instância do Weaviate (Cloud ou self-hosted)

## Deploy do Backend (FastAPI)

### Opção 1: Deploy no Render

1. Faça login na sua conta do Render
2. Clique em "New" e selecione "Blueprint"
3. Conecte seu repositório GitHub
4. Selecione o repositório `DiscoveryRAGAgentV2`
5. O Render detectará automaticamente o arquivo `render.yaml` e configurará o serviço
6. Configure as seguintes variáveis de ambiente:
   - `OPENAI_API_KEY`: Sua chave de API da OpenAI
   - `WEAVIATE_URL`: URL da sua instância Weaviate
   - `WEAVIATE_API_KEY`: Chave de API do Weaviate (se aplicável)
7. Clique em "Apply" para iniciar o deploy
8. Aguarde a conclusão do deploy (pode levar alguns minutos)
9. Anote o URL do serviço (geralmente `https://discovery-rag-agent-v2-api.onrender.com`)

### Opção 2: Deploy Manual

Se preferir fazer o deploy manualmente em outro provedor:

1. Navegue até a pasta do servidor:
   ```bash
   cd DiscoveryRAGAgentV2/server
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   ```bash
   export OPENAI_API_KEY=sua_chave_aqui
   export WEAVIATE_URL=sua_url_aqui
   export WEAVIATE_API_KEY=sua_chave_aqui
   ```

4. Inicie o servidor:
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000
   ```

## Deploy do Frontend (React)

### Opção 1: Deploy no Vercel

1. Faça login na sua conta do Vercel
2. Clique em "New Project"
3. Importe seu repositório GitHub
4. Selecione o repositório `DiscoveryRAGAgentV2`
5. Configure as seguintes opções:
   - Framework Preset: Create React App
   - Root Directory: `client`
   - Build Command: `npm run build`
   - Output Directory: `build`
6. Configure a variável de ambiente:
   - `REACT_APP_API_URL`: URL do seu backend (ex: `https://discovery-rag-agent-v2-api.onrender.com`)
7. Clique em "Deploy" para iniciar o deploy
8. Aguarde a conclusão do deploy (geralmente leva menos de 1 minuto)
9. Anote o URL do projeto (geralmente `https://discovery-rag-agent-v2.vercel.app`)

### Opção 2: Build Local e Deploy Manual

Se preferir fazer o build localmente e depois fazer o deploy:

1. Navegue até a pasta do cliente:
   ```bash
   cd DiscoveryRAGAgentV2/client
   ```

2. Instale as dependências:
   ```bash
   npm install
   ```

3. Configure a variável de ambiente:
   ```bash
   echo "REACT_APP_API_URL=https://seu-backend-url.com" > .env
   ```

4. Faça o build:
   ```bash
   npm run build
   ```

5. O diretório `build` conterá os arquivos estáticos que podem ser hospedados em qualquer serviço de hospedagem estática (Netlify, GitHub Pages, etc.)

## Verificação do Deploy

Após concluir o deploy de ambos os componentes:

1. Acesse o URL do frontend (ex: `https://discovery-rag-agent-v2.vercel.app`)
2. Navegue até a página de consulta
3. Faça uma consulta de teste para verificar se a comunicação com o backend está funcionando
4. Verifique se a visualização do fluxo está funcionando corretamente

## Solução de Problemas

### Problemas no Backend

- Verifique os logs no dashboard do Render
- Confirme se todas as variáveis de ambiente estão configuradas corretamente
- Teste o endpoint `/health` para verificar o status da API

### Problemas no Frontend

- Verifique os logs de build no dashboard do Vercel
- Abra o console do navegador para verificar erros de JavaScript
- Confirme se a variável `REACT_APP_API_URL` está apontando para o URL correto do backend

## Atualizações

Para atualizar a aplicação após fazer alterações no código:

1. Faça commit das alterações e push para o repositório GitHub
2. O Vercel e o Render detectarão automaticamente as alterações e iniciarão um novo deploy
3. Aguarde a conclusão dos deploys para ver as alterações em produção
