import sys

import pytest


def run_nexus_tests():
    print("🚀 Iniciando Testes do NEXUS LIFE OS via Pytest...")
    print("-" * 40)

    # Chama o pytest programaticamente apontando para a pasta 'tests'
    exit_code = pytest.main(["tests", "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    run_nexus_tests()
