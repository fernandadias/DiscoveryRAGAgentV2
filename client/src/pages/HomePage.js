import React from 'react';
import { Box, Heading, Text, VStack, Button, Image, Flex, SimpleGrid, Icon, useColorModeValue } from '@chakra-ui/react';
import { FiSearch, FiTrendingUp, FiTarget, FiLayers } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';

const FeatureCard = ({ icon, title, description }) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  
  return (
    <Box 
      p={6} 
      bg={cardBg} 
      borderRadius="lg" 
      boxShadow="md" 
      transition="all 0.3s"
      _hover={{ transform: 'translateY(-5px)', boxShadow: 'lg' }}
    >
      <Icon as={icon} w={10} h={10} color="brand.500" mb={4} />
      <Heading size="md" mb={2}>{title}</Heading>
      <Text color="text.secondary">{description}</Text>
    </Box>
  );
};

const HomePage = () => {
  return (
    <VStack spacing={10} align="stretch">
      <Box textAlign="center" py={10}>
        <Heading as="h1" size="2xl" mb={4}>
          Discovery RAG Agent
        </Heading>
        <Text fontSize="xl" maxW="2xl" mx="auto" color="text.secondary">
          Seu copiloto inteligente para ideação e discovery de produto, potencializado por IA avançada e RAG otimizado.
        </Text>
        <Button 
          as={RouterLink}
          to="/query"
          size="lg" 
          colorScheme="brand" 
          mt={8}
          leftIcon={<FiSearch />}
        >
          Iniciar Consulta
        </Button>
      </Box>
      
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={8} px={{ base: 4, md: 0 }}>
        <FeatureCard 
          icon={FiSearch}
          title="Consulta Informativa"
          description="Obtenha informações precisas sobre o que já sabemos com base em pesquisas e dados existentes."
        />
        <FeatureCard 
          icon={FiTrendingUp}
          title="Avaliação de Hipóteses"
          description="Analise hipóteses de produto com base nas diretrizes e conhecimento acumulado."
        />
        <FeatureCard 
          icon={FiLayers}
          title="Benchmark"
          description="Compare soluções com boas práticas de mercado e referências do setor."
        />
        <FeatureCard 
          icon={FiTarget}
          title="Objetivos do Time"
          description="Alinhe ideias com os objetivos estratégicos da equipe e KPIs prioritários."
        />
      </SimpleGrid>
      
      <Box mt={10}>
        <Heading size="lg" mb={6}>Como Funciona</Heading>
        <Flex 
          direction={{ base: 'column', md: 'row' }} 
          align="center" 
          justify="space-between"
          gap={8}
        >
          <Box flex="1">
            <VStack align="start" spacing={4}>
              <Text fontSize="lg">
                O Discovery RAG Agent utiliza tecnologia avançada de Retrieval Augmented Generation (RAG) para fornecer respostas precisas e contextualizadas.
              </Text>
              <Text>
                1. <strong>Consulta Inteligente:</strong> Seu input é analisado para identificar o objetivo da consulta.
              </Text>
              <Text>
                2. <strong>Recuperação Otimizada:</strong> Documentos relevantes são recuperados da base de conhecimento.
              </Text>
              <Text>
                3. <strong>Contexto Dinâmico:</strong> O sistema seleciona e prioriza as informações mais relevantes.
              </Text>
              <Text>
                4. <strong>Resposta Estruturada:</strong> Uma resposta clara e organizada é gerada com base no contexto.
              </Text>
            </VStack>
            <Button 
              as={RouterLink}
              to="/flow"
              variant="outline" 
              colorScheme="brand" 
              mt={6}
            >
              Ver Visualização do Fluxo
            </Button>
          </Box>
          <Box flex="1">
            {/* Placeholder para uma imagem ou diagrama do fluxo */}
            <Box 
              bg="gray.100" 
              borderRadius="md" 
              h="300px" 
              display="flex" 
              alignItems="center" 
              justifyContent="center"
            >
              <Text color="gray.500">Diagrama de Fluxo</Text>
            </Box>
          </Box>
        </Flex>
      </Box>
    </VStack>
  );
};

export default HomePage;
