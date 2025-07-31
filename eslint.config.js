// ESLint config for dashboard JS in HTML
export default [
  {
    files: ["eslint.config.js"],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: "module"
    }
  },
  {
    files: ["app/static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: "script",
      globals: {
        // Variables globales del navegador
        window: "readonly",
        document: "readonly",
        console: "readonly",
        setTimeout: "readonly",
        setInterval: "readonly",
        clearTimeout: "readonly",
        clearInterval: "readonly",
        FormData: "readonly",
        confirm: "readonly",
        alert: "readonly",
        fetch: "readonly",
        // jQuery
        $: "readonly",
        jQuery: "readonly",
        // APIs del navegador
        navigator: "readonly",
        // Bootstrap (si se usa)
        bootstrap: "readonly"
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
      "semi": ["error", "always"],
      "quotes": ["error", "double"],
      "no-extra-semi": "error",
      "no-unreachable": "error"
    }
  }
];

