"""
Módulo de prompts especializados por objetivo para o Discovery RAG Agent V2.

Este módulo implementa templates de prompts otimizados para diferentes objetivos
de consulta, maximizando a relevância e qualidade das respostas.
"""

from typing import List, Dict, Any, Optional
import json


class SpecializedPromptManager:
    """
    Gerencia prompts especializados por objetivo de consulta.
    
    Características:
    - Templates específicos para cada objetivo
    - Estruturação dinâmica do contexto
    - Formatação personalizada das respostas
    - Instruções específicas por tipo de consulta
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de prompts especializados.
        """
        # Carregar templates de prompts
        self.prompt_templates = {
            "informative": self._get_informative_template(),
            "hypothesis": self._get_hypothesis_template(),
            "benchmark": self._get_benchmark_template(),
            "objectives": self._get_objectives_template()
        }
        
        # Carregar templates de formatação de resposta
        self.response_formats = {
            "informative": self._get_informative_format(),
            "hypothesis": self._get_hypothesis_format(),
            "benchmark": self._get_benchmark_format(),
            "objectives": self._get_objectives_format()
        }
    
    def create_prompt(
        self, 
        query: str, 
        context: Dict[str, Any], 
        objective: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um prompt especializado para a consulta.
        
        Args:
            query: Consulta do usuário
            context: Contexto selecionado
            objective: Objetivo da consulta (opcional)
            
        Returns:
            Prompt completo com mensagens formatadas
        """
        # Determinar objetivo se não for fornecido
        if not objective:
            objective = "informative"  # Fallback para informativo
        
        # Garantir que o objetivo é válido
        if objective not in self.prompt_templates:
            objective = "informative"
        
        # Obter template para o objetivo
        template = self.prompt_templates[objective]
        
        # Obter formato de resposta para o objetivo
        response_format = self.response_formats[objective]
        
        # Extrair componentes do contexto
        chunks = context.get("compressed_chunks", "")
        product_guidelines = context.get("compressed_product_guidelines", "")
        design_guidelines = context.get("compressed_design_guidelines", "")
        benchmarks = context.get("compressed_benchmarks", "")
        team_objectives = context.get("compressed_team_objectives", "")
        
        # Construir o contexto formatado
        formatted_context = self._format_context(
            chunks,
            product_guidelines,
            design_guidelines,
            benchmarks,
            team_objectives,
            objective
        )
        
        # Substituir placeholders no template
        prompt = template.replace("{query}", query)
        prompt = prompt.replace("{context}", formatted_context)
        prompt = prompt.replace("{response_format}", response_format)
        
        # Construir mensagens para a API
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        
        return {
            "messages": messages,
            "objective": objective,
            "response_format": response_format
        }
    
    def _format_context(
        self,
        chunks: str,
        product_guidelines: str,
        design_guidelines: str,
        benchmarks: str,
        team_objectives: str,
        objective: str
    ) -> str:
        """
        Formata o contexto para o prompt.
        
        Args:
            chunks: Chunks recuperados
            product_guidelines: Diretrizes de produto
            design_guidelines: Diretrizes de design
            benchmarks: Benchmarks
            team_objectives: Objetivos do time
            objective: Objetivo da consulta
            
        Returns:
            Contexto formatado
        """
        formatted_context = ""
        
        # Adicionar chunks recuperados
        if chunks:
            formatted_context += "## Informações Recuperadas\n\n"
            formatted_context += chunks
            formatted_context += "\n\n"
        
        # Adicionar diretrizes de produto
        if product_guidelines:
            formatted_context += "## Diretrizes de Produto\n\n"
            formatted_context += product_guidelines
            formatted_context += "\n\n"
        
        # Adicionar diretrizes de design
        if design_guidelines:
            formatted_context += "## Diretrizes de Design\n\n"
            formatted_context += design_guidelines
            formatted_context += "\n\n"
        
        # Adicionar benchmarks
        if benchmarks:
            formatted_context += "## Benchmarks e Boas Práticas\n\n"
            formatted_context += benchmarks
            formatted_context += "\n\n"
        
        # Adicionar objetivos do time
        if team_objectives:
            formatted_context += "## Objetivos do Time\n\n"
            formatted_context += team_objectives
            formatted_context += "\n\n"
        
        return formatted_context
    
    def _get_informative_template(self) -> str:
        """
        Template para consultas informativas.
        
        Returns:
            Template de prompt
        """
        return """
        Você é um agente especialista em Discovery e Ideação de Produto, atuando como copiloto para designers e PMs.
        
        Seu objetivo é fornecer informações precisas e detalhadas com base no conhecimento disponível, sem especulações.
        
        # Contexto
        
        {context}
        
        # Instruções
        
        Responda à consulta do usuário utilizando APENAS as informações fornecidas no contexto acima.
        
        - Seja factual e objetivo, citando as fontes específicas das informações
        - Não especule além do que está explicitamente mencionado no contexto
        - Se o contexto não contiver informações suficientes, indique claramente o que não está disponível
        - Estruture sua resposta de forma clara e organizada
        - Use linguagem simples e direta
        
        # Formato da Resposta
        
        {response_format}
        
        # Consulta do Usuário
        
        {query}
        """
    
    def _get_hypothesis_template(self) -> str:
        """
        Template para avaliação de hipóteses.
        
        Returns:
            Template de prompt
        """
        return """
        Você é um agente especialista em Discovery e Ideação de Produto, atuando como copiloto para designers e PMs.
        
        Seu objetivo é avaliar criticamente hipóteses de produto, identificando pontos fortes, riscos e alinhamento com diretrizes.
        
        # Contexto
        
        {context}
        
        # Instruções
        
        Avalie a hipótese do usuário considerando:
        
        - Alinhamento com as diretrizes de produto e design
        - Consistência com as informações disponíveis sobre usuários e mercado
        - Potenciais riscos e desafios de implementação
        - Oportunidades de melhoria ou refinamento
        
        Sua análise deve ser:
        - Equilibrada, apresentando tanto pontos positivos quanto negativos
        - Baseada em evidências do contexto, não em opiniões pessoais
        - Construtiva, oferecendo sugestões de melhoria quando apropriado
        - Estruturada de forma clara, com seções bem definidas
        
        # Formato da Resposta
        
        {response_format}
        
        # Hipótese do Usuário
        
        {query}
        """
    
    def _get_benchmark_template(self) -> str:
        """
        Template para consultas de benchmark.
        
        Returns:
            Template de prompt
        """
        return """
        Você é um agente especialista em Discovery e Ideação de Produto, atuando como copiloto para designers e PMs.
        
        Seu objetivo é comparar ideias e soluções com benchmarks e boas práticas do mercado.
        
        # Contexto
        
        {context}
        
        # Instruções
        
        Compare a consulta do usuário com os benchmarks e boas práticas disponíveis:
        
        - Identifique padrões e tendências relevantes no mercado
        - Compare com soluções similares de concorrentes ou referências
        - Avalie o alinhamento com as melhores práticas de design e produto
        - Destaque oportunidades de diferenciação e inovação
        
        Sua análise deve:
        - Ser objetiva e baseada em fatos do contexto
        - Apresentar comparações claras e específicas
        - Oferecer insights acionáveis
        - Considerar tanto aspectos positivos quanto negativos
        
        # Formato da Resposta
        
        {response_format}
        
        # Consulta do Usuário
        
        {query}
        """
    
    def _get_objectives_template(self) -> str:
        """
        Template para consultas relacionadas a objetivos do time.
        
        Returns:
            Template de prompt
        """
        return """
        Você é um agente especialista em Discovery e Ideação de Produto, atuando como copiloto para designers e PMs.
        
        Seu objetivo é avaliar o alinhamento de ideias e propostas com os objetivos estratégicos do time.
        
        # Contexto
        
        {context}
        
        # Instruções
        
        Avalie como a consulta do usuário se alinha aos objetivos do time:
        
        - Identifique conexões diretas e indiretas com os objetivos estratégicos
        - Avalie o potencial impacto nos indicadores-chave de desempenho (KPIs)
        - Considere o alinhamento com a visão de produto e design
        - Destaque oportunidades para fortalecer o alinhamento estratégico
        
        Sua análise deve:
        - Ser específica, relacionando aspectos da consulta a objetivos concretos
        - Quantificar o alinhamento quando possível
        - Sugerir ajustes para melhorar o alinhamento estratégico
        - Considerar tanto benefícios de curto quanto de longo prazo
        
        # Formato da Resposta
        
        {response_format}
        
        # Consulta do Usuário
        
        {query}
        """
    
    def _get_informative_format(self) -> str:
        """
        Formato de resposta para consultas informativas.
        
        Returns:
            Template de formato
        """
        return """
        Estruture sua resposta da seguinte forma:
        
        ## Resumo
        [Breve resumo das principais informações encontradas]
        
        ## Detalhes
        [Informações detalhadas organizadas por tópicos relevantes]
        
        ## Fontes
        [Lista das fontes específicas utilizadas, indicando de onde cada informação foi extraída]
        
        ## Lacunas de Informação
        [Aspectos da consulta que não puderam ser respondidos com o contexto disponível]
        """
    
    def _get_hypothesis_format(self) -> str:
        """
        Formato de resposta para avaliação de hipóteses.
        
        Returns:
            Template de formato
        """
        return """
        Estruture sua resposta da seguinte forma:
        
        ## Resumo da Hipótese
        [Breve resumo da hipótese avaliada]
        
        ## Pontos Fortes
        [Lista dos aspectos positivos e alinhados com diretrizes]
        
        ## Considerações e Riscos
        [Lista de potenciais desafios, riscos ou pontos de atenção]
        
        ## Alinhamento com Diretrizes
        [Análise do alinhamento com diretrizes de produto e design]
        
        ## Recomendações
        [Sugestões concretas para refinar ou melhorar a hipótese]
        """
    
    def _get_benchmark_format(self) -> str:
        """
        Formato de resposta para consultas de benchmark.
        
        Returns:
            Template de formato
        """
        return """
        Estruture sua resposta da seguinte forma:
        
        ## Resumo Comparativo
        [Visão geral da comparação com benchmarks]
        
        ## Análise de Mercado
        [Comparação com soluções similares e tendências relevantes]
        
        ## Alinhamento com Boas Práticas
        [Avaliação do alinhamento com práticas recomendadas]
        
        ## Oportunidades de Diferenciação
        [Identificação de espaços para inovação e diferenciação]
        
        ## Recomendações
        [Sugestões concretas baseadas na análise de benchmark]
        """
    
    def _get_objectives_format(self) -> str:
        """
        Formato de resposta para consultas relacionadas a objetivos.
        
        Returns:
            Template de formato
        """
        return """
        Estruture sua resposta da seguinte forma:
        
        ## Resumo de Alinhamento
        [Visão geral do alinhamento com objetivos do time]
        
        ## Análise por Objetivo
        [Avaliação detalhada do alinhamento com cada objetivo relevante]
        
        ## Impacto Potencial em KPIs
        [Análise do possível impacto nos indicadores-chave]
        
        ## Oportunidades de Fortalecimento
        [Sugestões para aumentar o alinhamento estratégico]
        
        ## Recomendações
        [Próximos passos recomendados com base na análise]
        """


class ResponseProcessor:
    """
    Processa e formata as respostas do LLM.
    
    Características:
    - Validação de conformidade com o formato esperado
    - Extração de metadados e insights
    - Formatação consistente para a interface
    """
    
    def process_response(
        self, 
        response: str, 
        objective: str
    ) -> Dict[str, Any]:
        """
        Processa a resposta do LLM.
        
        Args:
            response: Resposta bruta do LLM
            objective: Objetivo da consulta
            
        Returns:
            Resposta processada com metadados
        """
        # Extrair seções da resposta
        sections = self._extract_sections(response)
        
        # Validar conformidade com o formato esperado
        is_compliant = self._validate_format(sections, objective)
        
        # Extrair insights e metadados
        metadata = self._extract_metadata(sections, objective)
        
        # Formatar para a interface
        formatted_response = self._format_for_interface(sections, objective)
        
        return {
            "response": formatted_response,
            "metadata": metadata,
            "is_compliant": is_compliant,
            "objective": objective,
            "sections": sections
        }
    
    def _extract_sections(self, response: str) -> Dict[str, str]:
        """
        Extrai seções da resposta.
        
        Args:
            response: Resposta do LLM
            
        Returns:
            Dicionário com seções extraídas
        """
        sections = {}
        current_section = "preamble"
        current_content = []
        
        # Dividir por linhas
        lines = response.split("\n")
        
        for line in lines:
            # Verificar se é um cabeçalho de seção
            if line.startswith("## "):
                # Finalizar seção atual
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []
                
                # Iniciar nova seção
                current_section = line[3:].strip().lower().replace(" ", "_")
            else:
                # Adicionar à seção atual
                current_content.append(line)
        
        # Adicionar última seção
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    def _validate_format(
        self, 
        sections: Dict[str, str], 
        objective: str
    ) -> bool:
        """
        Valida se a resposta segue o formato esperado.
        
        Args:
            sections: Seções extraídas
            objective: Objetivo da consulta
            
        Returns:
            True se estiver em conformidade, False caso contrário
        """
        # Definir seções esperadas por objetivo
        expected_sections = {
            "informative": ["resumo", "detalhes", "fontes", "lacunas_de_informação"],
            "hypothesis": ["resumo_da_hipótese", "pontos_fortes", "considerações_e_riscos", 
                          "alinhamento_com_diretrizes", "recomendações"],
            "benchmark": ["resumo_comparativo", "análise_de_mercado", 
                         "alinhamento_com_boas_práticas", "oportunidades_de_diferenciação", 
                         "recomendações"],
            "objectives": ["resumo_de_alinhamento", "análise_por_objetivo", 
                          "impacto_potencial_em_kpis", "oportunidades_de_fortalecimento", 
                          "recomendações"]
        }
        
        # Verificar se todas as seções esperadas estão presentes
        if objective in expected_sections:
            for section in expected_sections[objective]:
                if section not in sections:
                    return False
        
        return True
    
    def _extract_metadata(
        self, 
        sections: Dict[str, str], 
        objective: str
    ) -> Dict[str, Any]:
        """
        Extrai metadados e insights da resposta.
        
        Args:
            sections: Seções extraídas
            objective: Objetivo da consulta
            
        Returns:
            Metadados extraídos
        """
        metadata = {
            "objective": objective,
            "sections_count": len(sections),
            "has_recommendations": "recomendações" in sections,
            "sources_cited": "fontes" in sections,
            "has_gaps": "lacunas_de_informação" in sections
        }
        
        # Extrair metadados específicos por objetivo
        if objective == "hypothesis":
            metadata["has_risks"] = "considerações_e_riscos" in sections
            metadata["has_alignment"] = "alinhamento_com_diretrizes" in sections
        
        elif objective == "benchmark":
            metadata["has_market_analysis"] = "análise_de_mercado" in sections
            metadata["has_differentiation"] = "oportunidades_de_diferenciação" in sections
        
        elif objective == "objectives":
            metadata["has_kpi_impact"] = "impacto_potencial_em_kpis" in sections
            metadata["has_objective_analysis"] = "análise_por_objetivo" in sections
        
        return metadata
    
    def _format_for_interface(
        self, 
        sections: Dict[str, str], 
        objective: str
    ) -> str:
        """
        Formata a resposta para a interface.
        
        Args:
            sections: Seções extraídas
            objective: Objetivo da consulta
            
        Returns:
            Resposta formatada
        """
        # Definir ordem das seções por objetivo
        section_order = {
            "informative": ["resumo", "detalhes", "fontes", "lacunas_de_informação"],
            "hypothesis": ["resumo_da_hipótese", "pontos_fortes", "considerações_e_riscos", 
                          "alinhamento_com_diretrizes", "recomendações"],
            "benchmark": ["resumo_comparativo", "análise_de_mercado", 
                         "alinhamento_com_boas_práticas", "oportunidades_de_diferenciação", 
                         "recomendações"],
            "objectives": ["resumo_de_alinhamento", "análise_por_objetivo", 
                          "impacto_potencial_em_kpis", "oportunidades_de_fortalecimento", 
                          "recomendações"]
        }
        
        # Títulos formatados para as seções
        section_titles = {
            "resumo": "Resumo",
            "detalhes": "Detalhes",
            "fontes": "Fontes",
            "lacunas_de_informação": "Lacunas de Informação",
            "resumo_da_hipótese": "Resumo da Hipótese",
            "pontos_fortes": "Pontos Fortes",
            "considerações_e_riscos": "Considerações e Riscos",
            "alinhamento_com_diretrizes": "Alinhamento com Diretrizes",
            "recomendações": "Recomendações",
            "resumo_comparativo": "Resumo Comparativo",
            "análise_de_mercado": "Análise de Mercado",
            "alinhamento_com_boas_práticas": "Alinhamento com Boas Práticas",
            "oportunidades_de_diferenciação": "Oportunidades de Diferenciação",
            "resumo_de_alinhamento": "Resumo de Alinhamento",
            "análise_por_objetivo": "Análise por Objetivo",
            "impacto_potencial_em_kpis": "Impacto Potencial em KPIs",
            "oportunidades_de_fortalecimento": "Oportunidades de Fortalecimento"
        }
        
        # Construir resposta formatada
        formatted_response = ""
        
        # Adicionar seções na ordem correta
        if objective in section_order:
            for section_key in section_order[objective]:
                if section_key in sections:
                    title = section_titles.get(section_key, section_key.replace("_", " ").title())
                    formatted_response += f"## {title}\n\n"
                    formatted_response += sections[section_key]
                    formatted_response += "\n\n"
        else:
            # Fallback: adicionar todas as seções
            for section_key, content in sections.items():
                if section_key != "preamble":  # Ignorar preâmbulo
                    title = section_titles.get(section_key, section_key.replace("_", " ").title())
                    formatted_response += f"## {title}\n\n"
                    formatted_response += content
                    formatted_response += "\n\n"
        
        return formatted_response.strip()
