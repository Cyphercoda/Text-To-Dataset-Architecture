module.exports = {
  // Basic formatting
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  jsxSingleQuote: false,
  trailingComma: 'es5',
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'always',
  
  // Range formatting
  rangeStart: 0,
  rangeEnd: Infinity,
  
  // Parser options
  requirePragma: false,
  insertPragma: false,
  proseWrap: 'preserve',
  
  // HTML formatting
  htmlWhitespaceSensitivity: 'css',
  vueIndentScriptAndStyle: false,
  
  // Line endings
  endOfLine: 'lf',
  
  // Embedded language formatting
  embeddedLanguageFormatting: 'auto',
  
  // Plugin-specific options
  plugins: ['prettier-plugin-tailwindcss'],
  
  // Override options for specific file types
  overrides: [
    {
      files: '*.json',
      options: {
        printWidth: 80,
        parser: 'json',
      },
    },
    {
      files: '*.md',
      options: {
        printWidth: 80,
        proseWrap: 'always',
        parser: 'markdown',
      },
    },
    {
      files: '*.css',
      options: {
        printWidth: 120,
        parser: 'css',
      },
    },
    {
      files: '*.scss',
      options: {
        printWidth: 120,
        parser: 'scss',
      },
    },
    {
      files: '*.yaml',
      options: {
        printWidth: 80,
        tabWidth: 2,
        parser: 'yaml',
      },
    },
    {
      files: '*.yml',
      options: {
        printWidth: 80,
        tabWidth: 2,
        parser: 'yaml',
      },
    },
  ],
};