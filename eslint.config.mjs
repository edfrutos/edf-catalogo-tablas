import js from "@eslint/js";
import globals from "globals";
import pluginReact from "eslint-plugin-react";

export default [
  js.configs.recommended,
  {
    ignores: [
      "node_modules/",
      ".venv*/",
      "app/static/js/obsolete/",
      "**/*.min.js",
      "**/vendor/",
      "reports/",
      "logs/",
      ".git/",
      "__pycache__/",
      "*.pyc",
      "flask_session/",
      "backups/"
    ]
  },
  {
    files: ["**/*.{js,mjs,cjs,jsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        $: "readonly",
        jQuery: "readonly",
        bootstrap: "readonly",
        pdfjsLib: "readonly",
        marked: "readonly",
        pdfTitle: "readonly",
        currentPDF: "readonly",
        fileName: "readonly",
        ctx: "readonly",
        loadDriveBackups: "readonly",
        backupsPerPage: "writable",
        currentPage: "writable",
        displayBackupsWithPagination: "readonly",
        btn: "writable",
        originalText: "writable",
        downloadBackup: "readonly"
      },
      ecmaVersion: 2021,
      sourceType: "module"
    },
    rules: {
      "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
      "no-undef": "error"
    }
  },
  {
    files: ["**/*.jsx"],
    ...pluginReact.configs.flat.recommended,
    settings: {
      react: {
        version: "detect"
      }
    }
  }
];
