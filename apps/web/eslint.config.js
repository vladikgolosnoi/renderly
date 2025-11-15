import js from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginVue from "eslint-plugin-vue";

export default tseslint.config(
  {
    ignores: ["dist", "coverage"]
  },
  {
    files: ["**/*.{ts,vue}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended, ...pluginVue.configs["flat/essential"]],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json"
      }
    },
    rules: {
      "vue/multi-word-component-names": "off"
    }
  }
);
