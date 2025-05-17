import React from 'react';
import { VStack, Box, Flex, Text, Icon, Link, useColorModeValue } from '@chakra-ui/react';
import { NavLink as RouterLink } from 'react-router-dom';
import { FiHome, FiMessageSquare, FiActivity, FiSettings } from 'react-icons/fi';

const NavItem = ({ icon, children, to, ...rest }) => {
  return (
    <Link
      as={RouterLink}
      to={to}
      style={{ textDecoration: 'none' }}
      _focus={{ boxShadow: 'none' }}
    >
      {({ isActive }) => (
        <Flex
          align="center"
          p="4"
          mx="4"
          borderRadius="lg"
          role="group"
          cursor="pointer"
          bg={isActive ? 'brand.50' : 'transparent'}
          color={isActive ? 'brand.500' : 'text.primary'}
          _hover={{
            bg: 'brand.50',
            color: 'brand.500',
          }}
          {...rest}
        >
          {icon && (
            <Icon
              mr="4"
              fontSize="16"
              as={icon}
            />
          )}
          {children}
        </Flex>
      )}
    </Link>
  );
};

const Sidebar = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      as="nav"
      pos="fixed"
      top="0"
      left="0"
      zIndex="sticky"
      h="full"
      pb="10"
      overflowX="hidden"
      overflowY="auto"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={borderColor}
      w="60"
      display={{ base: 'none', md: 'block' }}
    >
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        <Text fontSize="2xl" fontWeight="bold" color="brand.500">
          Discovery
        </Text>
      </Flex>
      <VStack spacing={0} align="stretch" mt={6}>
        <NavItem icon={FiHome} to="/">
          Início
        </NavItem>
        <NavItem icon={FiMessageSquare} to="/query">
          Consulta
        </NavItem>
        <NavItem icon={FiActivity} to="/flow">
          Visualização de Fluxo
        </NavItem>
        <NavItem icon={FiSettings} to="/settings">
          Configurações
        </NavItem>
      </VStack>
    </Box>
  );
};

export default Sidebar;
