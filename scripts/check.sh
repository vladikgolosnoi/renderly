#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE_DIR="${ROOT_DIR}/coverage"
mkdir -p "${COVERAGE_DIR}"
rm -rf "${COVERAGE_DIR:?}/"*

echo "[Renderly] Running API linters..."
ruff check "${ROOT_DIR}/apps/api/app"

echo "[Renderly] Running API tests with coverage..."
python -m pytest \
  --cov=app \
  --cov-report=term-missing \
  --cov-report="xml:${COVERAGE_DIR}/api-coverage.xml" \
  "${ROOT_DIR}/apps/api/tests"

echo "[Renderly] Running Web linters..."
pushd "${ROOT_DIR}/apps/web" >/dev/null
npm run lint
echo "[Renderly] Running Web tests with coverage..."
npm run test -- --coverage --coverage.reporter=lcov --coverage.reporter=text
popd >/dev/null

if [ -d "${ROOT_DIR}/apps/web/coverage" ]; then
  cp -R "${ROOT_DIR}/apps/web/coverage" "${COVERAGE_DIR}/web"
fi
