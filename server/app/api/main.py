"""
API FastAPI para o Discovery RAG Agent V2.

Este módulo implementa os endpoints da API para conectar o frontend React
ao pipeline RAG otimizado.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import time
import logging
import json
import os

# Importar componentes do RAG
from app.rag.dynamic_context_selector import DynamicContextSelector
from app.rag.specialized_prompts import SpecializedPromptManager, ResponseProcessor
from app.rag.hierarchical_indexer import EnhancedRetriever

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Discovery RAG Agent API",
    description="API para o agente de Discovery e Ideação de Produto usando RAG otimizado",
    version="2.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados
class QueryRequest(BaseModel):
    query: str
    objective: Optional[str] = "informative"

class QueryResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]

class FlowStatusResponse(BaseModel):
    status: str
    current_step: int
    nodes: Dict[str, str]
    connections: Dict[str, str]
    metrics: Dict[str, Any]
    current_node_details: Optional[Dict[str, Any]]

# Estado global para simulação de fluxo
flow_simulations = {}

# Dependências
async def get_retriever():
    # Em uma implementação real, isso seria conectado ao Weaviate
    # Por enquanto, retornamos um mock
    return {
        "retriever": "mock_retriever",
        "status": "connected"
    }

async def get_context_selector():
    # Em uma implementação real, isso seria uma instância do DynamicContextSelector
    # Por enquanto, retornamos um mock
    return {
        "selector": "mock_selector",
        "status": "ready"
    }

async def get_prompt_manager():
    # Em uma implementação real, isso seria uma instância do SpecializedPromptManager
    # Por enquanto, retornamos um mock
    return SpecializedPromptManager()

# Rotas da API
@app.get("/")
async def root():
    return {"status": "online", "message": "Discovery RAG Agent V2 API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "api": "online",
            "retriever": "online",
            "context_selector": "online",
            "prompt_manager": "online"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    retriever = Depends(get_retriever),
    context_selector = Depends(get_context_selector),
    prompt_manager = Depends(get_prompt_manager)
):
    """
    Processa uma consulta do usuário e retorna uma resposta gerada pelo RAG.
    
    - Classifica o objetivo da consulta
    - Recupera chunks relevantes
    - Seleciona contexto dinamicamente
    - Gera resposta com prompt especializado
    """
    try:
        # Iniciar simulação de fluxo em background
        simulation_id = f"query_{int(time.time())}"
        background_tasks.add_task(
            simulate_flow_processing,
            simulation_id=simulation_id,
            query=request.query,
            objective=request.objective
        )
        
        # Log da consulta
        logger.info(f"Processando consulta: {request.query} (objetivo: {request.objective})")
        
        # Simular processamento RAG
        # Em uma implementação real, isso chamaria os componentes reais
        await asyncio.sleep(2)  # Simular tempo de processamento
        
        # Gerar resposta simulada
        response_text = generate_mock_response(request.query, request.objective)
        
        # Gerar metadados simulados
        metadata = {
            "objective": request.objective,
            "processingTime": "2.3s",
            "tokensUsed": 1250,
            "sourcesCount": 3,
            "simulationId": simulation_id
        }
        
        return {
            "response": response_text,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar consulta: {str(e)}")

@app.get("/flow/{simulation_id}", response_model=FlowStatusResponse)
async def get_flow_status(simulation_id: str):
    """
    Retorna o status atual de uma simulação de fluxo de processamento.
    """
    if simulation_id not in flow_simulations:
        raise HTTPException(status_code=404, detail=f"Simulação {simulation_id} não encontrada")
    
    return flow_simulations[simulation_id]

@app.post("/flow/start")
async def start_flow_simulation(
    request: QueryRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia uma nova simulação de fluxo de processamento.
    """
    simulation_id = f"flow_{int(time.time())}"
    
    background_tasks.add_task(
        simulate_flow_processing,
        simulation_id=simulation_id,
        query=request.query,
        objective=request.objective
    )
    
    return {
        "status": "started",
        "simulationId": simulation_id,
        "message": "Simulação iniciada com sucesso"
    }

# Funções auxiliares
def generate_mock_response(query: str, objective: str) -> str:
    """
    Gera uma resposta simulada com base na consulta e objetivo.
    """
    responses = {
        "informative": f"""## Resumo
Identificamos vários perfis de usuários com base em seus hábitos de uso da plataforma.

## Detalhes
Nossa análise de comportamento identificou os seguintes perfis principais:

1. **Usuários Frequentes**: Acessam a plataforma diariamente, principalmente para transações rápidas e consultas de saldo. Representam cerca de 35% da base de usuários.

2. **Usuários de Crédito**: Focados principalmente em produtos de crédito e parcelamento. Tendem a usar a plataforma semanalmente e representam 25% da base.

3. **Usuários de Investimento**: Utilizam principalmente as funcionalidades de investimento, com sessões mais longas e detalhadas. Representam 15% da base.

4. **Usuários Ocasionais**: Acessam a plataforma mensalmente, geralmente para pagamentos específicos. Representam 25% da base.

## Fontes
- Relatório de Análise de Comportamento (Q1 2025)
- Pesquisa de Segmentação de Usuários (Março 2025)
- Dados de Analytics da Plataforma (Janeiro-Abril 2025)

## Lacunas de Informação
- Não temos dados detalhados sobre o comportamento em diferentes dispositivos
- Faltam informações sobre a jornada completa entre canais
- Não há análise de correlação entre perfis e NPS""",

        "hypothesis": f"""## Resumo da Hipótese
A hipótese de personalização da home com base nos perfis de usuário tem forte potencial para aumentar o engajamento.

## Pontos Fortes
- Alinhada com os dados de comportamento que mostram perfis distintos
- Consistente com a estratégia de personalização da experiência
- Potencial para aumentar conversão em produtos específicos
- Tecnicamente viável com a infraestrutura atual

## Considerações e Riscos
- Complexidade de implementação e manutenção
- Possível confusão para usuários que alternam entre perfis
- Necessidade de testes A/B extensivos
- Impacto na performance da aplicação

## Alinhamento com Diretrizes
A hipótese está bem alinhada com as diretrizes de produto, especialmente nos princípios de "Experiência Personalizada" e "Simplicidade com Profundidade".

## Recomendações
- Iniciar com personalização limitada a 2-3 elementos da home
- Implementar mecanismo de feedback explícito
- Desenvolver métricas claras de sucesso
- Considerar abordagem gradual com grupos de controle""",

        "benchmark": f"""## Resumo Comparativo
A análise de benchmark mostra que a personalização da home é uma tendência crescente no setor financeiro, com diferentes abordagens e níveis de sofisticação.

## Análise de Mercado
- **Nubank**: Implementou personalização baseada em uso recente e histórico de transações
- **Itaú**: Utiliza segmentação por perfil financeiro com ênfase em investimentos
- **Mercado Pago**: Personalização baseada em recência de uso de produtos
- **PicPay**: Abordagem de personalização por objetivos declarados

A maioria das instituições implementa personalização gradual, começando com 30-40% dos elementos da interface.

## Alinhamento com Boas Práticas
- Personalização baseada em comportamento é considerada mais efetiva que baseada apenas em dados demográficos
- Transparência sobre a personalização é uma prática recomendada
- Oferecer controle ao usuário sobre a personalização aumenta a satisfação
- Testes A/B são essenciais antes de implementação completa

## Oportunidades de Diferenciação
- Personalização baseada em contexto (hora do dia, localização)
- Integração com objetivos financeiros declarados
- Personalização da navegação além da home
- Abordagem híbrida combinando comportamento e preferências explícitas

## Recomendações
- Implementar personalização em fases, começando com elementos de maior impacto
- Desenvolver sistema de feedback explícito sobre a relevância do conteúdo
- Considerar abordagem híbrida de personalização
- Estabelecer métricas claras de sucesso para cada fase""",

        "objectives": f"""## Resumo de Alinhamento
A personalização da home baseada em perfis de usuário está fortemente alinhada aos objetivos estratégicos do time para 2025.

## Análise por Objetivo
**1. Aumentar Engajamento em 30%**
- A personalização tem potencial para aumentar a frequência de uso
- Conteúdo mais relevante tende a aumentar o tempo de sessão
- Alinhamento estimado: Alto (85%)

**2. Melhorar Conversão em Produtos Chave**
- Destacar produtos relevantes para cada perfil pode aumentar conversões
- Oportunidade de cross-selling contextual
- Alinhamento estimado: Médio-Alto (75%)

**3. Reduzir Fricção na Jornada do Usuário**
- Acesso mais rápido a funcionalidades frequentes
- Redução de cliques para ações comuns
- Alinhamento estimado: Alto (80%)

## Impacto Potencial em KPIs
- **DAU/MAU**: Potencial aumento de 15-20%
- **Tempo de Sessão**: Potencial aumento de 25-30%
- **Taxa de Conversão**: Potencial aumento de 10-15% em produtos destacados
- **NPS**: Potencial aumento de 5-8 pontos

## Oportunidades de Fortalecimento
- Integrar objetivos explícitos do usuário na personalização
- Desenvolver métricas específicas para cada perfil
- Criar dashboard de acompanhamento de performance por segmento

## Recomendações
- Priorizar implementação para Q3 2025
- Estabelecer grupo de controle para medição precisa de impacto
- Desenvolver plano de comunicação sobre os benefícios da personalização
- Criar framework de decisão para resolução de conflitos entre objetivos"""
    }
    
    # Fallback para objetivo informativo se não encontrar correspondência
    return responses.get(objective, responses["informative"])

async def simulate_flow_processing(simulation_id: str, query: str, objective: str):
    """
    Simula o processamento de fluxo do RAG em tempo real.
    """
    # Inicializar estado da simulação
    flow_simulations[simulation_id] = {
        "status": "running",
        "current_step": 0,
        "nodes": {
            "query": "waiting",
            "classification": "waiting",
            "retrieval": "waiting",
            "reranking": "waiting",
            "context": "waiting",
            "prompt": "waiting",
            "generation": "waiting",
            "response": "waiting"
        },
        "connections": {
            "query_classification": "waiting",
            "classification_retrieval": "waiting",
            "retrieval_reranking": "waiting",
            "reranking_context": "waiting",
            "context_prompt": "waiting",
            "prompt_generation": "waiting",
            "generation_response": "waiting"
        },
        "metrics": {
            "processingTime": 0,
            "documentsRetrieved": 0,
            "chunksProcessed": 0,
            "tokensUsed": 0
        },
        "current_node_details": None
    }
    
    # Simular etapas do processamento
    steps = [
        # Etapa 1: Consulta
        {
            "delay": 1,
            "updates": {
                "current_step": 1,
                "nodes": {"query": "active"},
                "metrics": {"processingTime": 0.2},
                "current_node_details": {
                    "title": "Consulta do Usuário",
                    "description": f"Analisando a consulta: \"{query}\"",
                    "type": "input"
                }
            }
        },
        # Etapa 2: Conexão Consulta -> Classificação
        {
            "delay": 0.5,
            "updates": {
                "current_step": 2,
                "nodes": {"query": "completed"},
                "connections": {"query_classification": "active"},
                "metrics": {"processingTime": 0.5}
            }
        },
        # Etapa 3: Classificação
        {
            "delay": 1,
            "updates": {
                "current_step": 3,
                "connections": {"query_classification": "completed"},
                "nodes": {"classification": "active"},
                "metrics": {"processingTime": 0.8},
                "current_node_details": {
                    "title": "Classificação de Objetivo",
                    "description": f"Classificando a consulta como: \"{objective}\"",
                    "type": "process"
                }
            }
        },
        # Etapa 4: Conexão Classificação -> Recuperação
        {
            "delay": 0.5,
            "updates": {
                "current_step": 4,
                "nodes": {"classification": "completed"},
                "connections": {"classification_retrieval": "active"},
                "metrics": {"processingTime": 1.0}
            }
        },
        # Etapa 5: Recuperação
        {
            "delay": 1.5,
            "updates": {
                "current_step": 5,
                "connections": {"classification_retrieval": "completed"},
                "nodes": {"retrieval": "active"},
                "metrics": {
                    "processingTime": 1.5,
                    "documentsRetrieved": 3,
                    "chunksProcessed": 12
                },
                "current_node_details": {
                    "title": "Recuperação de Documentos",
                    "description": "Buscando chunks relevantes na base vetorial usando similaridade semântica",
                    "type": "storage"
                }
            }
        },
        # Etapa 6: Conexão Recuperação -> Reranking
        {
            "delay": 0.5,
            "updates": {
                "current_step": 6,
                "nodes": {"retrieval": "completed"},
                "connections": {"retrieval_reranking": "active"},
                "metrics": {"processingTime": 1.8}
            }
        },
        # Etapa 7: Reranking
        {
            "delay": 1,
            "updates": {
                "current_step": 7,
                "connections": {"retrieval_reranking": "completed"},
                "nodes": {"reranking": "active"},
                "metrics": {"processingTime": 2.3},
                "current_node_details": {
                    "title": "Reranking de Resultados",
                    "description": "Reordenando os 20 chunks iniciais para selecionar os 7 mais relevantes",
                    "type": "process"
                }
            }
        },
        # Etapa 8: Conexão Reranking -> Contexto
        {
            "delay": 0.5,
            "updates": {
                "current_step": 8,
                "nodes": {"reranking": "completed"},
                "connections": {"reranking_context": "active"},
                "metrics": {"processingTime": 2.5}
            }
        },
        # Etapa 9: Contexto
        {
            "delay": 1,
            "updates": {
                "current_step": 9,
                "connections": {"reranking_context": "completed"},
                "nodes": {"context": "active"},
                "metrics": {"processingTime": 3.0},
                "current_node_details": {
                    "title": "Seleção de Contexto",
                    "description": "Comprimindo e priorizando informações para o contexto final",
                    "type": "process"
                }
            }
        },
        # Etapa 10: Conexão Contexto -> Prompt
        {
            "delay": 0.5,
            "updates": {
                "current_step": 10,
                "nodes": {"context": "completed"},
                "connections": {"context_prompt": "active"},
                "metrics": {"processingTime": 3.2}
            }
        },
        # Etapa 11: Prompt
        {
            "delay": 1,
            "updates": {
                "current_step": 11,
                "connections": {"context_prompt": "completed"},
                "nodes": {"prompt": "active"},
                "metrics": {"processingTime": 3.5},
                "current_node_details": {
                    "title": "Construção do Prompt",
                    "description": f"Criando prompt especializado para consulta {objective} com contexto selecionado",
                    "type": "process"
                }
            }
        },
        # Etapa 12: Conexão Prompt -> Geração
        {
            "delay": 0.5,
            "updates": {
                "current_step": 12,
                "nodes": {"prompt": "completed"},
                "connections": {"prompt_generation": "active"},
                "metrics": {"processingTime": 3.7}
            }
        },
        # Etapa 13: Geração
        {
            "delay": 2,
            "updates": {
                "current_step": 13,
                "connections": {"prompt_generation": "completed"},
                "nodes": {"generation": "active"},
                "metrics": {
                    "processingTime": 4.5,
                    "tokensUsed": 1250
                },
                "current_node_details": {
                    "title": "Geração de Resposta",
                    "description": "Gerando resposta estruturada com base no prompt e contexto",
                    "type": "api"
                }
            }
        },
        # Etapa 14: Conexão Geração -> Resposta
        {
            "delay": 0.5,
            "updates": {
                "current_step": 14,
                "nodes": {"generation": "completed"},
                "connections": {"generation_response": "active"},
                "metrics": {"processingTime": 4.7}
            }
        },
        # Etapa 15: Resposta
        {
            "delay": 1,
            "updates": {
                "current_step": 15,
                "connections": {"generation_response": "completed"},
                "nodes": {"response": "active"},
                "metrics": {"processingTime": 5.0},
                "current_node_details": {
                    "title": "Formatação da Resposta",
                    "description": "Processando e formatando a resposta final para o usuário",
                    "type": "output"
                }
            }
        },
        # Etapa 16: Finalização
        {
            "delay": 1,
            "updates": {
                "current_step": 16,
                "nodes": {"response": "completed"},
                "status": "completed",
                "current_node_details": {
                    "title": "Processo Concluído",
                    "description": "Todos os passos foram executados com sucesso",
                    "type": "output"
                }
            }
        }
    ]
    
    # Executar simulação
    for step in steps:
        await asyncio.sleep(step["delay"])
        
        # Atualizar estado da simulação
        for key, value in step["updates"].items():
            if isinstance(value, dict):
                # Atualizar dicionário existente
                if key in flow_simulations[simulation_id]:
                    flow_simulations[simulation_id][key].update(value)
                else:
                    flow_simulations[simulation_id][key] = value
            else:
                # Substituir valor
                flow_simulations[simulation_id][key] = value
    
    # Manter simulação disponível por 10 minutos
    await asyncio.sleep(600)
    
    # Remover simulação
    if simulation_id in flow_simulations:
        del flow_simulations[simulation_id]
