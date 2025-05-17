// Theme configuration for Chakra UI with Stone colors
import { extendTheme } from '@chakra-ui/react';

const colors = {
  brand: {
    primary: '#30A46C',
    50: '#E6F5EF',
    100: '#C3E5D9',
    200: '#9FD5C3',
    300: '#7BC5AD',
    400: '#57B597',
    500: '#30A46C', // Primary color
    600: '#298357',
    700: '#226243',
    800: '#1B412E',
    900: '#13211A',
  },
  background: {
    primary: '#FFFFFF',
    secondary: '#F0F0F3',
  },
  text: {
    primary: '#1C2024',
    secondary: '#4A5568',
    tertiary: '#718096',
  },
};

const fonts = {
  body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
};

const components = {
  Button: {
    baseStyle: {
      fontWeight: 'medium',
      borderRadius: 'md',
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
        },
      },
      outline: {
        borderColor: 'brand.500',
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
        },
      },
      ghost: {
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
        },
      },
    },
  },
  Input: {
    variants: {
      outline: {
        field: {
          borderColor: 'gray.200',
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
        },
      },
    },
  },
  Textarea: {
    variants: {
      outline: {
        borderColor: 'gray.200',
        _focus: {
          borderColor: 'brand.500',
          boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
        },
      },
    },
  },
};

const theme = extendTheme({
  colors,
  fonts,
  components,
  styles: {
    global: {
      body: {
        bg: 'background.secondary',
        color: 'text.primary',
      },
    },
  },
});

export default theme;
