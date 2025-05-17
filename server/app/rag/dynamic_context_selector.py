"""
Módulo de seleção dinâmica de contexto para o Discovery RAG Agent V2.

Este módulo implementa técnicas avançadas para selecionar, filtrar e comprimir
o contexto mais relevante para cada consulta, maximizando a qualidade das respostas.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI


class DynamicContextSelector:
    """
    Implementa seleção dinâmica de contexto baseada no objetivo da consulta.
    
    Características:
    - Classificação automática do objetivo da consulta
    - Seleção de fontes relevantes para cada objetivo
    - Filtragem de conteúdo por relevância
    - Compressão inteligente para maximizar informação útil
    - Balanceamento de tokens entre diferentes fontes
    """
    
    def __init__(
        self,
        openai_client: Optional[AsyncOpenAI] = None,
        guidelines_repository = None,
        max_total_tokens: int = 6000
    ):
        """
        Inicializa o seletor dinâmico de contexto.
        
        Args:
            openai_client: Cliente OpenAI para classificação e compressão
            guidelines_repository: Repositório de diretrizes
            max_total_tokens: Limite máximo de tokens para o contexto
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.guidelines_repo = guidelines_repository
        self.max_total_tokens = max_total_tokens
        self.tokenizer = None  # Será inicializado sob demanda
        
    async def select_context(
        self, 
        query: str, 
        retrieved_chunks: List[Dict[str, Any]], 
        objective: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Seleciona o contexto mais relevante para uma consulta.
        
        Args:
            query: Consulta do usuário
            retrieved_chunks: Chunks recuperados pelo sistema RAG
            objective: Objetivo explícito (opcional)
            
        Returns:
            Contexto otimizado para a consulta
        """
        # 1. Classificar a intenção da consulta se não houver objetivo explícito
        if not objective:
            objective = await self._classify_intent(query)
        
        # 2. Selecionar fontes relevantes com base no objetivo
        relevant_sources = self._select_relevant_sources(objective)
        
        # 3. Recuperar diretrizes relevantes para a consulta
        product_guidelines = await self._get_relevant_guidelines(
            query, "product", relevant_sources.get("product_guidelines", False)
        )
        
        design_guidelines = await self._get_relevant_guidelines(
            query, "design", relevant_sources.get("design_guidelines", False)
        )
        
        benchmarks = await self._get_relevant_guidelines(
            query, "benchmark", relevant_sources.get("benchmarks", False)
        )
        
        team_objectives = await self._get_relevant_guidelines(
            query, "objectives", relevant_sources.get("team_objectives", False)
        )
        
        # 4. Filtrar chunks por relevância
        filtered_chunks = await self._filter_relevant_chunks(query, retrieved_chunks)
        
        # 5. Comprimir contexto para maximizar informação relevante
        compressed_context = await self._compress_context(
            query,
            filtered_chunks,
            product_guidelines,
            design_guidelines,
            benchmarks,
            team_objectives,
            objective
        )
        
        return {
            "objective": objective,
            "compressed_chunks": compressed_context["chunks"],
            "compressed_product_guidelines": compressed_context["product_guidelines"],
            "compressed_design_guidelines": compressed_context["design_guidelines"],
            "compressed_benchmarks": compressed_context["benchmarks"],
            "compressed_team_objectives": compressed_context["team_objectives"],
            "total_tokens": compressed_context["total_tokens"]
        }
    
    async def _classify_intent(self, query: str) -> str:
        """
        Classifica a intenção da consulta usando LLM.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Objetivo classificado
        """
        # Preparar prompt para o LLM
        prompt = f"""
        Classifique a intenção da seguinte consulta em uma das categorias:
        - informative: Busca informações factuais sobre o que já sabemos
        - hypothesis: Avaliação de uma hipótese ou ideia
        - benchmark: Comparação com boas práticas ou concorrentes
        - objectives: Alinhamento com objetivos do time
        
        Responda apenas com o nome da categoria, sem explicações.
        
        Consulta: {query}
        """
        
        # Obter resposta do LLM
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Extrair e validar a intenção
        intent = response.choices[0].message.content.strip().lower()
        
        # Validar se a resposta é uma das categorias válidas
        valid_intents = ["informative", "hypothesis", "benchmark", "objectives"]
        if intent not in valid_intents:
            intent = "informative"  # Fallback para informativo
            
        return intent
    
    def _select_relevant_sources(self, objective: str) -> Dict[str, bool]:
        """
        Determina quais fontes são relevantes com base no objetivo.
        
        Args:
            objective: Objetivo da consulta
            
        Returns:
            Dicionário indicando quais fontes devem ser incluídas
        """
        # Matriz de seleção de fontes por objetivo
        selection_matrix = {
            "informative": {
                "chunks": True,
                "product_guidelines": True,
                "design_guidelines": False,
                "benchmarks": False,
                "team_objectives": False
            },
            "hypothesis": {
                "chunks": True,
                "product_guidelines": True,
                "design_guidelines": True,
                "benchmarks": True,
                "team_objectives": False
            },
            "benchmark": {
                "chunks": True,
                "product_guidelines": True,
                "design_guidelines": True,
                "benchmarks": True,
                "team_objectives": False
            },
            "objectives": {
                "chunks": True,
                "product_guidelines": True,
                "design_guidelines": False,
                "benchmarks": False,
                "team_objectives": True
            }
        }
        
        return selection_matrix.get(objective, selection_matrix["informative"])
    
    async def _get_relevant_guidelines(
        self, 
        query: str, 
        guideline_type: str, 
        include: bool = True
    ) -> List[str]:
        """
        Recupera diretrizes relevantes do repositório.
        
        Args:
            query: Consulta do usuário
            guideline_type: Tipo de diretriz
            include: Se deve incluir este tipo de diretriz
            
        Returns:
            Lista de diretrizes relevantes
        """
        if not include or not self.guidelines_repo:
            return []
            
        # Recuperar diretrizes do repositório
        guidelines = await self.guidelines_repo.get_guidelines(guideline_type)
        
        # Filtrar apenas as seções relevantes para a consulta
        relevant_sections = await self._filter_relevant_sections(query, guidelines)
        
        return relevant_sections
    
    async def _filter_relevant_sections(
        self, 
        query: str, 
        sections: List[str]
    ) -> List[str]:
        """
        Filtra seções relevantes para a consulta.
        
        Args:
            query: Consulta do usuário
            sections: Lista de seções a filtrar
            
        Returns:
            Lista de seções relevantes
        """
        if not sections:
            return []
            
        # Preparar prompt para o LLM
        sections_text = "\n\n".join([f"Seção {i+1}: {section[:300]}..." for i, section in enumerate(sections)])
        
        prompt = f"""
        Identifique as seções mais relevantes para a seguinte consulta:
        
        Consulta: {query}
        
        Seções disponíveis:
        {sections_text}
        
        Liste apenas os números das seções relevantes, separados por vírgula.
        Se nenhuma seção for relevante, responda "0".
        """
        
        # Obter resposta do LLM
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Extrair números das seções relevantes
        sections_str = response.choices[0].message.content.strip()
        relevant_indices = []
        
        try:
            if sections_str != "0":
                for part in sections_str.split(","):
                    idx = int(part.strip()) - 1  # Converter para índice base-0
                    if 0 <= idx < len(sections):
                        relevant_indices.append(idx)
        except ValueError:
            # Fallback para todas as seções se houver erro de parsing
            relevant_indices = list(range(len(sections)))
            
        # Retornar apenas as seções relevantes
        return [sections[i] for i in relevant_indices]
    
    async def _filter_relevant_chunks(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filtra chunks por relevância para a consulta.
        
        Args:
            query: Consulta do usuário
            chunks: Lista de chunks a filtrar
            
        Returns:
            Lista de chunks relevantes
        """
        # Se já temos poucos chunks, não filtrar
        if len(chunks) <= 5:
            return chunks
            
        # Preparar prompt para o LLM
        chunks_text = "\n\n".join([f"Chunk {i+1}: {chunk['text'][:300]}..." for i, chunk in enumerate(chunks)])
        
        prompt = f"""
        Identifique os chunks mais relevantes para a seguinte consulta:
        
        Consulta: {query}
        
        Chunks disponíveis:
        {chunks_text}
        
        Liste apenas os números dos chunks relevantes, separados por vírgula.
        Se nenhum chunk for relevante, responda "0".
        """
        
        # Obter resposta do LLM
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Extrair números dos chunks relevantes
        chunks_str = response.choices[0].message.content.strip()
        relevant_indices = []
        
        try:
            if chunks_str != "0":
                for part in chunks_str.split(","):
                    idx = int(part.strip()) - 1  # Converter para índice base-0
                    if 0 <= idx < len(chunks):
                        relevant_indices.append(idx)
        except ValueError:
            # Fallback para todos os chunks se houver erro de parsing
            relevant_indices = list(range(len(chunks)))
            
        # Retornar apenas os chunks relevantes
        return [chunks[i] for i in relevant_indices]
    
    async def _compress_context(
        self, 
        query: str,
        chunks: List[Dict[str, Any]],
        product_guidelines: List[str],
        design_guidelines: List[str],
        benchmarks: List[str],
        team_objectives: List[str],
        objective: str
    ) -> Dict[str, Any]:
        """
        Comprime contexto para maximizar informação relevante.
        
        Args:
            query: Consulta do usuário
            chunks: Chunks relevantes
            product_guidelines: Diretrizes de produto
            design_guidelines: Diretrizes de design
            benchmarks: Benchmarks
            team_objectives: Objetivos do time
            objective: Objetivo da consulta
            
        Returns:
            Contexto comprimido
        """
        # Definir prioridades e limites de tokens para cada componente
        priorities = self._get_priorities_by_objective(objective)
        
        # Concatenar textos por componente
        chunks_text = "\n\n".join([chunk["text"] for chunk in chunks]) if chunks else ""
        product_text = "\n\n".join(product_guidelines) if product_guidelines else ""
        design_text = "\n\n".join(design_guidelines) if design_guidelines else ""
        benchmarks_text = "\n\n".join(benchmarks) if benchmarks else ""
        objectives_text = "\n\n".join(team_objectives) if team_objectives else ""
        
        # Calcular tokens iniciais
        initial_tokens = {
            "chunks": self._count_tokens(chunks_text),
            "product_guidelines": self._count_tokens(product_text),
            "design_guidelines": self._count_tokens(design_text),
            "benchmarks": self._count_tokens(benchmarks_text),
            "team_objectives": self._count_tokens(objectives_text)
        }
        
        # Calcular total de tokens
        total_initial_tokens = sum(initial_tokens.values())
        
        # Se estiver dentro do limite, não comprimir
        if total_initial_tokens <= self.max_total_tokens:
            return {
                "chunks": chunks_text,
                "product_guidelines": product_text,
                "design_guidelines": design_text,
                "benchmarks": benchmarks_text,
                "team_objectives": objectives_text,
                "total_tokens": total_initial_tokens
            }
        
        # Alocar tokens com base nas prioridades
        token_allocation = self._allocate_tokens(
            self.max_total_tokens,
            priorities,
            initial_tokens
        )
        
        # Comprimir cada componente para o limite alocado
        compressed = {}
        
        # Comprimir chunks
        if chunks_text and token_allocation["chunks"] > 0:
            compressed["chunks"] = await self._compress_component(
                query, 
                chunks_text, 
                "chunks recuperados", 
                token_allocation["chunks"]
            )
        else:
            compressed["chunks"] = ""
        
        # Comprimir diretrizes de produto
        if product_text and token_allocation["product_guidelines"] > 0:
            compressed["product_guidelines"] = await self._compress_component(
                query, 
                product_text, 
                "diretrizes de produto", 
                token_allocation["product_guidelines"]
            )
        else:
            compressed["product_guidelines"] = ""
        
        # Comprimir diretrizes de design
        if design_text and token_allocation["design_guidelines"] > 0:
            compressed["design_guidelines"] = await self._compress_component(
                query, 
                design_text, 
                "diretrizes de design", 
                token_allocation["design_guidelines"]
            )
        else:
            compressed["design_guidelines"] = ""
        
        # Comprimir benchmarks
        if benchmarks_text and token_allocation["benchmarks"] > 0:
            compressed["benchmarks"] = await self._compress_component(
                query, 
                benchmarks_text, 
                "benchmarks", 
                token_allocation["benchmarks"]
            )
        else:
            compressed["benchmarks"] = ""
        
        # Comprimir objetivos do time
        if objectives_text and token_allocation["team_objectives"] > 0:
            compressed["team_objectives"] = await self._compress_component(
                query, 
                objectives_text, 
                "objetivos do time", 
                token_allocation["team_objectives"]
            )
        else:
            compressed["team_objectives"] = ""
        
        # Calcular tokens finais
        total_tokens = sum([
            self._count_tokens(compressed["chunks"]),
            self._count_tokens(compressed["product_guidelines"]),
            self._count_tokens(compressed["design_guidelines"]),
            self._count_tokens(compressed["benchmarks"]),
            self._count_tokens(compressed["team_objectives"])
        ])
        
        compressed["total_tokens"] = total_tokens
        
        return compressed
    
    def _get_priorities_by_objective(self, objective: str) -> Dict[str, float]:
        """
        Define prioridades para cada componente com base no objetivo.
        
        Args:
            objective: Objetivo da consulta
            
        Returns:
            Dicionário de prioridades
        """
        # Matriz de prioridades por objetivo
        priority_matrix = {
            "informative": {
                "chunks": 0.85,
                "product_guidelines": 0.15,
                "design_guidelines": 0.0,
                "benchmarks": 0.0,
                "team_objectives": 0.0
            },
            "hypothesis": {
                "chunks": 0.5,
                "product_guidelines": 0.25,
                "design_guidelines": 0.25,
                "benchmarks": 0.0,
                "team_objectives": 0.0
            },
            "benchmark": {
                "chunks": 0.5,
                "product_guidelines": 0.15,
                "design_guidelines": 0.25,
                "benchmarks": 0.1,
                "team_objectives": 0.0
            },
            "objectives": {
                "chunks": 0.5,
                "product_guidelines": 0.25,
                "design_guidelines": 0.0,
                "benchmarks": 0.0,
                "team_objectives": 0.25
            }
        }
        
        return priority_matrix.get(objective, priority_matrix["informative"])
    
    def _allocate_tokens(
        self, 
        available_tokens: int, 
        priorities: Dict[str, float],
        initial_tokens: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Aloca tokens disponíveis entre as fontes com base em suas prioridades.
        
        Args:
            available_tokens: Número total de tokens disponíveis
            priorities: Dicionário de prioridades por fonte
            initial_tokens: Tokens iniciais por fonte
            
        Returns:
            Dicionário com a alocação de tokens por fonte
        """
        # Filtrar apenas fontes com conteúdo
        active_priorities = {k: v for k, v in priorities.items() if initial_tokens[k] > 0}
        
        # Se não houver fontes ativas, retornar zeros
        if not active_priorities:
            return {k: 0 for k in priorities}
        
        # Normalizar prioridades
        total_priority = sum(active_priorities.values())
        normalized_priorities = {k: v / total_priority for k, v in active_priorities.items()}
        
        # Alocar tokens proporcionalmente às prioridades
        allocation = {}
        for source in priorities:
            if source in normalized_priorities:
                allocation[source] = int(normalized_priorities[source] * available_tokens)
            else:
                allocation[source] = 0
        
        # Ajustar para garantir que o total seja exatamente igual aos tokens disponíveis
        adjustment = available_tokens - sum(allocation.values())
        if adjustment != 0 and active_priorities:
            # Adicionar ou remover tokens da fonte com maior prioridade
            max_priority_source = max(active_priorities, key=active_priorities.get)
            allocation[max_priority_source] += adjustment
        
        # Garantir que nenhuma alocação exceda os tokens iniciais
        for source, tokens in allocation.items():
            if tokens > initial_tokens[source]:
                # Redistribuir o excesso
                excess = tokens - initial_tokens[source]
                allocation[source] = initial_tokens[source]
                
                # Encontrar outras fontes que podem receber o excesso
                candidates = {k: v for k, v in active_priorities.items() 
                             if k != source and allocation[k] < initial_tokens[k]}
                
                if candidates:
                    # Normalizar prioridades dos candidatos
                    total_candidate_priority = sum(candidates.values())
                    for candidate, priority in candidates.items():
                        # Distribuir proporcionalmente
                        share = int((priority / total_candidate_priority) * excess)
                        allocation[candidate] += share
                        excess -= share
                    
                    # Adicionar qualquer resto à fonte com maior prioridade
                    if excess > 0 and candidates:
                        max_candidate = max(candidates, key=candidates.get)
                        allocation[max_candidate] += excess
        
        return allocation
    
    async def _compress_component(
        self, 
        query: str, 
        text: str, 
        component_name: str, 
        max_tokens: int
    ) -> str:
        """
        Comprime um componente de contexto para o limite de tokens.
        
        Args:
            query: Consulta do usuário
            text: Texto a comprimir
            component_name: Nome do componente
            max_tokens: Limite de tokens
            
        Returns:
            Texto comprimido
        """
        # Se já estiver dentro do limite, retornar como está
        if self._count_tokens(text) <= max_tokens:
            return text
            
        # Preparar prompt para o LLM
        prompt = f"""
        Comprima as seguintes informações ({component_name}) para fornecer o contexto mais relevante 
        para responder à consulta: "{query}"
        
        Mantenha apenas as informações essenciais, preservando detalhes importantes e removendo redundâncias.
        A resposta deve ser concisa mas completa, contendo todas as informações relevantes para a consulta.
        
        {component_name.capitalize()}:
        {text}
        """
        
        # Obter resposta do LLM
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0
        )
        
        compressed = response.choices[0].message.content.strip()
        
        return compressed
    
    def _count_tokens(self, text: str) -> int:
        """
        Conta o número de tokens em um texto.
        
        Args:
            text: Texto para contar tokens
            
        Returns:
            Número de tokens
        """
        # Implementação simplificada
        # Em produção, usar tiktoken para contagem precisa
        if not text:
            return 0
            
        # Estimativa aproximada: 4 caracteres por token
        return len(text) // 4
